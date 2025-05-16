import abc
from typing import Any, Callable

from ctreepo.ctree import CTree
from ctreepo.models import Platform

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


_REGISTRY: dict[Platform, list[type[CTreePostProc]]] = {platform: [] for platform in Platform}


def register_rule(platform: Platform) -> Callable[[type[CTreePostProc]], Any]:
    def wrapper(cls: type[CTreePostProc]) -> type[CTreePostProc]:
        if platform in _REGISTRY and cls not in _REGISTRY[platform]:
            _REGISTRY[platform].append(cls)
        return cls

    return wrapper
