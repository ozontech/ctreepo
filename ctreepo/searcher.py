import re
from typing import Literal

from .ctree import CTree

__all__ = ("CTreeSearcher",)


class CTreeSearcher:
    @classmethod
    def _search(
        cls,
        ct: CTree,
        string: str,
        include_tags: list[str],
        include_mode: Literal["or", "and"],
        exclude_tags: list[str],
        include_children: bool,
    ) -> list[CTree]:
        """рекурсивный поиск."""

        def _match_include_tags() -> bool:
            # len(include_tags) == 0 отрабатывается в родительской функции, тут считаем, что теги есть
            re_tags: list[str] = [tag.replace("re:", "") for tag in include_tags if tag.startswith("re:")]
            non_re_tags: list[str] = [tag for tag in include_tags if not tag.startswith("re:")]
            match_result: list[bool] = []

            if len(re_tags) != 0:
                match_ = []
                for tag in re_tags:
                    match_.append(any(re.fullmatch(tag, ct_tag) for ct_tag in ct.tags))
                if include_mode == "or":
                    match_result.append(any(match_))
                else:
                    match_result.append(all(match_))

            if len(non_re_tags) != 0:
                if include_mode == "or" and not set(non_re_tags).isdisjoint(set(ct.tags)):
                    match_result.append(True)
                elif include_mode == "and" and set(non_re_tags).issubset(set(ct.tags)):
                    match_result.append(True)
                else:
                    match_result.append(False)

            return any(match_result) if include_mode == "or" else all(match_result)

        def _match_exclude_tags() -> bool:
            re_tags: list[str] = [tag.replace("re:", "") for tag in exclude_tags if tag.startswith("re:")]
            non_re_tags: list[str] = [tag for tag in exclude_tags if not tag.startswith("re:")]
            match_result: list[bool] = []

            if len(re_tags) != 0:
                for tag in re_tags:
                    match_result.append(any(re.fullmatch(tag, ct_tag) for ct_tag in ct.tags))
            if len(non_re_tags) != 0:
                match_result.append(not set(non_re_tags).isdisjoint(set(ct.tags)))

            return any(match_result)

        if include_mode not in ["or", "and"]:
            raise ValueError("incorrect include_mode, 'or' or 'and' are allowed.")

        result = []

        match_string = bool(re.search(string, ct.line)) if len(string) != 0 else True
        match_include_tags = _match_include_tags() if len(include_tags) != 0 else True
        match_exclude_tags = _match_exclude_tags() if len(exclude_tags) != 0 else False
        match_tags = all((match_include_tags, not match_exclude_tags))

        match_result = all((match_string, match_tags))
        if match_result:
            result.append(ct.copy(children=include_children))
        if not match_result or not include_children:
            for child in ct.children.values():
                result.extend(
                    cls._search(
                        ct=child,
                        string=string,
                        include_tags=include_tags,
                        include_mode=include_mode,
                        exclude_tags=exclude_tags,
                        include_children=include_children,
                    )
                )

        return result

    @classmethod
    def search(
        cls,
        ct: CTree,
        *,
        string: str = "",
        include_tags: list[str] | None = None,
        include_mode: Literal["or", "and"] = "or",
        exclude_tags: list[str] | None = None,
        include_children: bool = False,
    ) -> CTree:
        """Поиск конфигурации в дереве.

        Args:
            ct (ConfigTree): где ищем
            string (str): что ищем, может быть regex строкой
            include_tags (list[str]): список тегов, по которым выборку делаем
            include_mode (Literal["or", "and"]): логика объединения критериев поиска
            exclude_tags (list[str]): список тегов-исключений, не должно быть на узле
            include_children (bool): включать потомков найденной секции или нет

        Returns:
            ConfigTree: новое дерево с отфильтрованным результатом
        """
        if include_tags is None:
            include_tags = []
        if exclude_tags is None:
            exclude_tags = []
        string = string.strip()
        root = ct.__class__()
        if len(string) == 0 and len(include_tags) == 0 and len(exclude_tags) == 0:
            return root
        filter_result = cls._search(
            ct=ct,
            string=string,
            include_tags=include_tags,
            include_mode=include_mode,
            exclude_tags=exclude_tags,
            include_children=include_children,
        )
        for node in filter_result:
            root.merge(node)
        root.update_node_hash()
        return root
