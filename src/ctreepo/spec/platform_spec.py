from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeVar

from .config_handler_registry import PostConfigHandlerRegistry, PreConfigHandlerRegistry

if TYPE_CHECKING:
    from ctreepo.ctree import CTree
__all__ = ("PlatformSpec",)


T = TypeVar("T", bound="CTree")


# тут бы pydantic или что еще для валидации использовать, но пока есть желание уменьшить число
# зависимостей, поэтому пока встроенные dataclass, а потом посмотрим
@dataclass(slots=True, frozen=True, repr=False)
class PlatformSpec:
    name: str
    scrapli_platform: str = field(default="")
    spaces: str = field(default="")
    section_sep: str = field(default="")
    section_exit: str = field(default="")
    undo: str = field(default="")
    junk_lines: list[str] = field(default_factory=list)
    mask_patterns: list[str] = field(default_factory=list)
    sections_required_exit: list[str] = field(default_factory=list)
    sections_without_exit: list[str] = field(default_factory=list)
    sections_no_diff: list[str] = field(default_factory=list)
    ordered_sections: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"

    def pre_run(self, config: str) -> str:
        for func in PreConfigHandlerRegistry.get(self.name):
            config = func(config)
        return config

    def post_run(self, root: T) -> None:
        for func in PostConfigHandlerRegistry.get(self.name):
            func(root)
