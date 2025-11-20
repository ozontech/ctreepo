from typing import TYPE_CHECKING, TypeVar

from ctreepo.spec.diff_handler_registry import DiffHandlerRegistry

if TYPE_CHECKING:
    from ctreepo.ctree import CTree


__all__ = ("undo_route_policy",)

T = TypeVar("T", bound="CTree")


# это можно сделать через шаблоны, но для примера и тестов остается тут
@DiffHandlerRegistry.register("huawei_vrp")
def undo_route_policy(diff: T, current: T, target: T) -> None:
    rebuild = False
    for child in diff:
        if not child.line.startswith("undo route-policy "):
            continue
        rebuild = True
        if " permit " in child.line:
            child.line = child.line.replace("permit ", "")
        elif " deny " in child.line:
            child.line = child.line.replace("deny ", "")
        else:
            raise ValueError(f"неизвестная настройка {child.line!r}")
    if rebuild:
        diff.rebuild()
