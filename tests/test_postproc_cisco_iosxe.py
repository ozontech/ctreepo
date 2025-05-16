from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Platform


def test_cisco_no_post_processing() -> None:
    current_config = dedent(
        """
        router ospf 1
         passive-interface default
         no passive-interface Tunnel1
         network 192.168.100.1 0.0.0.0 area 1.2.3.4
         network 10.1.0.2 0.0.0.0 area 1.2.3.4
        !
        """,
    )
    target_config = dedent(
        """
        router ospf 1
         no passive-interface Tunnel1
         network 192.168.100.1 0.0.0.0 area 1.2.3.4
         network 10.1.0.2 0.0.0.0 area 1.2.3.4
        !
        """,
    )
    diff_config = dedent(
        """
        router ospf 1
         no passive-interface default
        !
        """,
    ).strip()
    parser = CTreeParser(Platform.CISCO_IOSXE)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config


def test_cisco_bgp_post_processing() -> None:
    current_config = dedent(
        """
        router ospf 1
         passive-interface default
         no passive-interface Tunnel1
         network 192.168.100.1 0.0.0.0 area 1.2.3.4
         network 10.1.0.2 0.0.0.0 area 1.2.3.4
        !
        router bgp 64512
         bgp log-neighbor-changes
         neighbor RR peer-group
         neighbor RR remote-as 64512
         neighbor RR ebgp-multihop 255
         neighbor RR update-source Loopback0
         neighbor 192.168.255.1 remote-as 64512
         neighbor 192.168.255.1 update-source Loopback0
         !
         address-family ipv4
          network 192.168.100.0 mask 255.255.255.0
          redistribute ospf 1 route-map rm_OSPF2BGP
          neighbor RR send-community both
          neighbor RR advertisement-interval 0
          neighbor 192.168.255.1 activate
          neighbor 192.168.255.1 soft-reconfiguration inbound
          neighbor 192.168.255.1 prefix-list pl_BGP_out out
         exit-address-family
         address-family ipv6
          neighbor RR send-community both
          neighbor RR advertisement-interval 0
          redistribute connected route-map rm_OSPF2BGP
         exit-address-family
        !
        """,
    ).strip()
    target_config = dedent(
        """
        router ospf 1
         passive-interface default
         no passive-interface Tunnel1
         network 192.168.100.1 0.0.0.0 area 1.2.3.4
        !
        router bgp 64512
         bgp log-neighbor-changes
         neighbor 192.168.255.1 remote-as 64512
         neighbor 192.168.255.1 update-source Loopback0
         !
         address-family ipv4
          network 192.168.100.0 mask 255.255.255.0
          neighbor 192.168.255.1 activate
          neighbor 192.168.255.1 soft-reconfiguration inbound
          neighbor 192.168.255.1 prefix-list pl_BGP_out out
         exit-address-family
         address-family ipv6
          redistribute connected route-map rm_OSPF2BGP
         exit-address-family
        """,
    ).strip()
    diff_raw_config = dedent(
        """
        router ospf 1
         no network 10.1.0.2 0.0.0.0 area 1.2.3.4
        !
        router bgp 64512
         no neighbor RR peer-group
         no neighbor RR remote-as 64512
         no neighbor RR ebgp-multihop 255
         no neighbor RR update-source Loopback0
         address-family ipv4
          no redistribute ospf 1 route-map rm_OSPF2BGP
          no neighbor RR send-community both
          no neighbor RR advertisement-interval 0
         address-family ipv6
          no neighbor RR send-community both
          no neighbor RR advertisement-interval 0
        !
        """,
    ).strip()
    diff_processed_config = dedent(
        """
        router ospf 1
         no network 10.1.0.2 0.0.0.0 area 1.2.3.4
        !
        router bgp 64512
         no neighbor RR peer-group
         address-family ipv4
          no redistribute ospf 1 route-map rm_OSPF2BGP
        !
        """,
    ).strip()
    parser = CTreeParser(Platform.CISCO_IOSXE)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff_raw = CTreeDiffer.diff(current, target, post_proc_rules=[])
    diff_processed = CTreeDiffer.diff(current, target)
    assert diff_raw.config == diff_raw_config
    assert diff_processed.config == diff_processed_config
