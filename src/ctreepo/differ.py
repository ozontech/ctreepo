import re
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar, cast

from ctreepo.renderer import CTreeRenderer
from ctreepo.sorter import CTreeSorter
from ctreepo.spec.diff_handler_registry import DiffHandlerRegistry

if TYPE_CHECKING:
    from ctreepo.ctree import CTree

__all__ = ("CTreeDiffer",)


T = TypeVar("T", bound="CTree")

# CTreeDiffer считает разница между двумя деревьями, по умолчанию сравниваем то, что должно быть с тем, что есть
# и формируем разницу. Затем удаляем узлы на основе шаблонов, что бы при изменении параметров
# например load-interval 30 -> load-interval 60 можно было сказать, что 30/60 это опция и достаточно просто сказать
# load-interval 60, она перепишет load-interval 30 и нет необходимости делать no load-interval 30
#
# sections_without_diff
# в спецификации платформы можно указать regex для секций, у которых не вычисляется diff, а
# которые перезаписываются целиком, например rpl в IOS-XR: при входе в такую секцию старая стирается и новую
# нужно полностью перебить, а не докатывать разницу. При поиске узлов, которые нужно удалить если в целевом дереве
# дереве секции нет ИЛИ хеши узлов текущего и целевого дерева разные, то рекурсивно не проваливаемся внутрь
# (как при обычном сравнении) а просто говорим, что секцию нужно удалить. При поиске узлов, которые нужно добавить
# логика такая же: если узла в текущем дереве нет ИЛИ хеши разные, то полностью копируем узел со всеми потомками.
# Когда нужно или удалить или добавить секцию разницы с обычным сравнением нет, когда нужно поменять - рекурсивно
# не проваливаемся, а действуем так, как будто секцию нужно удалить и потом добавить. В результате в диффе будет
# no section-name/section-name, это, конечно, можно через шаблон убрать (no section-name), но подразумевается, что
# для таких секций это должно автоматически делаться, поэтому дополнительно это проверяем.
#
# ordered_sections
# в спецификации платформы так же указываем regex секций, которые считаем чувствительными к порядку команд, например
# порядок tacacs серверов в группе, или acl без entry (как в старых IOS). Тут логика сложнее: мы берем узел из
# целевого дерева и начинаем идти по текущему до тех пор, пока не найдем совпадение, все, что прошли до этого - под
# удаление. Как только нашли совпадение, берем следующий узел целевого дерева и продолжаем движение по текущему
# дерево до совпадения, что успели пройти - под удаление. Дальше перед получением списка узлов, которые нужно добавить,
# нужно сделать "применение" промежуточного результата, т.е. удалить узлы, которые мы отметили под удаление, иначе они
# будут не будут давать возможно корректно добавить узлы (они же уже есть).


class CTreeDiffer:
    DEL_TAG = "diff-del"
    ADD_TAG = "diff-add"
    REMOVE_UNDO = "<<--n/a-->>"

    @classmethod
    def _check_no_diff_section(cls, node: T) -> bool:
        # TODO не тестировал скорость, но интересно, если через "|".join() делать без цикла, будет ли быстрее
        for section in node.spec.sections_no_diff:
            if re.fullmatch(section, node.line_formal):
                return True
        return False

    @classmethod
    def _check_ordered_section(cls, node: T) -> bool:
        # TODO такой же вопрос, как с no-diff
        for section in node.spec.ordered_sections:
            if re.fullmatch(section, node.line_formal):
                return True
        return False

    @classmethod
    def _remove_undo_nodes(cls, root: T) -> None:
        # удаляем:
        # - по совпадению шаблонов
        #   no load-interval 30
        #   load-interval 60
        #   с шаблоном `load-interval (?<VAL>\d+)` настраивают один и тот же параметр, и
        #   нужно убрать undo-вариант, так как параметр будет перезаписан новым значением
        # - по спец "UNDO>> <<--n/a-->>" маркеру
        # - для section-no-diff если есть настройка и удаление секции, то удаление нужно удалить
        #   no prefix-set ps-some-networks <<-- вот это лишняя
        #   prefix-set ps-some-networks
        #    5.6.7.0/24
        #   !
        def _add_matched_node(pattern: re.Pattern[str], node: T) -> None:
            for child in node:
                # ищем только undo-ноды
                if cls.DEL_TAG not in child.tags:
                    continue
                if pattern.fullmatch(child.line):
                    to_delete.add(child)
                    return

        to_delete: set[T] = set()
        for node in root:
            if len(node.children) != 0:
                cls._remove_undo_nodes(node)
            # если специально отмечено, что undo для этой команды не применимо, то удаляем узел
            if cls.DEL_TAG in node.tags and node.undo == cls.REMOVE_UNDO:
                to_delete.add(node)
                continue
            # если это no-diff секция, то просто ищем undo этой секции и удаляем его
            no_diff = cls._check_no_diff_section(node)
            if no_diff:
                undo_node = root[rf"{node.spec.undo} {node.line}"]
                if undo_node is not None:
                    to_delete.add(undo_node)
                # дальше смотреть смысла нет, так как такие секции переписываются полностью
                continue
            # нет шаблона - нечего и смотреть
            if len(node.template) == 0:
                continue
            # задача найти undo-ноды соответствующие добавляемым, поэтому смотрим только на ADD ноды
            if cls.ADD_TAG not in node.tags:
                continue
            # у нас строки с undo в начале, поэтому нужно к шаблону добавить undo
            pattern = re.compile(rf"{node.spec.undo} {node.template}")
            if node.parent is not None:
                _add_matched_node(pattern, node.parent)

        for node in to_delete:
            node.delete()

    @classmethod
    def _get_masked_node(cls, line: str, root: T) -> T | None:
        masked_line = CTreeRenderer.mask_output(line, root.spec)
        for child in root:
            masked_child = CTreeRenderer.mask_output(child.line, root.spec)
            if masked_child == masked_line:
                return child
        return None

    @classmethod
    def _get_ordered_nodes_to_delete(cls, current: T, target: T) -> list[T]:
        if current == target:
            return []
        # суть такая: есть глобальный indx для продвижения по current и есть текущий узел из
        # target. берем очередной текущий узел из target и увеличиваем indx пока пока узел из
        # current по позиции indx не будет равен текущему из target. все что прошли - удаляем
        # когда встретили равенство, берем следующий очередной из target и продолжаем увеличивать
        # indx.
        result = []
        max_indx = len(current)
        current_list = cast("list[T]", list(current))

        # TODO переписать без break
        indx = 0
        for target_child in target:
            while indx < max_indx:
                current_child = current_list[indx]
                indx += 1
                if target_child == current_child:
                    break
                root = current_child.copy(with_children=False)
                node = list(root.flatten)[-1]
                node.line = f"{node.spec.undo} {node.line}"
                node.tags_add(cls.DEL_TAG, deep=False)
                if node.parent is not None:
                    node.parent.rebuild()
                result.append(root)
            if indx == max_indx:
                break

        return result

    @classmethod
    def _get_ordered_nodes_to_add(cls, current: T, target: T) -> list[T]:
        if current == target:
            return []
        # суть такая: секция упорядоченная, поэтому в пределе мы просто копируем target как есть,
        # тогда последовательность сохранится. Но у нас в current возможно уже есть какая-то верхняя
        # часть (head) из target, нужно только найти, где она заканчивается и копировать все, что ниже.
        # для этого идем сверху по target и ищем позицию равной target_child ноды в current (если такой
        # нет, то копируем весь target). Как только нашли, берем следующий target_child и ищем в current
        # дальше (не сначала), нам важно обеспечить правильный порядок. И так далее, пока не дойдем до конца
        # current, тут считаем, что нужно копировать все в низ от текущего target_child (включая его).
        # само копирование делаем наоборот - сначала копируем весь target, идем по этой копии, и удаляем
        # то, что есть в current, в остатке получаем низ target, который нужно добавить

        max_indx = len(current)
        current_list = list(current)
        root = target.copy(with_children=True)
        path = [n.line for n in target.path()]
        new_target = root.node(*path)
        assert new_target is not None
        to_delete: set[T] = set()

        # TODO переписать без break
        indx = 0
        for target_child in new_target:
            while indx < max_indx:
                current_child = current_list[indx]
                indx += 1
                if target_child == current_child:
                    to_delete.add(target_child)
                    break
            if indx == max_indx:
                break
        for node in to_delete:
            node.delete()
        return [root]

    @classmethod
    def _get_nodes_to_delete(
        cls,
        current: T,  # текущая конфигурация
        target: T,  # целевая конфигурация
        masked: bool,
    ) -> list[T]:
        def _copy_node() -> None:
            # делаем копию текущего узла без потомков
            root = current_child.copy(with_children=False)
            # нам возвращается корень, поэтому нужно спуститься в самый низ, там одна нода, поэтому можно
            # просто flatten использовать, ну или как в _to_add через path путь получить
            node = list(root.flatten)[-1]
            # формируем наивную undo строку, дальше отдельно будем поправим, если если node.undo
            node.line = f"{node.spec.undo} {node.line}"
            # так же докидываем служебный тег, что бы можно было потом использовать/фильтровать
            node.tags_add(cls.DEL_TAG, deep=False)
            # обновляем часть дерева, так как поменяли строку
            if node.parent is not None:
                node.parent.rebuild()
            result.append(root)

        # первым делом проверяем, важен ли порядок в текущей секции
        ordered = cls._check_ordered_section(target)
        # если да, то перенаправляем в другой алгоритм
        if ordered:
            return cls._get_ordered_nodes_to_delete(current, target)

        result = []
        # ищем ноды, которые нужно удалить, поэтому бегаем по current и проверяем, если ли они в target
        for current_child in current:
            # проверяем, нужно ли для текущего узла вообще дифф вычислять
            no_diff = cls._check_no_diff_section(current_child)
            # если поиск с учетом маскировки секретов
            if masked:
                target_child = cls._get_masked_node(current_child.line, target)
            else:
                target_child = target[current_child.line]
            # в target нет текущего узла - полностью удаляем узел из current
            if target_child is None:
                _copy_node()
            # ИЛИ для _no_diff: в target есть узел, но он не равен current_child
            # TODO интересно как сочетать маскирование и no_diff в одной ноде, в реальности
            # такого быть не должно, но желательно предусмотреть это
            elif no_diff and target_child != current_child:
                _copy_node()
            # в target есть текущий узел и они равны - пропускаем
            elif target_child == current_child:
                continue
            # во всех остальных случая проваливаемся рекурсивно в сравнении current_child <> target_child
            else:
                nested_result = cls._get_nodes_to_delete(current_child, target_child, masked)
                result.extend(nested_result)
        return result

    @classmethod
    def _get_nodes_to_add(
        cls,
        current: T,  # текущая конфигурация
        target: T,  # целевая конфигурация
        masked: bool,
    ) -> list[T]:
        def _copy_node() -> None:
            root = target_child.copy(with_children=True)
            # так же докидываем служебный тег, что бы можно было потом использовать/фильтровать
            path = [n.line for n in target_child.path()]
            copied_node = root.node(*path)
            assert copied_node is not None
            copied_node.tags_add(cls.ADD_TAG, deep=True)
            result.append(root)

        # первым делом проверяем, важен ли порядок в текущей секции
        ordered = cls._check_ordered_section(target)
        # если да, то перенаправляем в другой алгоритм
        if ordered:
            return cls._get_ordered_nodes_to_add(current, target)

        result = []
        # ищем ноды, которые нужно добавить, поэтому бегаем по target и проверяем, если ли они в current
        for target_child in target:
            # проверяем, нужно ли секцию вообще дифф вычислять
            no_diff = cls._check_no_diff_section(target_child)
            # если поиск с учетом маскировки секретов
            if masked:
                current_child = cls._get_masked_node(target_child.line, current)
            else:
                current_child = current[target_child.line]
            # в current нет текущего target_child узла - полностью добавляем (с потомками) узел в current
            if current_child is None:
                _copy_node()
            # ИЛИ для no_diff: в current есть узел, но он не равен target_child
            elif no_diff and current_child != target_child:
                _copy_node()
            # в current есть текущий target_child узел и они равны - ничего не делаем
            elif current_child == target_child:
                continue
            # в остальных случаях (в current есть узел, но нет равенства) - спускаемся рекурсивно на уровень ниже
            else:
                nested_result = cls._get_nodes_to_add(current_child, target_child, masked)
                result.extend(nested_result)
        return result

    @classmethod
    def _align_undo_lines(cls, root: T) -> None:
        # в самом конце пробегаем по получившемуся результату и правим undo строки по следующей логике:
        # - если есть node.undo, то заменяем line на undo
        # - если строка начинается с двойного undo, то убираем их (значит изначально была настройка вида no ...)
        double_undo = f"{root.spec.undo} " * 2
        # TODO тут может есть смысл не flatten а рекурсию сделать, что бы можно было делать rebuild отдельных
        # секций, так как сейчас этот момент пропущен и после изменения line ключ в children остается старым
        for node in root.flatten:
            # смотрим только удаляемые команды
            if cls.DEL_TAG not in node.tags:
                continue
            if node.undo:
                node.line = node.undo
            elif node.line.startswith(double_undo):
                node.line = node.line.removeprefix(double_undo)

    @classmethod
    def diff(
        cls,
        current: T,
        target: T,
        *,
        # проверяем строки после маскировки секретов (True), или до (False)
        masked: bool = False,
        diff_handlers: list[Callable[[T, T, T], None]] | None = None,
    ) -> T:
        if target.spec.name != current.spec.name:
            raise RuntimeError("деревья должны быть одной спецификации")

        root = current.__class__.create_root(current.spec)

        # сначала то, что нужно удалить из current,
        # т.е. те узлы, которые есть в current, но отсутствуют в target
        diff_list = cls._get_nodes_to_delete(current, target, masked)
        for node in diff_list:
            root.merge(node)

        # теперь то, что нужно добавить в current,
        # т.е. узлы, которых нет в current, но есть в target
        diff_list = cls._get_nodes_to_add(current, target, masked)
        for node in diff_list:
            root.merge(node)

        # чистим от мусора
        cls._remove_undo_nodes(root)

        # если есть специфичная undo, то меняем наивную версию на специфику
        cls._align_undo_lines(root)

        # TODO это сюда вставил, но по хорошему нужно в _remove_undo_nodes и _align_undo_lines
        # отлавливать моменты где у нас получается расхождение line и ключей children и там точечно
        # делать rebuild, а на массой на весь дифф
        root.rebuild(deep=True)

        CTreeSorter.sort(cls.ADD_TAG, cls.DEL_TAG, node=root)

        # пробегаем по post-proc правилам и дорабатываем diff
        if diff_handlers is None:
            for func in DiffHandlerRegistry.get(root.spec.name):
                func(root, current, target)
        else:
            for func in diff_handlers:  # type: ignore[assignment]
                func(root, current, target)

        return root
