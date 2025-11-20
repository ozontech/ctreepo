from collections import defaultdict
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from ctreepo.ctree import CTree


__all__ = ("DiffHandlerRegistry",)

T = TypeVar("T", bound="CTree")


class DiffHandlerRegistry:
    _handlers: dict[str, list[Callable[[T, T, T], None]]] = defaultdict(list)

    # TODO вынести platform: str в отдельный тип
    @classmethod
    def register(cls, platform: str) -> Callable[[Callable[[T, T, T], None]], Callable[[T, T, T], None]]:
        def decorator(func: Callable[[T, T, T], None]) -> Callable[[T, T, T], None]:
            if func in cls._handlers[platform]:
                raise ValueError(f"{func!r} для {platform!r} уже зарегистрирован")
            cls._handlers[platform].append(func)  # type: ignore[arg-type]
            return func

        return decorator

    @classmethod
    def get(cls, platform: str) -> Iterator[Callable[[T, T, T], None]]:
        yield from cls._handlers[platform]

    @classmethod
    def reset(cls, platform: str) -> None:
        cls._handlers[platform].clear()
