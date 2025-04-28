from .ctree import CTree
from .models import Vendor
from .postproc import CTreePostProc, register_rule

__all__ = (
    "AristaPostProcAAA",
    "AristaPostProcBGP",
    "AristaPostProcEnable",
    "AristaPostProcPrefixList",
    "AristaPostProcSNMP",
    "AristaPostProcTacacsKey",
    "AristaPostProcUsers",
)


@register_rule(Vendor.ARISTA)
class AristaPostProcAAA(CTreePostProc):
    @classmethod
    def process(cls, ct: CTree) -> None:
        lines_to_check = (
            "aaa authentication login default",
            "aaa authentication login console",
            "aaa authentication enable default",
        )
        lines_to_delete = [
            f"no {' '.join(node.line.split()[:4])}"
            for node in ct.children.values()
            if node.line.startswith(lines_to_check)
        ]
        nodes_to_delete = set([node for node in ct.children.values() if node.line.startswith(tuple(lines_to_delete))])
        for node in nodes_to_delete:
            node.delete()
        ct.rebuild()


@register_rule(Vendor.ARISTA)
class AristaPostProcBGP(CTreePostProc):
    @classmethod
    def process(cls, ct: CTree) -> None:
        def _delete_nodes(ct: CTree) -> None:
            nodes_to_delete: list[CTree] = []
            for node in ct.children.values():
                if len(node.children) != 0:
                    _delete_nodes(node)
                    if len(node.children) == 0:
                        nodes_to_delete.append(node)
                else:
                    if node.line.startswith(tuple(lines_to_delete)) and not node.line.endswith(" peer group"):
                        nodes_to_delete.append(node)
            for node in nodes_to_delete:
                node.delete()

            ct.rebuild()

        bgp_nodes = [node for node in ct.children.values() if node.line.startswith("router bgp ")]
        if len(bgp_nodes) != 1:
            return
        else:
            bgp = bgp_nodes[0]
        bgp_global = {node.line: node for node in bgp.children.values() if len(node.children) == 0}
        bgp_af = {node.line: node for node in bgp.children.values() if len(node.children) != 0}
        bgp.children = bgp_global | bgp_af
        bgp.rebuild()

        lines_to_delete = set()
        for node in bgp.children.values():
            if node.line.startswith("no neighbor ") and node.line.endswith(" peer group"):
                # no neighbor GROUP-PEER peer group
                _, _, peer_name, _, _ = node.line.split()
                lines_to_delete.add(f"no neighbor {peer_name}")
        _delete_nodes(bgp)
        bgp.rebuild()


@register_rule(Vendor.ARISTA)
class AristaPostProcEnable(CTreePostProc):
    @classmethod
    def process(cls, ct: CTree) -> None:
        nodes_to_delete: set[CTree] = set()
        for node in ct.children.values():
            if node.line.startswith("enable password"):
                if node.line == "enable password":
                    nodes_to_delete.add(node)
                nodes_to_delete.update([n for n in ct.children.values() if n.line.startswith("no enable password")])
        for node in nodes_to_delete:
            node.delete()
        ct.rebuild()


@register_rule(Vendor.ARISTA)
class AristaPostProcPrefixList(CTreePostProc):
    @classmethod
    def process(cls, ct: CTree) -> None:
        pl_statements: dict[str, list[str]] = {}
        to_change: list[CTree] = []
        # в pl_statements записываем pl и seq, которые будем настраивать
        for child in ct.children.values():
            if child.line.startswith("ip prefix-list "):
                _, _, pl_name, _, pl_indx, *_ = child.line.split()
                if pl_name not in pl_statements:
                    pl_statements[pl_name] = []
                pl_statements[pl_name].append(pl_indx)

        # проверяем, если no опция для комбинации pl+seq есть в pl_statements
        # значит мы меняем запись, если нет - значит просто удаляем
        for child in ct.children.values():
            if child.line.startswith("no ip prefix-list "):
                _, _, _, pl_name, _, pl_indx, *_ = child.line.split()
                if pl_indx in pl_statements.get(pl_name, []):
                    to_change.append(child)
                # и если просто удаляем, тогда меняем line у узла на тот формат, который принимается устройством
                else:
                    child.line = f"no ip prefix-list {pl_name} seq {pl_indx}"

        # те записи, которые меняем, нужно удалить перед тем, как настраивать
        clear_before_configure: dict[str, CTree] = {}
        for node in to_change:
            _, _, _, pl_name, _, pl_indx, *_ = node.line.split()
            new_node = ct.__class__(
                line=f"no ip prefix-list {pl_name} seq {pl_indx}",
                parent=node.parent,
                tags=[tag for tag in node.tags if tag != "post"],
            )
            clear_before_configure |= {new_node.line: new_node}
            node.delete()

        ct.children = clear_before_configure | ct.children
        ct.rebuild()


@register_rule(Vendor.ARISTA)
class AristaPostProcTacacsKey(CTreePostProc):
    @classmethod
    def process(cls, ct: CTree) -> None:
        # если строка без пароля то удаляем этот и undo узлы
        if "tacacs-server key" in ct.children:
            lines_to_delete = ["tacacs-server key", "no tacacs-server key"]
        # если есть новый пароль, то удаляем только undo узел
        elif len([node for node in ct.children.values() if node.line.startswith("tacacs-server key ")]) == 1:
            lines_to_delete = ["no tacacs-server key"]
        else:
            lines_to_delete = []

        nodes_to_delete = set([node for node in ct.children.values() if node.line.startswith(tuple(lines_to_delete))])
        for node in nodes_to_delete:
            node.delete()
        ct.rebuild()


@register_rule(Vendor.ARISTA)
class AristaPostProcUsers(CTreePostProc):
    @classmethod
    def process(cls, ct: CTree) -> None:
        lines_to_delete = []
        nodes_to_delete = set()
        for node in ct.children.values():
            if not node.line.startswith("username "):
                continue
            ### шаг 1
            # пустой пароль - значит во входных данных ничего не было и пароль не меняем, поэтому
            # эти узлы, и соответствующие им no-узлы нужно удалить
            if node.line.endswith("privilege 15 role network-admin secret"):
                _, user, *_ = node.line.split()
                lines_to_delete.append(f"username {user} privilege 15 role network-admin secret")
                lines_to_delete.append(f"no username {user} privilege 15 role network-admin secret sha512 ")
            ### шаг 2
            # обычный узел с password, значит мы меняем пароль, поэтому нужно no-узел удалить
            elif not node.line.startswith("no ") and " privilege 15 role network-admin secret " in node.line:
                _, user, *_ = node.line.split()
                lines_to_delete.append(f"no username {user} privilege 15 role network-admin secret sha512 ")
        nodes_to_delete.update([node for node in ct.children.values() if node.line.startswith(tuple(lines_to_delete))])
        for node in nodes_to_delete:
            node.delete()
        ct.rebuild()

        ### шаг 3
        # теперь, если остались no-узлы с password, значит удаляем пользователя целиком, а значит
        # нужно поменять строку на no username {user}
        lines_to_delete = []
        nodes_to_delete = set()
        for node in ct.children.values():
            if node.line.startswith("no ") and " privilege 15 role network-admin secret sha512 " in node.line:
                _, _, user, *_ = node.line.split()
                lines_to_delete.append(f"no username {user} ")  # с пробелом в конце
                node.line = f"no username {user}"  # а тут без, что бы endswith не захватил эту строку
        nodes_to_delete.update([node for node in ct.children.values() if node.line.startswith(tuple(lines_to_delete))])
        for node in nodes_to_delete:
            node.delete()
        ct.rebuild()


@register_rule(Vendor.ARISTA)
class HuaweiPostProcInterface(CTreePostProc):
    @classmethod
    def _process_interface(cls, ct: CTree) -> None:
        secondary_ips: list[CTree] = []
        primary_ip: CTree | None = None
        for node in list(ct.children.values()):
            # если есть ip и secondary ip, тогда secondary должны идти после
            if node.line.startswith("ip address ") and node.line.endswith(" secondary"):
                secondary_ips.append(node)
            elif node.line.startswith("ip address "):
                primary_ip = node

        if primary_ip is not None:
            for node in secondary_ips:
                node.move_after(primary_ip)

    @classmethod
    def process(cls, ct: CTree) -> None:
        for node in ct.children.values():
            if node.line.startswith("interface "):
                cls._process_interface(node)


@register_rule(Vendor.ARISTA)
class AristaPostProcSNMP(CTreePostProc):
    @classmethod
    def process(cls, ct: CTree) -> None:
        nodes_to_delete: set[CTree] = set()
        for node in list(ct.children.values()):
            # если строка не имеет отношение к snmp
            if not node.line.startswith(("no snmp-server ", "snmp-server ")):
                continue
            # если нет нового community, то удаляем узел
            if node.line.startswith("snmp-server community  "):
                nodes_to_delete.add(node)
                prefix, postfix = node.line.split("  ")
                nodes_to_delete.update(
                    [n for n in ct.children.values() if n.line.startswith(f"no {prefix}") and n.line.endswith(postfix)]
                )
            # если удаляем community, тогда в начало это переносим, иначе могут быть конфликты
            elif node.line.startswith("no snmp-server community "):
                node.tags = [tag for tag in node.tags if tag != "post"]
                node.tags.append("pre")
        for node in nodes_to_delete:
            node.delete()
