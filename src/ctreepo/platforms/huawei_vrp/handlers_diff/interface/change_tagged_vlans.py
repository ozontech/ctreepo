from typing import TYPE_CHECKING, TypeVar

from ctreepo.spec.diff_handler_registry import DiffHandlerRegistry
from ctreepo.utils import range_huawei_vlans, unrange_huawei_vlans

if TYPE_CHECKING:
    from ctreepo.ctree import CTree

__all__ = ("change_tagged_vlans",)

T = TypeVar("T", bound="CTree")


@DiffHandlerRegistry.register("huawei_vrp")
def change_tagged_vlans(diff: T, current: T, target: T) -> None:
    # удаляем только нужные vlan, а не всю строку целиком
    # добавлять можно с пересечение, эффекта это не окажет
    def _process(interface_node: T) -> None:
        old_allowed_node: T | None = None
        new_vlans: set[int] = set()
        old_vlans: set[int] = set()
        for node in interface_node:
            # vlan 1 идет отдельной командой, просто пропускаем эту настройку
            if node.line == "undo port trunk allow-pass vlan 1":
                continue
            # состав новых vlans
            elif node.line.startswith(
                (
                    "port trunk allow-pass vlan ",
                    "port hybrid tagged vlan ",
                ),
            ):
                new_vlans = set(unrange_huawei_vlans(node.line.split(" vlan ")[-1]))
            # состав старых vlans
            elif node.line.startswith(
                (
                    "undo port trunk allow-pass vlan ",
                    "undo port hybrid tagged vlan ",
                ),
            ):
                old_allowed_node = node
                old_vlans = set(unrange_huawei_vlans(node.line.split(" vlan ")[-1]))

        if old_allowed_node is not None:
            vlans_diff = old_vlans.difference(new_vlans)
            if vlans_diff:
                cmd = old_allowed_node.line.split(" vlan ")[0]
                old_allowed_node.line = cmd + " vlan " + range_huawei_vlans(sorted(vlans_diff))
            else:
                old_allowed_node.delete()
        interface_node.rebuild()

    for node in diff:
        if not node.line.startswith("interface "):
            continue
        _process(node)
