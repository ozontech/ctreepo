from collections import deque
from collections.abc import Iterable, Iterator, Sequence
from typing import Literal, Self, TypeAlias

from ctreepo.filter import CTreeFilter
from ctreepo.hasher import CTreeHasher
from ctreepo.renderer import CTreeRenderer
from ctreepo.sorter import CTreeSorter
from ctreepo.spec.platform_spec import PlatformSpec

Tag: TypeAlias = str | Sequence["Tag"]


class CTree:
    __slots__ = (
        "_hash",  # хеш от line + хеши потомков
        "_line",  # строка настройки
        "children",  # словарь с вложенными потомками узла
        "parent",  # родитель узла
        "spec",  # спецификация платформы
        "tags",  # теги узла
        "template",  # шаблон, что бы разобрать строку на команду и аргументы
        "undo",  # как удаляем опцию из конфигурации, если есть какая-то специфика
    )

    def __init__(
        self,
        line: str,
        parent: Self | None = None,
        tags: set[str] | None = None,
        template: str = "",
        undo: str = "",
    ) -> None:
        line = line.strip()
        # спецификация платформы, задается при создании рута, остальные ноды просто наследуют
        self.spec: PlatformSpec

        self._line: str = ""
        self._hash: str | None = None

        self.parent = parent
        self.line = line
        self.children: dict[str, Self] = {}

        if parent is not None:
            parent.children[line] = self
            self.spec = parent.spec

        if tags is not None:
            self.tags = tags.copy()
        elif parent is not None:
            self.tags = parent.tags.copy()
        else:
            self.tags = set()

        self.template = template
        self.undo = undo

    def __eq__(self, other: object) -> bool:
        """Сравнение двух нод."""
        if not isinstance(other, type(self)):
            return NotImplemented

        # TODO вопрос пока открытый: что считать равными нодами, нужно ли кроме самой строки учитывать
        # теги/шаблоны/undo и другие атрибуты. Сейчас тут логика разъехалась так как хеш считается только
        # по строкам. И если хеши равны, то говорим что и ноды (ветки так как хеш учитывает потомков)
        # равны. А если хеши не равны, то мы идем дальше и там учитываем, например теги, что хеш не считает.
        # И не понятно пока, нужно ли вообще теги брать в расчет, или считать только по строкам (line)
        if self.hash != other.hash:
            return False
        # TODO тут сравнения line/children/line_formal/рекурсию пока отключил, так как в теории это все должно
        # покрываться хешем, а ресурсы эти сравнения едят. Обратный случай, во всяком случае не известен,
        # но если встречу, то нужно будет включить обратно.
        # if self.line != other.line:
        #     return False
        # if len(self.children) != len(other.children):
        #     return False
        # if self.line_formal != other.line_formal:
        #     return False
        # if self.tags != other.tags:
        #     return False

        # for self_node in self:
        #     other_node = other.children.get(self_node.line)
        #     if other_node is None or self_node != other_node:
        #         return False

        return True

    def __getitem__(self, key: str) -> Self | None:
        return self.children.get(key)

    def __hash__(self) -> int:
        return hash(self.line_formal)

    def __iter__(self) -> Iterator[Self]:
        """Итерируемся по детям узла."""
        return iter(self.children.values())

    def __len__(self) -> int:
        return len(self.children)

    def __repr__(self) -> str:
        """Формальное представление объекта."""
        return f"({id(self)}) '{str(self)}'"

    def __str__(self) -> str:
        """Строковое представление: сама строка или 'root', если для корня вызываем."""
        return self.line or "root"

    def _copy_children(self, nodes: Iterable[Self], parent: Self) -> None:
        for node in nodes:
            new_obj = node._copy_node(parent)
            if node.children:
                self._copy_children(nodes=node.children.values(), parent=new_obj)

    def _copy_node(self, parent: Self) -> Self:
        return self.__class__(
            line=self.line,
            parent=parent,
            tags=self.tags.copy(),
            template=self.template,
            undo=self.undo,
        )

    @property
    def config(self) -> str:
        """Рендер дерева в текстовую конфигурацию."""
        return CTreeRenderer.config(self)

    def config_by_tags(self, *tags: Tag, skip_no_tag: bool = True) -> Iterator[str]:
        """Генератор конфигурации в порядке переданных тегов."""
        yield from CTreeSorter.config_by_tags(*tags, node=self, skip_no_tag=skip_no_tag, mode="config")

    @property
    def config_masked(self) -> str:
        """Рендер дерева в текстовую конфигурацию с маскированием секретов."""
        config = CTreeRenderer.config(self)
        return CTreeRenderer.mask_output(output=config, spec=self.spec)

    def config_sorted(self, *tags: str, skip_no_tag: bool = True) -> str:
        return "\n".join(self.config_by_tags(*tags, skip_no_tag=skip_no_tag))

    def copy(self, with_children: bool = True) -> Self:
        """Копирование узла в новое дерево с сохранением пути до рута."""
        new_root = self.__class__.create_root(self.spec)
        parent = new_root
        for node in self.path():
            parent = node._copy_node(parent)
        if with_children:
            self._copy_children(nodes=self.children.values(), parent=parent)
        return new_root

    @classmethod
    def create_root(cls, spec: PlatformSpec) -> Self:
        """Создание root'а нового дерева для платформы."""
        root = cls(line="")
        root.spec = spec
        return root

    def delete(self) -> None:
        """Удаление узла и всех его потомков."""
        to_delete: list[CTree] = [self]
        stack: deque[CTree] = deque()
        if len(self.children) != 0:
            stack.extendleft(self.children.values())
        while len(stack) > 0:
            node = stack.popleft()
            to_delete.append(node)
            if len(node.children) != 0:
                stack.extend(reversed(node.children.values()))
        for node in reversed(to_delete):
            if node.parent is not None:
                node.parent.children.pop(node.line)

    def filter(
        self,
        *,
        string: str = "",
        include_tags: Sequence[str] | None = None,
        include_mode: Literal["or", "and"] = "or",
        exclude_tags: Sequence[str] | None = None,
        include_children: bool = False,
    ) -> Self:
        """Фильтрация нод по тегам/строке."""
        return CTreeFilter.filter(
            self,
            string=string,
            include_tags=include_tags,
            include_mode=include_mode,
            exclude_tags=exclude_tags,
            include_children=include_children,
        )

    @property
    def flatten(self) -> Iterator[Self]:
        stack: deque[Self] = deque(self.children.values())
        while stack:
            node = stack.popleft()
            yield node
            stack.extendleft(reversed(node.children.values()))

    @property
    def hash(self) -> str:
        """Ленивое вычисление хеша ветки."""
        if self._hash is None:
            self._hash = CTreeHasher.calc_hash(self)
        return self._hash

    @property
    def line(self) -> str:
        return self._line

    @line.setter
    def line(self, value: str) -> None:
        value = value.strip()
        if value == self._line:
            return
        self._line = value
        if self._hash is not None:
            self.reset_hash()

    @property
    def line_formal(self) -> str:
        """Конфигурационная команда с учетом полного пути."""
        return CTreeRenderer.node_formal_line(self)

    def merge(self, other: Self) -> None:
        """Слияние двух деревьев."""
        if self.spec != other.spec:
            raise ValueError("Слияние возможно только с одинаковой спецификацией")
        for node in other:
            if node.line not in self.children:
                node_copy = node._copy_node(self)
                self._copy_children(nodes=node.children.values(), parent=node_copy)
                self.reset_hash()
            else:
                self.children[node.line].merge(node)

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

    def node(self, *path: str) -> Self | None:
        """Получение узла по переданному в списке пути."""
        _node = self
        for line in path:
            if line not in _node.children:
                return None
            _node = _node.children[line]
        return _node

    @property
    def patch(self) -> str:
        """Рендер дерева в текстовый патч."""
        return CTreeRenderer.patch(self)

    def patch_by_tags(self, *tags: str, skip_no_tag: bool = True) -> Iterator[str]:
        """Генератор патча в порядке переданных тегов."""
        yield from CTreeSorter.config_by_tags(*tags, node=self, skip_no_tag=skip_no_tag, mode="patch")

    @property
    def patch_masked(self) -> str:
        """Рендер дерева в текстовый патч с маскированием секретов."""
        patch = CTreeRenderer.patch(self)
        return CTreeRenderer.mask_output(output=patch, spec=self.spec)

    def patch_sorted(self, *tags: str, skip_no_tag: bool = True) -> str:
        return "\n".join(self.patch_by_tags(*tags, skip_no_tag=skip_no_tag))

    def path(self, reverse: bool = True) -> list[Self]:
        """Путь от корня к узлу (reverse=True) или от ноды к корню (reverse=False) в виде списка нод."""
        return CTreeRenderer.node_path(self, reverse)

    def rebuild(self, deep: bool = False) -> None:
        """Обновляет дерево после изменений в line."""
        new_children = {child.line: child for child in self.children.values()}
        self.children = new_children
        if not deep:
            return
        for node in self:
            node.rebuild(deep)

    def reset_hash(self) -> None:
        """Сбрасывает хеш у себя и вверх по цепочке родителей."""
        CTreeHasher.reset_hash(self)

    def sort(self, *tags: str, reverse: bool = False) -> None:
        """Сортировка детей узла в указанном порядке тегов."""
        CTreeSorter.sort(*tags, node=self, reverse=reverse)

    def tags_add(self, *tags: str, deep: bool = True) -> None:
        """Добавляет теги к узлу и (deep=True) всем его потомкам."""
        _tags = set(tags)
        if not _tags:
            return
        if deep:
            for node in self:
                node.tags_add(*tags, deep=deep)
        self.tags.update(_tags)

    def tags_remove(self, *tags: str, deep: bool = True) -> None:
        """Удаляет теги у узла и (deep=True) всех его потомков."""
        _tags = set(tags)
        if not _tags:
            return
        if deep:
            for node in self:
                node.tags_remove(*tags, deep=deep)
        self.tags.difference_update(_tags)
        self.tags.difference_update(_tags)
