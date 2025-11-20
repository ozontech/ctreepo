from textwrap import dedent

from ctreepo.ctree import CTree
from ctreepo.sorter import CTreeSorter


def test_ctree_sorter_sort(config_tree: CTree) -> None:
    sorted_config = dedent(
        """
        route-map rm_PERMIT permit 10
        !
        interface Loopback200
         description test-200
         ip address 192.168.200.1 255.255.255.255
        !
        router bgp 64512
         neighbor 192.168.255.1 remote-as 64512
         neighbor 192.168.255.1 update-source Loopback0
         neighbor 192.168.255.1 password 7 some-secret
         address-family ipv4
          network 192.168.100.0 mask 255.255.255.0
          neighbor 192.168.255.1 activate
         !
         address-family vpnv4
          network 192.168.1.0 mask 255.255.255.0
         !
         address-family ipv6
         !
         address-family vpnv6
         !
        !
        route-map rm_DENY deny 10
         match ip address 101
        !
        service tcp-keepalives-in
        service timestamps debug datetime msec localtime show-timezone
        !
        interface Loopback0
         description test-0
         ip address 192.168.1.1 255.255.255.255
        !
        interface Loopback100
         description test-100
         ip address 192.168.100.1 255.255.255.255
        !
        interface FastEthernet0
         switchport access vlan 100
         no ip address
        !
        """,
    ).strip()
    CTreeSorter.sort("rm_PERMIT", "Loopback200", "routing", "rm", node=config_tree)
    assert config_tree.config == sorted_config


def test_ctree_sorter_sort_reverse(config_tree: CTree) -> None:
    sorted_config = dedent(
        """
        route-map rm_DENY deny 10
         match ip address 101
        !
        router bgp 64512
         neighbor 192.168.255.1 remote-as 64512
         neighbor 192.168.255.1 update-source Loopback0
         neighbor 192.168.255.1 password 7 some-secret
         address-family ipv4
          network 192.168.100.0 mask 255.255.255.0
          neighbor 192.168.255.1 activate
         !
         address-family vpnv4
          network 192.168.1.0 mask 255.255.255.0
         !
         address-family ipv6
         !
         address-family vpnv6
         !
        !
        interface Loopback200
         description test-200
         ip address 192.168.200.1 255.255.255.255
        !
        route-map rm_PERMIT permit 10
        !
        service tcp-keepalives-in
        service timestamps debug datetime msec localtime show-timezone
        !
        interface Loopback0
         description test-0
         ip address 192.168.1.1 255.255.255.255
        !
        interface Loopback100
         description test-100
         ip address 192.168.100.1 255.255.255.255
        !
        interface FastEthernet0
         switchport access vlan 100
         no ip address
        !
        """,
    ).strip()
    CTreeSorter.sort("rm_PERMIT", "Loopback200", "routing", "rm", node=config_tree, reverse=True)
    assert config_tree.config == sorted_config


def test_ctree_sorter_sort_no_tags(config_tree: CTree, tree_config: str) -> None:
    CTreeSorter.sort(node=config_tree)
    assert config_tree.config == tree_config


def test_ctree_sorter_config_by_tags(config_tree: CTree) -> None:
    tags = ("ip", "rm", "interface", "bgp")

    result = "\n".join(CTreeSorter.config_by_tags(*tags, node=config_tree, skip_no_tag=True, mode="config"))
    expected = dedent(
        """
        interface Loopback0
         ip address 192.168.1.1 255.255.255.255
        !
        interface Loopback100
         ip address 192.168.100.1 255.255.255.255
        !
        interface Loopback200
         ip address 192.168.200.1 255.255.255.255
        !
        route-map rm_DENY deny 10
         match ip address 101
        !
        route-map rm_PERMIT permit 10
        !
        interface Loopback0
         description test-0
        !
        interface Loopback100
         description test-100
        !
        interface Loopback200
         description test-200
        !
        interface FastEthernet0
         switchport access vlan 100
         no ip address
        !
        router bgp 64512
         neighbor 192.168.255.1 remote-as 64512
         neighbor 192.168.255.1 update-source Loopback0
         neighbor 192.168.255.1 password 7 some-secret
         address-family ipv4
          network 192.168.100.0 mask 255.255.255.0
          neighbor 192.168.255.1 activate
         !
         address-family vpnv4
          network 192.168.1.0 mask 255.255.255.0
         !
         address-family ipv6
         !
         address-family vpnv6
         !
        !
        """,
    ).strip()
    assert result == expected

    result = "\n".join(CTreeSorter.config_by_tags(*tags, node=config_tree, skip_no_tag=False, mode="config"))
    expected += "\nservice tcp-keepalives-in\nservice timestamps debug datetime msec localtime show-timezone\n!"
    assert result == expected


def test_ctree_sorter_patch_by_tags(config_tree: CTree) -> None:
    tags = ("ip", "rm", "interface", "bgp")

    result = "\n".join(CTreeSorter.config_by_tags(*tags, node=config_tree, skip_no_tag=True, mode="patch"))
    expected = dedent(
        """
        interface Loopback0
        ip address 192.168.1.1 255.255.255.255
        exit
        interface Loopback100
        ip address 192.168.100.1 255.255.255.255
        exit
        interface Loopback200
        ip address 192.168.200.1 255.255.255.255
        exit
        route-map rm_DENY deny 10
        match ip address 101
        exit
        route-map rm_PERMIT permit 10
        exit
        interface Loopback0
        description test-0
        exit
        interface Loopback100
        description test-100
        exit
        interface Loopback200
        description test-200
        exit
        interface FastEthernet0
        switchport access vlan 100
        no ip address
        exit
        router bgp 64512
        neighbor 192.168.255.1 remote-as 64512
        neighbor 192.168.255.1 update-source Loopback0
        neighbor 192.168.255.1 password 7 some-secret
        address-family ipv4
        network 192.168.100.0 mask 255.255.255.0
        neighbor 192.168.255.1 activate
        exit
        address-family vpnv4
        network 192.168.1.0 mask 255.255.255.0
        exit
        address-family ipv6
        exit
        address-family vpnv6
        exit
        exit
        """,
    ).strip()
    assert result == expected

    result = "\n".join(CTreeSorter.config_by_tags(*tags, node=config_tree, skip_no_tag=False, mode="patch"))
    expected += "\nservice tcp-keepalives-in\nservice timestamps debug datetime msec localtime show-timezone"
    assert result == expected
