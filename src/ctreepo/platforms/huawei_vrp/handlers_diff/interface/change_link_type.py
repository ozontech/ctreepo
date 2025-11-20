from typing import TYPE_CHECKING, TypeVar

from ctreepo.spec.diff_handler_registry import DiffHandlerRegistry

if TYPE_CHECKING:
    from ctreepo.ctree import CTree

__all__ = ("change_link_type",)

T = TypeVar("T", bound="CTree")


def _process_interface(interface: T) -> None:
    # здесь у нас настройка конкретного интерфейса и есть варианты:
    # - установка нового значения port link-type [trunk|hybrid|access]
    # - удаление undo port link-type (сброс в access)
    #   !!! тут важно с шаблон применять, так как сырые кейсы не учитываю
    # - без изменения link-type

    if "port link-type hybrid" in interface.children:
        link_type = "hybrid"
    elif "port link-type trunk" in interface.children:
        link_type = "trunk"
    elif "port link-type access" in interface.children:
        link_type = "access"
    # вот тут undo из шаблона
    elif "undo port link-type" in interface.children:
        link_type = "access"
    else:
        return

    to_delete: set[T] = set()
    remove_patterns = [
        f"{prf} {ltype}"
        for ltype in ("hybrid", "trunk", "access")
        if ltype != link_type
        for prf in ("undo port", "port")
    ]
    if link_type == "access":
        remove_patterns.append("undo port default vlan ")
    if link_type != "access":
        remove_patterns.append("undo port default vlan ")

    to_delete.update(node for node in interface if node.line.startswith(tuple(remove_patterns)))

    for node in to_delete:
        node.delete()


@DiffHandlerRegistry.register("huawei_vrp")
def change_link_type(diff: T, current: T, target: T) -> None:
    # обработка смены типа интерфейса между trunk, hybrid, access
    for node in diff:
        if not node.line.startswith("interface "):
            continue
        _process_interface(node)
