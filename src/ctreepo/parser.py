import re
from pathlib import Path

from ctreepo.ctree import CTree
from ctreepo.renderer import CTreeRenderer
from ctreepo.spec import PlatformRegistry
from ctreepo.tagging import TaggingRules
from ctreepo.utils.regex_cache import REGEX_CHARS, CTreeRegexCache

# при разборе конфига с шаблоном применяем следующие правила:
# - именованные группы остаются в шаблоне
# - позиционные и regex'ы вне групп заменяются на значения из конфигурационной строки
# сделано так для того, что бы можно было в шаблоне описывать общую структуру команды
# сохраняя при этом уникальность при конкретном конфиге, например синтаксис команды
# neighbor <neighbor-ip> route-map <map-name> in
# но в конфигурации есть разные neighbor-ip и map-name будет уникальна для каждого из них
# поэтому при применении входного шаблона вида
#  `neighbor \S+ route-map (?P<name>\S+) in`
# он будет специфицирован для каждого ip (потому что этот regex не в группе), шаблоны будут
#  - neighbor 1.2.3.4 route-map (?P<name>\S+) in
#  - neighbor 4.3.2.1 route-map (?P<name>\S+) in
# и так далее для каждого из соседей
# в undo части (после CTreeParser.UNDO_SEP в строке шаблона) можно делать референс на значения
# групп (позиционные и именованные), которые были захвачены в шаблоне. Например строка вида
#  `(description) (?<val>.*) UNDO>> no \1`
# будет трансформирована в шаблон `description (?<val>.*)` и undo `no description`
#
# итого:
# - именованные группы остаются в шаблоне и определяют параметры команды, при вычислении диффа
#   это учитывается и undo команда не выполняется, а опция просто переписывается командой с новыми параметрами
#   на значения можно делать бек-реф в undo части
# - позиционные группы меняются на реальные значения, т.е. пропадают из шаблона и при вычислении диффа это
#   обычный уникальный текст.
#   на значения можно делать бек-реф в undo части
# - обычные не групповые regex меняются на реальные значения, бек-реф в undo части не работает


class CTreeParser:
    UNDO_SEP = "UNDO>>"

    def __init__(
        self,
        platform: str,
        *,
        tagging_rules: TaggingRules | None = None,
        custom_platform_yaml: Path | None = None,
    ) -> None:
        if tagging_rules is None:
            self._tagging_rules = []
        else:
            self._tagging_rules = tagging_rules.rules.get(platform, [])
        self._spec = PlatformRegistry.get_spec(platform, custom_platform_yaml=custom_platform_yaml)

    def _get_tags(self, parent: CTree, line: str) -> set[str] | None:
        if len(self._tagging_rules) == 0:
            return None

        if parent.line:
            formal_parent = CTreeRenderer.node_formal_line(parent)
            formal_line = formal_parent + CTreeRenderer.formal_path_sep + line
        else:
            formal_line = line

        for rule in self._tagging_rules:
            if m := re.fullmatch(rule.regex, formal_line):
                return {
                    *(tag.format_map(m.groupdict()) for tag in rule.tags),
                    *m.groups(),
                }
        return None

    def _get_template_node(self, line: str, template_list: list[CTree]) -> CTree | None:
        # ищем узел в дереве шаблонов (передается текущий уровень)
        # под regex которого попадет конфигурационная строка
        for template in template_list:
            # if re.fullmatch(template.line, line) is not None:
            if CTreeRegexCache.get_pattern(template.line).fullmatch(line) is not None:
                return template
        # return None
        return CTree.create_root(self._spec)

    def _get_template_line(self, line: str, template_line: str) -> str:
        # если ноды нет (приходит пустой root), то и делать нечего, пустые строки возвращаем
        if not template_line:
            return ""

        # доп проверка, но как такое может быть пока не ясно, у нас template_node возвращается
        # по этому совпадению, возможно стоит исключить после проверки покрытия
        line_pattern = CTreeRegexCache.get_pattern(template_line)
        # if (m := re.fullmatch(template_line, line)) is None:
        #     return ""
        if (m := line_pattern.fullmatch(line)) is None:
            return ""

        template_result = ""

        pos, _ = m.regs[0]
        # должен быть всегда 0
        if pos != 0:
            raise ValueError("шаблон не захватывает начало конфигурационной строки")
        # дальше буду на примере шаблона 'ip address \S+(?: (?P<MASK>\S+)|(?P<PLEN>\/\d+))' и строки
        # 'ip address 192.168.100.1 255.255.255.255' детально описывать, а то после времени
        # было больно рефакторить процедуру

        # {'MASK': '\\S+', 'PLEN': '\\/\\d+'} - список паттернов в шаблоне, дальше в цикле разбора Match
        # объекта проверяю, есть ли имя группы в этом словаре и получаю сам паттерн, что бы скрафтить
        # template_result шаблон
        regex_pattern = CTreeRegexCache.get_pattern(REGEX_CHARS)
        patterns = dict(regex_pattern.findall(template_line))

        # в шаблоне может быть микс типов групп, нам нужно сохранить только именованные, поэтому
        # получаем их индексы (они есть всегда и они сквозные, даже если группа именованная)
        # {1: 'MASK', 2: 'PLEN'}
        named_group_by_index = {index: name for name, index in m.re.groupindex.items()}
        # regs это кортеж границ попадания в группы, включая группу 0 (все совпадение)
        # ((0, 40), (25, 40), (-1, -1))
        for group_indx, (start, end) in enumerate(m.regs):
            # если не именованная группа - пропускаем
            group = named_group_by_index.get(group_indx)
            if group is None:
                continue

            # если ничего в группе нет (нет совпадений) - пропускаем
            # в нашем примере такая ситуация будет для группы PLEN, там в шаблоне ИЛИ, и сработала другая группа
            if start == -1 and end == -1:
                continue

            # если не удалось найти паттерн для группы - пропускаем, хотя такого быть не должно
            pattern = patterns.get(group)
            if pattern is None:
                continue

            # крафтим строку шаблона по кускам, постепенно сдвигая pos указатель
            if start > pos:
                template_result += line[pos:start]
            template_result += f"(?P<{group}>{pattern})"
            pos = end
        if pos != 0 and pos < len(line):
            template_result += line[pos:]
        return template_result

    def _get_undo_line(self, line: str, template_undo: str, template_line: str) -> str:
        if not template_undo:
            return ""
        pattern = CTreeRegexCache.get_pattern(template_line)
        return pattern.sub(template_undo, line).strip()
        # return re.sub(template_line, template_undo, line).strip()

    def parse(self, config: str, template: CTree | None = None) -> CTree:
        root = CTree.create_root(self._spec)
        section = [root]
        spaces = [0]
        previous_node: CTree = root
        skip_pattern_re = re.compile("|".join(root.spec.junk_lines))

        # логика такая: дерево с шаблоном может быть в любом порядке составлено, т.е. если мы вошли в секцию
        # конфига, то это не значит, что в шаблоне вообще есть такая секция. поэтому для шаблона просто
        # следим за сменой уровня, и на каждом уровне делаем поиск на соответствие строки конфигурации
        if template is None:
            template = CTree.create_root(self._spec)
        template_stack = [list(template.children.values())]

        config = root.spec.pre_run(config)
        for line in config.splitlines():
            if len(line.strip()) == 0:
                continue
            if skip_pattern_re.fullmatch(line):
                continue

            # число пробелов у текущей строки
            current_space = len(line) - len(line.lstrip())

            if self.UNDO_SEP in line:
                line, undo = map(str.strip, line.split(sep=self.UNDO_SEP, maxsplit=1))
            else:
                line = line.lstrip()
                undo = ""

            # мы вошли в секцию
            if current_space > spaces[-1]:
                section.append(previous_node)
                spaces.append(current_space)
                # значит в последнем списке стека шаблонов ищем шаблон, который совпадет со строкой
                # previous_node, т.е. строкой-родителем для нашей текущей конфигурационной строки.
                previous_template = self._get_template_node(previous_node.line, template_stack[-1])
                if previous_template is None:
                    template_stack.append([])
                else:
                    template_stack.append(list(previous_template.children.values()))

            # мы вышли из секции
            elif current_space < spaces[-1]:
                while current_space != spaces[-1]:
                    section.pop()
                    spaces.pop()
                    template_stack.pop()

            parent = section[-1]
            tags = self._get_tags(parent, line)

            if line in parent.children:
                previous_node = parent.children[line]
            else:
                # делаем поиск по верхнему списку шаблонов, есть что-то, что покрывает нашу конфигурационную строку
                template_node = self._get_template_node(line, template_stack[-1])
                # - line - конфигурация из переданной строки, не меняем(!), могут быть спец символы, скобки и пр.
                # - undo - из переданной строки - не меняем, этот undo прилетел из сырого конфига, ну типа
                #   побочный эффект как можно задать undo, прямо в конфиге, но без бек-рефа. можно делать как
                #   быстрый способ что бы шаблон не создавать
                # - template_node (line + undo) - шаблон line нужно модифицировать (разобрать группы), в undo нужно
                #   раскрыть бек-реф
                if template_node is None:
                    template_line = ""
                    undo_line = ""
                else:
                    template_line = self._get_template_line(line, template_node.line)
                    undo_line = self._get_undo_line(line, template_node.undo, template_node.line)

                previous_node = CTree(
                    line=line,
                    parent=parent,
                    tags=tags,
                    template=template_line,
                    # оставляем за сырым undo приоритет
                    undo=undo or undo_line,
                )

        root.spec.post_run(root)
        return root
