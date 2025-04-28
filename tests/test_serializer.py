from textwrap import dedent

import pytest

from ctreepo import CTreeParser, CTreeSerializer, Vendor
from ctreepo.parser import TaggingRules, TaggingRulesDict

config = dedent(
    """
    sflow collector 1 ip 100.64.0.1 vpn-instance MGMT
    #
    storm suppression statistics enable
    #
    ip vpn-instance MGMT
     ipv4-family
      route-distinguisher 192.168.0.1:123
    #
    ip vpn-instance LAN
     ipv4-family
      route-distinguisher 192.168.0.1:123
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
    ntp-service authentication-keyid 1 authentication-mode md5 cipher secret_password
    #
    radius-server template RADIUS_TEMPLATE
     radius-server shared-key cipher secret_password
     radius-server algorithm loading-share
    #
    """
).strip()

config_dict = {
    "line": "",
    "tags": [],
    "template": "",
    "children": {
        "sflow collector 1 ip 100.64.0.1 vpn-instance MGMT": {
            "line": "sflow collector 1 ip 100.64.0.1 vpn-instance MGMT",
            "tags": [],
            "template": "",
            "children": {},
        },
        "storm suppression statistics enable": {
            "line": "storm suppression statistics enable",
            "tags": [],
            "template": "",
            "children": {},
        },
        "ip vpn-instance MGMT": {
            "line": "ip vpn-instance MGMT",
            "tags": ["vpn", "MGMT"],
            "template": "",
            "children": {
                "ipv4-family": {
                    "line": "ipv4-family",
                    "tags": ["vpn", "MGMT"],
                    "template": "",
                    "children": {
                        "route-distinguisher 192.168.0.1:123": {
                            "line": "route-distinguisher 192.168.0.1:123",
                            "tags": ["vpn", "MGMT"],
                            "template": "",
                            "children": {},
                        }
                    },
                }
            },
        },
        "ip vpn-instance LAN": {
            "line": "ip vpn-instance LAN",
            "tags": ["vpn", "LAN"],
            "template": "",
            "children": {
                "ipv4-family": {
                    "line": "ipv4-family",
                    "tags": ["vpn", "LAN"],
                    "template": "",
                    "children": {
                        "route-distinguisher 192.168.0.1:123": {
                            "line": "route-distinguisher 192.168.0.1:123",
                            "tags": ["rd", "LAN", "192.168.0.1:123"],
                            "template": "",
                            "children": {},
                        },
                        "vpn-target 123:123 export-extcommunity evpn": {
                            "line": "vpn-target 123:123 export-extcommunity evpn",
                            "tags": ["rt", "LAN"],
                            "template": "",
                            "children": {},
                        },
                        "vpn-target 123:123 import-extcommunity evpn": {
                            "line": "vpn-target 123:123 import-extcommunity evpn",
                            "tags": ["vpn", "LAN"],
                            "template": "",
                            "children": {},
                        },
                    },
                },
                "vxlan vni 123": {
                    "line": "vxlan vni 123",
                    "tags": ["vpn", "LAN"],
                    "template": "",
                    "children": {},
                },
            },
        },
        "interface gi0/0/0": {
            "line": "interface gi0/0/0",
            "tags": ["interface", "gi0/0/0"],
            "template": "",
            "children": {
                "ip address 1.1.1.1 255.255.255.252": {
                    "line": "ip address 1.1.1.1 255.255.255.252",
                    "tags": ["ip", "interface-1", "gi0/0/0"],
                    "template": "",
                    "children": {},
                }
            },
        },
        "interface gi0/0/1": {
            "line": "interface gi0/0/1",
            "tags": ["interface", "gi0/0/1"],
            "template": "",
            "children": {
                "ip address 1.1.1.1 255.255.255.252": {
                    "line": "ip address 1.1.1.1 255.255.255.252",
                    "tags": ["ip", "interface-2", "gi0/0/1"],
                    "template": "",
                    "children": {},
                }
            },
        },
        "ntp-service authentication-keyid 1 authentication-mode md5 cipher secret_password": {
            "line": "ntp-service authentication-keyid 1 authentication-mode md5 cipher secret_password",
            "tags": [],
            "template": "",
            "children": {},
        },
        "radius-server template RADIUS_TEMPLATE": {
            "line": "radius-server template RADIUS_TEMPLATE",
            "tags": [],
            "template": "",
            "children": {
                "radius-server shared-key cipher secret_password": {
                    "line": "radius-server shared-key cipher secret_password",
                    "tags": [],
                    "template": "",
                    "children": {},
                },
                "radius-server algorithm loading-share": {
                    "line": "radius-server algorithm loading-share",
                    "tags": [],
                    "template": "",
                    "children": {},
                },
            },
        },
    },
}


@pytest.fixture(scope="session")
def get_dict_loader() -> TaggingRules:
    tagging_rules_dict: dict[Vendor, list[dict[str, str | list[str]]]] = {
        Vendor.HUAWEI: [
            {"regex": r"^ip vpn-instance (\S+)$", "tags": ["vpn"]},
            {"regex": r"^ip vpn-instance (\S+) .* export-extcommunity evpn", "tags": ["rt"]},
            {"regex": r"^interface (\S+)$", "tags": ["interface"]},
            {"regex": r"^interface (gi0/0/0) .* ip address \S+ \S+$", "tags": ["ip", "interface-1"]},
            {"regex": r"^interface (gi0/0/1) .* ip address \S+ \S+$", "tags": ["ip", "interface-2"]},
            {"regex": r"^ip vpn-instance (LAN) .* route-distinguisher (\S+)", "tags": ["rd"]},
        ],
    }
    loader = TaggingRulesDict(tagging_rules_dict)
    return loader


def test_to_dict(get_dict_loader: TaggingRules) -> None:
    parser = CTreeParser(vendor=Vendor.HUAWEI, tagging_rules=get_dict_loader)
    root = parser.parse(config)
    serialized_config = CTreeSerializer.to_dict(root)
    assert serialized_config == config_dict


def test_from_dict(get_dict_loader: TaggingRules) -> None:
    parser = CTreeParser(vendor=Vendor.HUAWEI, tagging_rules=get_dict_loader)
    root_from_config = parser.parse(config)

    root_from_dict = CTreeSerializer.from_dict(Vendor.HUAWEI, config_dict)
    assert root_from_config == root_from_dict
