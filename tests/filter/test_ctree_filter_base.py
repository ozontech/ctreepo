from textwrap import dedent

from ctreepo.ctree import CTree
from ctreepo.filter import CTreeFilter


def test_filter_by_string(config_tree: CTree) -> None:
    # поиск по строке
    result = CTreeFilter.filter(
        config_tree,
        string="192.168.255.1",
    )
    expected = dedent(
        r"""
        router bgp 64512
         neighbor 192.168.255.1 remote-as 64512
         neighbor 192.168.255.1 update-source Loopback0
         neighbor 192.168.255.1 password 7 some-secret
         address-family ipv4
          neighbor 192.168.255.1 activate
         !
        !
        """,
    ).strip()
    assert result.config == expected


def test_filter_by_regex_string(config_tree: CTree) -> None:
    # поиск по regex строке
    result = CTreeFilter.filter(
        config_tree,
        string=r"192.168.(?:1|255).1",
    )
    expected = dedent(
        r"""
        interface Loopback0
         ip address 192.168.1.1 255.255.255.255
        !
        router bgp 64512
         neighbor 192.168.255.1 remote-as 64512
         neighbor 192.168.255.1 update-source Loopback0
         neighbor 192.168.255.1 password 7 some-secret
         address-family ipv4
          neighbor 192.168.255.1 activate
         !
        !
        """,
    ).strip()
    assert result.config == expected


def test_filter_by_include_tag(config_tree: CTree) -> None:
    # поиск по include tag
    result = CTreeFilter.filter(
        config_tree,
        include_tags=("interface:Loopback100",),
    )
    expected = dedent(
        r"""
        interface Loopback100
         description test-100
         ip address 192.168.100.1 255.255.255.255
        !
        """,
    ).strip()
    assert result.config == expected


def test_filter_by_include_regex_tag(config_tree: CTree) -> None:
    # тег в виде regex выражения
    result = CTreeFilter.filter(
        config_tree,
        include_tags=(r"re:Loopback\d00",),
    )
    expected = dedent(
        r"""
        interface Loopback100
         description test-100
         ip address 192.168.100.1 255.255.255.255
        !
        interface Loopback200
         description test-200
         ip address 192.168.200.1 255.255.255.255
        !
        """,
    ).strip()
    assert result.config == expected


def test_filter_by_include_tags_or(config_tree: CTree) -> None:
    # несколько include tags с or логикой
    result = CTreeFilter.filter(
        config_tree,
        include_tags=("Loopback100", "Loopback200"),
        include_mode="or",
    )
    expected = dedent(
        r"""
        interface Loopback100
         description test-100
         ip address 192.168.100.1 255.255.255.255
        !
        interface Loopback200
         description test-200
         ip address 192.168.200.1 255.255.255.255
        !
        """,
    ).strip()
    assert result.config == expected


def test_filter_by_include_tags_and_match(config_tree: CTree) -> None:
    # несколько include tags с and логикой (есть результат)
    result = CTreeFilter.filter(
        config_tree,
        include_tags=(r"re:Loopback\d00", "ip"),
        include_mode="and",
    )
    expected = dedent(
        r"""
        interface Loopback100
         ip address 192.168.100.1 255.255.255.255
        !
        interface Loopback200
         ip address 192.168.200.1 255.255.255.255
        !
        """,
    ).strip()
    assert result.config == expected


def test_filter_by_include_tags_and_no_match(config_tree: CTree) -> None:
    # несколько include tags с and логикой (пустой результат)
    result = CTreeFilter.filter(
        config_tree,
        include_tags=("Loopback100", "Loopback200"),
        include_mode="and",
    )
    expected = ""
    assert result.config == expected


def test_filter_by_include_tags_exclude_tags(config_tree: CTree) -> None:
    # комбинация include и exclude tags
    result = CTreeFilter.filter(
        config_tree,
        include_tags=(r"re:Loopback\d00", "ip"),
        include_mode="and",
    )
    expected = dedent(
        r"""
        interface Loopback100
         ip address 192.168.100.1 255.255.255.255
        !
        interface Loopback200
         ip address 192.168.200.1 255.255.255.255
        !
        """,
    ).strip()
    assert result.config == expected


def test_filter_by_string_include_tags(config_tree: CTree) -> None:
    # комбинация строки и include tags
    result = CTreeFilter.filter(
        config_tree,
        string="192.168.100.1",
        include_tags=(r"re:Loopback\d00", "ip"),
        include_mode="and",
    )
    expected = dedent(
        r"""
        interface Loopback100
         ip address 192.168.100.1 255.255.255.255
        !
        """,
    ).strip()
    assert result.config == expected


def test_filter_by_string_exclude_regex_tags(config_tree: CTree) -> None:
    # комбинация строки и exclude tags
    result = CTreeFilter.filter(
        config_tree,
        exclude_tags=(r"re:Loopback\d00", r"re:bgp|routing"),
    )
    expected = dedent(
        r"""
        service tcp-keepalives-in
        service timestamps debug datetime msec localtime show-timezone
        !
        route-map rm_DENY deny 10
        !
        interface Loopback0
         description test-0
         ip address 192.168.1.1 255.255.255.255
        !
        interface FastEthernet0
         switchport access vlan 100
         no ip address
        !
        route-map rm_PERMIT permit 10
        !
        """,
    ).strip()
    assert result.config == expected


def test_filter_by_string_exclude_tags(config_tree: CTree) -> None:
    # комбинация строки и exclude tags
    result = CTreeFilter.filter(
        config_tree,
        exclude_tags=(r"re:Loopback\d00", "bgp", "rm", "ip"),
    )
    expected = dedent(
        r"""
        service tcp-keepalives-in
        service timestamps debug datetime msec localtime show-timezone
        !
        interface Loopback0
         description test-0
        !
        interface FastEthernet0
         switchport access vlan 100
         no ip address
        !
        """,
    ).strip()
    assert result.config == expected


def test_filter_by_include_tags_with_children(config_tree: CTree) -> None:
    # include tags с копированием потомков
    result = CTreeFilter.filter(
        config_tree,
        include_tags=("eth",),
        include_children=True,
    )
    expected = dedent(
        r"""
        interface FastEthernet0
         switchport access vlan 100
         no ip address
        !
        """,
    ).strip()
    assert result.config == expected


def test_filter_by_include_tags_without_children(config_tree: CTree) -> None:
    # include tags без копирования потомков
    result = CTreeFilter.filter(
        config_tree,
        include_tags=("eth",),
        include_children=False,
    )
    expected = dedent(
        r"""
        interface FastEthernet0
        !
        """,
    ).strip()
    assert result.config == expected


def test_filter_by_exclude_tag_deep(config_tree: CTree) -> None:
    # exclude tag тег где-то глубоко
    result = CTreeFilter.filter(
        config_tree,
        include_tags=("FastEthernet0",),
        exclude_tags=("no-ip",),
    )
    expected = dedent(
        r"""
        interface FastEthernet0
         switchport access vlan 100
        !
        """,
    ).strip()
    assert result.config == expected


def test_filter_by_include_tag_deep(config_tree: CTree) -> None:
    # include tag тег где-то глубоко
    result = CTreeFilter.filter(
        config_tree,
        include_tags=("no-ip",),
    )
    expected = dedent(
        r"""
        interface FastEthernet0
         no ip address
        !
        """,
    ).strip()
    assert result.config == expected
