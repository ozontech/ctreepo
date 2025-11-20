from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Literal, TypeAlias, TypeVar

from ctreepo.filter import CTreeFilter

if TYPE_CHECKING:
    from ctreepo.ctree import CTree

T = TypeVar("T", bound="CTree")
Tag: TypeAlias = str | Sequence["Tag"]


class CTreeSorter:
    # заглушка для узлов без тега
    NO_TAGS = "<< nodes_without_tags >>"

    @classmethod
    def _get_branch_tags(cls, node: T) -> set[str]:
        tags = node.tags.copy()
        for child in node:
            tags.update(cls._get_branch_tags(child))
        return tags

    @classmethod
    def _get_first_matched_tag(cls, branch_tags: set[str], requested_order: tuple[str, ...]) -> str:
        for tag in requested_order:
            if tag in branch_tags:
                return tag
        return cls.NO_TAGS

    @classmethod
    def sort(cls, *tags: str, node: T, reverse: bool = False) -> None:
        """Сортировка детей узла в указанном порядке тегов."""
        if not tags:
            return

        # словарь тег:список-узлов-с-этим-тегом
        children: dict[str, list[T]]

        if not reverse:
            children = {tag: [] for tag in tags}
        else:
            children = {tag: [] for tag in reversed(tags)}
        children[cls.NO_TAGS] = []

        for child in node:
            branch_tags = cls._get_branch_tags(child)
            tag = cls._get_first_matched_tag(branch_tags, tags)
            children[tag].append(child)

        node.children = {}
        for child_list in children.values():
            for child in child_list:
                node.children[child.line] = child

    @classmethod
    def config_by_tags(
        cls,
        *tags: Tag,
        node: T,
        skip_no_tag: bool,
        mode: Literal["config", "patch"],
    ) -> Iterator[str]:
        """Отдает части конфигурации (текст) по переданному порядку тегов.

        Уже использованные теги идут как exclude для последующей фильтрации.
        skip_no_tag - отдавать оставшуюся конфигурацию, после прохождения по всем переданным тегам, или нет.
        можно указать "*" в качестве тега, это значит все остальное, кроме перечисленных, например
        "tag1", "*", "tag2" -> порядок будет "tag1", "все кроме tag1/2", "tag2"
        """

        def _to_text() -> str:
            if mode == "config":
                return filtered.config
            elif mode == "patch":
                return filtered.patch
            else:
                raise ValueError(f"неизвестный режим {mode!r}")

        # TODO при преобразовании в dict теряется возможность повторного использования тегов,
        # типа такого порядка: tag1, tag2, tag3, tag1. Возможно оно и не нужно, но подумать как
        # переделать на список списков, что бы можно было повторно теги использовать
        tags_dict: dict[str, list[Tag]] = {}
        for tag in tags:
            if tag == "*":
                tag = "re:.+"
            if tag in tags_dict:
                raise ValueError("повторное использование тегов не допускается")
            if isinstance(tag, str):
                tags_dict[tag] = []
            elif isinstance(tag, Sequence) and isinstance(tag[0], str):
                tags_dict[tag[0]] = list(tag)[1:]
            else:
                raise ValueError("неправильный формат передачи тегов")

        current_level = list(tags_dict.keys())
        for indx, tag in enumerate(current_level):
            if tag == "re:.+":
                exclude_tags = [t for t in tags_dict if t != "re:.+"]
            else:
                exclude_tags = [t for t in current_level[:indx] if t != "re:.+"]

            filtered = CTreeFilter.filter(
                node,
                include_tags=[tag],
                exclude_tags=exclude_tags,
                include_children=False,
            )
            if tags_dict[tag]:
                yield from cls.config_by_tags(
                    *tags_dict[tag],
                    node=filtered,
                    skip_no_tag=skip_no_tag,
                    mode=mode,
                )
            else:
                yield _to_text()
        if skip_no_tag:
            return
        filtered = CTreeFilter.filter(
            node,
            exclude_tags=current_level,
            include_children=False,
        )
        yield _to_text()
