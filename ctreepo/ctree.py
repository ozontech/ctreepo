from __future__ import annotations

import hashlib
import re
from collections import deque
from typing import Deque, Self

from . import settings
from .models import Vendor

__all__ = ("CTree",)


class CTree:
    __slots__ = (
        "line",  # строка настройки
        "parent",  # родитель узла
        "children",  # словарь с вложенными потомками узла
        "tags",  # теги узла
        "template",  # шаблон, что бы разобрать строку на команду и аргументы
        "undo_line",  # как удаляем строку, если не указано, то undo добавляем
        "prefix",  # префикс перед строкой, используется в human-diff (-/+)
        "node_hash",  # хеш узла с учетом дочерних узлов
    )

    @property
    def vendor(self) -> Vendor:
        """количество пробелов для нового уровня."""
        raise NotImplementedError("property should be overridden")

    @property
    def spaces(self) -> str:
        """количество пробелов для нового уровня."""
        raise NotImplementedError("property should be overridden")

    @property
    def section_exit(self) -> str:
        """как выходим из секции: exit/quit/..."""
        raise NotImplementedError("property should be overridden")

    @property
    def section_separator(self) -> str:
        """Чем разделяем блоки конфига между собой: !/#/..."""
        raise NotImplementedError("property should be overridden")

    @property
    def sections_without_exit(self) -> list[str]:
        """Список секций, из которых не нужно выходить.

        Некоторые секции не работают если явно выходить из них,
        например сертификаты в cisco, xpl в huawei.
        """
        raise NotImplementedError("property should be overridden")

    @property
    def sections_require_exit(self) -> list[str]:
        """Секции, которые могут быть пустыми.

        И для них необходимо явно прописывать выход,
        например route-map rm_DENY deny 10.
        """
        raise NotImplementedError("property should be overridden")

    @property
    def junk_lines(self) -> list[str]:
        """список линий, которые нужно игнорировать при анализе конфигурации."""
        raise NotImplementedError("property should be overridden")

    @property
    def undo(self) -> str:
        """как убираем конфигурацию, в общем случае: no/undo/..."""
        raise NotImplementedError("property should be overridden")

    @property
    def mask_patterns(self) -> list[str]:
        """паттерны для маскирования строк, указываем текст перед тем, что нужно заменить."""
        raise NotImplementedError("property should be overridden")

    masking_string: str = settings.MASKING_STRING

    def __init__(
        self,
        line: str = "",
        parent: Self | None = None,
        tags: list[str] | None = None,
        template: str = "",
    ) -> None:
        self.line = line.strip()

        self.parent = parent
        self.children: dict[str, Self] = {}
        self.prefix = ""
        if tags is not None:
            self.tags = tags
        elif parent is not None:
            self.tags = parent.tags
        else:
            self.tags = []

        if parent is not None:
            parent.children[line.strip()] = self

        if len(template) != 0:
            self.template, self.undo_line = self._get_template_undo(self.line, template)
        else:
            self.template = ""
            self.undo_line = ""

        # тут можно сразу считать, но смысла кмк нет пока неизвестны потомки, поэтому пересчет
        # нужно делать после построения дерева
        self.node_hash = ""

    def _get_template_undo(self, line: str, template: str) -> tuple[str, str]:
        if settings.TEMPLATE_SEPARATOR in template:
            apply_template, remove_template = map(str.strip, template.split(settings.TEMPLATE_SEPARATOR))
        else:
            apply_template = template.strip()
            remove_template = ""
        apply_result = ""
        remove_result = ""

        if (m := re.fullmatch(apply_template, line)) is None:
            return apply_result, remove_result
        patterns = dict(re.findall(r"\(\?P<(\S+?)>(\S+?)\)", apply_template))
        start, _ = m.regs[0]
        named_group_by_index = {index: name for name, index in m.re.groupindex.items()}
        for indx, (_s, _e) in enumerate(m.regs):
            # если не именованная группа - пропускаем
            group = named_group_by_index.get(indx)
            if group is None:
                continue

            # если ничего в группе нет совпадения - пропускаем
            if _s == -1 and _e == -1:
                continue

            # если не удалось найти паттерн для группы - пропускаем
            pattern = patterns.get(group)
            if pattern is None:
                continue

            if _s > start:
                apply_result += line[start:_s]
            apply_result += f"(?P<{group}>{pattern})"
            start = _e

        if len(remove_template) == 0:
            return apply_result, remove_result
        remove_result = re.sub(apply_template, remove_template, line).strip()
        return apply_result, remove_result

    @classmethod
    def mask_line(cls, line: str) -> str:
        pattern: str = "|".join(cls.mask_patterns)  # type: ignore [arg-type]
        if (m := re.fullmatch(pattern, line)) is not None:
            secret = [g for g in m.groups() if g is not None][0]
            return line.replace(secret, cls.masking_string)
        else:
            return line

    @property
    def masked_line(self) -> str:
        return self.mask_line(self.line)

    def __str__(self) -> str:
        """строковое представление: сама строка или 'root', если для корня вызываем."""
        return self.line or "root"

    def __repr__(self) -> str:
        """формальное представление объекта."""
        return f"({id(self)}) '{str(self)}'"

    def delete(self) -> None:
        to_delete: list[CTree] = [self]
        stack: Deque[CTree] = deque()
        if len(self.children) != 0:
            stack.extendleft(self.children.values())
        while len(stack) > 0:
            node = stack.popleft()
            to_delete.append(node)
            if len(node.children) != 0:
                stack.extendleft(list(node.children.values())[::-1])
        for node in to_delete[::-1]:
            if node.parent is not None:
                _ = node.parent.children.pop(node.line)
                del node

    def __hash__(self) -> int:
        """вычисление hash."""
        # todo тут получается два вида хеша: один только на основе строки конфигурации, и нужен для того
        # todo что бы сделать объект хэшируемым, второй хеш нужен для сравнения на основе как строки, так
        # todo и потомков, что бы при одинаковых хешах у нод не лазить по потомкам. объединить может их?
        return hash(self.formal_path)

    # todo добавить сравнение, с учетом порядка команд, как в differ сделано
    def __eq__(self, other: object) -> bool:
        """сравниваем два объекта.

        считаем узлы равными, если у них равны между собой:
        - строки настройки
        - одинаковые родители
        - одинаковые потомки

        Args:
            other (object): с чем сравниваем

        Returns:
            bool: равны или нет узлы
        """
        if not isinstance(other, self.__class__):
            return NotImplemented
        # возможно стоит сравнивать маскированные строки, что бы исключить разницу из-за хешей
        if self.line != other.line:
            return False
        if len(self.children) != len(other.children):
            return False

        self_parents = self._formal_path
        other_parents = other._formal_path

        if self_parents != other_parents:
            return False

        if set(self.tags) != set(other.tags):
            return False

        children_eq = []
        for line, node in self.children.items():
            other_node = other.children.get(line)
            if other_node is None:
                return False
            children_eq.append(node == other_node)
        return all(children_eq)

    @property
    def _formal_path(self) -> list[str]:
        result = []
        node = self
        while node.parent is not None:
            result.append(node.line)
            node = node.parent
        result.reverse()
        return result

    @property
    def formal_path(self) -> str:
        return " / ".join(self._formal_path)

    def _config(self, symbol: str, level: int, masked: bool) -> list[str]:
        line = self.masked_line if masked else self.line
        # if line == self.empty_section_placeholder:
        #     return []
        result = [self.prefix + symbol * level + line]
        for child in self.children.values():
            result.extend(child._config(symbol=symbol, level=level + 1, masked=masked))
        return result

    def _build_config(self, masked: bool) -> str:
        result = []
        level = 0
        node = self
        while node.parent is not None:
            result.append(node.masked_line if masked else node.line)
            level += 1
            node = node.parent
        result.reverse()
        result = [self.spaces * indx + line for indx, line in enumerate(result)]
        for child in self.children.values():
            result.extend(child._config(symbol=self.spaces, level=level, masked=masked))
            if self.parent is None:
                result.append(" " * len(child.prefix) + self.section_separator)
        return "\n".join(result)

    @property
    def config(self) -> str:
        return self._build_config(masked=False)

    @property
    def masked_config(self) -> str:
        return self._build_config(masked=True)

    @property
    def _formal_config(self) -> list[list[str]]:
        result = []
        for node in self.children.values():
            if len(node.children) == 0:
                result.append(node._formal_path)
            else:
                result.extend(node._formal_config)
        return result

    @property
    def formal_config(self) -> str:
        result = []

        node = self
        if len(self.children) == 0:
            return self.formal_path
        for node in self.children.values():
            if len(node.children) == 0:
                result.append(node._formal_path)
            else:
                result.extend(node._formal_config)

        return "\n".join([" / ".join(config) for config in result])

    def _build_patch(self: Self, masked: bool) -> str:
        nodes = deque(self.children.values())
        result = []
        path_to_root = []

        node = self
        while node.parent is not None:
            path_to_root.append(node.masked_line if masked else node.line)
            node = node.parent
        path_to_root.reverse()

        while len(nodes) > 0:
            node = nodes.popleft()
            # if node.line == node.empty_section_placeholder:
            #     continue
            result.append(node.masked_line if masked else node.line)
            if len(node.children) != 0:
                if not re.fullmatch("|".join(self.sections_without_exit), node.formal_path):
                    nodes.appendleft(self.__class__(line=self.section_exit))
                nodes.extendleft(list(node.children.values())[::-1])
            elif len(self.sections_require_exit) != 0 and re.fullmatch(
                "|".join(self.sections_require_exit), node.formal_path
            ):
                nodes.appendleft(self.__class__(line=self.section_exit))
        result = path_to_root + result + [self.section_exit] * len(path_to_root)
        return "\n".join(result)

    @property
    def patch(self) -> str:
        return self._build_patch(masked=False)

    @property
    def masked_patch(self) -> str:
        return self._build_patch(masked=True)

    def _copy(self, children: bool, parent: Self | None) -> Self:
        if self.parent is not None and parent is None:
            parent = self.parent._copy(children=False, parent=None)

        new_obj = self.__class__(line=self.line, parent=parent, tags=self.tags.copy(), template=self.template)
        new_obj.prefix = self.prefix
        new_obj.undo_line = self.undo_line
        if children:
            for child in self.children.values():
                _ = child._copy(children, new_obj)
        return new_obj

    def copy(self, children: bool = True) -> Self:
        root = self._copy(children=children, parent=None)
        while root.parent is not None:
            root = root.parent
        return root

    def merge(self, other: Self) -> None:
        for line, node in other.children.items():
            if line not in self.children:
                _ = node._copy(children=True, parent=self)
            else:
                self.children[line].merge(node)

    def _subtract(self, other: Self, masked: bool = False) -> None:
        nodes_to_delete = []
        for child in self.children.values():
            line = child.exists_in(other, masked)
            if len(line) != 0:
                if len(child.children) != 0:
                    child._subtract(other.children[line])
                if len(child.children) == 0:
                    nodes_to_delete.append(child)
        for node in nodes_to_delete:
            node.delete()

    def subtract(self, other: Self) -> Self:
        result = self.copy()
        result._subtract(other=other)
        return result

    def _apply(self, other: Self) -> None:
        for child in other.children.values():
            if child.line.startswith(child.undo):
                line = child.line.replace(child.undo, "").strip()
                if line in self.children:
                    self.children[line].delete()
            else:
                if child.exists_in(self):
                    self.children[child.line]._apply(other=child)
                else:
                    child._copy(children=True, parent=self)

    def apply(self, other: Self) -> Self:
        result = self.copy()
        result._apply(other=other)
        result.update_node_hash()
        return result

    def rebuild(self, deep: bool = False) -> None:
        new_children = {child.line: child for child in self.children.values()}
        self.children = new_children
        if deep:
            for child in self.children.values():
                child.rebuild(deep)
        self.update_node_hash()

    def exists_in(self, other: Self, masked: bool = False) -> str:
        if masked:
            for line, node in other.children.items():
                if self.masked_line == node.masked_line:
                    return line
            return ""
        else:
            if self.line in other.children:
                return self.line
            else:
                return ""

    def reorder(self, tags: list[str], *, reverse: bool = False) -> None:
        def _get_children_tags(node: Self) -> list[str]:
            tags = node.tags.copy()
            for child in node.children.values():
                tags.extend(_get_children_tags(child))
            return list(set(tags))

        if len(tags) == 0:
            return

        no_tags = "_no_tags_nodes"
        children: dict[str, list[Self]]

        if not reverse:
            children = {tag: [] for tag in tags}
        else:
            children = {tag: [] for tag in reversed(tags)}
        children[no_tags] = []

        for child in self.children.values():
            child_tags = _get_children_tags(child)
            common_tags = set(tags).intersection(set(child_tags))
            if len(common_tags) == 0:
                children[no_tags].append(child)
            else:
                tag = common_tags.pop()
                children[tag].append(child)

        self.children = {}
        for child_list in children.values():
            for child in child_list:
                self.children[child.line] = child

    def move_before(self, node: Self) -> None:
        if self.parent is None or node.parent is None:
            return
        if id(self.parent) != id(node.parent):
            return
        children: dict[str, Self] = {}
        met_self = False
        met_node = False
        for line, child in node.parent.children.items():
            if met_self and not met_node:
                return
            if child.line == self.line:
                met_self = True
            elif child.line == node.line:
                children[self.line] = self
                children[line] = node
                met_node = True
            else:
                children[line] = child
        node.parent.children = children

    def move_after(self, node: Self) -> None:
        if self.parent is None or node.parent is None:
            return
        if id(self.parent) != id(node.parent):
            return
        children: dict[str, Self] = {}
        met_self = False
        met_node = False
        for line, child in node.parent.children.items():
            if not met_self and met_node:
                return
            if child.line == self.line:
                met_self = True
            elif child.line == node.line:
                children[line] = node
                children[self.line] = self
                met_node = True
            else:
                children[line] = child
        node.parent.children = children

    def remove_tags(self, tags: list[str], children: bool = True) -> None:
        if children:
            for child in self.children.values():
                child.remove_tags(tags, children)
        self.tags = [tag for tag in self.tags if tag not in tags]

    @classmethod
    def pre_run(cls: type, config: str) -> str:
        return config

    def post_run(self) -> None:
        return

    def update_node_hash(self) -> None:
        for node in self.children.values():
            node.update_node_hash()
        hashes = [node.node_hash for node in self.children.values()]
        hashes.append(hashlib.sha256(self.line.encode()).hexdigest())
        self.node_hash = hashlib.sha256("".join(sorted(hashes)).encode()).hexdigest()
