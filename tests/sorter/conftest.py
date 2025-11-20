import pytest

from ctreepo.ctree import CTree
from ctreepo.parser import CTreeParser
from ctreepo.tagging import TaggingRulesFromDict

CONFIG_TEXT = r"""
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
!
route-map rm_DENY deny 10
 match ip address 101
!
interface Loopback0
 description test-0
 ip address 192.168.1.1 255.255.255.255
!
interface Loopback100
 description test-100
 ip address 192.168.100.1 255.255.255.255
!
interface Loopback200
 description test-200
 ip address 192.168.200.1 255.255.255.255
!
interface FastEthernet0
 switchport access vlan 100
 no ip address
!
route-map rm_PERMIT permit 10
!
router bgp 64512
 neighbor 192.168.255.1 remote-as 64512
 neighbor 192.168.255.1 update-source Loopback0
 neighbor 192.168.255.1 password 7 some-secret
 address-family ipv4
  network 192.168.100.0 mask 255.255.255.0
  neighbor 192.168.255.1 activate
 exit-address-family
 address-family vpnv4
  network 192.168.1.0 mask 255.255.255.0
 exit-address-family
 address-family ipv6
 exit-address-family
 address-family vpnv6
 exit-address-family
!
""".strip()


TREE_CONFIG = r"""
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
!
route-map rm_DENY deny 10
 match ip address 101
!
interface Loopback0
 description test-0
 ip address 192.168.1.1 255.255.255.255
!
interface Loopback100
 description test-100
 ip address 192.168.100.1 255.255.255.255
!
interface Loopback200
 description test-200
 ip address 192.168.200.1 255.255.255.255
!
interface FastEthernet0
 switchport access vlan 100
 no ip address
!
route-map rm_PERMIT permit 10
!
router bgp 64512
 neighbor 192.168.255.1 remote-as 64512
 neighbor 192.168.255.1 update-source Loopback0
 neighbor 192.168.255.1 password 7 some-secret
 address-family ipv4
  network 192.168.100.0 mask 255.255.255.0
  neighbor 192.168.255.1 activate
 !
 address-family vpnv4
  network 192.168.1.0 mask 255.255.255.0
 !
 address-family ipv6
 !
 address-family vpnv6
 !
!
""".strip()


CONFIG_TAGS = {
    r"router bgp \d+": ["routing", "bgp"],
    r"route-map (?P<rm_name>\S+) (?:deny|permit) \d+": ["rm"],
    r"interface (?P<if_name>\S+) / ip address \S+ \S+": ["interface", "ip", "{if_name}", "interface:{if_name}"],
    r"interface (?P<if_name>\S+)": ["interface", "{if_name}", "interface:{if_name}"],
}


@pytest.fixture(scope="package")
def config_text() -> str:
    return CONFIG_TEXT


@pytest.fixture(scope="package")
def tree_config() -> str:
    return TREE_CONFIG


@pytest.fixture(scope="package")
def config_tags() -> dict[str, list[str]]:
    return CONFIG_TAGS


@pytest.fixture(scope="function")
def config_tree(config_text: str, config_tags: dict[str, list[str]]) -> CTree:
    tagging_rules = TaggingRulesFromDict("cisco_iosxe", config_tags)
    parser = CTreeParser("cisco_iosxe", tagging_rules=tagging_rules)
    root = parser.parse(config_text)
    return root
