from ctreepo.ctree import CTree
from ctreepo.models import Platform
from ctreepo.postproc.postproc import CTreePostProc, register_rule

__all__ = ("HuaweiVRPLocalUser",)


@register_rule(Platform.HUAWEI_VRP)
class HuaweiVRPLocalUser(CTreePostProc):
    """Удаление настроек пользователя при удалении самого пользователя."""

    @classmethod
    def _process(cls, ct: CTree) -> None:
        undo_nodes = [node for node in ct.children.values() if node.line.startswith("undo local-user ")]
        if len(undo_nodes) == 0:
            return

        users_to_delete: set[str] = set()
        nodes_to_delete: dict[str, list[CTree]] = {}
        for node in undo_nodes:
            _, _, user, *rest = node.line.split()
            if len(rest) == 0 or " password " in node.line:
                users_to_delete.add(user)
            else:
                if user not in nodes_to_delete:
                    nodes_to_delete[user] = []
                nodes_to_delete[user].append(node)

        for user in users_to_delete:
            for node in nodes_to_delete.get(user, []):
                node.delete()

    @classmethod
    def process(cls, ct: CTree) -> None:
        if "aaa" not in ct.children:
            return
        cls._process(ct.children["aaa"])
