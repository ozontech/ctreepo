from typing import Any

from ctreepo.ctree import CTree
from ctreepo.factory import CTreeFactory
from ctreepo.models import Platform

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
    def from_dict(cls, platform: Platform, data: dict[str, Any], parent: CTree | None = None) -> CTree:
        _ct_class = CTreeFactory._PLATFORM_MAP[platform]
        node = _ct_class(
            line=data.get("line", ""),
            tags=data.get("tags", []),
            template=data.get("template", ""),
            parent=parent,
        )
        node.undo_line = data.get("undo_line", "")
        for child in data.get("children", {}).values():
            cls.from_dict(platform, child, node)
        node.update_node_hash()
        return node
