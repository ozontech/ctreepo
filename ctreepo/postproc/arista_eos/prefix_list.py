from ctreepo import settings
from ctreepo.ctree import CTree
from ctreepo.models import Platform
from ctreepo.postproc.postproc import CTreePostProc, register_rule

__all__ = ("AristaEOSPrefixList",)


@register_rule(Platform.ARISTA_EOS)
class AristaEOSPrefixList(CTreePostProc):
    r"""Обработка prefix-list: убрать undo-tag для удаляемых записей и поднять их наверх.

    Пример маски, для формирования undo команды
    f"(ip prefix-list \S+ seq \d+) .* {settings.TEMPLATE_SEPARATOR} no \1"
    """

    @classmethod
    def process(cls, ct: CTree) -> None:
        prefix_lists = [n for n in ct.children.values() if n.line.startswith(("ip prefix-list ", "no ip prefix-list "))]
        if len(prefix_lists) == 0:
            return

        # {pl-name: {"10": node1, "20": node2}}
        to_add: dict[str, dict[str, CTree]] = {}
        to_remove: dict[str, dict[str, CTree]] = {}
        for node in prefix_lists:
            if node.line.startswith("ip prefix-list "):
                _, _, pl_name, _, pl_indx, *_ = node.line.split()
                if pl_name not in to_add:
                    to_add[pl_name] = {}
                to_add[pl_name][pl_indx] = node
            elif node.line.startswith("no ip prefix-list "):
                _, _, _, pl_name, _, pl_indx, *_ = node.line.split()
                if pl_name not in to_remove:
                    to_remove[pl_name] = {}
                to_remove[pl_name][pl_indx] = node
                node.tags = [tag for tag in node.tags if tag != settings.TAG_ON_UNDO]

        for pl_name, pl_entries in to_remove.items():
            if pl_name not in to_add:
                continue
            for seq_id, undo_node in pl_entries.items():
                if seq_id not in to_add[pl_name]:
                    continue
                undo_node.move_before(to_add[pl_name][seq_id])
        ct.rebuild()
