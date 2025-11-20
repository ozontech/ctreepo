from typing import TYPE_CHECKING, TypeVar

from ctreepo.spec.diff_handler_registry import DiffHandlerRegistry

if TYPE_CHECKING:
    from ctreepo.ctree import CTree

__all__ = ("secondary_after_primary_ip",)

T = TypeVar("T", bound="CTree")


@DiffHandlerRegistry.register("huawei_vrp")
def secondary_after_primary_ip(diff: T, current: T, target: T) -> None:
    # убедиться, что если есть настройка secondary и primary ip, то secondary всегда будут
    # после primary
    def _process_interface(node: T) -> None:
        secondary_ips: list[T] = []
        primary_ip: T | None = None
        for child in node:
            if child.line.startswith("ip address ") and child.line.endswith(" sub"):
                # добавляем только если еще не встретили primary, иначе наша строка
                # идет после и условие и так выполняется
                if primary_ip is None:
                    secondary_ips.append(child)
            elif child.line.startswith("ip address "):
                # если встретили primary, а secondary_ip все еще пуст, то дальше смысла
                # нет смотреть, условие и так выполняется
                if len(secondary_ips) == 0:
                    return
                primary_ip = child
        if primary_ip is None:
            return
        for child in secondary_ips:
            child.move_after(primary_ip)

    for node in diff:
        if node.line.startswith("interface "):
            _process_interface(node)
