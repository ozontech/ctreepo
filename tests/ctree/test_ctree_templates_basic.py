from collections import deque
from textwrap import dedent

import pytest

from ctreepo import CTreeParser, Platform, settings


@pytest.mark.parametrize(
    "config, template, result_template, result_undo_line",
    [
        # базовый тест
        (
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description description
                 ip mtu 1200
                #
                """,
            ),
            dedent(
                r"""
                interface \S+
                 description (?P<DESCRIPTION>.*)
                 ip mtu (?P<MTU>\d+)
                #
                """,
            ),
            dedent(
                r"""
                <empty-line>
                description (?P<DESCRIPTION>.*)
                ip mtu (?P<MTU>\d+)
                """,
            ).strip(),
            dedent(
                r"""
                <empty-line>
                <empty-line>
                <empty-line>
                """,
            ).strip(),
        ),
        # два объекта на один шаблон
        (
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description description
                 ip mtu 1200
                #
                interface GigabitEthernet1/0/2
                 description description
                 load-interval 30
                 speed 100
                #
                """,
            ),
            dedent(
                r"""
                interface \S+
                 description (?P<DESCRIPTION>.*)
                 ip mtu (?P<MTU>\d+)
                 load-interval (?P<INTERVAL>\d+)
                #
                """,
            ),
            dedent(
                r"""
                <empty-line>
                description (?P<DESCRIPTION>.*)
                ip mtu (?P<MTU>\d+)
                <empty-line>
                description (?P<DESCRIPTION>.*)
                load-interval (?P<INTERVAL>\d+)
                <empty-line>
                """,
            ).strip(),
            dedent(
                r"""
                <empty-line>
                <empty-line>
                <empty-line>
                <empty-line>
                <empty-line>
                <empty-line>
                <empty-line>
                """,
            ).strip(),
        ),
        # вложенные группы
        (
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description description
                 ip mtu 1200
                #
                """,
            ),
            dedent(
                r"""
                interface \S+
                 (description) ((?P<DESCRIPTION>.*))
                 ip mtu (?P<MTU>\d+)
                 load-interval (?P<INTERVAL>\d+)
                #
                """,
            ),
            dedent(
                r"""
                <empty-line>
                description (?P<DESCRIPTION>.*)
                ip mtu (?P<MTU>\d+)
                """,
            ).strip(),
            dedent(
                r"""
                <empty-line>
                <empty-line>
                <empty-line>
                """,
            ).strip(),
        ),
        # шаблон на удаление
        (
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description description
                 ip mtu 1200
                 some-command
                #
                """,
            ),
            dedent(
                rf"""
                interface \S+
                 (description) ((?P<DESCRIPTION>.*)) {settings.TEMPLATE_SEPARATOR} undo \1
                 ip mtu (?P<MTU>\d+) {settings.TEMPLATE_SEPARATOR} undo ip mtu
                 load-interval (?P<INTERVAL>\d+)
                #
                """,
            ),
            dedent(
                r"""
                <empty-line>
                description (?P<DESCRIPTION>.*)
                ip mtu (?P<MTU>\d+)
                <empty-line>
                """,
            ).strip(),
            dedent(
                r"""
                <empty-line>
                undo description
                undo ip mtu
                <empty-line>
                """,
            ).strip(),
        ),
        # шаблон на удаление с комбинацией групп
        (
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description description
                 ip mtu 1200
                 some-command
                #
                """,
            ),
            dedent(
                rf"""
                interface \S+
                 (description) ((?P<DESCRIPTION>.*)) {settings.TEMPLATE_SEPARATOR} undo \1 \3 \2
                 ip mtu (?P<MTU>\d+) {settings.TEMPLATE_SEPARATOR} undo ip mtu
                 load-interval (?P<INTERVAL>\d+)
                #
                """,
            ),
            dedent(
                r"""
                <empty-line>
                description (?P<DESCRIPTION>.*)
                ip mtu (?P<MTU>\d+)
                <empty-line>
                """,
            ).strip(),
            dedent(
                r"""
                <empty-line>
                undo description description description
                undo ip mtu
                <empty-line>
                """,
            ).strip(),
        ),
        # пример для AP у wlc
        (
            dedent(
                """
                ap-id 123 type-id 321 ap-mac cafe-dead-abcd ap-sn 123456
                 ap-name my-test-ap
                #
                """,
            ),
            dedent(
                rf"""
                ap-id (\d+) type-id \d+ ap-mac \S+ ap-sn \S+ {settings.TEMPLATE_SEPARATOR} undo ap ap-id \1
                """,
            ),
            dedent(
                r"""
                <empty-line>
                <empty-line>
                """,
            ).strip(),
            dedent(
                r"""
                undo ap ap-id 123
                <empty-line>
                """,
            ).strip(),
        ),
        # группа без совпадения
        (
            dedent(
                """
                snmp-server community read public000
                snmp-server community read public111 acl 111
                snmp-server community read public222 acl 222 view iso-old
                snmp-server community read public333 view iso-new
                #
                """,
            ),
            dedent(
                rf"""(snmp-server community read \S+)(?: acl (?P<ACL>\S+))?(?: view (?P<VIEW>\S+))? """
                rf"""{settings.TEMPLATE_SEPARATOR} undo \1""",
            ),
            dedent(
                r"""
                <empty-line>
                snmp-server community read public111 acl (?P<ACL>\S+)
                snmp-server community read public222 acl (?P<ACL>\S+) view (?P<VIEW>\S+)
                snmp-server community read public333 view (?P<VIEW>\S+)
                """,
            ).strip(),
            dedent(
                r"""
                undo snmp-server community read public000
                undo snmp-server community read public111
                undo snmp-server community read public222
                undo snmp-server community read public333
                """,
            ).strip(),
        ),
        # некорректный паттерн
        (
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description test interface
                #
                """,
            ),
            dedent(
                r"""
                interface \S+
                 description (?P<DESCRIPTION>\S+ \S+)
                #
                """,
            ),
            dedent(
                r"""
                <empty-line>
                <empty-line>
                """,
            ).strip(),
            dedent(
                r"""
                <empty-line>
                <empty-line>
                """,
            ).strip(),
        ),
    ],
)
def test_ctree_template_basic(config: str, template: str, result_template: str, result_undo_line: str) -> None:
    parser = CTreeParser(platform=Platform.HUAWEI_VRP)

    template_tree = parser.parse(template)
    root = parser.parse(config, template_tree)
    q = deque(list(root.children.values())[::-1])
    node_templates = []
    node_undo_lines = []
    while len(q) != 0:
        node = q.pop()
        q.extend(list(node.children.values())[::-1])
        node_templates.append(node.template if len(node.template) != 0 else "<empty-line>")
        node_undo_lines.append(node.undo_line if len(node.undo_line) != 0 else "<empty-line>")
    node_templates_str = "\n".join(node_templates)
    node_undo_lines_str = "\n".join(node_undo_lines)

    assert node_templates_str == result_template
    assert node_undo_lines_str == result_undo_line
