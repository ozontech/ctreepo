import re
from collections import deque
from typing import Literal

from . import settings
from .ctree import CTree
from .models import DiffAction
from .postproc import _REGISTRY, CTreePostProc

__all__ = ("CTreeDiffer",)


class CTreeDiffer:
    @classmethod
    def _check_ordered(cls, a: CTree, ordered_sections: list[str] | None = None) -> bool:
        if ordered_sections is not None:
            for section in ordered_sections:
                formal_line = " / ".join(a._formal_path)
                if re.fullmatch(section, formal_line):
                    return True
        return False

    @classmethod
    def _check_no_diff(cls, a: CTree, no_diff_sections: list[str] | None = None) -> bool:
        if not isinstance(no_diff_sections, list) or no_diff_sections is None:
            return False
        for section in no_diff_sections:
            formal_line = " / ".join(a._formal_path)
            if re.search(section, formal_line):
                return True
        return False

    @classmethod
    def _delete_nodes_by_template(cls, root: CTree) -> None:
        to_delete: set[CTree] = set()
        for node in root.children.values():
            if len(node.children) != 0:
                cls._delete_nodes_by_template(node)
            if len(node.template) == 0:
                continue
            patterns = []
            if len(node.undo_line) != 0:
                patterns.append(node.undo_line)
            if node.line.startswith(f"{node.undo} "):
                patterns.append(node.template.replace(f"{node.undo} ", "", 1))
            else:
                patterns.append(f"{node.undo} {node.template}")
            pattern = "|".join(patterns)
            for n in root.children.values():
                if re.fullmatch(pattern, n.line):
                    to_delete.add(n)
        for node in to_delete:
            node.delete()

    @classmethod
    def _diff_list(
        cls,
        a: CTree,  # текущая конфигурация
        b: CTree,  # целевая
        *,
        existed_diff: CTree | None = None,
        ordered_sections: list[str] | None = None,
        no_diff_sections: list[str] | None = None,
        masked: bool = False,
        negative: bool = False,  # если True, то вычисляем, что нужно удалить, т.е. чего нет в целевой конфигурации
    ) -> list[CTree]:
        result = []
        _ordered = cls._check_ordered(a, ordered_sections)
        indx = 0
        if existed_diff is not None:
            b = b.apply(existed_diff)
        for child in a.children.values():
            # для секций, требующих полной перезаписи (без вычисления diff'a)
            _no_diff = cls._check_no_diff(child, no_diff_sections)
            if _no_diff:
                # делаем <undo> <section> (если она есть) когда negative=True
                #! upd: не делаем, потому что будет reordering и <undo> уедет в конец, если
                #! нужно удалять секцию, то это нужно добавлять через post-processing
                #! upd2: не понял, к чему это было и почему проблему вызывает, но без этого
                #! не работает корректно вычисление разницы
                if negative:
                    if not child.exists_in(b):
                        root = child.copy(children=not negative)
                        node = root
                        while len(node.children) == 1:
                            node = list(node.children.values())[0]
                        if len(node.undo_line) != 0:
                            node.line = node.undo_line
                        else:
                            node.line = f"{node.undo} {node.line}"
                        root.rebuild(deep=True)
                        result.append(root)
                # целиком добавляем (negative=False)
                else:
                    line = child.exists_in(b)
                    if len(line) == 0 or child != b.children.get(line):
                        root = child.copy(children=True)
                        result.append(root)
                continue
            if _ordered:
                if len(b.children) > indx and child.line == list(b.children.values())[indx].line:
                    line = child.line
                    indx += 1
                else:
                    line = ""
            else:
                line = child.exists_in(b, masked)
            if len(line) == 0:
                root = child.copy(children=not negative)
                if negative:
                    node = root
                    while len(node.children) == 1:
                        node = list(node.children.values())[0]
                    if node.line.startswith(f"{node.undo} "):
                        if len(node.undo_line) != 0:
                            node.line = node.undo_line
                        else:
                            node.line = node.line.replace(f"{node.undo} ", "", 1)
                        # пока не знаю, нужно ли модифицировать шаблоны или нет, с первого взгляда нет
                        # так как тогда эти ноды станут как и "оригинальными" (из целевого шаблона).
                        # по логике мы их должны находить у удалять на основе шаблона оригинальной ноды
                        # node.template = node.template.replace(f"{node.undo} ", "", 1)
                    else:
                        if len(node.undo_line) != 0:
                            node.line = node.undo_line
                        else:
                            node.line = f"{node.undo} {node.line}"

                        # выше комментарий про модификацию шаблона
                        # if len(node.template) != 0:
                        #     node.template = f"{node.undo} {node.template}"
                        # else:
                        #     node.template = ""
                    root.rebuild(deep=True)
                result.append(root)
            else:
                # проваливаемся в рекурсивное сравнение потомков только если
                # они существуют и (хеши нод разные или секция _ordered)
                if len(child.children) != 0 and (
                    child.node_hash != b.children[line].node_hash
                    or _ordered
                    # если где-то забыли хеш посчитать
                    or len(child.node_hash) == 0
                ):
                    nested_result = cls._diff_list(
                        child,
                        b.children[line],
                        existed_diff=None,
                        ordered_sections=ordered_sections,
                        no_diff_sections=no_diff_sections,
                        masked=masked,
                        negative=negative,
                    )
                    result.extend(nested_result)
        return result

    @classmethod
    def diff(
        cls,
        a: CTree,
        b: CTree,
        *,
        masked: bool = False,
        ordered_sections: list[str] | None = None,
        no_diff_sections: list[str] | None = None,
        reorder_root: bool = True,
        post_proc_rules: list[type[CTreePostProc]] | None = None,
    ) -> CTree:
        # TODO тут подумать, что бы сразу в нужный parent крепить узел, а не делать merge списка потом

        if a.__class__ != b.__class__:
            raise RuntimeError("a and b should be instances of the same class")

        root = a.__class__()

        diff_list = cls._diff_list(
            a,
            b,
            existed_diff=None,
            ordered_sections=ordered_sections,
            no_diff_sections=no_diff_sections,
            masked=masked,
            negative=True,
        )
        for leaf in diff_list:
            root.merge(leaf)

        diff_list = cls._diff_list(
            b,
            a,
            existed_diff=root,
            ordered_sections=ordered_sections,
            no_diff_sections=no_diff_sections,
            masked=masked,
            negative=False,
        )
        for leaf in diff_list:
            root.merge(leaf)

        negative = {node.line: node for node in root.children.values() if node.line.startswith(node.undo)}
        for node in negative.values():
            node.tags.append(settings.TAG_ON_UNDO)
        if reorder_root:
            positive = {node.line: node for node in root.children.values() if not node.line.startswith(node.undo)}
            root.children = positive | negative

        # пробегаем по diff и удаляем ноды, которые совпадают по шаблонам
        cls._delete_nodes_by_template(root)

        # пробегаем по post-proc правилам и дорабатываем diff
        if post_proc_rules is None:
            post_proc_rules = _REGISTRY.get(root.vendor) or []
        for rule in post_proc_rules:
            rule.process(root)

        return root

    @classmethod
    def _human_diff(cls, current: CTree, target: CTree) -> list[CTree]:
        def _add_node(action: DiffAction, node: CTree) -> None:
            node_copy = node.copy(action != DiffAction.EXISTS)
            line = node_copy.line
            n = node_copy
            while line != node.line:
                n = list(n.children.values())[0]
                line = n.line
            n.prefix = action
            result.append(node_copy)
            if action == DiffAction.EXISTS:
                return
            nodes = deque(node_copy.children.values())
            while nodes:
                n = nodes.pop()
                nodes.extendleft(n.children.values())
                n.prefix = action

        result: list[CTree] = []
        indx = 0
        for node in current.children.values():
            if node.line not in target.children:
                _add_node(DiffAction.DEL, node)
                continue

            target_indx_node = list(target.children).index(node.line)
            while indx < target_indx_node:
                line = list(target.children)[indx]
                if line not in current.children:
                    _add_node(DiffAction.ADD, target.children[line])
                indx += 1

            # вот тут важно добавлять узел с ' ', что бы потом при merge он не перетирался
            # узлами с '+'/'-'
            _add_node(DiffAction.EXISTS, node)
            result.extend(cls._human_diff(node, target.children[node.line]))

        while indx < len(target.children):
            if list(target.children)[indx] not in current.children:
                node = list(target.children.values())[indx]
                _add_node(DiffAction.ADD, node)
            indx += 1

        return result

    @classmethod
    def _human_diff_remove_existed(cls, root: CTree) -> None:
        to_delete: set[CTree] = set()
        for node in root.children.values():
            if len(node.children) != 0:
                cls._human_diff_remove_existed(node)
            if node.prefix == DiffAction.EXISTS and len(node.children) == 0:
                to_delete.add(node)
        for node in to_delete:
            node.delete()

    @classmethod
    def human_diff(
        cls,
        current: CTree,
        target: CTree,
        mode: Literal["full", "diff-only"] = "diff-only",
    ) -> str:
        root = current.__class__()
        diff_list = cls._human_diff(current, target)
        for node in diff_list:
            root.merge(node)
        if mode == "diff-only":
            cls._human_diff_remove_existed(root)
        return root.config
