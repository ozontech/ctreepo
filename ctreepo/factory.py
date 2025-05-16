from .ctree import CTree
from .models import Platform
from .platforms import AristaEOS, CiscoIOSXE, HuaweiVRP

__all__ = (
    "ctree_factory",
    "ctree_class",
)


def ctree_class(platform: Platform) -> type[CTree]:
    platform_map: dict[Platform, type[CTree]] = {
        Platform.ARISTA_EOS: AristaEOS,
        Platform.CISCO_IOSXE: CiscoIOSXE,
        Platform.HUAWEI_VRP: HuaweiVRP,
    }

    if platform not in platform_map:
        raise NotImplementedError(f"unknown platform {platform}")
    else:
        return platform_map[platform]


def ctree_factory(
    platform: Platform,
    line: str = "",
    parent: CTree | None = None,
    tags: list[str] | None = None,
) -> CTree:
    _ct = ctree_class(platform)
    node = _ct(line=line, parent=parent, tags=tags)
    # тут уже CTree, cast не нужен, но для истории оставлю
    # node = cast(CTree, node)
    return node
