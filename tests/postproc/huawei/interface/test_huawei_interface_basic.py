from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Platform


def test_huawei_interface_basic() -> None:
    """Базовый."""
    config_interfaces_1 = dedent(
        """
        interface 25GE1/0/1
         port link-type trunk
         undo port trunk allow-pass vlan 1
         stp edged-port enable
         storm suppression multicast packets 50
         storm suppression broadcast packets 200
         sflow sampling collector 1
         sflow sampling inbound
         device transceiver 25GBASE-COPPER
        #
        interface 25GE1/0/1.1234 mode l2
         encapsulation untag
         bridge-domain 1234
         statistics enable
        #
        interface 25GE1/0/2
         port link-type trunk
         undo port trunk allow-pass vlan 1
         stp edged-port enable
         storm suppression multicast packets 50
         storm suppression broadcast packets 200
         sflow sampling collector 1
         sflow sampling inbound
         device transceiver 25GBASE-COPPER
        #
        interface 25GE1/0/2.1234 mode l2
         encapsulation untag
         bridge-domain 1234
         statistics enable
        #
        """,
    ).strip()

    config_interfaces_2 = dedent(
        """
        #
        interface 25GE1/0/2
         port link-type trunk
         undo port trunk allow-pass vlan 1
         stp edged-port enable
         storm suppression multicast packets 50
         storm suppression broadcast packets 200
         sflow sampling collector 1
         sflow sampling inbound
         description test
         device transceiver 25GBASE-COPPER
        #
        interface 25GE1/0/2.1234 mode l2
         encapsulation untag
         bridge-domain 1234
         statistics enable
        #
        """,
    ).strip()

    diff_config = dedent(
        """
        interface 25GE1/0/2
         description test
        #
        undo interface 25GE1/0/1.1234 mode l2
        #
        undo interface 25GE1/0/1
        #
        """,
    ).strip()
    diff_patch = dedent(
        """
        interface 25GE1/0/2
        description test
        quit
        undo interface 25GE1/0/1.1234 mode l2
        undo interface 25GE1/0/1
        """,
    ).strip()
    parser = CTreeParser(Platform.HUAWEI_VRP)

    root1 = parser.parse(config_interfaces_1)
    root2 = parser.parse(config_interfaces_2)

    diff = CTreeDiffer.diff(root1, root2)
    assert diff.config == diff_config
    assert diff.patch == diff_patch
