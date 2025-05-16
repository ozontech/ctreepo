from .ctree import CTree
from .models import Vendor
from .vendors import AristaCT, CiscoCT, HuaweiCT

__all__ = ("ctree_factory", "ctree_class")


def ctree_class(vendor: Vendor) -> type[CTree]:
    vendor_map: dict[Vendor, type[CTree]] = {
        Vendor.ARISTA: AristaCT,
        Vendor.CISCO: CiscoCT,
        Vendor.HUAWEI: HuaweiCT,
    }

    if vendor not in vendor_map:
        raise NotImplementedError(f"unknown vendor {vendor}")
    else:
        return vendor_map[vendor]


def ctree_factory(
    vendor: Vendor,
    line: str = "",
    parent: CTree | None = None,
    tags: list[str] | None = None,
) -> CTree:
    _ct = ctree_class(vendor)
    node = _ct(line=line, parent=parent, tags=tags)
    # тут уже CTree, cast не нужен, но для истории оставлю
    # node = cast(CTree, node)
    return node
