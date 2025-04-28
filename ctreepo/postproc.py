import abc
from typing import Any, Callable

from .ctree import CTree
from .models import Vendor

__all__ = (
    "register_rule",
    "CTreePostProc",
    "_REGISTRY",
)


class CTreePostProc(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def process(cls, ct: CTree) -> None:
        """Пост-обработка конфигурации, например изменение, добавление, удаление команд."""


_REGISTRY: dict[Vendor, list[type[CTreePostProc]]] = {vendor: [] for vendor in Vendor}


def register_rule(vendor: Vendor) -> Callable[[type[CTreePostProc]], Any]:
    def wrapper(cls: type[CTreePostProc]) -> type[CTreePostProc]:
        if vendor in _REGISTRY and cls not in _REGISTRY[vendor]:
            _REGISTRY[vendor].append(cls)
        return cls

    return wrapper
