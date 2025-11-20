from pathlib import Path
from typing import Any

from ctreepo.ctree import CTree
from ctreepo.spec import PlatformRegistry

__all__ = ("CTreeSerializer",)


class CTreeSerializer:
    @classmethod
    def _to_dict(cls, node: CTree) -> dict[str, Any]:
        result: dict[str, dict[str, Any]] = {
            node.line: {
                "line": node.line,
                "tags": sorted(node.tags),
                "template": node.template,
                "undo": node.undo,
                "children": {},
            },
        }
        for child in node:
            result[node.line]["children"] |= cls._to_dict(child)
        return result

    # TODO переделать на сохранение в protobuf
    @classmethod
    def to_dict(cls, root: CTree) -> dict[str, Any]:
        result: dict[str, dict[str, Any]] = {}
        for child in root:
            result |= cls._to_dict(child)
        return result

    @classmethod
    def _from_dict(cls, data: dict[str, Any], parent: CTree) -> None:
        node = CTree(
            line=data["line"],
            parent=parent,
            tags=set(data["tags"]),
            template=data["template"],
            undo=data["undo"],
        )
        for child in data.get("children", {}).values():
            cls._from_dict(child, node)

    @classmethod
    def from_dict(cls, platform: str, data: dict[str, Any], *, custom_platform_yaml: Path | None = None) -> CTree:
        spec = PlatformRegistry.get_spec(platform, custom_platform_yaml=custom_platform_yaml)
        root = CTree.create_root(spec)

        for child in data.values():
            cls._from_dict(child, root)

        return root
