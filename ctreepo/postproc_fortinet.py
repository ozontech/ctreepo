from collections import deque

from .ctree import CTree
from .models import Vendor
from .postproc import CTreePostProc, register_rule

__all__ = ("FortinetFortiOSUnset",)


@register_rule(Vendor.FORTINET)
class FortinetFortiOSUnset(CTreePostProc):
    @classmethod
    def process(cls, ct: CTree) -> None:
        nodes = deque(ct.children.values())

        while nodes:
            node = nodes.popleft()
            nodes.extendleft(reversed(node.children.values()))
            if node.line.startswith("unset set "):
                node.line = node.line.replace("unset set ", "unset ")

        ct.rebuild(True)
