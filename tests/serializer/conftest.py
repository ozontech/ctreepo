from typing import Any

import pytest

from ctreepo.ctree import CTree
from ctreepo.parser import CTreeParser
from ctreepo.tagging import TaggingRulesFromDict

CONFIG_TEXT = r"""
service tcp-keepalives-in
!
interface Loopback0
 description test-0
 ip address 192.168.1.1 255.255.255.255
!
router bgp 64512
 neighbor 192.168.255.1 password 7 some-secret
 address-family ipv4
  network 192.168.100.0 mask 255.255.255.0
  neighbor 192.168.255.1 activate
 exit-address-family
 address-family vpnv4
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
    r"route-map (?P<rm_name>\S+) (?:deny|permit) \d+": ["rm", "{rm_name}"],
    r"interface (?P<if_name>\S+) / ip address \S+ \S+": ["interface", "ip", "{if_name}", "interface:{if_name}"],
    r"interface (?P<if_name>\S+)": ["interface", "{if_name}", "interface:{if_name}"],
}

CONFIG_DICT = {
    "service tcp-keepalives-in": {
        "line": "service tcp-keepalives-in",
        "tags": [],
        "template": "",
        "undo": "",
        "children": {},
    },
    "interface Loopback0": {
        "line": "interface Loopback0",
        "tags": ["Loopback0", "interface", "interface:Loopback0"],
        "template": "",
        "undo": "",
        "children": {
            "description test-0": {
                "line": "description test-0",
                "tags": ["Loopback0", "interface", "interface:Loopback0"],
                "template": "description (?P<VAL>.*)",
                "undo": "no description test-0",
                "children": {},
            },
            "ip address 192.168.1.1 255.255.255.255": {
                "line": "ip address 192.168.1.1 255.255.255.255",
                "tags": ["Loopback0", "interface", "interface:Loopback0", "ip"],
                "template": "ip address 192.168.1.1(?P<MASK>\\s+[\\d.]+)",
                "undo": "no ip address 192.168.1.1 255.255.255.255",
                "children": {},
            },
        },
    },
    "router bgp 64512": {
        "line": "router bgp 64512",
        "tags": ["bgp", "routing"],
        "template": "",
        "undo": "",
        "children": {
            "neighbor 192.168.255.1 password 7 some-secret": {
                "line": "neighbor 192.168.255.1 password 7 some-secret",
                "tags": ["bgp", "routing"],
                "template": "",
                "undo": "",
                "children": {},
            },
            "address-family ipv4": {
                "line": "address-family ipv4",
                "tags": ["bgp", "routing"],
                "template": "",
                "undo": "",
                "children": {
                    "network 192.168.100.0 mask 255.255.255.0": {
                        "line": "network 192.168.100.0 mask 255.255.255.0",
                        "tags": ["bgp", "routing"],
                        "template": "",
                        "undo": "",
                        "children": {},
                    },
                    "neighbor 192.168.255.1 activate": {
                        "line": "neighbor 192.168.255.1 activate",
                        "tags": ["bgp", "routing"],
                        "template": "",
                        "undo": "",
                        "children": {},
                    },
                },
            },
            "address-family vpnv4": {
                "line": "address-family vpnv4",
                "tags": ["bgp", "routing"],
                "template": "",
                "undo": "",
                "children": {},
            },
        },
    },
}


@pytest.fixture(scope="package")
def config_dict() -> dict[str, dict[str, Any]]:
    return CONFIG_DICT


@pytest.fixture(scope="package")
def config_tree() -> CTree:
    tagging_rules = TaggingRulesFromDict("cisco_iosxe", CONFIG_TAGS)
    parser = CTreeParser("cisco_iosxe", tagging_rules=tagging_rules)
    template = parser.parse(CONFIG_TEMPLATE)
    root = parser.parse(CONFIG_TEXT, template)
    return root
