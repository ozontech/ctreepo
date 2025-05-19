from textwrap import dedent

import pytest

from ctreepo import CTreeDiffer, CTreeParser, Platform
from ctreepo.postproc.huawei_vrp import HuaweiVRPBGP


@pytest.mark.parametrize(
    "current_config, target_config, raw_diff_config, pp_diff_config",
    [
        (
            dedent(
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
            ),
            dedent(
                """
                bgp 12345
                 router-id 1.2.3.4
                 ipv4-family vpn-instance VRF
                  maximum load-balancing 4
                """,
            ),
            dedent(
                """
                bgp 12345
                 ipv4-family vpn-instance VRF
                  undo group PEER-GROUP external
                  undo peer PEER-GROUP bfd min-tx-interval 300 min-rx-interval 300
                  undo peer PEER-GROUP bfd enable
                #
                """,
            ).strip(),
            dedent(
                """
                bgp 12345
                 ipv4-family vpn-instance VRF
                  undo group PEER-GROUP
                #
                """,
            ).strip(),
        ),
        (
            dedent(
                """
                bgp 12345
                 router-id 1.2.3.4
                 peer 192.168.0.1 as-number 12345
                 ipv4-family unicast
                  peer 192.168.0.1 enable
                  peer 192.168.0.1 ip-prefix PL_IN import
                #
                """,
            ),
            dedent(
                """
                bgp 12345
                 router-id 1.2.3.4
                 ipv4-family unicast
                """,
            ),
            dedent(
                """
                bgp 12345
                 undo peer 192.168.0.1 as-number 12345
                 ipv4-family unicast
                  undo peer 192.168.0.1 enable
                  undo peer 192.168.0.1 ip-prefix PL_IN import
                #
                """,
            ).strip(),
            dedent(
                """
                bgp 12345
                 undo peer 192.168.0.1
                #
                """,
            ).strip(),
        ),
    ],
)
def test_pp_huawei_vrp_bgp_peer_delete(
    current_config: str,
    target_config: str,
    raw_diff_config: str,
    pp_diff_config: str,
) -> None:
    parser = CTreeParser(platform=Platform.HUAWEI_VRP)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    raw_diff = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert raw_diff.config == raw_diff_config

    pp_diff = CTreeDiffer.diff(current, target, post_proc_rules=[HuaweiVRPBGP])
    assert pp_diff.config == pp_diff_config
