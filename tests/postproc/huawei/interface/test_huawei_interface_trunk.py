from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Vendor


def test_huawei_interface_trunk_change_vlan() -> None:
    """изменение состава allowed-pass vlans на trunk интерфейсе."""
    current_config = dedent(
        """
        interface Eth-Trunk1
         port trunk allow-pass vlan 10 19 to 24
        #
        interface Eth-Trunk2
         port trunk allow-pass vlan 10 to 15
        #
        interface Eth-Trunk3
         port trunk allow-pass vlan 10 to 15
        #
        interface Eth-Trunk4
         port trunk allow-pass vlan 10
        #
        interface Eth-Trunk5
         port trunk allow-pass vlan 10 to 15
        #
        """
    ).strip()
    target_config = dedent(
        """
        interface Eth-Trunk1
         port trunk allow-pass vlan 15 23 to 24 26
        #
        interface Eth-Trunk2
         port trunk allow-pass vlan 11 to 16
        #
        interface Eth-Trunk3
         port trunk allow-pass vlan 20 to 25
        #
        interface Eth-Trunk4
         port trunk allow-pass vlan 20
        #
        interface Eth-Trunk5
         port trunk allow-pass vlan 10 to 15 20
        #
        """
    ).strip()
    diff_config_raw = dedent(
        """
        interface Eth-Trunk1
         undo port trunk allow-pass vlan 10 19 to 24
         port trunk allow-pass vlan 15 23 to 24 26
        #
        interface Eth-Trunk2
         undo port trunk allow-pass vlan 10 to 15
         port trunk allow-pass vlan 11 to 16
        #
        interface Eth-Trunk3
         undo port trunk allow-pass vlan 10 to 15
         port trunk allow-pass vlan 20 to 25
        #
        interface Eth-Trunk4
         undo port trunk allow-pass vlan 10
         port trunk allow-pass vlan 20
        #
        interface Eth-Trunk5
         undo port trunk allow-pass vlan 10 to 15
         port trunk allow-pass vlan 10 to 15 20
        #
        """
    ).strip()
    diff_config = dedent(
        """
        interface Eth-Trunk1
         undo port trunk allow-pass vlan 10 19 to 22
         port trunk allow-pass vlan 15 23 to 24 26
        #
        interface Eth-Trunk2
         undo port trunk allow-pass vlan 10
         port trunk allow-pass vlan 11 to 16
        #
        interface Eth-Trunk3
         undo port trunk allow-pass vlan 10 to 15
         port trunk allow-pass vlan 20 to 25
        #
        interface Eth-Trunk4
         undo port trunk allow-pass vlan 10
         port trunk allow-pass vlan 20
        #
        interface Eth-Trunk5
         port trunk allow-pass vlan 10 to 15 20
        #
        """
    ).strip()

    parser = CTreeParser(Vendor.HUAWEI)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff.config == diff_config_raw

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
