from pathlib import Path

import pytest

from ctreepo.ctree import CTree
from ctreepo.parser import CTreeParser
from ctreepo.tagging import TaggingRulesFromDict

CONFIG_TEXT = r"""
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
!
route-map rm_DENY deny 10
!
interface Loopback0
 description test-0
 ip address 192.168.1.1 255.255.255.255
!
interface Loopback100
 description test-100
 ip address 192.168.1.1 255.255.255.255
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


@pytest.fixture(scope="package")
def config_text() -> str:
    return CONFIG_TEXT


CONFIG_TAGS = {
    r"router bgp \d+": ["routing", "bgp"],
    r"route-map (?P<rm_name>\S+) (?:deny|permit) \d+": ["rm", "{rm_name}"],
    r"interface (?P<if_name>\S+) / ip address \S+ \S+": ["interface", "ip", "{if_name}", "interface:{if_name}"],
    r"interface (?P<if_name>\S+)": ["interface", "{if_name}", "interface:{if_name}"],
    r"crypto pki certificate chain (?P<cert_name>\S+)": ["pki", "cert", "{cert_name}"],
}


@pytest.fixture(scope="package")
def config_tags_dict() -> dict[str, list[str]]:
    return CONFIG_TAGS


@pytest.fixture(scope="package")
def config_tags_yaml_file() -> str:
    return str(Path(Path(__file__).parent, "tags.yaml"))


@pytest.fixture(scope="package")
def config_tree(config_tags_dict: dict[str, list[str]]) -> CTree:
    tagging_rules = TaggingRulesFromDict("cisco_iosxe", config_tags_dict)
    parser = CTreeParser("cisco_iosxe", tagging_rules=tagging_rules)
    root = parser.parse(CONFIG_TEXT)
    return root
