from collections import deque

from ctreepo.ctree import CTree
from ctreepo.models import Platform
from ctreepo.postproc.postproc import CTreePostProc, register_rule

__all__ = ("AristaEOSBGP",)


#! копия CiscoIOSXEBGP, с поправкой на синтаксис
#! peer-group -> peer group
#! address-family ipv4 vrf LAN -> vrf LAN
@register_rule(Platform.ARISTA_EOS)
class AristaEOSBGP(CTreePostProc):
    """Пост-обработка секции bgp.

    - сортировка: все глобальные команды до AF
    - если пир/группы удаляются, то убрать лишние ноды
    - убрать пустые ноды AF
    """

    @classmethod
    def _delete_peers_per_level(cls, ct: CTree) -> None:
        # на верхнем уровне ищем, что удалять, а удаляем на верхнем + дочерних
        # вызываем для секции bgp и каждой af в отдельности
        peers_to_delete: set[str] = set()
        kept_nodes: set[CTree] = set()

        # ищем, что удалять только на верхнем уровне:
        for node in ct.children.values():
            # no neighbor <peer-group-name> peer-group
            if node.line.startswith("no neighbor ") and node.line.endswith(" peer group"):
                _, _, group, *_ = node.line.split()
                peers_to_delete.add(f"no neighbor {group}")
                kept_nodes.add(node)
            # no neighbor <ip-address> peer-group <peer-group-name>
            elif node.line.startswith("no neighbor ") and " peer group " in node.line:
                _, _, ip, *_, group = node.line.split()
                peers_to_delete.add(f"no neighbor {ip}")
                if f"no neighbor {group} peer group" not in ct.children:
                    kept_nodes.add(node)
            # no neighbor <ip-address> remote-as <remote-as>
            elif (
                node.line.startswith("no neighbor ")
                and " remote-as " in node.line
                and not node.line.startswith(tuple(peers_to_delete))
            ):
                _, _, ip, *_ = node.line.split()
                peers_to_delete.add(f"no neighbor {ip}")
                kept_nodes.add(node)

        # удаляем на верхнем + вложенных уровнях
        flatten_level = deque(ct.children.values())
        indx = 0
        while indx < len(flatten_level):
            flatten_level.extend(flatten_level[indx].children.values())
            indx += 1
        to_delete = [n for n in flatten_level if n.line.startswith(tuple(peers_to_delete)) and n not in kept_nodes]
        for node in to_delete:
            node.delete()

    @classmethod
    def _delete_peers(cls, ct: CTree) -> None:
        # пир/группа определена глобально, тогда удаляется со всех af
        cls._delete_peers_per_level(ct)
        # пир/группа определена внутри af, тогда уделяется только внутри этой af
        for node in ct.children.values():
            if node.line.startswith(("vrf ", "address-family ")) and len(node.children) != 0:
                cls._delete_peers_per_level(node)

    @classmethod
    def _delete_empty_af(cls, ct: CTree) -> None:
        """Удаляем все af ноды, если под ними ничего не осталось."""
        to_delete = [
            n for n in ct.children.values() if n.line.startswith(("vrf ", "address-family ")) and len(n.children) == 0
        ]
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
        bgp_nodes = [node for node in ct.children.values() if node.line.startswith("router bgp ")]
        if len(bgp_nodes) != 1:
            return
        bgp = bgp_nodes[0]

        cls._reorder(bgp)
        cls._delete_peers(bgp)
        cls._delete_empty_af(bgp)

        bgp.rebuild(deep=True)
