from textwrap import dedent

import pytest

from ctreepo import CTreeDiffer, CTreeParser, Platform
from ctreepo.postproc.cisco_iosxe.bgp import CiscoIOSXEBGP


@pytest.mark.parametrize(
    "current_config, target_config, raw_diff_config, pp_diff_config",
    [
        # базовый тест
        (
            dedent(
                """
                router bgp 65000
                 bgp router-id 192.168.0.1
                 neighbor 1.1.1.1 remote-as 65000
                 neighbor 1.1.1.1 update-source Loopback0
                 neighbor 1.1.1.1 route-map RM out
                """,
            ),
            dedent(
                """
                router bgp 65000
                 bgp router-id 192.168.0.1
                """,
            ),
            dedent(
                """
                router bgp 65000
                 no neighbor 1.1.1.1 remote-as 65000
                 no neighbor 1.1.1.1 update-source Loopback0
                 no neighbor 1.1.1.1 route-map RM out
                !
                """,
            ).strip(),
            dedent(
                """
                router bgp 65000
                 no neighbor 1.1.1.1 remote-as 65000
                !
                """,
            ).strip(),
        ),
        # удаление соседа или пир-группы, определенных глобально
        (
            dedent(
                """
                router bgp 65000
                 bgp router-id 192.168.0.1
                 !
                 neighbor PEER peer-group
                 neighbor PEER remote-as 65000
                 neighbor PEER update-source Loopback0
                 neighbor 1.1.1.1 peer-group PEER
                 neighbor 1.1.1.1 remote-as 64512
                 neighbor 2.2.2.2 peer-group PEER
                 address-family ipv4
                  neighbor PEER send-community both
                  neighbor 1.1.1.1 activate
                  neighbor 1.1.1.1 send-community both
                  exit-address-family
                 address-family ipv4 unicast
                  neighbor PEER send-community both
                  neighbor 2.2.2.2 activate
                  neighbor 2.2.2.2 route-map RM out
                  exit-address-family
                 !
                 neighbor 3.3.3.3 remote-as 65000
                 neighbor 3.3.3.3 update-source Loopback0
                 neighbor 3.3.3.3 route-map RM out
                 address-family ipv4
                  neighbor 3.3.3.3 activate
                  neighbor 3.3.3.3 send-community both
                  exit-address-family
                """,
            ),
            dedent(
                """
                router bgp 65000
                 bgp router-id 192.168.0.1
                 address-family ipv4
                 exit-address-family
                 address-family ipv4 unicast
                 exit-address-family
                """,
            ),
            dedent(
                """
                router bgp 65000
                 no neighbor PEER peer-group
                 no neighbor PEER remote-as 65000
                 no neighbor PEER update-source Loopback0
                 no neighbor 1.1.1.1 peer-group PEER
                 no neighbor 1.1.1.1 remote-as 64512
                 no neighbor 2.2.2.2 peer-group PEER
                 address-family ipv4
                  no neighbor PEER send-community both
                  no neighbor 1.1.1.1 activate
                  no neighbor 1.1.1.1 send-community both
                  no neighbor 3.3.3.3 activate
                  no neighbor 3.3.3.3 send-community both
                 address-family ipv4 unicast
                  no neighbor PEER send-community both
                  no neighbor 2.2.2.2 activate
                  no neighbor 2.2.2.2 route-map RM out
                 no neighbor 3.3.3.3 remote-as 65000
                 no neighbor 3.3.3.3 update-source Loopback0
                 no neighbor 3.3.3.3 route-map RM out
                !
                """,
            ).strip(),
            dedent(
                """
                router bgp 65000
                 no neighbor PEER peer-group
                 no neighbor 3.3.3.3 remote-as 65000
                !
                """,
            ).strip(),
        ),
        # удаление одного соседа из состава пир-группы
        (
            dedent(
                """
                router bgp 65000
                 bgp router-id 192.168.0.1
                 neighbor PEER peer-group
                 neighbor PEER remote-as 65000
                 neighbor PEER update-source Loopback0
                 neighbor 1.1.1.1 peer-group PEER
                 neighbor 1.1.1.1 remote-as 64512
                 neighbor 2.2.2.2 peer-group PEER
                 address-family ipv4
                  neighbor PEER send-community both
                  neighbor 1.1.1.1 activate
                  neighbor 1.1.1.1 send-community both
                  exit-address-family
                 address-family ipv4 unicast
                  neighbor PEER send-community both
                  neighbor 2.2.2.2 activate
                  neighbor 2.2.2.2 route-map RM out
                  exit-address-family
                """,
            ),
            dedent(
                """
                router bgp 65000
                 bgp router-id 192.168.0.1
                 neighbor PEER peer-group
                 neighbor PEER remote-as 65000
                 neighbor PEER update-source Loopback0
                 neighbor 1.1.1.1 peer-group PEER
                 neighbor 1.1.1.1 remote-as 64512
                 address-family ipv4
                  neighbor PEER send-community both
                  neighbor 1.1.1.1 activate
                  neighbor 1.1.1.1 send-community both
                  exit-address-family
                 address-family ipv4 unicast
                  neighbor PEER send-community both
                  exit-address-family
                """,
            ),
            dedent(
                """
                router bgp 65000
                 no neighbor 2.2.2.2 peer-group PEER
                 address-family ipv4 unicast
                  no neighbor 2.2.2.2 activate
                  no neighbor 2.2.2.2 route-map RM out
                !
                """,
            ).strip(),
            dedent(
                """
                router bgp 65000
                 no neighbor 2.2.2.2 peer-group PEER
                !
                """,
            ).strip(),
        ),
        # удаление соседей из разных af
        (
            dedent(
                """
                router bgp 65000
                 bgp router-id 192.168.0.1
                 address-family ipv4 vrf vrf1
                  neighbor PEER_VRF1 peer-group
                  neighbor PEER_VRF1 remote-as 65000
                  neighbor PEER_VRF1 update-source Loopback0
                  neighbor 4.4.4.4 peer-group PEER_VRF1
                  neighbor 4.4.4.4 activate
                  neighbor 5.5.5.5 peer-group PEER_VRF1
                  neighbor 5.5.5.5 activate
                  neighbor 6.6.6.6 remote-as 65000
                  neighbor 6.6.6.6 activate
                  neighbor 6.6.6.6 send-community both
                  exit-address-family
                 address-family ipv4 vrf vrf2
                  neighbor PEER_VRF2 peer-group
                  neighbor PEER_VRF2 remote-as 65000
                  neighbor PEER_VRF2 update-source Loopback0
                  neighbor 4.4.4.4 peer-group PEER_VRF2
                  neighbor 4.4.4.4 activate
                  neighbor 5.5.5.5 peer-group PEER_VRF2
                  neighbor 5.5.5.5 activate
                  neighbor 6.6.6.6 remote-as 65000
                  neighbor 6.6.6.6 activate
                  neighbor 6.6.6.6 send-community both
                  exit-address-family
                """,
            ),
            dedent(
                """
                router bgp 65000
                 bgp router-id 192.168.0.1
                 address-family ipv4 vrf vrf1
                  neighbor PEER_VRF1 peer-group
                  neighbor PEER_VRF1 remote-as 65000
                  neighbor PEER_VRF1 update-source Loopback0
                  neighbor 4.4.4.4 peer-group PEER_VRF1
                  neighbor 4.4.4.4 activate
                  neighbor 6.6.6.6 remote-as 65000
                  neighbor 6.6.6.6 activate
                  neighbor 6.6.6.6 send-community both
                  exit-address-family
                 address-family ipv4 vrf vrf2
                  neighbor 6.6.6.6 remote-as 65000
                  neighbor 6.6.6.6 activate
                  neighbor 6.6.6.6 send-community both
                  exit-address-family
                """,
            ),
            dedent(
                """
                router bgp 65000
                 address-family ipv4 vrf vrf1
                  no neighbor 5.5.5.5 peer-group PEER_VRF1
                  no neighbor 5.5.5.5 activate
                 address-family ipv4 vrf vrf2
                  no neighbor PEER_VRF2 peer-group
                  no neighbor PEER_VRF2 remote-as 65000
                  no neighbor PEER_VRF2 update-source Loopback0
                  no neighbor 4.4.4.4 peer-group PEER_VRF2
                  no neighbor 4.4.4.4 activate
                  no neighbor 5.5.5.5 peer-group PEER_VRF2
                  no neighbor 5.5.5.5 activate
                !
                """,
            ).strip(),
            dedent(
                """
                router bgp 65000
                 address-family ipv4 vrf vrf1
                  no neighbor 5.5.5.5 peer-group PEER_VRF1
                 address-family ipv4 vrf vrf2
                  no neighbor PEER_VRF2 peer-group
                !
                """,
            ).strip(),
        ),
    ],
)
def test_pp_cisco_iosxe_bgp(
    current_config: str,
    target_config: str,
    raw_diff_config: str,
    pp_diff_config: str,
) -> None:
    parser = CTreeParser(platform=Platform.CISCO_IOSXE)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    raw_diff = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert raw_diff.config == raw_diff_config

    pp_diff = CTreeDiffer.diff(current, target, post_proc_rules=[CiscoIOSXEBGP])
    assert pp_diff.config == pp_diff_config
