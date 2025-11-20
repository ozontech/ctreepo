from collections import defaultdict
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from ctreepo.ctree import CTree

__all__ = (
    "PreConfigHandlerRegistry",
    "PostConfigHandlerRegistry",
)

# TODO вынести в utils определение типов, подумать над переходом на дженерик (а нужен ли он?)
T = TypeVar("T", bound="CTree")


class PreConfigHandlerRegistry:
    # TODO сделать алиас для Callable[[str], str]
    _handlers: dict[str, list[Callable[[str], str]]] = defaultdict(list)

    @classmethod
    def register(cls, platform: str) -> Callable[[Callable[[str], str]], Callable[[str], str]]:
        def decorator(func: Callable[[str], str]) -> Callable[[str], str]:
            if func in cls._handlers[platform]:
                raise ValueError(f"{func!r} для {platform!r} уже зарегистрирован")
            cls._handlers[platform].append(func)
            return func

        return decorator

    @classmethod
    def get(cls, platform: str) -> Iterator[Callable[[str], str]]:
        yield from cls._handlers[platform]

    @classmethod
    def reset(cls, platform: str) -> None:
        cls._handlers[platform].clear()


class PostConfigHandlerRegistry:
    # TODO сделать алиас для Callable[[T], None]
    _handlers: dict[str, list[Callable[[T], None]]] = defaultdict(list)

    @classmethod
    def register(cls, platform: str) -> Callable[[Callable[[T], None]], Callable[[T], None]]:
        def decorator(func: Callable[[T], None]) -> Callable[[T], None]:
            if func in cls._handlers[platform]:
                raise ValueError(f"{func!r} для {platform!r} уже зарегистрирован")
            # TODO доделать типизацию, generic тут не к чему вроде, но из-за его отсутствия T
            # получается везде разный
            cls._handlers[platform].append(func)  # type: ignore[arg-type]
            return func

        return decorator

    @classmethod
    def get(cls, platform: str) -> Iterator[Callable[[T], None]]:
        yield from cls._handlers[platform]

    @classmethod
    def reset(cls, platform: str) -> None:
        cls._handlers[platform].clear()
