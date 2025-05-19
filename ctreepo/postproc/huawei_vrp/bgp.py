from collections import deque

from ctreepo.ctree import CTree
from ctreepo.models import Platform
from ctreepo.postproc.postproc import CTreePostProc, register_rule

__all__ = ("HuaweiVRPBGP",)


@register_rule(Platform.HUAWEI_VRP)
class HuaweiVRPBGP(CTreePostProc):
    """Пост-обработка секции bgp.

    - сортировка: все глобальные команды до AF
    - если пир/группы удаляются, то убрать лишние ноды
    - убрать пустые ноды AF
    """

    AF = (
        "ipv4-family ",
        "ipv6-family ",
        "l2vpn-family ",
    )

    @classmethod
    def _delete_peers_per_level(cls, ct: CTree) -> None:
        print(f"{ct=}")
        # на верхнем уровне ищем, что удалять, а удаляем на верхнем + дочерних
        # вызываем для секции bgp и каждой af в отдельности
        peers_to_delete: set[str] = set()
        kept_node: set[CTree] = set()

        # ищем, что удалять только на верхнем уровне:
        for node in ct.children.values():
            # undo group PEER-GROUP <internal/external>
            if node.line.startswith("undo group "):
                _, _, group, *_ = node.line.split()
                node.line = f"undo group {group}"
                peers_to_delete.add(group)
                kept_node.add(node)
            # undo peer <IP> as-number <AS>
            elif node.line.startswith("undo peer") and " as-number" in node.line:
                _, _, ip, *_ = node.line.split()
                node.line = f"undo peer {ip}"
                peers_to_delete.add(ip)
                kept_node.add(node)

        print(f"{peers_to_delete=}")
        # удаляем на верхнем + вложенных уровнях
        flatten_level = deque(ct.children.values())
        indx = 0
        while indx < len(flatten_level):
            flatten_level.extend(flatten_level[indx].children.values())
            indx += 1

        to_delete: set[CTree] = set()
        for peer in peers_to_delete:
            to_delete.update(n for n in flatten_level if peer in n.line and n not in kept_node)
        for node in to_delete:
            node.delete()

    @classmethod
    def _delete_peers(cls, ct: CTree) -> None:
        # пир/группа определена глобально, тогда удаляется со всех af
        cls._delete_peers_per_level(ct)
        # пир/группа определена внутри af, тогда уделяется только внутри этой af
        for node in ct.children.values():
            if node.line.startswith(cls.AF) and len(node.children) != 0:
                cls._delete_peers_per_level(node)

    @classmethod
    def _delete_empty_af(cls, ct: CTree) -> None:
        """Удаляем все af ноды, если под ними ничего не осталось."""
        to_delete = [n for n in ct.children.values() if n.line.startswith(cls.AF) and len(n.children) == 0]
        for node in to_delete:
            node.delete()

    @classmethod
    def _reorder(cls, ct: CTree) -> None:
        """Все глобальные bgp команды идут перед настройками af."""
        bgp_global = {node.line: node for node in ct.children.values() if len(node.children) == 0}
        bgp_af = {node.line: node for node in ct.children.values() if len(node.children) != 0}
        ct.children = bgp_global | bgp_af

    @classmethod
    def process(cls, ct: CTree) -> None:
        bgp_nodes = [node for node in ct.children.values() if node.line.startswith("bgp ")]
        if len(bgp_nodes) != 1:
            return
        bgp = bgp_nodes[0]

        cls._reorder(bgp)
        cls._delete_peers(bgp)
        cls._delete_empty_af(bgp)

        bgp.rebuild(deep=True)
