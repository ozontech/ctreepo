from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Vendor

current_config = dedent(
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
    """
).strip()
target_config = dedent(
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
    """
).strip()


def test_differ_wo_rules() -> None:
    diff_config = dedent(
        """
        interface 25GE1/0/2
         description test
        #
        undo interface 25GE1/0/1
        #
        undo interface 25GE1/0/1.1234 mode l2
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        interface 25GE1/0/2
        description test
        quit
        undo interface 25GE1/0/1
        undo interface 25GE1/0/1.1234 mode l2
        """
    ).strip()
    parser = CTreeParser(vendor=Vendor.HUAWEI)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_differ_w_rules() -> None:
    diff_config = dedent(
        """
        interface 25GE1/0/2
         description test
        #
        undo interface 25GE1/0/1.1234 mode l2
        #
        undo interface 25GE1/0/1
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        interface 25GE1/0/2
        description test
        quit
        undo interface 25GE1/0/1.1234 mode l2
        undo interface 25GE1/0/1
        """
    ).strip()
    parser = CTreeParser(vendor=Vendor.HUAWEI)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_double_undo() -> None:
    current_config = dedent(
        """
        no service dhcp
        no service pad
        ip dhcp bootp ignore
        interface Loopback0
         ip address 1.2.3.4 255.255.255.255
         no keepalive
        interface Loopback1
         ip address 1.2.3.4 255.255.255.255
        """
    )
    target_config = dedent(
        """
        service pad
        no ip dhcp bootp ignore
        interface Loopback0
         ip address 1.2.3.4 255.255.255.255
        """
    )
    diff_config = dedent(
        """
        service dhcp
        !
        service pad
        !
        interface Loopback0
         keepalive
        !
        no ip dhcp bootp ignore
        !
        no interface Loopback1
        !
        """
    ).strip()
    parser = CTreeParser(Vendor.CISCO)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
