from ctreepo.ctree import CTree
from ctreepo.models import Platform
from ctreepo.postproc.postproc import CTreePostProc, register_rule

__all__ = ("AristaEOSInterface",)


@register_rule(Platform.ARISTA_EOS)
class AristaEOSInterface(CTreePostProc):
    """Secondary ip после primary."""

    @classmethod
    def _process_interface(cls, ct: CTree) -> None:
        secondary_ips: list[CTree] = []
        primary_ip: CTree | None = None
        for node in ct.children.values():
            # если есть ip и secondary ip, тогда secondary должны идти после
            if node.line.startswith("ip address ") and node.line.endswith(" secondary"):
                secondary_ips.append(node)
            elif node.line.startswith("ip address "):
                primary_ip = node

        if primary_ip is not None:
            for node in secondary_ips:
                node.move_after(primary_ip)

    @classmethod
    def process(cls, ct: CTree) -> None:
        for node in ct.children.values():
            if node.line.startswith("interface "):
                cls._process_interface(node)
