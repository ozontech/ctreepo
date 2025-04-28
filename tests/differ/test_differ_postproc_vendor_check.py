from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Vendor
from ctreepo.postproc_huawei import HuaweiPostProcInterface, HuaweiPostProcRoutePolicy

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


def test_differ_postproc_vendor_check() -> None:
    diff_config = dedent(
        """
        interface 25GE1/0/2
           description test
        !
        no interface 25GE1/0/1
        !
        no interface 25GE1/0/1.1234 mode l2
        !
        """
    ).strip()
    diff_patch = dedent(
        """
        interface 25GE1/0/2
        description test
        exit
        no interface 25GE1/0/1
        no interface 25GE1/0/1.1234 mode l2
        """
    ).strip()
    parser = CTreeParser(vendor=Vendor.ARISTA)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(
        a=current,
        b=target,
        post_proc_rules=[
            HuaweiPostProcRoutePolicy,
            HuaweiPostProcInterface,
        ],
    )
    assert diff.config == diff_config
    assert diff.patch == diff_patch
