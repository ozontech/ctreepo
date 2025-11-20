import pytest

from ctreepo.ctree import CTree
from ctreepo.parser import CTreeParser
from ctreepo.tagging import TaggingRulesFromDict

CURRENT_CONFIG_TEXT = r"""
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
no service dhcp
!
route-map rm_DENY deny 10
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
interface Loopback400
 description test-400
!
interface FastEthernet0
 switchport access vlan 100
 no ip address
 load-interval 30
!
route-map rm_PERMIT permit 10
!
router bgp 64512
 neighbor 192.168.255.1 remote-as 64512
 neighbor 192.168.255.1 update-source Loopback0
 neighbor 192.168.255.1 password 7 some-secret-old-hash
 address-family ipv4
  network 192.168.100.0 mask 255.255.255.0
  neighbor 192.168.255.1 activate
  neighbor 192.168.255.1 route-map rm_TEST_in_OLD in
  neighbor 192.168.255.2 activate
  neighbor 192.168.255.2 route-map rm_TEST_in_OLD in
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

TARGET_CONFIG_TEXT = r"""
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
no service pad
!
interface Loopback0
 description test-0-changed
 ip address 192.168.1.2 255.255.255.255
!
interface Loopback100
 ip address 192.168.100.1 255.255.255.255
!
interface Loopback200
 description test-200
 ip address 192.168.200.1 255.255.255.255
!
interface Loopback300
 description test-300
 ip address 192.168.103.1 255.255.255.255
!
interface FastEthernet0
 switchport access vlan 100
 ip address 192.168.123.1 255.255.255.252
 load-interval 60
!
route-map rm_PERMIT permit 10
 match ip address 101
!
router bgp 64512
 neighbor 192.168.255.1 remote-as 64512
 neighbor 192.168.255.1 update-source Loopback0
 neighbor 192.168.255.1 password 7 some-secret-new-hash
 address-family ipv4
  network 192.168.200.0 mask 255.255.255.0
  neighbor 192.168.255.1 activate
  neighbor 192.168.255.1 route-map rm_TEST_in in
  no neighbor 192.168.255.2 activate
  neighbor 192.168.255.2 route-map rm_TEST_in_OLD in
 exit-address-family
 address-family vpnv4
  network 192.168.1.0 mask 255.255.255.0
  network 192.168.2.0 mask 255.255.255.0
 exit-address-family
 address-family ipv6
 exit-address-family
 address-family vpnv6
 exit-address-family
!
""".strip()


CONFIG_TAGS = {
    r"router bgp \d+": ["routing", "bgp"],
    r"route-map (?P<rm_name>\S+) (?:deny|permit) \d+": ["rm", "{rm_name}"],
    r"interface (?P<if_name>\S+) / ip address \S+ \S+": ["interface", "ip", "{if_name}", "interface:{if_name}"],
    r"interface (?P<if_name>\S+)": ["interface", "{if_name}", "interface:{if_name}"],
    r"crypto pki certificate chain (?P<cert_name>\S+)": ["pki", "cert", "{cert_name}"],
}


@pytest.fixture(scope="package")
def current_config() -> str:
    return CURRENT_CONFIG_TEXT


@pytest.fixture(scope="package")
def target_config() -> str:
    return TARGET_CONFIG_TEXT


@pytest.fixture(scope="package")
def config_tags() -> dict[str, list[str]]:
    return CONFIG_TAGS


@pytest.fixture(scope="package")
def current(
    current_config: str,
    config_tags: dict[str, list[str]],
) -> CTree:
    tagging_rules = TaggingRulesFromDict("cisco_iosxe", config_tags)
    parser = CTreeParser("cisco_iosxe", tagging_rules=tagging_rules)
    root = parser.parse(current_config)
    return root


@pytest.fixture(scope="package")
def target(
    target_config: str,
    config_tags: dict[str, list[str]],
) -> CTree:
    tagging_rules = TaggingRulesFromDict("cisco_iosxe", config_tags)
    parser = CTreeParser("cisco_iosxe", tagging_rules=tagging_rules)
    root = parser.parse(target_config)
    return root


@pytest.fixture(scope="package")
def parser(
    config_tags: dict[str, list[str]],
) -> CTreeParser:
    tagging_rules = TaggingRulesFromDict("cisco_iosxe", config_tags)
    return CTreeParser("cisco_iosxe", tagging_rules=tagging_rules)
