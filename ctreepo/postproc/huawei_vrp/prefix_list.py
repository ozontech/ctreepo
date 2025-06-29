from ctreepo.ctree import CTree
from ctreepo.models import Platform
from ctreepo.postproc.postproc import CTreePostProc, register_rule

__all__ = ("HuaweiVRPPrefixList",)


@register_rule(Platform.HUAWEI_VRP)
class HuaweiVRPPrefixList(CTreePostProc):
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
