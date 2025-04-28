import re
from typing import Iterator

from .ctree import CTree
from .models import Vendor
from .postproc import CTreePostProc, register_rule

__all__ = (
    "HuaweiPostProcAAA",
    "HuaweiPostProcBGP",
    "HuaweiPostProcBridgeDomain",
    "HuaweiPostProcInterface",
    "HuaweiPostProcPrefixList",
    "HuaweiPostProcRadius",
    "HuaweiPostProcRoutePolicy",
    "HuaweiPostProcSNMP",
    "HuaweiPostProcTacacs",
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


def _expand_bd_interfaces(line: str) -> Iterator[str]:
    start, _, stop = line.split()
    if start.startswith("Eth-Trunk"):
        prefix = "Eth-Trunk"
        start_id = start[9:]
        stop_id = stop[9:]
    else:
        prefix, start_id = start.rsplit("/", 1)
        prefix += "/"
        _, stop_id = stop.rsplit("/", 1)
    if not start_id.isdigit() or not stop_id.isdigit():
        raise ValueError("wrong interface number")
    for num in range(int(start_id), int(stop_id) + 1):
        yield prefix + str(num)


@register_rule(Vendor.HUAWEI)
class DeleteNoValue(CTreePostProc):
    @classmethod
    def _process(cls, ct: CTree) -> set[CTree]:
        to_delete: set[CTree] = set()
        delete_root = False
        for node in ct.children.values():
            if len(node.children) != 0:
                to_delete.update(cls._process(node))
            # ловим возможные варианты строк с <<no-value>> и удаляем их вместе с undo нодами:
            if "<<no-value>>" in node.line:
                to_delete.add(node)
                to_delete.update(
                    n
                    for n in ct.children.values()
                    if re.fullmatch(node.undo + " " + node.line.replace("<<no-value>>", r"\S+"), n.line)
                )

        for node in to_delete:
            delete_root = True
            node.delete()

        if len(ct.children) == 0 and delete_root:
            return set((ct,))
        else:
            return set()

    @classmethod
    def process(cls, ct: CTree) -> None:
        to_delete: set[CTree] = cls._process(ct)
        for node in to_delete:
            node.delete()


@register_rule(Vendor.HUAWEI)
class HuaweiPostProcAAA(CTreePostProc):
    @classmethod
    def process(cls, ct: CTree) -> None:
        """Пост-обработка секции aaa.

        - Для пустых секций добавляем заглушку, что бы корректно генерировался патч
        - Работаем с пользователями:
            - если пароль пустой в diff, значит он не меняется и этот узел и
                соответствующий ему undo нужно удалить
            - если пароль пустой (не задан в vars) и при этом нет undo узла, значит сейчас
                на устройстве нет пользователя и нужно уделить все узлы с его именем, иначе
                система будет выпадать с ошибкой
            - если в diff есть пароль, значит мы его меняем, и соответствующий undo
                узел нужно удалить (только его)
            - если есть undo пользователя, тогда нужно удалить все ноды с его настройками
                и оставить только undo username
            - правим настройки, типа privilege level и пр, что бы они системой принимались
        - Если после всех манипуляций секция aaa стала пустой (а такое может быть, если diff
            состоял только из узлов с паролями, которые были удалены алгоритмом), тогда и саму
            секцию aaa нужно удалить
        """
        aaa = ct.children.get("aaa")
        if aaa is None:
            return
        lines_to_delete = []
        nodes_to_delete = set()
        for node in aaa.children.values():
            ### шаг 1
            # пустой пароль - значит во входных данных ничего не было и пароль не меняем, поэтому
            # эти узлы, и соответствующие им undo-узлы нужно удалить
            if node.line.endswith("password irreversible-cipher"):
                _, user, *_ = node.line.split()
                lines_to_delete.append(f"local-user {user} password irreversible-cipher")
                undo_line = f"undo local-user {user} password irreversible-cipher"
                lines_to_delete.append(undo_line)
                # проверяем, если ли undo нода, если есть, значит пользователь существует уже в системе
                # если нет - значит нужно удалить все ноды для настройки этого пользователя
                if len([node for node in aaa.children.values() if node.line.startswith(undo_line)]) == 0:
                    lines_to_delete.append(f"local-user {user}")
            ### шаг 2
            # undo-узел и обычный узел с password для одного и того же пользователя,
            # значит мы меняем пароль, поэтому нужно undo-узел удалить
            elif not node.line.startswith("undo ") and " password irreversible-cipher " in node.line:
                _, user, *_ = node.line.split()
                lines_to_delete.append(f"undo local-user {user} password irreversible-cipher")

        nodes_to_delete.update([node for node in aaa.children.values() if node.line.startswith(tuple(lines_to_delete))])
        for node in nodes_to_delete:
            node.delete()
        aaa.rebuild()

        ### шаг 3
        # теперь, если остались undo-узлы с password, значит удаляем пользователя целиком, а значит
        # нужно поменять строку на undo local-user {user}, и удалить остальные узлы с этим пользователем
        lines_to_delete = []
        nodes_to_delete = set()
        for node in aaa.children.values():
            if node.line.startswith("undo ") and " password irreversible-cipher " in node.line:
                _, _, user, *_ = node.line.split()
                lines_to_delete.append(f"undo local-user {user} ")  # с пробелом в конце
                node.line = f"undo local-user {user}"  # а тут без, что бы endswith не захватил эту строку
        nodes_to_delete.update([node for node in aaa.children.values() if node.line.startswith(tuple(lines_to_delete))])
        for node in nodes_to_delete:
            node.delete()
        aaa.rebuild()

        ### шаг 4
        # правим undo узлы, что бы они принимались устройством
        for child in aaa.children.values():
            if not child.line.startswith("undo "):
                continue
            # видимо придется вносить еще или переделывать эту часть, пока только о level и service-type знаю
            if " service-type " in child.line or " level " in child.line:
                child.line = " ".join(child.line.split()[:4])
        aaa.rebuild()
        if len(aaa.children) == 0:
            aaa.delete()


@register_rule(Vendor.HUAWEI)
class HuaweiPostProcBGP(CTreePostProc):
    @classmethod
    def _process_af(cls, ct: CTree) -> None:
        to_delete: set[CTree] = set()
        for node in ct.children.values():
            if node.line.startswith("undo group "):
                group = node.line.split()[2]
                node.line = f"undo group {group}"
                to_delete.update([n for n in ct.children.values() if n.line.startswith(f"undo peer {group}")])
        for node in to_delete:
            node.delete()

    @classmethod
    def process(cls, ct: CTree) -> None:
        # сначала глобальная bgp конфигурация, затем af
        filtered_bgp = [node for node in ct.children.values() if node.line.startswith("bgp")]
        if len(filtered_bgp) != 1:
            return
        else:
            bgp = filtered_bgp[0]
        bgp_global = {node.line: node for node in bgp.children.values() if len(node.children) == 0}
        bgp_af = {node.line: node for node in bgp.children.values() if len(node.children) != 0}
        bgp.children = bgp_global | bgp_af
        for af in bgp_af.values():
            cls._process_af(af)
        bgp.rebuild(deep=True)


#!должно быть выше интерфейсов
@register_rule(Vendor.HUAWEI)
class HuaweiPostProcBridgeDomain(CTreePostProc):
    @classmethod
    def _process_bd(cls, ct: CTree) -> None:
        bd_id = ct.line.split()[-1]
        old_interfaces: set[str] = set()
        new_interfaces: set[str] = set()
        nodes_to_delete: set[CTree] = set()
        for node in ct.children.values():
            # смотрим на состав интерфейсов в bridge-domain, вместо undo/apply целиком списка
            # нужно вычислить разницу и сделать undo/apply только нужных интерфейсов
            if " access-port interface " in node.line:
                _, interfaces = node.line.rsplit(" interface ", maxsplit=1)
                if " to " in interfaces:
                    interface_range = set(_expand_bd_interfaces(interfaces))
                else:
                    interface_range = set((interfaces,))

                if node.line.startswith("undo "):
                    old_interfaces.update(interface_range)
                else:
                    new_interfaces.update(interface_range)
                nodes_to_delete.add(node)

        for node in nodes_to_delete:
            node.delete()

        del_interfaces = sorted(old_interfaces - new_interfaces)
        add_interfaces = sorted(new_interfaces - old_interfaces)
        add_pre_tag = False
        for interface in del_interfaces:
            _ = ct.__class__(f"undo vlan {bd_id} access-port interface {interface}", ct, ct.tags.copy() + ["pre"])
            add_pre_tag = True
        for interface in add_interfaces:
            _ = ct.__class__(f"vlan {bd_id} access-port interface {interface}", ct, ct.tags.copy())
        ct.children = dict(sorted(ct.children.items(), key=lambda item: not item[0].startswith("undo ")))
        if add_pre_tag:
            ct.tags.append("pre")

    @classmethod
    def process(cls, ct: CTree) -> None:
        for child in ct.children.values():
            if not child.line.startswith("bridge-domain "):
                continue
            _, bd_id, *_ = child.line.split()
            if not bd_id.isdigit():
                continue
            cls._process_bd(child)


@register_rule(Vendor.HUAWEI)
class HuaweiPostProcInterfaceChangeLinkType(CTreePostProc):
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


@register_rule(Vendor.HUAWEI)
class HuaweiPostProcInterfaceUnrangeVlans(CTreePostProc):
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


@register_rule(Vendor.HUAWEI)
class HuaweiPostProcInterfaceQoSdrr(CTreePostProc):
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


@register_rule(Vendor.HUAWEI)
class HuaweiPostProcInterface(CTreePostProc):
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
                }
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


@register_rule(Vendor.HUAWEI)
class HuaweiPostProcPrefixList(CTreePostProc):
    @classmethod
    def process(cls, ct: CTree) -> None:
        pl_statements: dict[str, list[str]] = {}
        to_delete: list[CTree] = []
        for child in ct.children.values():
            if child.line.startswith("ip ip-prefix "):
                _, _, pl_name, _, pl_indx, *_ = child.line.split()
                if pl_name not in pl_statements:
                    pl_statements[pl_name] = []
                pl_statements[pl_name].append(pl_indx)
        for child in ct.children.values():
            if child.line.startswith("undo ip ip-prefix "):
                _, _, _, pl_name, _, pl_indx, *_ = child.line.split()
                if pl_indx in pl_statements.get(pl_name, []):
                    to_delete.append(child)
                else:
                    child.line = f"undo ip ip-prefix {pl_name} index {pl_indx}"
        for node in to_delete:
            node.delete()
        ct.rebuild()


@register_rule(Vendor.HUAWEI)
class HuaweiPostProcRoutePolicy(CTreePostProc):
    @classmethod
    def process(cls, ct: CTree) -> None:
        for child in ct.children.values():
            if child.line.startswith("undo route-policy "):
                child.line = child.line.replace("permit ", "")
                child.line = child.line.replace("deny ", "")
        ct.rebuild()


@register_rule(Vendor.HUAWEI)
class HuaweiPostProcRadius(CTreePostProc):
    @classmethod
    def _process_radius_section(cls, radius: CTree) -> None:
        to_delete: set[CTree] = set()
        for node in radius.children.values():
            # пустой пароль - значит во входных данных ничего не было и пароль не меняем, поэтому
            # этот узел, и соответствующий ему undo-узел нужно удалить
            if node.line.endswith("shared-key cipher"):
                to_delete.add(node)
                to_delete.update([n for n in radius.children.values() if n.line.startswith(f"undo {node.line}")])
        for node in to_delete:
            node.delete()

        # если остались undo-узлы с password, значит их нужно поменять,
        # отрезав пароль, иначе система не примет команду
        to_delete = set()
        for node in radius.children.values():
            if node.line.startswith("undo ") and " shared-key cipher " in node.line:
                node.line = " ".join(node.line.split()[:-2])

        # в конце проверяем, если потомков не осталось, то удаляем корневой узел
        radius.rebuild()
        if len(radius.children) == 0:
            radius.delete()

    @classmethod
    def process(cls, ct: CTree) -> None:
        radius_sections = [n for n in ct.children.values() if n.line.startswith("radius-server template ")]
        for section in radius_sections:
            cls._process_radius_section(section)


@register_rule(Vendor.HUAWEI)
class HuaweiPostProcTacacs(CTreePostProc):
    @classmethod
    def process(cls, ct: CTree) -> None:
        filtered_tacacs = [
            node
            for node in ct.children.values()
            if node.line.startswith(("hwtacacs-server template", "hwtacacs server template"))
        ]
        if len(filtered_tacacs) != 1:
            return
        else:
            tacacs = filtered_tacacs[0]

        lines_to_delete = []
        nodes_to_delete = set()
        for node in tacacs.children.values():
            ### шаг 1
            # пустой пароль - значит во входных данных ничего не было и пароль не меняем, поэтому
            # этот узел, и соответствующий ему undo-узел нужно удалить
            # ("shared-key cipher  secondary", "shared-key cipher  third")
            if node.line.endswith("shared-key cipher"):
                lines_to_delete.append(node.line)
                lines_to_delete.append(f"undo {node.line}")
            ### шаг 2
            # undo-узел и обычный узел с password, значит мы меняем пароль, нужно undo-узел удалить
            elif not node.line.startswith("undo ") and " shared-key cipher " in node.line:
                lines_to_delete.append(f"undo {node.line}")
        nodes_to_delete.update(
            [node for node in tacacs.children.values() if node.line.startswith(tuple(lines_to_delete))]
        )
        for node in nodes_to_delete:
            node.delete()
        tacacs.rebuild()

        ### шаг 3
        # теперь, если остались undo-узлы с password, значит их нужно поменять,
        # отрезав пароль, иначе система не примет команду
        lines_to_delete = []
        nodes_to_delete = set()
        for node in tacacs.children.values():
            if node.line.startswith("undo ") and " shared-key cipher " in node.line:
                lines_to_delete.append(" ".join(node.line.split()[:-2]))
        nodes_to_delete.update(
            [node for node in tacacs.children.values() if node.line.startswith(tuple(lines_to_delete))]
        )
        for node in nodes_to_delete:
            node.delete()
        tacacs.rebuild()
        if len(tacacs.children) == 0:
            tacacs.delete()


@register_rule(Vendor.HUAWEI)
class HuaweiPostProcSNMP(CTreePostProc):
    @classmethod
    def process(cls, ct: CTree) -> None:
        nodes_to_delete: set[CTree] = set()
        for node in list(ct.children.values()):
            # если строка не имеет отношение к snmp
            if not node.line.startswith(("undo snmp-agent", "snmp-agent")):
                continue
            # если нет нового community, то удаляем узел
            if node.line.startswith("snmp-agent community ") and "cipher  " in node.line:
                nodes_to_delete.add(node)
                prefix, postfix = node.line.split("cipher  ")
                nodes_to_delete.update(
                    [
                        n
                        for n in ct.children.values()
                        if n.line.startswith(f"undo {prefix}") and n.line.endswith(postfix)
                    ]
                )
            elif node.line.startswith("snmp-agent community ") and node.line.endswith("cipher"):
                nodes_to_delete.add(node)
                nodes_to_delete.update(
                    [
                        n
                        for n in ct.children.values()
                        if n.line.startswith(f"undo {node.line}") and len(n.line.split()) == 6
                    ]
                )
            # если удаляем community, тогда в начало это переносим, иначе могут быть конфликты
            elif node.line.startswith("undo snmp-agent community "):
                node.tags = [tag for tag in node.tags if tag != "post"]
                node.tags.append("pre")
        for node in nodes_to_delete:
            node.delete()
