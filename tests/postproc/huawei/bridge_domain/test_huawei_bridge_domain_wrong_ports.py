from textwrap import dedent

import pytest

from ctreepo import CTreeDiffer, CTreeParser, Vendor


def test_huawei_bridge_domain_wrong_ports() -> None:
    current_config = dedent(
        """
        bridge-domain 100
         statistics enable
         vlan 100 access-port interface Eth-TrunkABC to Eth-TrunkCBA
        #
        """
    )
    target_config = dedent(
        """
        bridge-domain 100
         statistics enable
        #
        """
    )
    parser = CTreeParser(Vendor.HUAWEI)
    current = parser.parse(current_config)
    target = parser.parse(target_config)

    with pytest.raises(ValueError) as exc:
        _ = CTreeDiffer.diff(current, target)
    assert str(exc.value) == "wrong interface number"
