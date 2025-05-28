from .ctree import CTree
from .models import Platform
from .platforms import AristaEOS, CiscoIOSXE, HuaweiVRP

__all__ = ("CTreeFactory",)


class CTreeFactory:
    _PLATFORM_MAP: dict[Platform, type[CTree]] = {
        Platform.ARISTA_EOS: AristaEOS,
        Platform.CISCO_IOSXE: CiscoIOSXE,
        Platform.HUAWEI_VRP: HuaweiVRP,
    }

    @classmethod
    def create(
        cls,
        platform: Platform,
        line: str = "",
        parent: CTree | None = None,
        tags: list[str] | None = None,
    ) -> CTree:
        if platform not in cls._PLATFORM_MAP:
            raise ValueError(f"unknown platform '{platform}'")
        _ct = cls._PLATFORM_MAP[platform]
        node = _ct(line=line, parent=parent, tags=tags)
        return node
