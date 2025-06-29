from textwrap import dedent

import pytest

from ctreepo import CTreeFactory, Platform
from ctreepo.platforms import AristaEOS, CiscoIOSXE, HuaweiVRP


def test_ctree_class() -> None:
    assert len(CTreeFactory._PLATFORM_MAP) == 3
    for _plt, _cls in zip(
        (Platform.ARISTA_EOS, Platform.HUAWEI_VRP, Platform.CISCO_IOSXE),
        (AristaEOS, HuaweiVRP, CiscoIOSXE),
        strict=True,
    ):
        assert CTreeFactory._PLATFORM_MAP[_plt] == _cls
    # assert CTreeFactory._PLATFORM_MAP[Platform.ARISTA_EOS] == AristaEOS
    # assert CTreeFactory._PLATFORM_MAP[Platform.HUAWEI_VRP] == HuaweiVRP
    # assert CTreeFactory._PLATFORM_MAP[Platform.CISCO_IOSXE] == CiscoIOSXE


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
        """,
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
        """,
    ).strip()

    huawei_root = CTreeFactory.create(Platform.HUAWEI_VRP)
    huawei_lan = CTreeFactory.create(Platform.HUAWEI_VRP, "ip vpn-instance LAN", huawei_root)
    huawei_ipv4_af_lan = CTreeFactory.create(Platform.HUAWEI_VRP, " ipv4-family", huawei_lan)
    _ = CTreeFactory.create(Platform.HUAWEI_VRP, "  vpn-target 123:123 export-extcommunity evpn", huawei_ipv4_af_lan)
    _ = CTreeFactory.create(Platform.HUAWEI_VRP, "  vpn-target 123:123 import-extcommunity evpn", huawei_ipv4_af_lan)
    _ = CTreeFactory.create(Platform.HUAWEI_VRP, " vxlan vni 123", huawei_lan)
    huawei_intf_000 = CTreeFactory.create(Platform.HUAWEI_VRP, "interface gi0/0/0", huawei_root)
    _ = CTreeFactory.create(Platform.HUAWEI_VRP, " ip address 1.1.1.1 255.255.255.252", huawei_intf_000)
    huawei_intf_001 = CTreeFactory.create(Platform.HUAWEI_VRP, "interface gi0/0/1", huawei_root)
    _ = CTreeFactory.create(Platform.HUAWEI_VRP, " ip address 1.1.1.1 255.255.255.252", huawei_intf_001)
    assert huawei_root.config == huawei_config

    arista_root = CTreeFactory.create(Platform.ARISTA_EOS)
    arista_lan = CTreeFactory.create(Platform.ARISTA_EOS, "ip vpn-instance LAN", arista_root)
    arista_ipv4_af_lan = CTreeFactory.create(Platform.ARISTA_EOS, " ipv4-family", arista_lan)
    _ = CTreeFactory.create(Platform.ARISTA_EOS, "  vpn-target 123:123 export-extcommunity evpn", arista_ipv4_af_lan)
    _ = CTreeFactory.create(Platform.ARISTA_EOS, "  vpn-target 123:123 import-extcommunity evpn", arista_ipv4_af_lan)
    _ = CTreeFactory.create(Platform.ARISTA_EOS, " vxlan vni 123", arista_lan)
    arista_intf_000 = CTreeFactory.create(Platform.ARISTA_EOS, "interface gi0/0/0", arista_root)
    _ = CTreeFactory.create(Platform.ARISTA_EOS, " ip address 1.1.1.1 255.255.255.252", arista_intf_000)
    arista_intf_001 = CTreeFactory.create(Platform.ARISTA_EOS, "interface gi0/0/1", arista_root)
    _ = CTreeFactory.create(Platform.ARISTA_EOS, " ip address 1.1.1.1 255.255.255.252", arista_intf_001)
    assert arista_root.config == arista_config

    platform = "incorrect"
    with pytest.raises(Exception) as exc:
        _ = CTreeFactory.create(platform)  # type: ignore[arg-type]
    assert str(exc.value) == f"unknown platform '{platform}'"
