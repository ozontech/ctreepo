import re
from collections import deque
from typing import TYPE_CHECKING, TypeVar

from ctreepo.spec.platform_spec import PlatformSpec

if TYPE_CHECKING:
    from ctreepo.ctree import CTree

T = TypeVar("T", bound="CTree")


class CTreeRenderer:
    formal_path_sep = " / "
    secret_mask = "****"  # noqa: S105

    @classmethod
    def node_path(cls, node: T, reverse: bool = True) -> list[T]:
        """Путь от корня к ноде (reverse=True) или от ноды к корню (reverse=False) в виде списка нод."""
        result = []
        _node = node
        while _node.parent is not None:
            result.append(_node)
            _node = _node.parent
        if reverse:
            result.reverse()
        return result

    @classmethod
    def node_formal_line(cls, node: T) -> str:
        path = cls.node_path(node)
        return cls.formal_path_sep.join(n.line for n in path)

    @classmethod
    def mask_output(cls, output: str, spec: PlatformSpec) -> str:
        for pattern in spec.mask_patterns:
            output = re.sub(
                pattern,
                lambda m: m.group(0).replace(m.group(1), cls.secret_mask),
                output,
            )

        return output

    @classmethod
    def _config(cls, level: int, node: T) -> list[str]:
        result: list[str] = []

        result.append(node.spec.spaces * level + node.line)
        for child in node:
            result.extend(cls._config(level=level + 1, node=child))

        # TODO сделать кеш регулярок
        sections_require_exit_pattern = re.compile("|".join(node.spec.sections_required_exit))
        if len(result) != 1:
            result.append(node.spec.spaces * level + child.spec.section_sep)
        elif sections_require_exit_pattern.fullmatch(node.line_formal):
            result.append(node.spec.spaces * level + node.spec.section_sep)

        return result

    @classmethod
    def config(cls, node: T) -> str:
        result: list[str] = []
        level = 0
        _node = node

        while _node.parent is not None:
            result.append(_node.line)
            level += 1
            _node = _node.parent
        result.reverse()
        result = [node.spec.spaces * indx + line for indx, line in enumerate(result)]
        for child in node:
            child_result = cls._config(level=level, node=child)
            if len(child_result) != 1 and result and result[-1] != node.spec.section_sep:
                result.append(child.spec.section_sep)

            result.extend(child_result)

        if len(result) == 1 or (len(result) > 0 and result[-1] != child.spec.section_sep):
            result.append(child.spec.section_sep)

        return "\n".join(result)

    @classmethod
    def patch(cls, node: T) -> str:
        result = []
        level = 0
        _node = node.parent
        while _node and _node.parent is not None:
            result.append(_node.line)
            level += 1
            _node = _node.parent

        result.reverse()

        re_sections_require_exit: re.Pattern[str] = re.compile("|".join(node.spec.sections_required_exit))
        re_sections_without_exit: re.Pattern[str] = re.compile("|".join(node.spec.sections_without_exit))

        nodes: deque[T | None] = deque([node])
        while nodes:
            _node = nodes.popleft()
            # None - индикатор выхода из секции - вставляем quit
            if _node is None:
                result.append(node.spec.section_exit)
                continue
            # у root.line эта пустая строка, её пропускаем
            if _node.line:
                result.append(_node.line)

            if _node.children:
                # добавляем quit только для реальных секций, из рута и секций без exit выходить не нужно
                if _node.line and not re_sections_without_exit.fullmatch(_node.line_formal):
                    nodes.appendleft(None)
                nodes.extendleft(reversed(_node.children.values()))
            # если секция требует выхода, но детей у нее нет, то все равно exit добавляем
            elif re_sections_require_exit.fullmatch(_node.line_formal):
                nodes.appendleft(None)

        result = result + [node.spec.section_exit] * level
        return "\n".join(result)
