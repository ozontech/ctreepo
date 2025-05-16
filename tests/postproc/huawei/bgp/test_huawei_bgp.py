from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Platform


def test_huawei_bgp_base() -> None:
    """Тест настройки bgp с нуля.

    Сначала должны глобальные секции должны идти, потом address-family.
    """
    current_config = ""
    target_config = dedent(
        """
        route-map RM_TEST permit 10
         match ip address prefix-list PL_TEST
        #
        bgp 12345
         router-id 1.2.3.4
         no bgp default ipv4-unicast
         maximum-paths 4 ecmp 64
         address-family ipv4
          neighbor PEER_GROUP_1 activate
          neighbor PEER_GROUP_2 activate
         vrf VRF_NAME_1
          router-id 1.2.3.4
          rd 1.2.3.4:123
          route-target import evpn 123:456
          route-target export evpn 123:456
          bgp listen range 1.2.3.0/24 peer-group PEER_GROUP_1 peer-filter AS12345
         address-family evpn
          neighbor PEER_GROUP_3 activate
         neighbor PEER_GROUP_1 peer group
         neighbor PEER_GROUP_1 bfd
         neighbor PEER_GROUP_2 peer group
         neighbor PEER_GROUP_3 peer group
         neighbor 192.168.0.1 peer group PEER_GROUP_1
         neighbor 192.168.0.1 remote-as 12345
         neighbor 192.168.0.2 peer group PEER_GROUP_2
         neighbor 192.168.0.2 remote-as 12345
         neighbor 192.168.0.3 peer group PEER_GROUP_3
         neighbor 192.168.0.3 remote-as 12345
        #
        """,
    ).strip()
    diff_config = dedent(
        """
        route-map RM_TEST permit 10
         match ip address prefix-list PL_TEST
        #
        bgp 12345
         router-id 1.2.3.4
         no bgp default ipv4-unicast
         maximum-paths 4 ecmp 64
         neighbor PEER_GROUP_1 peer group
         neighbor PEER_GROUP_1 bfd
         neighbor PEER_GROUP_2 peer group
         neighbor PEER_GROUP_3 peer group
         neighbor 192.168.0.1 peer group PEER_GROUP_1
         neighbor 192.168.0.1 remote-as 12345
         neighbor 192.168.0.2 peer group PEER_GROUP_2
         neighbor 192.168.0.2 remote-as 12345
         neighbor 192.168.0.3 peer group PEER_GROUP_3
         neighbor 192.168.0.3 remote-as 12345
         address-family ipv4
          neighbor PEER_GROUP_1 activate
          neighbor PEER_GROUP_2 activate
         vrf VRF_NAME_1
          router-id 1.2.3.4
          rd 1.2.3.4:123
          route-target import evpn 123:456
          route-target export evpn 123:456
          bgp listen range 1.2.3.0/24 peer-group PEER_GROUP_1 peer-filter AS12345
         address-family evpn
          neighbor PEER_GROUP_3 activate
        #
        """,
    ).strip()
    diff_patch = dedent(
        """
        route-map RM_TEST permit 10
        match ip address prefix-list PL_TEST
        quit
        bgp 12345
        router-id 1.2.3.4
        no bgp default ipv4-unicast
        maximum-paths 4 ecmp 64
        neighbor PEER_GROUP_1 peer group
        neighbor PEER_GROUP_1 bfd
        neighbor PEER_GROUP_2 peer group
        neighbor PEER_GROUP_3 peer group
        neighbor 192.168.0.1 peer group PEER_GROUP_1
        neighbor 192.168.0.1 remote-as 12345
        neighbor 192.168.0.2 peer group PEER_GROUP_2
        neighbor 192.168.0.2 remote-as 12345
        neighbor 192.168.0.3 peer group PEER_GROUP_3
        neighbor 192.168.0.3 remote-as 12345
        address-family ipv4
        neighbor PEER_GROUP_1 activate
        neighbor PEER_GROUP_2 activate
        quit
        vrf VRF_NAME_1
        router-id 1.2.3.4
        rd 1.2.3.4:123
        route-target import evpn 123:456
        route-target export evpn 123:456
        bgp listen range 1.2.3.0/24 peer-group PEER_GROUP_1 peer-filter AS12345
        quit
        address-family evpn
        neighbor PEER_GROUP_3 activate
        quit
        quit
        """,
    ).strip()

    parser = CTreeParser(Platform.HUAWEI_VRP)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_huawei_bgp_peer_group_delete() -> None:
    """Удаление пира.

    Все остальные команды, кроме undo group ... не нужны.
    """
    current_config = dedent(
        """
        bgp 12345
         router-id 1.2.3.4
         ipv4-family vpn-instance VRF
          maximum load-balancing 4
          group PEER-GROUP external
          peer PEER-GROUP bfd min-tx-interval 300 min-rx-interval 300
          peer PEER-GROUP bfd enable
        #
        """,
    ).strip()
    target_config = dedent(
        """
        bgp 12345
         router-id 1.2.3.4
         ipv4-family vpn-instance VRF
          maximum load-balancing 4
        #
        """,
    ).strip()
    diff_patch = dedent(
        """
        bgp 12345
        ipv4-family vpn-instance VRF
        undo group PEER-GROUP
        quit
        quit
        """,
    ).strip()

    parser = CTreeParser(Platform.HUAWEI_VRP)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target)
    assert diff.patch == diff_patch
