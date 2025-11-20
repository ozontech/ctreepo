from typing import TYPE_CHECKING, TypeVar

from ctreepo.spec.diff_handler_registry import DiffHandlerRegistry

if TYPE_CHECKING:
    from ctreepo.ctree import CTree

__all__ = ("undo_interface_order",)

T = TypeVar("T", bound="CTree")


@DiffHandlerRegistry.register("huawei_vrp")
def undo_interface_order(diff: T, current: T, target: T) -> None:
    # undo подынтерфейсов делаем в самом начале, что бы не мешались в остальных операциях
    # попутно вешаем на них тег "pre", что бы можно было разбить на части конфигурацию
    for node in diff:
        if node.line.startswith("undo interface ") and "." in node.line:
            node.tags_add("pre")

    diff.sort("pre")
