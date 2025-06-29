from collections.abc import Iterator

from ctreepo.ctree import CTree
from ctreepo.models import Platform
from ctreepo.postproc.postproc import CTreePostProc, register_rule

__all__ = ("HuaweiVRPBridgeDomain",)


def _expand_bd_interfaces(line: str) -> Iterator[str]:
    start, _, stop = line.split()
    if start.startswith("Eth-Trunk"):
        prefix = "Eth-Trunk"
        start_id = start[9:]
        stop_id = stop[9:]
    else:
        prefix, start_id = start.rsplit("/", 1)
        prefix += "/"
        _, stop_id = stop.rsplit("/", 1)
    if not start_id.isdigit() or not stop_id.isdigit():
        raise ValueError("wrong interface number")
    for num in range(int(start_id), int(stop_id) + 1):
        yield prefix + str(num)


@register_rule(Platform.HUAWEI_VRP)
class HuaweiVRPBridgeDomain(CTreePostProc):
    @classmethod
    def _process_bd(cls, ct: CTree) -> None:
        bd_id = ct.line.split()[-1]
        old_interfaces: set[str] = set()
        new_interfaces: set[str] = set()
        nodes_to_delete: set[CTree] = set()
        for node in ct.children.values():
            # смотрим на состав интерфейсов в bridge-domain, вместо undo/apply целиком списка
            # нужно вычислить разницу и сделать undo/apply только нужных интерфейсов
            if " access-port interface " in node.line:
                _, interfaces = node.line.rsplit(" interface ", maxsplit=1)
                if " to " in interfaces:
                    interface_range = set(_expand_bd_interfaces(interfaces))
                else:
                    interface_range = {interfaces}

                if node.line.startswith("undo "):
                    old_interfaces.update(interface_range)
                else:
                    new_interfaces.update(interface_range)
                nodes_to_delete.add(node)

        for node in nodes_to_delete:
            node.delete()

        del_interfaces = sorted(old_interfaces - new_interfaces)
        add_interfaces = sorted(new_interfaces - old_interfaces)
        add_pre_tag = False
        for interface in del_interfaces:
            _ = ct.__class__(f"undo vlan {bd_id} access-port interface {interface}", ct, ct.tags.copy() + ["pre"])
            add_pre_tag = True
        for interface in add_interfaces:
            _ = ct.__class__(f"vlan {bd_id} access-port interface {interface}", ct, ct.tags.copy())
        ct.children = dict(sorted(ct.children.items(), key=lambda item: not item[0].startswith("undo ")))
        if add_pre_tag:
            ct.tags.append("pre")

    @classmethod
    def process(cls, ct: CTree) -> None:
        for node in ct.children.values():
            if not node.line.startswith("bridge-domain "):
                continue
            _, bd_id, *_ = node.line.split()
            if not bd_id.isdigit():
                continue
            cls._process_bd(node)
