import re
from typing import TYPE_CHECKING, TypeVar

from ctreepo.spec.diff_handler_registry import DiffHandlerRegistry

if TYPE_CHECKING:
    from ctreepo.ctree import CTree


__all__ = ("delete_no_value",)

T = TypeVar("T", bound="CTree")

NO_VALUE = "<<no-value>>"


def _delete_no_value(root: T) -> set[T]:
    to_delete: set[T] = set()
    delete_root = False
    for node in root:
        if len(node) != 0:
            to_delete.update(_delete_no_value(node))
        if NO_VALUE in node.line:
            undo = node.spec.undo + " " + node.line.replace(NO_VALUE, r"\S+")
            to_delete.add(node)
            to_delete.update(n for n in root if re.fullmatch(undo, n.line))

    for node in to_delete:
        delete_root = True
        node.delete()

    if len(root) == 0 and delete_root:
        return {root}
    else:
        return set()


@DiffHandlerRegistry.register("huawei_vrp")
def delete_no_value(diff: T, current: T, target: T) -> None:
    to_delete: set[CTree] = _delete_no_value(diff)
    for node in to_delete:
        node.delete()
