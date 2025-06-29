from pathlib import Path

from ctreepo.ctree import CTree
from ctreepo.differ import CTreeDiffer
from ctreepo.factory import CTreeFactory
from ctreepo.models import Platform
from ctreepo.parser import CTreeParser, TaggingRules, TaggingRulesDict, TaggingRulesFile

__all__ = ("CTreePO",)


class CTreePO:
    def __init__(
        self,
        platform: Platform,
        current_config: str = "",
        target_config: str = "",
        tagging_file: str | None = None,
        tagging_list: list[dict[str, str | list[str]]] | None = None,
        commands_template: str | None = None,
        # extra_sections_require_exit: list[str] | None = None,
        # extra_sections_without_exit: list[str] | None = None,
        # extra_junk_lines: list[str] | None = None,
        # extra_mask_patterns: list[str] | None = None,
    ):
        self.platform = platform
        self.cls = CTreeFactory._PLATFORM_MAP[platform]

        self.parser = CTreeParser(
            platform=platform,
            tagging_rules=self._get_tagging_rules(platform, tagging_file, tagging_list),
        )

        self._commands_template: CTree | None = self._get_commands_template(platform, commands_template)

        self._current_config = current_config
        self._current: CTree | None = None

        self._target_config = target_config
        self._target: CTree | None = None

        self._diff: CTree
        self._human_diff: str

    @property
    def current(self) -> CTree:
        if self._current is None:
            self._current = self.parser.parse(
                config=self._current_config,
                template=self._commands_template,
            )
        return self._current

    @property
    def target(self) -> CTree:
        if self._target is None:
            self._target = self.parser.parse(
                config=self._target_config,
                template=self._commands_template,
            )
        return self._target

    def _get_commands_template(self, platform: Platform, commands_template: str | None) -> CTree | None:
        if isinstance(commands_template, str) and len(commands_template) == 0:
            return None
        if commands_template is None:
            template_file = Path(Path(__file__).parent, "templates", platform).with_suffix(".txt")
        else:
            template_file = Path(commands_template)
        if not template_file.is_file():
            return None
        with open(template_file) as f:
            template_data = f.read()
        return self.parser.parse(template_data)

    def _get_tagging_rules(
        self,
        platform: Platform,
        tagging_file: str | None,
        tagging_list: list[dict[str, str | list[str]]] | None,
    ) -> TaggingRules | None:
        tagging_rules: TaggingRules | None = None
        if tagging_file is not None:
            tagging_rules = TaggingRulesFile(tagging_file)
        elif tagging_list is not None:
            tagging_rules = TaggingRulesDict({platform: tagging_list})
        return tagging_rules

    @property
    def diff(self) -> CTree:
        diff = getattr(self, "_diff", None)
        if diff is None:
            self.calculate_diff()
        return self._diff

    @property
    def human_diff(self) -> str:
        human_diff = getattr(self, "_human_diff", None)
        if human_diff is None:
            self.calculate_human_diff()
        return self._human_diff

    def calculate_diff(self) -> None:
        self._diff = CTreeDiffer.diff(
            a=self.current,
            b=self.target,
        )

    def calculate_human_diff(self) -> None:
        self._human_diff = CTreeDiffer.human_diff(
            current=self.current,
            target=self.target,
            mode="diff-only",
        )
