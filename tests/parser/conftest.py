import pytest

from ctreepo.ctree import CTree
from ctreepo.spec import PlatformRegistry

CONFIG_TEXT = r"""
service tcp-keepalives-in
!
interface Loopback0
 description test-0
 ip address 192.168.0.1 255.255.255.255
 ip address 192.168.0.2 255.255.255.255 secondary
 ip address 192.168.0.3/32
 ip address 192.168.0.4/32 secondary
 load-interval 30
!
interface Loopback1
 description test-1
 load-interval 30
!
route-map rm_PERMIT permit 10

router bgp 64512
 neighbor 192.168.255.1 password 7 some-secret
 address-family ipv4
  network 192.168.100.0 mask 255.255.255.0
  neighbor 192.168.255.1 activate
  neighbor 192.168.255.1 activate
 exit-address-family
 address-family vpnv4
  network 192.168.1.0 mask 255.255.255.0
 exit-address-family
 address-family ipv6
 exit-address-family
!
""".strip()

CONFIG_TEMPLATE = r"""
interface \S+
 (description) (?P<VAL>.*) UNDO>> no \1 \g<VAL>
 ip address ([\d.]+)((?P<MASK>\s+[\d.]+)|(?P<PLEN>\/\d+))\s?(secondary)? UNDO>> no ip address \1\2 \5
 (load-interval) (?P<VAL>\d+) UNDO>> no \1
!
route-map \S+ (?:permit|deny) \d+
!
""".strip()

CONFIG_TAGS = {
    r"router bgp \d+": ["routing", "bgp"],
    r"route-map (?P<rm_name>\S+) (?:deny|permit) \d+": ["rm"],
}


@pytest.fixture(scope="package")
def manual_tree() -> CTree:
    spec = PlatformRegistry.get_spec("cisco_iosxe")
    root = CTree.create_root(spec)
    _ = CTree(line="service tcp-keepalives-in", parent=root)
    loopback0 = CTree(line="interface Loopback0", parent=root)
    _ = CTree(line="description test-0", parent=loopback0)
    _ = CTree(line="ip address 192.168.0.1 255.255.255.255", parent=loopback0)
    _ = CTree(line="ip address 192.168.0.2 255.255.255.255 secondary", parent=loopback0)
    _ = CTree(line="ip address 192.168.0.3/32", parent=loopback0)
    _ = CTree(line="ip address 192.168.0.4/32 secondary", parent=loopback0)
    _ = CTree(line="load-interval 30", parent=loopback0)
    loopback1 = CTree(line="interface Loopback1", parent=root)
    _ = CTree(line="description test-1", parent=loopback1)
    _ = CTree(line="load-interval 30", parent=loopback1)
    _ = CTree(line="route-map rm_PERMIT permit 10", parent=root, tags={"rm", "rm_PERMIT"})
    bgp = CTree(line="router bgp 64512", parent=root, tags={"routing", "bgp"})
    _ = CTree(line="neighbor 192.168.255.1 password 7 some-secret", parent=bgp)
    ipv4 = CTree(line="address-family ipv4", parent=bgp)
    vpnv4 = CTree(line="address-family vpnv4", parent=bgp)
    _ = CTree(line="address-family ipv6", parent=bgp)
    _ = CTree(line="network 192.168.100.0 mask 255.255.255.0", parent=ipv4)
    _ = CTree(line="neighbor 192.168.255.1 activate", parent=ipv4)
    _ = CTree(line="network 192.168.1.0 mask 255.255.255.0", parent=vpnv4)
    return root


@pytest.fixture(scope="package")
def config_text() -> str:
    return CONFIG_TEXT


@pytest.fixture(scope="package")
def config_template() -> str:
    return CONFIG_TEMPLATE


@pytest.fixture(scope="package")
def config_tags() -> dict[str, list[str]]:
    return CONFIG_TAGS
