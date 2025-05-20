from typing import Any

from .ctree import CTree
from .factory import ctree_class
from .models import Vendor

__all__ = ("CTreeSerializer",)


class CTreeSerializer:
    @classmethod
    def to_dict(cls, root: CTree) -> dict[str, Any]:
        children: dict[str, dict[str, Any]] = {}
        result = {
            "line": root.line,
            "tags": root.tags,
            "template": root.template,
            "undo_line": root.undo_line,
        }
        for child in root.children.values():
            children |= {child.line: cls.to_dict(child)}
        return result | {"children": children}

    @classmethod
    def from_dict(cls, vendor: Vendor, data: dict[str, Any], parent: CTree | None = None) -> CTree:
        _ct_class = ctree_class(vendor)
        node = _ct_class(
            line=data.get("line", ""),
            tags=data.get("tags", []),
            template=data.get("template", ""),
            parent=parent,
        )
        node.undo_line = data.get("undo_line", "")
        for child in data.get("children", {}).values():
            cls.from_dict(vendor, child, node)
        node.update_node_hash()
        return node
