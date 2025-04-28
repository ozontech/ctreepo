from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Vendor


def test_huawei_interface_qos_drr_delete() -> None:
    """Удаление qos drr."""
    current_config = dedent(
        """
        interface GigabitEthernet0/0/1
         undo portswitch
         mtu 9198
         description TEST-DESCRIPTION-1
         qos queue 5 shaping percent cir 30
         qos queue 6 shaping percent cir 5
         qos queue 7 shaping percent cir 5
         qos drr 0 to 4
         qos queue 0 drr weight 10
         qos queue 1 drr weight 20
         qos queue 2 drr weight 30
         qos queue 3 drr weight 40
         qos queue 4 drr weight 50
         qos queue 1 ecn
        #
        """
    ).strip()
    target_config = dedent(
        """
        #
        interface GigabitEthernet0/0/1
         undo portswitch
         mtu 9198
         description TEST-DESCRIPTION-2
        #
        """
    ).strip()
    diff_config = dedent(
        """
        interface GigabitEthernet0/0/1
         undo description TEST-DESCRIPTION-1
         undo qos queue 5 shaping percent cir 30
         undo qos queue 6 shaping percent cir 5
         undo qos queue 7 shaping percent cir 5
         undo qos drr 0 to 4
         undo qos queue 1 ecn
         description TEST-DESCRIPTION-2
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        interface GigabitEthernet0/0/1
        undo description TEST-DESCRIPTION-1
        undo qos queue 5 shaping percent cir 30
        undo qos queue 6 shaping percent cir 5
        undo qos queue 7 shaping percent cir 5
        undo qos drr 0 to 4
        undo qos queue 1 ecn
        description TEST-DESCRIPTION-2
        quit
        """
    ).strip()
    parser = CTreeParser(Vendor.HUAWEI)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
    assert diff.patch == diff_patch
