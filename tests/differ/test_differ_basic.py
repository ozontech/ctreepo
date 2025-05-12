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


def test_rule_with_undo() -> None:
    current_str = dedent(
        """
        interface LoopBack0
         description OLD
         command arg1 arg2
         load-interval 30
        acl name ACL 1234
         rule 10 permit ip source 192.168.0.0 0.0.0.255
         rule 10 description mgmt-network
         rule 15 permit tcp destination-port range 1024 2048
        """
    )
    target_str = dedent(
        """
        interface LoopBack0
         description NEW
         command arg1 arg22
        acl name ACL 1234
         rule 10 permit ip source 192.168.1.0 0.0.0.255
         rule 10 description old mgmt-network
         rule 15 permit tcp destination-port range 1024 2048
        """
    )
    template_str = dedent(
        r"""
        interface \S+
         description (?P<DESCRIPTION>.*)               UNDO>> undo description \1
         command (?P<ARG1>\S+) (?P<ARG2>\S+)           UNDO>> undo command \1
         load-interval (?P<INTERVAL>\d+)               UNDO>> undo load-interval
        acl name \S+ \d+
         rule (\d+) description (?P<DESCRIPTION>.*)    UNDO>> undo rule \1 description
         rule (\d+) (?P<RULE>.*)                       UNDO>> undo rule \1
        """
    )
    diff_config_raw = dedent(
        """
        interface LoopBack0
         undo description OLD
         undo command arg1 arg2
         undo load-interval 30
         description NEW
         command arg1 arg22
        #
        acl name ACL 1234
         undo rule 10 permit ip source 192.168.0.0 0.0.0.255
         undo rule 10 description mgmt-network
         rule 10 permit ip source 192.168.1.0 0.0.0.255
         rule 10 description old mgmt-network
        #
        """
    ).strip()
    diff_config = dedent(
        """
        interface LoopBack0
         undo load-interval
         description NEW
         command arg1 arg22
        #
        acl name ACL 1234
         rule 10 permit ip source 192.168.1.0 0.0.0.255
         rule 10 description old mgmt-network
        #
        """
    ).strip()
    parser = CTreeParser(Vendor.HUAWEI)

    template = parser.parse(template_str)
    current = parser.parse(current_str, template)
    current_raw = parser.parse(current_str)
    target = parser.parse(target_str, template)
    target_raw = parser.parse(target_str)

    diff = CTreeDiffer().diff(current, target)
    diff_raw = CTreeDiffer().diff(current_raw, target_raw)

    assert diff.config == diff_config
    assert diff_raw.config == diff_config_raw
