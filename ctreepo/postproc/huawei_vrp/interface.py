from collections.abc import Iterator

from ctreepo.ctree import CTree
from ctreepo.models import Platform
from ctreepo.postproc.postproc import CTreePostProc, register_rule

__all__ = (
    "HuaweiVRPInterface",
    "HuaweiVRPInterfaceChangeLinkType",
    "HuaweiVRPInterfaceUnrangeVlans",
    "HuaweiVRPInterfaceDRR",
)


def _unrange_vlans(line: str) -> Iterator[int]:
    vlans = line.split()
    pointer = 0
    while pointer < len(vlans):
        start = vlans[pointer]
        end = vlans[pointer]
        pointer += 1
        if pointer < len(vlans) and vlans[pointer] == "to":
            end = vlans[pointer + 1]
            pointer += 2
        for vlan in range(int(start), int(end) + 1):
            yield vlan


def _range_vlans(vlans: list[int]) -> str:
    result: list[str] = []
    pointer = 0
    while pointer < len(vlans):
        if pointer < len(vlans) - 1 and vlans[pointer] + 1 == vlans[pointer + 1]:
            if len(result) == 0 or result[-1] != "to":
                result.append(str(vlans[pointer]))
                result.append("to")
        else:
            result.append(str(vlans[pointer]))
        pointer += 1

    return " ".join(result)


@register_rule(Platform.HUAWEI_VRP)
class HuaweiVRPInterface(CTreePostProc):
    @classmethod
    def _process_interface(cls, ct: CTree) -> None:
        # меняем или нет режим порта l2/l3 (portswitch/undo portswitch), если да, то нужно порядок менять
        # все undo команды вначале, все apply команды в конце
        change_mode = False
        # меняем тип порта на trunk или нет, нужно что бы убедиться, что некоторые команды идут после смены
        secondary_ips: list[CTree] = []
        primary_ip: CTree | None = None

        for node in list(ct.children.values()):
            # если назначается lag, то нам нужно убедиться, что удаление sub-interfaces (если оно есть)
            # идет до настройки main интерфейса. Для этого нам нужно найти все эти ноды и через move_before
            # переместить их перед нашим интерфейсом, а можем добавить тег pre, отфильтровав по которому будем
            # получать prerequisite команды, которые необходимо выполнить перед основным применение патча.
            if node.line.startswith("eth-trunk "):
                # игнорируем mypy так как None никогда в не может быть, и нет смысла на это проверять
                sub_if = [n for n in ct.parent.children.values() if n.line.startswith(f"undo {ct.line}.")]  # type: ignore [union-attr]
                # вариант с pre, но тут завязка на tag идет, похоже на персонализацию, нужно добавить какие-то
                # описания обязательных тегов, типа pre/post
                for n in sub_if:
                    n.remove_tags(["post"])
                    n.tags.append("pre")
                # вариант с move_before для истории оставляю
                # for n in sub_if:
                #     n.tags = ct.tags.copy()
                #     n.move_before(ct)
            # если выводим порт из состава lag, то делаем это в pre, потому что дальнейшая конфигурация может быть
            # с ошибкой из-за того, что порт в составе lag
            elif node.line.startswith("undo eth-trunk "):
                node.remove_tags(["post"])
                node.tags.append("pre")
            # есть кейсы, когда lag переводится l2->l3 и нужно заранее удалить l2-related команды с членов
            elif node.line.startswith("undo storm suppression "):
                node.remove_tags(["post"])
                node.tags.append("pre")
            elif node.line.startswith(("undo mtu",)):
                node.line = " ".join(node.line.split()[:-1])
            # ловим portswitch / undo portswitch - смена режима работы порта l2/l3
            elif node.line.endswith("portswitch"):
                change_mode = True
            # undo qos drr удаляет связанные команды по весам самих очередей, поэтому такие узлы удаляем
            elif node.line.startswith(("port mode ", "undo port mode ")):
                shut = node.__class__("shutdown", ct, node.tags.copy() + ["pre", "skip-dry-run"])
                shut.move_before(node)
                no_shut = node.__class__("undo shutdown", ct, node.tags.copy() + ["post", "skip-dry-run"])
                no_shut.move_after(node)
                node.tags.append("skip-dry-run")
                # игнорируем mypy так как None никогда в не может быть, и нет смысла на это проверять
                node.parent.tags.append("skip-dry-run")  # type: ignore [union-attr]
            # если есть ip и secondary ip, тогда secondary должны идти после
            elif node.line.startswith("ip address ") and node.line.endswith(" sub"):
                secondary_ips.append(node)
            elif node.line.startswith("ip address "):
                primary_ip = node

        if primary_ip is not None:
            for node in secondary_ips:
                node.move_after(primary_ip)

        if change_mode:
            new_order = {
                node.line: node
                for node in ct.children.values()
                if node.line.startswith("undo ") and not node.line.endswith("portswitch")
            }
            new_order.update({node.line: node for node in ct.children.values() if node.line.endswith("portswitch")})
            new_order.update(
                {
                    node.line: node
                    for node in ct.children.values()
                    if not node.line.startswith("undo ") and not node.line.endswith("portswitch")
                },
            )
            ct.children = new_order

        ct.rebuild()

    @classmethod
    def process(cls, ct: CTree) -> None:
        for node in ct.children.values():
            if node.line.startswith("interface "):
                cls._process_interface(node)
            # если удаляется sub-interface, то с него нужно убрать тег post + поднять выше основного
            # интерфейса на случай, если там что-то настраивается
            elif node.line.startswith("undo interface ") and "." in node.line:
                node.remove_tags(["post"])
                if_name = node.line.split()[2].split(".")[0]
                main_if = ct.children.get(f"undo interface {if_name}") or ct.children.get(f"interface {if_name}")
                if main_if is not None:
                    main_if.move_after(node)


@register_rule(Platform.HUAWEI_VRP)
class HuaweiVRPInterfaceUnrangeVlans(CTreePostProc):
    @classmethod
    def _process(cls, ct: CTree) -> None:
        old_allowed_node: CTree | None = None
        new_vlan_list: list[int] = []
        old_vlan_list: list[int] = []
        for node in ct.children.values():
            # vlan 1 идет отдельной командой, просто пропускаем эту настройку
            if node.line == "undo port trunk allow-pass vlan 1":
                continue
            # состав vlan в allow-pass
            elif node.line.startswith("port trunk allow-pass vlan "):
                new_vlan_list = list(_unrange_vlans(node.line.replace("port trunk allow-pass vlan ", "")))
            elif node.line.startswith("undo port trunk allow-pass vlan "):
                old_allowed_node = node
                old_vlan_list = list(_unrange_vlans(node.line.replace("undo port trunk allow-pass vlan ", "")))
            # состав vlan в hybrid
            elif node.line.startswith("port hybrid tagged vlan "):
                new_vlan_list = list(_unrange_vlans(node.line.replace("port hybrid tagged vlan ", "")))
            elif node.line.startswith("undo port hybrid tagged vlan "):
                old_allowed_node = node
                old_vlan_list = list(_unrange_vlans(node.line.replace("undo port hybrid tagged vlan ", "")))

        if old_allowed_node is not None:
            vlans_diff = sorted([vlan for vlan in old_vlan_list if vlan not in new_vlan_list])
            if len(vlans_diff) != 0:
                if old_allowed_node.line.startswith("undo port trunk allow-pass vlan "):
                    old_allowed_node.line = "undo port trunk allow-pass vlan " + _range_vlans(vlans_diff)
                elif old_allowed_node.line.startswith("undo port hybrid tagged vlan "):
                    old_allowed_node.line = "undo port hybrid tagged vlan " + _range_vlans(vlans_diff)
            else:
                old_allowed_node.delete()
        ct.rebuild()

    @classmethod
    def process(cls, ct: CTree) -> None:
        for node in ct.children.values():
            if node.line.startswith("interface "):
                cls._process(node)


@register_rule(Platform.HUAWEI_VRP)
class HuaweiVRPInterfaceChangeLinkType(CTreePostProc):
    @classmethod
    def _undo_link_type(cls, ct: CTree, link_type: str) -> None:
        to_delete: set[CTree] = set()
        undo = ct.children.get(f"undo port link-type {link_type}")
        if undo is not None:
            undo.line = "undo port link-type"
        to_delete.update(
            node
            for node in ct.children.values()
            if node.line.startswith((f"undo port {link_type}", f"port {link_type}"))
        )
        if link_type == "access":
            to_delete.update(node for node in ct.children.values() if node.line.startswith("undo port default vlan "))

        for node in to_delete:
            node.delete()
        ct.rebuild()

    @classmethod
    def _clear(cls, ct: CTree) -> None:
        # когда есть отмена старого режима и назначение нового отдельными командами
        if "undo port link-type hybrid" in ct.children:
            cls._undo_link_type(ct, "hybrid")
        elif "undo port link-type trunk" in ct.children:
            cls._undo_link_type(ct, "trunk")
        elif "undo port link-type access" in ct.children:
            cls._undo_link_type(ct, "access")

        # конга есть отмена старого режима перезаписыванием новым значением
        if "port link-type hybrid" in ct.children:
            cls._undo_link_type(ct, "trunk")
            cls._undo_link_type(ct, "access")
        elif "port link-type trunk" in ct.children:
            cls._undo_link_type(ct, "access")
            cls._undo_link_type(ct, "hybrid")
        elif "port link-type access" in ct.children:
            cls._undo_link_type(ct, "trunk")
            cls._undo_link_type(ct, "hybrid")

    @classmethod
    def _reorder_link_type(cls, ct: CTree, link_type: str) -> None:
        new_type = ct.children[f"port link-type {link_type}"]
        keywords = {
            "access": ("port default vlan",),
            "trunk": ("undo port trunk", "port trunk"),
            "hybrid": ("undo port hybrid", "port hybrid"),
        }
        for node in ct.children.values():
            if node.line.startswith(keywords[link_type]):
                node.move_after(new_type)

    @classmethod
    def _reorder(cls, ct: CTree) -> None:
        # если идет назначение режима, то все связные команды должны идти после него
        if "port link-type hybrid" in ct.children:
            cls._reorder_link_type(ct, "hybrid")
        elif "port link-type trunk" in ct.children:
            cls._reorder_link_type(ct, "trunk")
        elif "port link-type access" in ct.children:
            cls._reorder_link_type(ct, "access")

    @classmethod
    def process(cls, ct: CTree) -> None:
        for node in ct.children.values():
            if node.line.startswith("interface "):
                cls._clear(node)
                cls._reorder(node)


@register_rule(Platform.HUAWEI_VRP)
class HuaweiVRPInterfaceDRR(CTreePostProc):
    @classmethod
    def _process(cls, ct: CTree) -> None:
        to_delete: set[CTree] = set()
        for node in ct.children.values():
            if node.line.startswith("undo qos drr"):
                *_, from_, _, to_ = node.line.split()
                queues = [f"undo qos queue {q} drr" for q in range(int(from_), int(to_) + 1)]
                to_delete.update(n for n in ct.children.values() if n.line.startswith(tuple(queues)))

        for node in to_delete:
            node.delete()

    @classmethod
    def process(cls, ct: CTree) -> None:
        for node in ct.children.values():
            if node.line.startswith("interface "):
                cls._process(node)
