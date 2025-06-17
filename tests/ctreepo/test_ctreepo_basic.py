from pathlib import Path
from textwrap import dedent

import pytest

from ctreepo import CTreePO, Platform
from ctreepo.parser import CTreeParser

with open("./tests/ctreepo/cisco-config-current.txt", "r") as f:
    current = f.read()


with open("./tests/ctreepo/cisco-config-target.txt", "r") as f:
    target = f.read()


def test_ctreepo_human_diff() -> None:
    human_diff = dedent(
        """
         interface GigabitEthernet0/0
        - description -= user =-
        - switchport access vlan 100
        + description -= server =-
        + switchport trunk allowed vlan 10,20,30,55-60,70
        + switchport trunk native vlan 123
        + switchport mode trunk
         !
         interface Loopback0
        - description -= RID =-
        + ip address 10.0.0.1 255.255.255.255
         !
         router bgp 64512
          address-family ipv4
        -  network 192.168.100.0 mask 255.255.255.0
        +  network 192.168.101.0 mask 255.255.255.0
         !
        """,
    ).strip("\n")
    ct = CTreePO(
        current=current,
        target=target,
        platform=Platform.CISCO_IOSXE,
    )
    assert ct.human_diff == human_diff


def test_ctreepo_diff() -> None:
    diff = dedent(
        """
        interface GigabitEthernet0/0
         no switchport access vlan 100
         description -= server =-
         switchport trunk allowed vlan 10,20,30,55-60,70
         switchport trunk native vlan 123
         switchport mode trunk
        !
        interface Loopback0
         no description
         ip address 10.0.0.1 255.255.255.255
        !
        router bgp 64512
         address-family ipv4
          no network 192.168.100.0 mask 255.255.255.0
          network 192.168.101.0 mask 255.255.255.0
        !
        """,
    ).strip()
    ct = CTreePO(
        current=current,
        target=target,
        platform=Platform.CISCO_IOSXE,
    )
    assert ct.diff.config == diff


@pytest.mark.parametrize(
    ("commands_template"),
    [
        # шаблон не указан, по умолчанию берем равным имени платформы
        None,
        # отключаем использование шаблона
        "",
        # явно указываем файл (существующий)
        "./ctreepo/templates/cisco_iosxe.txt",
        # явно указываем файл (несуществующий)
        "./dummy.txt",
    ],
)
def test_ctreepo_command_template(commands_template: str | None) -> None:
    ct = CTreePO(
        current=current,
        target=target,
        platform=Platform.CISCO_IOSXE,
        commands_template=commands_template,
    )
    if isinstance(commands_template, str) and len(commands_template) == 0:
        assert ct._commands_template is None
        return

    parser = CTreeParser(Platform.CISCO_IOSXE)
    template_file: Path
    if commands_template is None:
        template_file = Path(Path.cwd(), "ctreepo", "templates", Platform.CISCO_IOSXE).with_suffix(".txt")
    else:
        template_file = Path(commands_template)

    if not template_file.is_file():
        assert ct._commands_template is None
        return

    with open(template_file) as f:
        template_data = f.read()

    template = parser.parse(template_data)
    assert template.config == ct._commands_template.config  # type: ignore [union-attr]


@pytest.mark.parametrize(
    ("tagging_rules"),
    [
        # файл с правилами не указан
        None,
        # правила в файле (существующем)
        "./tests/ctreepo/test_ctreepo_basic.yaml",
    ],
)
def test_ctreepo_tagging_rules_file(tagging_rules: str | None) -> None:
    ct = CTreePO(
        current=current,
        target=target,
        platform=Platform.CISCO_IOSXE,
        tagging_file=tagging_rules,
    )
    if tagging_rules is None:
        assert len(ct.parser.tagging_rules) == 0
        return
    assert ct.current.children["service tcp-keepalives-in"].tags == ["service"]
    assert ct.current.children["interface GigabitEthernet0/0"].tags == ["interface", "GigabitEthernet0/0"]
    assert ct.current.children["interface Loopback0"].tags == ["interface", "loopback", "Loopback0"]
    assert ct.current.children["router bgp 64512"].tags == ["bgp"]

    assert ct.target.children["service tcp-keepalives-in"].tags == ["service"]
    assert ct.target.children["interface GigabitEthernet0/0"].tags == ["interface", "GigabitEthernet0/0"]
    assert ct.target.children["interface Loopback0"].tags == ["interface", "loopback", "Loopback0"]
    assert ct.target.children["router bgp 64512"].tags == ["bgp"]


def test_ctreepo_tagging_rules_dict() -> None:
    tagging_rules: list[dict[str, str | list[str]]] = [
        {
            "regex": r"^service .*",
            "tags": ["service"],
        },
        {
            "regex": r"^interface (Loopback\d+)$",
            "tags": ["interface", "loopback"],
        },
        {
            "regex": r"^interface (\S+)$",
            "tags": ["interface"],
        },
        {
            "regex": r"^router bgp \d+$",
            "tags": ["bgp"],
        },
    ]
    ct = CTreePO(
        current=current,
        target=target,
        platform=Platform.CISCO_IOSXE,
        tagging_list=tagging_rules,
    )
    assert ct.current.children["service tcp-keepalives-in"].tags == ["service"]
    assert ct.current.children["interface GigabitEthernet0/0"].tags == ["interface", "GigabitEthernet0/0"]
    assert ct.current.children["interface Loopback0"].tags == ["interface", "loopback", "Loopback0"]
    assert ct.current.children["router bgp 64512"].tags == ["bgp"]

    assert ct.target.children["service tcp-keepalives-in"].tags == ["service"]
    assert ct.target.children["interface GigabitEthernet0/0"].tags == ["interface", "GigabitEthernet0/0"]
    assert ct.target.children["interface Loopback0"].tags == ["interface", "loopback", "Loopback0"]
    assert ct.target.children["router bgp 64512"].tags == ["bgp"]
