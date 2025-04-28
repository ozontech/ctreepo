from pathlib import Path
from typing import Any, Literal

from .ctree import CTree
from .differ import CTreeDiffer
from .models import Vendor
from .parser import CTreeParser, TaggingRulesDict, TaggingRulesFile
from .postproc import CTreePostProc
from .searcher import CTreeSearcher
from .serializer import CTreeSerializer

__all__ = ("CTreeEnv",)


class CTreeEnv:
    def __init__(
        self,
        vendor: Vendor,
        *,
        tagging_rules: Path | str | list[dict[str, str | list[str]]] | None = None,
        ordered_sections: list[str] | None = None,
        no_diff_sections: list[str] | None = None,
        post_proc_rules: list[type[CTreePostProc]] | None = None,
        template: str | CTree | None = None,
    ):
        if isinstance(tagging_rules, str) or isinstance(tagging_rules, Path):
            _tr_file = TaggingRulesFile(tagging_rules)
        else:
            _tr_file = None
        if isinstance(tagging_rules, list):
            _tr_dict = TaggingRulesDict({vendor: tagging_rules})
        else:
            _tr_dict = None

        self.vendor = vendor
        self._parser = CTreeParser(vendor=self.vendor, tagging_rules=_tr_file or _tr_dict)
        self._ordered_sections = ordered_sections
        self._no_diff_sections = no_diff_sections
        self._post_proc_rules = post_proc_rules
        self._template: CTree | None
        if isinstance(template, str):
            self._template = self._parser.parse(template)
        elif isinstance(template, CTree):
            self._template = template
        else:
            self._template = None

    def parse(
        self,
        config: str,
        template: CTree | None = None,
    ) -> CTree:
        return self._parser.parse(
            config=config,
            template=template or self._template,
        )

    def diff(
        self,
        a: CTree,
        b: CTree,
        masked: bool = False,
        reorder_root: bool = True,
    ) -> CTree:
        return CTreeDiffer.diff(
            a=a,
            b=b,
            masked=masked,
            reorder_root=reorder_root,
            ordered_sections=self._ordered_sections,
            no_diff_sections=self._no_diff_sections,
            post_proc_rules=self._post_proc_rules,
        )

    def to_dict(
        self,
        ct: CTree,
    ) -> dict[str, Any]:
        return CTreeSerializer.to_dict(root=ct)

    def from_dict(
        self,
        data: dict[str, Any],
    ) -> CTree:
        return CTreeSerializer.from_dict(
            vendor=self.vendor,
            data=data,
        )

    def search(
        self,
        ct: CTree,
        *,
        string: str = "",
        include_tags: list[str] | None = None,
        include_mode: Literal["or", "and"] = "or",
        exclude_tags: list[str] | None = None,
        include_children: bool = False,
    ) -> CTree:
        return CTreeSearcher.search(
            ct=ct,
            string=string,
            include_tags=include_tags,
            include_mode=include_mode,
            exclude_tags=exclude_tags,
            include_children=include_children,
        )
