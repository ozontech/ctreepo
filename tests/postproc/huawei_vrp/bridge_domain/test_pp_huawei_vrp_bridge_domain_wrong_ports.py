from textwrap import dedent

import pytest

from ctreepo import CTreeDiffer, CTreeParser, Platform
from ctreepo.postproc.huawei_vrp import HuaweiVRPBridgeDomain


def test_pp_huawei_vrp_bridge_domain_wrong_ports() -> None:
    current_config = dedent(
        """
        bridge-domain 100
         statistics enable
         vlan 100 access-port interface Eth-TrunkABC to Eth-TrunkCBA
        #
        """,
    )
    target_config = dedent(
        """
        bridge-domain 100
         statistics enable
        #
        """,
    )
    parser = CTreeParser(Platform.HUAWEI_VRP)
    current = parser.parse(current_config)
    target = parser.parse(target_config)

    with pytest.raises(ValueError) as exc:
        _ = CTreeDiffer.diff(current, target, post_proc_rules=[HuaweiVRPBridgeDomain])
    assert str(exc.value) == "wrong interface number"
