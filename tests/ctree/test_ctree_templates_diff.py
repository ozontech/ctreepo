from textwrap import dedent

import pytest

from ctreepo import CTreeDiffer, CTreeParser, Platform, settings


@pytest.mark.parametrize(
    "current_str, target_str, template, diff_str",
    [
        # использование undo_line
        (
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description test description
                 ip mtu 1200
                 load-interval 30
                #
                interface GigabitEthernet1/0/2
                 description test description
                 ip mtu 1200
                 ip address 1.2.3.4 255.255.255.0
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description test description
                 load-interval 30
                #
                interface GigabitEthernet1/0/2
                 ip mtu 1200
                 ip address 1.2.3.4 255.255.255.0
                #
                """,
            ),
            dedent(
                rf"""
                interface \S+
                 description (?P<DESCRIPTION>.*) {settings.TEMPLATE_SEPARATOR} undo description
                 ip mtu (?P<MTU>\d+)
                 load-interval (?P<INTERVAL>\d+)
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 undo ip mtu 1200
                #
                interface GigabitEthernet1/0/2
                 undo description
                #
                """,
            ).strip(),
        ),
        # использование undo_line для undo команд
        (
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description test description
                 load-interval 30
                 undo keepalive
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description test description
                 load-interval 30
                #
                """,
            ),
            dedent(
                rf"""
                interface \S+
                 description (?P<DESCRIPTION>.*) {settings.TEMPLATE_SEPARATOR} undo description
                 ip mtu (?P<MTU>\d+)
                 load-interval (?P<INTERVAL>\d+)
                 undo keepalive {settings.TEMPLATE_SEPARATOR} keepalive
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 keepalive
                #
                """,
            ).strip(),
        ),
    ],
)
def test_ctree_template_diff(current_str: str, target_str: str, template: str, diff_str: str) -> None:
    parser = CTreeParser(platform=Platform.HUAWEI_VRP)

    template_tree = parser.parse(template)
    current = parser.parse(current_str, template_tree)
    target = parser.parse(target_str, template_tree)
    diff = CTreeDiffer.diff(current, target)

    assert diff.config == diff_str


def test_ctree_template_diff_ordered() -> None:
    current_str = dedent(
        """
        interface Vbdif1234
         mtu 9000
        #
        xpl route-filter RP_XPL_1
         refuse
         end-filter
        #
        xpl route-filter RP_XPL_2
         refuse
         end-filter
        #
        snmp community public
        """,
    )
    target_str = dedent(
        """
        interface Vbdif1234
         mtu 9216
        #
        xpl route-filter RP_XPL_1
         pass
         end-filter
        #
        snmp community public
        """,
    )
    template_str = dedent(
        rf"""
        interface \S+
         mtu (?P<MTU>\d+)
        #
        (xpl route-filter (\S+))  {settings.TEMPLATE_SEPARATOR} undo \1 test > \2
        #
        """,
    )
    diff_str = dedent(
        """
        interface Vbdif1234
         mtu 9216
        #
        xpl route-filter RP_XPL_1
         pass
         end-filter
        #
        undo xpl route-filter RP_XPL_2 test > RP_XPL_2
        #
        """,
    ).strip()

    parser = CTreeParser(platform=Platform.HUAWEI_VRP)

    template = parser.parse(template_str)
    current = parser.parse(current_str, template)
    target = parser.parse(target_str, template)

    diff = CTreeDiffer.diff(current, target, no_diff_sections=[r"xpl.*"])

    assert diff.config == diff_str
