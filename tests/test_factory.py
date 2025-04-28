from textwrap import dedent

import pytest

from ctreepo import Vendor, ctree_factory
from ctreepo.factory import ctree_class
from ctreepo.vendors import AristaCT, CiscoCT, HuaweiCT


def test_ctree_class() -> None:
    assert ctree_class(Vendor.ARISTA) == AristaCT
    assert ctree_class(Vendor.HUAWEI) == HuaweiCT
    assert ctree_class(Vendor.CISCO) == CiscoCT


def test_new() -> None:
    huawei_config = dedent(
        """
        ip vpn-instance LAN
         ipv4-family
          vpn-target 123:123 export-extcommunity evpn
          vpn-target 123:123 import-extcommunity evpn
         vxlan vni 123
        #
        interface gi0/0/0
         ip address 1.1.1.1 255.255.255.252
        #
        interface gi0/0/1
         ip address 1.1.1.1 255.255.255.252
        #
        """
    ).strip()
    arista_config = dedent(
        """
        ip vpn-instance LAN
           ipv4-family
              vpn-target 123:123 export-extcommunity evpn
              vpn-target 123:123 import-extcommunity evpn
           vxlan vni 123
        !
        interface gi0/0/0
           ip address 1.1.1.1 255.255.255.252
        !
        interface gi0/0/1
           ip address 1.1.1.1 255.255.255.252
        !
        """
    ).strip()

    huawei_root = ctree_factory(Vendor.HUAWEI)
    huawei_lan = ctree_factory(Vendor.HUAWEI, "ip vpn-instance LAN", huawei_root)
    huawei_ipv4_af_lan = ctree_factory(Vendor.HUAWEI, " ipv4-family", huawei_lan)
    _ = ctree_factory(Vendor.HUAWEI, "  vpn-target 123:123 export-extcommunity evpn", huawei_ipv4_af_lan)
    _ = ctree_factory(Vendor.HUAWEI, "  vpn-target 123:123 import-extcommunity evpn", huawei_ipv4_af_lan)
    _ = ctree_factory(Vendor.HUAWEI, " vxlan vni 123", huawei_lan)
    huawei_intf_000 = ctree_factory(Vendor.HUAWEI, "interface gi0/0/0", huawei_root)
    _ = ctree_factory(Vendor.HUAWEI, " ip address 1.1.1.1 255.255.255.252", huawei_intf_000)
    huawei_intf_001 = ctree_factory(Vendor.HUAWEI, "interface gi0/0/1", huawei_root)
    _ = ctree_factory(Vendor.HUAWEI, " ip address 1.1.1.1 255.255.255.252", huawei_intf_001)
    assert huawei_root.config == huawei_config

    arista_root = ctree_factory(Vendor.ARISTA)
    arista_lan = ctree_factory(Vendor.ARISTA, "ip vpn-instance LAN", arista_root)
    arista_ipv4_af_lan = ctree_factory(Vendor.ARISTA, " ipv4-family", arista_lan)
    _ = ctree_factory(Vendor.ARISTA, "  vpn-target 123:123 export-extcommunity evpn", arista_ipv4_af_lan)
    _ = ctree_factory(Vendor.ARISTA, "  vpn-target 123:123 import-extcommunity evpn", arista_ipv4_af_lan)
    _ = ctree_factory(Vendor.ARISTA, " vxlan vni 123", arista_lan)
    arista_intf_000 = ctree_factory(Vendor.ARISTA, "interface gi0/0/0", arista_root)
    _ = ctree_factory(Vendor.ARISTA, " ip address 1.1.1.1 255.255.255.252", arista_intf_000)
    arista_intf_001 = ctree_factory(Vendor.ARISTA, "interface gi0/0/1", arista_root)
    _ = ctree_factory(Vendor.ARISTA, " ip address 1.1.1.1 255.255.255.252", arista_intf_001)
    assert arista_root.config == arista_config

    vendor = "incorrect"
    with pytest.raises(Exception) as exc:
        _ = ctree_factory(vendor)  # type: ignore[arg-type]
    assert str(exc.value) == f"unknown vendor {vendor}"
