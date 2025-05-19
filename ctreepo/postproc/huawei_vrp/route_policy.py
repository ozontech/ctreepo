from ctreepo.ctree import CTree
from ctreepo.models import Platform
from ctreepo.postproc.postproc import CTreePostProc, register_rule

__all__ = ("HuaweiVRPRoutePolicy",)


@register_rule(Platform.HUAWEI_VRP)
class HuaweiVRPRoutePolicy(CTreePostProc):
    @classmethod
    def process(cls, ct: CTree) -> None:
        for child in ct.children.values():
            if child.line.startswith("undo route-policy "):
                child.line = child.line.replace("permit ", "")
                child.line = child.line.replace("deny ", "")
        ct.rebuild()
