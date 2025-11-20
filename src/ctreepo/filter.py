import re
from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal, TypeVar

if TYPE_CHECKING:
    from ctreepo.ctree import CTree

T = TypeVar("T", bound="CTree")

__all__ = ("CTreeFilter",)


class CTreeFilter:
    REGEX_TAG_PREFIX = "re:"

    @classmethod
    def _filter(
        cls,
        ct: T,
        string: str,
        include_tags: Sequence[str],
        include_mode: Literal["or", "and"],
        exclude_tags: Sequence[str],
        include_children: bool,
    ) -> list[T]:
        """рекурсивный поиск."""

        def _match_include_tags() -> bool:
            # теги с регулярным выражением, начинаются на "re:"
            regex_tags: list[str] = [
                tag.replace(cls.REGEX_TAG_PREFIX, "") for tag in include_tags if tag.startswith(cls.REGEX_TAG_PREFIX)
            ]
            # обычные строковые теги
            str_tags: list[str] = [tag for tag in include_tags if not tag.startswith("re:")]
            match_result: list[bool] = []

            if len(regex_tags) != 0:
                match_ = []
                for tag in regex_tags:
                    match_.append(any(re.fullmatch(tag, ct_tag) for ct_tag in ct.tags))
                if include_mode == "or":
                    match_result.append(any(match_))
                else:
                    match_result.append(all(match_))

            if len(str_tags) != 0:
                if include_mode == "or" and not set(str_tags).isdisjoint(set(ct.tags)):
                    match_result.append(True)
                elif include_mode == "and" and set(str_tags).issubset(set(ct.tags)):
                    match_result.append(True)
                else:
                    match_result.append(False)

            return any(match_result) if include_mode == "or" else all(match_result)

        def _match_exclude_tags() -> bool:
            re_tags: list[str] = [
                tag.replace(cls.REGEX_TAG_PREFIX, "") for tag in exclude_tags if tag.startswith(cls.REGEX_TAG_PREFIX)
            ]
            non_re_tags: list[str] = [tag for tag in exclude_tags if not tag.startswith("re:")]
            match_result: list[bool] = []

            if len(re_tags) != 0:
                for tag in re_tags:
                    match_result.append(any(re.fullmatch(tag, ct_tag) for ct_tag in ct.tags))
            if len(non_re_tags) != 0:
                match_result.append(not set(non_re_tags).isdisjoint(set(ct.tags)))

            return any(match_result)

        result = []

        match_string = bool(re.search(string, ct.line)) if len(string) != 0 else True
        match_include_tags = _match_include_tags() if len(include_tags) != 0 else True
        match_exclude_tags = _match_exclude_tags() if len(exclude_tags) != 0 else False
        match_result = match_string and match_include_tags and not match_exclude_tags

        if match_result:
            result.append(ct.copy(with_children=include_children))
        if not match_result or not include_children:
            for child in ct:
                result.extend(
                    cls._filter(
                        ct=child,
                        string=string,
                        include_tags=include_tags,
                        include_mode=include_mode,
                        exclude_tags=exclude_tags,
                        include_children=include_children,
                    ),
                )

        return result

    @classmethod
    def filter(
        cls,
        ct: T,
        *,
        string: str = "",
        include_tags: Sequence[str] | None = None,
        include_mode: Literal["or", "and"] = "or",
        exclude_tags: Sequence[str] | None = None,
        include_children: bool = False,
    ) -> T:
        """Поиск конфигурации в дереве.

        Args:
            ct (CTree): где ищем
            string (str): что ищем, может быть regex строкой
            include_tags (Iterable[str]): список тегов, по которым выборку делаем
            include_mode (Literal["or", "and"]): логика объединения критериев поиска
            exclude_tags (Iterable[str]): список тегов-исключений, не должно быть на узле
            include_children (bool): включать потомков найденной секции или нет

        Returns:
            CTree: новое дерево с отфильтрованным результатом
        """
        if include_mode not in ("or", "and"):
            raise ValueError("include_mode должен быть 'or' или 'and'.")

        if include_tags is None:
            include_tags = []
        if exclude_tags is None:
            exclude_tags = []
        string = string.strip()

        if len(string) == 0 and len(include_tags) == 0 and len(exclude_tags) == 0:
            return ct

        root = ct.__class__.create_root(ct.spec)

        nodes = cls._filter(
            ct=ct,
            string=string,
            include_tags=include_tags,
            include_mode=include_mode,
            exclude_tags=exclude_tags,
            include_children=include_children,
        )
        for node in nodes:
            root.merge(node)

        return root
