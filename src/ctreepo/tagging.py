from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, Protocol, TypeVar

import yaml

T = TypeVar("T")


class SingletonByFile(Generic[T], type):
    _INSTANCES: dict[tuple["SingletonByFile[T]", Path], T] = {}

    def __call__(cls, filename: Path | str) -> T:
        if isinstance(filename, str):
            filename = Path(Path.cwd(), filename)
        if not filename.is_file():
            raise ValueError(f"файла '{filename}' не существует")
        key = (cls, filename)
        if key not in cls._INSTANCES:
            cls._INSTANCES[key] = super().__call__(filename)
        return cls._INSTANCES[key]


@dataclass(frozen=True, slots=True)
class TaggingRule:
    regex: str
    tags: set[str]


class TaggingRules(Protocol):
    @property
    def rules(self) -> dict[str, list[TaggingRule]]: ...

    def load(self) -> None: ...


class TaggingRulesFromYAML(metaclass=SingletonByFile):
    def __init__(self, filename: Path | str, *, yaml_key: str = "tagging-rules") -> None:
        if isinstance(filename, str):
            filename = Path(Path.cwd(), filename)
        self._filename = filename
        self._rules: dict[str, list[TaggingRule]] | None = None
        self.yaml_key = yaml_key

    @property
    def rules(self) -> dict[str, list[TaggingRule]]:
        if self._rules is None:
            self.load()
            assert self._rules is not None
        return self._rules

    def load(self) -> None:
        _rules = {}
        with open(self._filename) as f:
            data = yaml.safe_load(f)
        for platform, rules in (data.get(self.yaml_key) or {}).items():
            _rules[platform] = [TaggingRule(regex=regex, tags=set(tags)) for regex, tags in rules.items()]

        self._rules = _rules


class TaggingRulesFromDict:
    def __init__(
        self,
        platform: str,
        rules: Mapping[str, Iterable[str]],
    ) -> None:
        self.platform = platform
        self._raw_rules = rules
        self._rules: dict[str, list[TaggingRule]] | None = None

    @property
    def rules(self) -> dict[str, list[TaggingRule]]:
        if self._rules is None:
            self.load()
            assert self._rules is not None
        return self._rules

    def load(self) -> None:
        rules = []
        for regex, tags in self._raw_rules.items():
            rules.append(TaggingRule(regex=regex, tags=set(tags)))
        self._rules = {self.platform: rules}
