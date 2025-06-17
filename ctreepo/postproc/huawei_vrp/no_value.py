import re

from ctreepo import settings
from ctreepo.ctree import CTree
from ctreepo.models import Platform
from ctreepo.postproc.postproc import CTreePostProc, register_rule

__all__ = ("HuaweiVRPNoValue",)


@register_rule(Platform.HUAWEI_VRP)
class HuaweiVRPNoValue(CTreePostProc):
    @classmethod
    def _process(cls, ct: CTree) -> set[CTree]:
        to_delete: set[CTree] = set()
        delete_root = False
        for node in ct.children.values():
            if len(node.children) != 0:
                to_delete.update(cls._process(node))
            # ловим возможные варианты строк с <<no-value>> и удаляем их вместе с undo нодами:
            if settings.NO_VALUE in node.line:
                to_delete.add(node)
                to_delete.update(
                    n
                    for n in ct.children.values()
                    if re.fullmatch(node.undo + " " + node.line.replace(settings.NO_VALUE, r"\S+"), n.line)
                )

        for node in to_delete:
            delete_root = True
            node.delete()

        if len(ct.children) == 0 and delete_root:
            return {ct}
        else:
            return set()

    @classmethod
    def process(cls, ct: CTree) -> None:
        to_delete: set[CTree] = cls._process(ct)
        for node in to_delete:
            node.delete()
