from textwrap import dedent

import pytest

from ctreepo.parser import CTreeParser


@pytest.mark.parametrize(
    ("line", "template", "undo"),
    [
        (
            "description test-0",
            r"description (?P<VAL>.*)",
            "no description test-0",
        ),
        (
            "ip address 192.168.0.1 255.255.255.255",
            r"ip address 192.168.0.1(?P<MASK>\s+[\d.]+)",
            "no ip address 192.168.0.1 255.255.255.255",
        ),
        (
            "ip address 192.168.0.2 255.255.255.255 secondary",
            r"ip address 192.168.0.2(?P<MASK>\s+[\d.]+) secondary",
            "no ip address 192.168.0.2 255.255.255.255 secondary",
        ),
        (
            "ip address 192.168.0.3/32",
            r"ip address 192.168.0.3(?P<PLEN>\/\d+)",
            "no ip address 192.168.0.3/32",
        ),
        (
            "ip address 192.168.0.4/32 secondary",
            r"ip address 192.168.0.4(?P<PLEN>\/\d+) secondary",
            "no ip address 192.168.0.4/32 secondary",
        ),
        (
            "load-interval 30",
            r"load-interval (?P<VAL>\d+)",
            "no load-interval",
        ),
    ],
)
def test_ctree_parser_loopback0_template(
    line: str,
    template: str,
    undo: str,
    config_text: str,
    config_template: str,
) -> None:
    parser = CTreeParser("cisco_iosxe")
    tmpl = parser.parse(config_template)
    root = parser.parse(config_text, tmpl)

    loopback0 = root.children["interface Loopback0"].children
    assert loopback0[line].template == template
    assert loopback0[line].undo == undo


def test_ctree_parser_inplace_template() -> None:
    config_text = dedent(
        """
        interface Loopback100
         description test-100 UNDO>> no description
         ip address 192.168.100.1 255.255.255.255
        !
        """,
    ).strip()
    expected_text = dedent(
        """
        interface Loopback100
         description test-100
         ip address 192.168.100.1 255.255.255.255
        !
        """,
    ).strip()
    parser = CTreeParser("cisco_iosxe")
    root = parser.parse(config_text)
    assert root.config == expected_text
    assert root.children["interface Loopback100"].children["description test-100"].template == ""
    assert root.children["interface Loopback100"].children["description test-100"].undo == "no description"
