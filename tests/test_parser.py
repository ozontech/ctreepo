from pathlib import Path
from textwrap import dedent

import pytest

from ctreepo import CTreeParser, Platform
from ctreepo.models import TaggingRule
from ctreepo.parser import TaggingRules, TaggingRulesDict, TaggingRulesFile

huawei_config = dedent(
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
     description test
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
    """,
).strip()

arista_config = dedent(
    """
    sflow collector 1 ip 100.64.0.1 vpn-instance MGMT
    !
    storm suppression statistics enable
    !
    ip vpn-instance MGMT
       ipv4-family
          route-distinguisher 192.168.0.1:123
    !
    ip vpn-instance LAN
       ipv4-family
          route-distinguisher 192.168.0.1:123
          vpn-target 123:123 export-extcommunity evpn
          vpn-target 123:123 import-extcommunity evpn
       vxlan vni 123
    !
    interface gi0/0/0
       description test
       ip address 1.1.1.1 255.255.255.252
    !
    interface gi0/0/1
       ip address 1.1.1.1 255.255.255.252
    !
    ntp-service authentication-keyid 1 authentication-mode md5 cipher secret_password
    !
    radius-server template RADIUS_TEMPLATE
       radius-server shared-key cipher secret_password
       radius-server algorithm loading-share
    !
    """,
).strip()


@pytest.fixture(scope="session")
def get_dict_loader() -> TaggingRules:
    tagging_rules_dict: dict[Platform, list[dict[str, str | list[str]]]] = {
        Platform.HUAWEI_VRP: [
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


@pytest.fixture(scope="session")
def get_file_loader() -> TaggingRules:
    loader = TaggingRulesFile(Path(__file__).with_suffix(".yaml"))
    return loader


def test_instance() -> None:
    parser = CTreeParser(Platform.HUAWEI_VRP)
    root = parser.parse(huawei_config)
    assert root.config == huawei_config

    parser = CTreeParser(Platform.ARISTA_EOS)
    root = parser.parse(arista_config)
    assert root.config == arista_config


def test_empty_line() -> None:
    src_config = dedent(
        """
        interface gi0/0/0

           ip address 1.1.1.1 255.255.255.252
        !
        """,
    ).strip()
    config = dedent(
        """
        interface gi0/0/0
           ip address 1.1.1.1 255.255.255.252
        !
        """,
    ).strip()
    parser = CTreeParser(Platform.ARISTA_EOS)
    root = parser.parse(src_config)
    assert root.config == config


def test_deep_nested() -> None:
    config = dedent(
        """
        storm suppression statistics enable
        #
        ip vpn-instance LAN
         ipv4-family
          route-distinguisher 192.168.0.1:123
           vpn-target 123:123 export-extcommunity evpn
            vpn-target 123:123 import-extcommunity evpn
             sublevel-1
              sublevel-2
         vxlan vni 123
        #
        interface gi0/0/0
         ip address 1.1.1.1 255.255.255.252
        #
        """,
    ).strip()
    parser = CTreeParser(Platform.HUAWEI_VRP)
    root = parser.parse(config)
    assert root.config == config


def test_dict_rules(get_dict_loader: TaggingRules) -> None:
    parser = CTreeParser(Platform.HUAWEI_VRP, get_dict_loader)
    assert parser.tagging_rules == [
        TaggingRule(regex=r"^ip vpn-instance (\S+)$", tags=["vpn"]),
        TaggingRule(regex=r"^ip vpn-instance (\S+) .* export-extcommunity evpn", tags=["rt"]),
        TaggingRule(regex=r"^interface (\S+)$", tags=["interface"]),
        TaggingRule(regex=r"^interface (gi0/0/0) .* ip address \S+ \S+$", tags=["ip", "interface-1"]),
        TaggingRule(regex=r"^interface (gi0/0/1) .* ip address \S+ \S+$", tags=["ip", "interface-2"]),
        TaggingRule(regex=r"^ip vpn-instance (LAN) .* route-distinguisher (\S+)", tags=["rd"]),
    ]


def test_file_rules(get_file_loader: TaggingRules) -> None:
    parser = CTreeParser(Platform.HUAWEI_VRP, get_file_loader)
    assert parser.tagging_rules == [
        TaggingRule(regex=r"^ip vpn-instance (\S+)$", tags=["vpn"]),
        TaggingRule(regex=r"^ip vpn-instance (\S+) .* export-extcommunity evpn", tags=["rt"]),
        TaggingRule(regex=r"^interface (\S+)$", tags=["interface"]),
        TaggingRule(regex=r"^interface (gi0/0/0) .* ip address \S+ \S+$", tags=["ip", "interface-1"]),
        TaggingRule(regex=r"^interface (gi0/0/1) .* ip address \S+ \S+$", tags=["ip", "interface-2"]),
        TaggingRule(regex=r"^ip vpn-instance (LAN) .* route-distinguisher (\S+)", tags=["rd"]),
    ]


def test_tags(get_dict_loader: TaggingRules) -> None:
    parser = CTreeParser(Platform.HUAWEI_VRP, get_dict_loader)
    root = parser.parse(huawei_config)
    assert root.config == huawei_config

    vpn = root.children["ip vpn-instance LAN"]
    assert set(vpn.tags) == set(["vpn", "LAN"])
    assert len(vpn.tags) == 2

    mgmt = root.children["ip vpn-instance MGMT"]
    assert set(mgmt.tags) == set(["vpn", "MGMT"])
    assert len(mgmt.tags) == 2

    af = vpn.children["ipv4-family"]
    assert set(af.tags) == set(["vpn", "LAN"])
    assert len(af.tags) == 2

    interface = root.children["interface gi0/0/0"]
    assert set(interface.tags) == set(["interface", "gi0/0/0"])
    assert len(interface.tags) == 2

    radius = root.children["radius-server template RADIUS_TEMPLATE"]
    assert set(radius.tags) == set()
    assert len(radius.tags) == 0

    rd = root.children["ip vpn-instance LAN"].children["ipv4-family"].children["route-distinguisher 192.168.0.1:123"]
    assert set(rd.tags) == set(["rd", "LAN", "192.168.0.1:123"])
    assert len(rd.tags) == 3

    rd = root.children["ip vpn-instance MGMT"].children["ipv4-family"].children["route-distinguisher 192.168.0.1:123"]
    assert set(rd.tags) == set(["vpn", "MGMT"])
    assert len(rd.tags) == 2

    ip = root.children["interface gi0/0/0"].children["ip address 1.1.1.1 255.255.255.252"]
    assert set(ip.tags) == set(["ip", "interface-1", "gi0/0/0"])
    assert len(ip.tags) == 3

    ip = root.children["interface gi0/0/1"].children["ip address 1.1.1.1 255.255.255.252"]
    assert set(ip.tags) == set(["ip", "interface-2", "gi0/0/1"])
    assert len(ip.tags) == 3


def test_file_rules_loader() -> None:
    loader1 = TaggingRulesFile(Path(__file__).with_suffix(".yaml"))
    loader2 = TaggingRulesFile(str(Path(__file__).with_suffix(".yaml")))
    assert id(loader1) == id(loader2)
    assert loader1.rules == {
        Platform.HUAWEI_VRP: [
            TaggingRule(regex=r"^ip vpn-instance (\S+)$", tags=["vpn"]),
            TaggingRule(regex=r"^ip vpn-instance (\S+) .* export-extcommunity evpn", tags=["rt"]),
            TaggingRule(regex=r"^interface (\S+)$", tags=["interface"]),
            TaggingRule(regex=r"^interface (gi0/0/0) .* ip address \S+ \S+$", tags=["ip", "interface-1"]),
            TaggingRule(regex=r"^interface (gi0/0/1) .* ip address \S+ \S+$", tags=["ip", "interface-2"]),
            TaggingRule(regex=r"^ip vpn-instance (LAN) .* route-distinguisher (\S+)", tags=["rd"]),
        ],
        Platform.ARISTA_EOS: [
            TaggingRule(regex="^interface (\\S+)$", tags=["interface"]),
        ],
    }


def test_dict_rules_loader() -> None:
    tagging_rules_dict = {
        Platform.HUAWEI_VRP: [
            {"regex": r"^ip vpn-instance (\S+)$", "tags": ["vpn"]},
            {"regex": r"^ip vpn-instance (\S+) .* export-extcommunity evpn", "tags": ["rt"]},
            {"regex": r"^interface (\S+)$", "tags": ["interface"]},
            {"regex": r"^interface (gi0/0/0) .* ip address \S+ \S+$", "tags": ["ip", "interface-1"]},
            {"regex": r"^interface (gi0/0/1) .* ip address \S+ \S+$", "tags": ["ip", "interface-2"]},
            {"regex": r"^ip vpn-instance (LAN) .* route-distinguisher (\S+)", "tags": ["rd"]},
        ],
        Platform.ARISTA_EOS: [
            {"regex": "^interface (\\S+)$", "tags": ["interface"]},
        ],
        "unknown_platform": [
            {"regex": "^interface (\\S+)$", "tags": ["interface"]},
        ],
    }
    loader = TaggingRulesDict(tagging_rules_dict)  # type: ignore[arg-type]
    assert loader.rules == {
        Platform.HUAWEI_VRP: [
            TaggingRule(regex=r"^ip vpn-instance (\S+)$", tags=["vpn"]),
            TaggingRule(regex=r"^ip vpn-instance (\S+) .* export-extcommunity evpn", tags=["rt"]),
            TaggingRule(regex=r"^interface (\S+)$", tags=["interface"]),
            TaggingRule(regex=r"^interface (gi0/0/0) .* ip address \S+ \S+$", tags=["ip", "interface-1"]),
            TaggingRule(regex=r"^interface (gi0/0/1) .* ip address \S+ \S+$", tags=["ip", "interface-2"]),
            TaggingRule(regex=r"^ip vpn-instance (LAN) .* route-distinguisher (\S+)", tags=["rd"]),
        ],
        Platform.ARISTA_EOS: [
            TaggingRule(regex="^interface (\\S+)$", tags=["interface"]),
        ],
    }


def test_repeated_section() -> None:
    config = dedent(
        """
        bgp 12345
         ipv4-family vpn-instance VRF_LAN
          peer MY_PEER_1 route-policy RP_MY_1 import
         ipv4-family unicast
          import-route direct route-policy RP_LOOPBACKS
         ipv4-family vpn-instance VRF_LAN
          peer MY_PEER_2 route-policy RP_MY_2 import
        """,
    )
    target_config = dedent(
        """
        bgp 12345
         ipv4-family vpn-instance VRF_LAN
          peer MY_PEER_1 route-policy RP_MY_1 import
          peer MY_PEER_2 route-policy RP_MY_2 import
         ipv4-family unicast
          import-route direct route-policy RP_LOOPBACKS
        #
        """,
    ).strip()
    parser = CTreeParser(Platform.HUAWEI_VRP)
    root = parser.parse(config)
    assert root.config == target_config
