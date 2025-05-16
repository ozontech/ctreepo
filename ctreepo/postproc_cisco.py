from .ctree import CTree
from .models import Vendor
from .postproc import CTreePostProc, register_rule

__all__ = ("CiscoPostProcBGP",)


@register_rule(Vendor.CISCO)
class CiscoPostProcBGP(CTreePostProc):
    @classmethod
    def _delete_nodes(cls, ct: CTree, lines_to_delete: set[str]) -> None:
        nodes_to_delete: list[CTree] = []
        for node in ct.children.values():
            if len(node.children) != 0:
                cls._delete_nodes(node, lines_to_delete)
                if len(node.children) == 0:
                    nodes_to_delete.append(node)
            else:
                if node.line.startswith(tuple(lines_to_delete)) and not node.line.endswith(" peer-group"):
                    nodes_to_delete.append(node)
        for node in nodes_to_delete:
            node.delete()

    @classmethod
    def process(cls, ct: CTree) -> None:
        """Пост-обработка секции bgp для Cisco.

        - если есть команда "no neighbor <GROUP-NAME> peer-group", значит группы в целевой
            конфигурации вообще нет, и нужно все команды "no neighbor <GROUP-NAME> <some-options>"
            удалить, а оставить только одну "no neighbor <GROUP-NAME> peer-group", устройство
            остальное само вычистит

        Args:
            ct (CTree): дерево, для модификации
        """
        # найдем секцию bgp, если она есть
        bgp_nodes = [node for node in ct.children.values() if node.line.startswith("router bgp ")]
        if len(bgp_nodes) != 1:
            return
        bgp = bgp_nodes[0]

        # пересортируем секцию bgp, что бы все глобальные bgp команды шли перед настройками af
        bgp_global = {node.line: node for node in bgp.children.values() if len(node.children) == 0}
        bgp_af = {node.line: node for node in bgp.children.values() if len(node.children) != 0}
        bgp.children = bgp_global | bgp_af

        # теперь нужно сформировать признаки, как найти команды, которые будем удалять из diff'а
        lines_to_delete = set()
        for node in bgp.children.values():
            # можно через re поймать строку, но выбрал такой вариант
            if node.line.startswith("no neighbor ") and node.line.endswith(" peer-group"):
                # no neighbor <GROUP-NAME> peer-group
                _, _, group_name, _ = node.line.split()
                lines_to_delete.add(f"no neighbor {group_name}")

        # после получения признаков, удаляем ноды, которые им соответствуют
        cls._delete_nodes(bgp, lines_to_delete)
