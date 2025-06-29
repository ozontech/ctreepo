from textwrap import dedent

import pytest

from ctreepo import CTreeDiffer, CTreeParser, Platform
from ctreepo.postproc.huawei_vrp import HuaweiVRPBridgeDomain


@pytest.mark.parametrize(
    "current_config, target_config, raw_diff_config, pp_diff_config",
    [
        (
            dedent(
                """
                bridge-domain 100
                 statistics enable
                 vlan 100 access-port interface Eth-Trunk1 to Eth-Trunk10
                 vlan 100 access-port interface 10GE1/0/1 to 10GE1/0/6
                 vlan 100 access-port interface 10GE1/0/7 to 10GE1/0/42
                 vlan 100 access-port interface 10GE1/0/44
                 vlan 100 access-port interface 10GE1/0/46 to 10GE1/0/48
                #
                """,
            ),
            dedent(
                """
                bridge-domain 100
                 statistics enable
                 vlan 100 access-port interface Eth-Trunk1 to Eth-Trunk4
                 vlan 100 access-port interface Eth-Trunk6 to Eth-Trunk10
                 vlan 100 access-port interface 10GE1/0/2 to 10GE1/0/6
                 vlan 100 access-port interface 10GE1/0/7 to 10GE1/0/48
                bridge-domain test
                 statistics enable
                #
                """,
            ),
            dedent(
                """
                bridge-domain 100
                 undo vlan 100 access-port interface Eth-Trunk1 to Eth-Trunk10
                 undo vlan 100 access-port interface 10GE1/0/1 to 10GE1/0/6
                 undo vlan 100 access-port interface 10GE1/0/7 to 10GE1/0/42
                 undo vlan 100 access-port interface 10GE1/0/44
                 undo vlan 100 access-port interface 10GE1/0/46 to 10GE1/0/48
                 vlan 100 access-port interface Eth-Trunk1 to Eth-Trunk4
                 vlan 100 access-port interface Eth-Trunk6 to Eth-Trunk10
                 vlan 100 access-port interface 10GE1/0/2 to 10GE1/0/6
                 vlan 100 access-port interface 10GE1/0/7 to 10GE1/0/48
                #
                bridge-domain test
                 statistics enable
                #
                """,
            ).strip(),
            dedent(
                """
                bridge-domain 100
                 undo vlan 100 access-port interface 10GE1/0/1
                 undo vlan 100 access-port interface Eth-Trunk5
                 vlan 100 access-port interface 10GE1/0/43
                 vlan 100 access-port interface 10GE1/0/45
                #
                bridge-domain test
                 statistics enable
                #
                """,
            ).strip(),
        ),
    ],
)
def test_pp_huawei_vrp_bridge_domain_access_port(
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

    pp_diff = CTreeDiffer.diff(current, target, post_proc_rules=[HuaweiVRPBridgeDomain])
    assert pp_diff.config == pp_diff_config
