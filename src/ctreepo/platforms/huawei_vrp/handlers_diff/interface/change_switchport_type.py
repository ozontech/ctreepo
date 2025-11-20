from typing import TYPE_CHECKING, TypeVar

from ctreepo.differ import CTreeDiffer
from ctreepo.spec.diff_handler_registry import DiffHandlerRegistry

if TYPE_CHECKING:
    from ctreepo.ctree import CTree

__all__ = ("change_switchport_type",)

T = TypeVar("T", bound="CTree")


@DiffHandlerRegistry.register("huawei_vrp")
def change_switchport_type(diff: T, current: T, target: T) -> None:
    # тут нужно убелиться, что switchport/undo switchport выполняется после всех undo команд
    # добавить другие кейсы, но пока не знаю о них
    def _process(interface_node: T) -> None:
        switchport_node: T | None = None
        last_undo_after_switchport: T | None = None
        for node in interface_node:
            if node.line in ("portswitch", f"{node.spec.undo} portswitch"):
                switchport_node = node
            elif CTreeDiffer.DEL_TAG in node.tags and switchport_node is not None:
                last_undo_after_switchport = node

        if switchport_node is None or last_undo_after_switchport is None:
            return
        switchport_node.move_after(last_undo_after_switchport)

    for node in diff:
        if not node.line.startswith("interface "):
            continue
        _process(node)
