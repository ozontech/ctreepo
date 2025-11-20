import hashlib
from typing import TYPE_CHECKING, TypeVar

from ctreepo.utils.regex_cache import CTreeRegexCache

if TYPE_CHECKING:
    from ctreepo.ctree import CTree

T = TypeVar("T", bound="CTree")


class CTreeHasher:
    @classmethod
    def _check_ordered_section(cls, node: T) -> bool:
        # TODO такой же вопрос, как с no-diff
        for section in node.spec.ordered_sections:
            pattern = CTreeRegexCache.get_pattern(section)
            if pattern.fullmatch(node.line_formal):
                return True
        return False

    @classmethod
    def reset_hash(cls, node: T) -> None:
        """Сбрасывает хеш у ноды и вверх по цепочке родителей."""
        if node._hash is not None:
            pass
            # TODO убрать print
            # print(f"сброс хеша для {node.line or 'root'}, id: {id(node)}")  # pragma: no cover
        node._hash = None
        if node.parent and node.parent._hash:
            # TODO убрать print
            # print(
            #     f"сброс хеша рекурсивно для родителя {node.line or 'root'}, parent id: {id(node.parent)}",
            # )  # pragma: no cover
            cls.reset_hash(node.parent)

    @classmethod
    def calc_hash(cls, node: T) -> str:
        """Возвращает SHA-256 от строки узла + хэшей детей."""
        # TODO убрать print
        # print(f"расчет хеша для {node.line or 'root'}, id: {id(node)}")  # pragma: no cover
        hasher = hashlib.sha256()
        hasher.update(node.line.encode())
        # если ordered секция, то её нельзя сортировать
        if len(node) != 0 and cls._check_ordered_section(node):
            children_lines = list(node.children.keys())
        else:
            children_lines = sorted(node.children.keys())

        for line in children_lines:
            hasher.update(node.children[line].hash.encode())

        return hasher.hexdigest()


# import hashlib
# import re
# l = ["A", "B", "E", "D", "C"]
# def check(l: list[str], s: bool) -> str:
#     hasher = hashlib.sha256()
#     if s:
#         for i in sorted(l):
#             hasher.update(i.encode())
#     else:
#         for i in l:
#             hasher.update(i.encode())
#     return hasher.hexdigest()

# check(l, False)
# check(l, True)
# check(l, False)
# check(l, True)
# check(l, True)
