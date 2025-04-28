from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Vendor


def test_huawei_interface_link_type_remove() -> None:
    """Удаление link-type trunk и связанных с ним команд."""
    current_config = dedent(
        """
        interface GigabitEthernet0/0/1
         description TEST-DESCRIPTION-1
         port link-type trunk
         undo port trunk allow-pass vlan 1
         port trunk allow-pass vlan 500 to 505
         stp edged-port enable
        #
        """
    ).strip()
    target_config = dedent(
        """
        #
        interface GigabitEthernet0/0/1
         description TEST-DESCRIPTION-1
         stp edged-port enable
        #
        """
    ).strip()
    diff_config = dedent(
        """
        interface GigabitEthernet0/0/1
         undo port link-type
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        interface GigabitEthernet0/0/1
        undo port link-type
        quit
        """
    ).strip()
    parser = CTreeParser(Vendor.HUAWEI)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_huawei_interface_link_type_change() -> None:
    """Смена типа с hybrid на trunk."""
    current_config = dedent(
        """
        interface GigabitEthernet0/0/1
         auto speed 10 100
         port link-type hybrid
         voice-vlan 101 enable
         vcmp disable
         port hybrid pvid vlan 102
         port hybrid tagged vlan 103
         port hybrid untagged vlan 104
         stp edged-port enable
         authentication-profile my_profile
         unicast-suppression packets 10
         multicast-suppression packets 20
         broadcast-suppression packets 30
        #
        """
    ).strip()

    target_config = dedent(
        """
        #
        interface GigabitEthernet0/0/1
         auto speed 10 100
         port link-type trunk
         port trunk pvid vlan 102
         port trunk allow-pass vlan 102 105 107
         voice-vlan 102 enable
         vcmp disable
         stp edged-port enable
         authentication-profile my_profile
         unicast-suppression packets 10
         multicast-suppression packets 20
         broadcast-suppression packets 30
        #
        """
    ).strip()

    diff_config = dedent(
        """
        interface GigabitEthernet0/0/1
         undo port link-type
         undo voice-vlan 101 enable
         port link-type trunk
         port trunk pvid vlan 102
         port trunk allow-pass vlan 102 105 107
         voice-vlan 102 enable
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        interface GigabitEthernet0/0/1
        undo port link-type
        undo voice-vlan 101 enable
        port link-type trunk
        port trunk pvid vlan 102
        port trunk allow-pass vlan 102 105 107
        voice-vlan 102 enable
        quit
        """
    ).strip()
    parser = CTreeParser(Vendor.HUAWEI)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
    assert diff.patch == diff_patch
