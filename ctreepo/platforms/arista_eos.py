from ctreepo.ctree import CTree
from ctreepo.models import Platform

__all__ = ("AristaEOS",)


class AristaEOS(CTree):
    platform = Platform.ARISTA_EOS
    spaces = "   "
    undo = "no"
    section_exit = "exit"
    section_separator = "!"
    sections_require_exit = [
        r"route-map \S+ (?:deny|permit) \d+",
        r"vlan \d+.*",
    ]
    sections_without_exit = []
    junk_lines = [
        r"\s*!.*",
        r"end",
    ]
    mask_patterns = [
        r".*(?:password|secret)(?: sha512)? (\S+)",
        r".*(?:key|md5)(?: 7)? (\S+)",
    ]
