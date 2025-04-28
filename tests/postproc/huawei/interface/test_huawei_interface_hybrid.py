from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Vendor


def test_huawei_interface_hybrid_change_vlan() -> None:
    """изменение состава tagged vlans на hybrid интерфейсе."""
    current_config = dedent(
        """
        interface Eth-Trunk1
         port hybrid tagged vlan 10 19 to 24
        #
        interface Eth-Trunk2
         port hybrid tagged vlan 10 to 15
        #
        interface Eth-Trunk3
         port hybrid tagged vlan 10 to 15
        #
        interface Eth-Trunk4
         port hybrid tagged vlan 10
        #
        interface Eth-Trunk5
         port hybrid tagged vlan 10 to 15
        #
        """
    ).strip()
    target_config = dedent(
        """
        interface Eth-Trunk1
         port hybrid tagged vlan 15 23 to 24 26
        #
        interface Eth-Trunk2
         port hybrid tagged vlan 12 to 17
        #
        interface Eth-Trunk3
         port hybrid tagged vlan 20 to 25
        #
        interface Eth-Trunk4
         port hybrid tagged vlan 20
        #
        interface Eth-Trunk5
         port hybrid tagged vlan 10 to 15 20
        #
        """
    ).strip()
    diff_config_raw = dedent(
        """
        interface Eth-Trunk1
         undo port hybrid tagged vlan 10 19 to 24
         port hybrid tagged vlan 15 23 to 24 26
        #
        interface Eth-Trunk2
         undo port hybrid tagged vlan 10 to 15
         port hybrid tagged vlan 12 to 17
        #
        interface Eth-Trunk3
         undo port hybrid tagged vlan 10 to 15
         port hybrid tagged vlan 20 to 25
        #
        interface Eth-Trunk4
         undo port hybrid tagged vlan 10
         port hybrid tagged vlan 20
        #
        interface Eth-Trunk5
         undo port hybrid tagged vlan 10 to 15
         port hybrid tagged vlan 10 to 15 20
        #
        """
    ).strip()
    diff_config = dedent(
        """
        interface Eth-Trunk1
         undo port hybrid tagged vlan 10 19 to 22
         port hybrid tagged vlan 15 23 to 24 26
        #
        interface Eth-Trunk2
         undo port hybrid tagged vlan 10 to 11
         port hybrid tagged vlan 12 to 17
        #
        interface Eth-Trunk3
         undo port hybrid tagged vlan 10 to 15
         port hybrid tagged vlan 20 to 25
        #
        interface Eth-Trunk4
         undo port hybrid tagged vlan 10
         port hybrid tagged vlan 20
        #
        interface Eth-Trunk5
         port hybrid tagged vlan 10 to 15 20
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
