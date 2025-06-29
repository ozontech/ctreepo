from ctreepo.ctree import CTree
from ctreepo.models import Platform
from ctreepo.postproc.postproc import CTreePostProc, register_rule

__all__ = ("HuaweiVRPSNMP",)


@register_rule(Platform.HUAWEI_VRP)
class HuaweiVRPSNMP(CTreePostProc):
    @classmethod
    def process(cls, ct: CTree) -> None:
        for node in list(ct.children.values()):
            if node.line.startswith("undo snmp-agent community "):
                node.tags = [tag for tag in node.tags if tag != "post"]
                node.tags.append("pre")
