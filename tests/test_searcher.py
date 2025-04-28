from textwrap import dedent
from typing import Literal

import pytest

from ctreepo import CTree, CTreeParser, CTreeSearcher, CTreeSerializer, Vendor, ctree_factory
from ctreepo.parser import TaggingRulesDict

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


@pytest.fixture(scope="session")
def get_config_tree() -> CTree:
    tagging_rules_dict: dict[Vendor, list[dict[str, str | list[str]]]] = {
        Vendor.HUAWEI: [
            {"regex": r"^ip vpn-instance (\S+)$", "tags": ["vpn"]},
            {"regex": r"^ip vpn-instance (\S+) .* export-extcommunity evpn", "tags": ["rt"]},
            {"regex": r"^interface (\S+)$", "tags": ["interface"]},
            {"regex": r"^interface (gi0/0/0) .* ip address \S+ \S+$", "tags": ["ip", "interface-1"]},
            {"regex": r"^interface (gi0/0/1) .* ip address \S+ \S+$", "tags": ["ip", "interface-2"]},
            {"regex": r"^ip vpn-instance (\S+) .* route-distinguisher (\S+)", "tags": ["rd"]},
        ],
    }
    loader = TaggingRulesDict(tagging_rules_dict)
    parser = CTreeParser(vendor=Vendor.HUAWEI, tagging_rules=loader)
    root = parser.parse(config)
    return root


def test_string(get_config_tree: CTree) -> None:
    filtered_config = dedent(
        """
        interface gi0/0/0
         ip address 1.1.1.1 255.255.255.252
        #
        interface gi0/0/1
         ip address 1.1.1.1 255.255.255.252
        #
        """
    ).strip()
    filtered_dict = {
        "line": "",
        "tags": [],
        "template": "",
        "children": {
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
        },
    }
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, string="ip address 1.1.1.1 255.255.255.252")
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_regex(get_config_tree: CTree) -> None:
    filtered_config = dedent(
        """
        sflow collector 1 ip 100.64.0.1 vpn-instance MGMT
        #
        ip vpn-instance MGMT
         ipv4-family
          route-distinguisher 192.168.0.1:123
        #
        ip vpn-instance LAN
         ipv4-family
          route-distinguisher 192.168.0.1:123
        #
        interface gi0/0/0
         ip address 1.1.1.1 255.255.255.252
        #
        interface gi0/0/1
         ip address 1.1.1.1 255.255.255.252
        #
        """
    ).strip()
    filtered_dict = {
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
                                "tags": ["rd", "MGMT", "192.168.0.1:123"],
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
                            }
                        },
                    }
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
        },
    }
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, string=r"(?:\d+\.){3}\d+")
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_tag(get_config_tree: CTree) -> None:
    filtered_config = dedent(
        """
        ip vpn-instance MGMT
         ipv4-family
        #
        ip vpn-instance LAN
         ipv4-family
          vpn-target 123:123 import-extcommunity evpn
         vxlan vni 123
        #
        """
    ).strip()
    filtered_dict = {
        "line": "",
        "tags": [],
        "template": "",
        "children": {
            "ip vpn-instance MGMT": {
                "line": "ip vpn-instance MGMT",
                "tags": ["vpn", "MGMT"],
                "template": "",
                "children": {
                    "ipv4-family": {
                        "line": "ipv4-family",
                        "tags": ["vpn", "MGMT"],
                        "template": "",
                        "children": {},
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
        },
    }
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, include_tags=["vpn"])
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_tags_or(get_config_tree: CTree) -> None:
    filtered_config = dedent(
        """
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
        """
    ).strip()
    filtered_dict = {
        "line": "",
        "tags": [],
        "template": "",
        "children": {
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
                                "tags": ["rd", "MGMT", "192.168.0.1:123"],
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
                                "template": "",
                                "children": {},
                                "line": "route-distinguisher 192.168.0.1:123",
                                "tags": ["rd", "LAN", "192.168.0.1:123"],
                            },
                            "vpn-target 123:123 export-extcommunity evpn": {
                                "template": "",
                                "children": {},
                                "line": "vpn-target 123:123 export-extcommunity evpn",
                                "tags": ["rt", "LAN"],
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
        },
    }
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, include_tags=["vpn", "LAN", "MGMT"], include_mode="or")
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_tags_and(get_config_tree: CTree) -> None:
    filtered_config = dedent(
        """
        ip vpn-instance LAN
         ipv4-family
          route-distinguisher 192.168.0.1:123
        #
        """
    ).strip()
    filtered_dict = {
        "line": "",
        "tags": [],
        "template": "",
        "children": {
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
                                "template": "",
                                "children": {},
                                "line": "route-distinguisher 192.168.0.1:123",
                                "tags": ["rd", "LAN", "192.168.0.1:123"],
                            },
                        },
                    },
                },
            },
        },
    }
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, include_tags=["rd", "LAN"], include_mode="and")
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_tags_exclude(get_config_tree: CTree) -> None:
    filtered_config = dedent(
        """
        ip vpn-instance MGMT
         ipv4-family
        #
        """
    ).strip()

    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, include_tags=["vpn"], exclude_tags=["LAN"])
    assert filtered_root.config == filtered_config


def test_string_tags_and(get_config_tree: CTree) -> None:
    filtered_config = dedent(
        """
        interface gi0/0/0
         ip address 1.1.1.1 255.255.255.252
        #
        """
    ).strip()
    filtered_dict = {
        "line": "",
        "tags": [],
        "template": "",
        "children": {
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
        },
    }
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, string="ip address", include_tags=["gi0/0/0", "ip"], include_mode="and")
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_string_tags_or(get_config_tree: CTree) -> None:
    filtered_config = dedent(
        """
        interface gi0/0/0
         ip address 1.1.1.1 255.255.255.252
        #
        interface gi0/0/1
         ip address 1.1.1.1 255.255.255.252
        #
        """
    ).strip()
    filtered_dict = {
        "line": "",
        "tags": [],
        "template": "",
        "children": {
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
                "template": "",
                "children": {
                    "ip address 1.1.1.1 255.255.255.252": {
                        "template": "",
                        "children": {},
                        "line": "ip address 1.1.1.1 255.255.255.252",
                        "tags": ["ip", "interface-2", "gi0/0/1"],
                    },
                },
                "line": "interface gi0/0/1",
                "tags": ["interface", "gi0/0/1"],
            },
        },
    }
    root = get_config_tree
    filtered_root = CTreeSearcher.search(
        root, string=r"(?:\d+\.){3}\d+", include_tags=["gi0/0/0", "gi0/0/1"], include_mode="or"
    )
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_null_tags(get_config_tree: CTree) -> None:
    filtered_config = ""
    filtered_dict = {"line": "", "tags": [], "template": "", "children": {}}
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, include_tags=["gi0/0/0", "gi0/0/1"], include_mode="and")
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_null_string(get_config_tree: CTree) -> None:
    filtered_config = ""
    filtered_dict = {"line": "", "tags": [], "template": "", "children": {}}
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, string="unknown")
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_null_empty(get_config_tree: CTree) -> None:
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root)
    assert filtered_root == ctree_factory(vendor=root.vendor)


def test_children(get_config_tree: CTree) -> None:
    without_children_config = dedent(
        """
        ip vpn-instance MGMT
         ipv4-family
        #
        ip vpn-instance LAN
         ipv4-family
        #
        """
    ).strip()
    with_children_config = dedent(
        """
        ip vpn-instance MGMT
         ipv4-family
          route-distinguisher 192.168.0.1:123
        #
        ip vpn-instance LAN
         ipv4-family
          route-distinguisher 192.168.0.1:123
          vpn-target 123:123 export-extcommunity evpn
          vpn-target 123:123 import-extcommunity evpn
        #
        """
    ).strip()
    root = get_config_tree
    without_children = CTreeSearcher.search(ct=root, string="ipv4-family", include_children=False)
    with_children = CTreeSearcher.search(ct=root, string="ipv4-family", include_children=True)
    assert without_children.config == without_children_config
    assert with_children.config == with_children_config


def test_exclude_children_by_tag() -> None:
    config_str = dedent(
        """
        no platform punt-keepalive disable-kernel-core
        no service pad
        !
        router bgp 64512
         neighbor CSC peer-group
         neighbor CSC remote-as 12345
         !
         address-family ipv4
          neighbor CSC send-community both
          neighbor CSC route-map rm_CSC_PE_in in
         exit-address-family
        !
        """
    )
    bgp_all_str = dedent(
        """
        router bgp 64512
         neighbor CSC peer-group
         neighbor CSC remote-as 12345
         address-family ipv4
          neighbor CSC send-community both
          neighbor CSC route-map rm_CSC_PE_in in
        !
        """
    ).strip()
    bgp_rm_attach_str = dedent(
        """
        router bgp 64512
         address-family ipv4
          neighbor CSC route-map rm_CSC_PE_in in
        !
        """
    ).strip()
    bgp_no_rm_str = dedent(
        """
        router bgp 64512
         neighbor CSC peer-group
         neighbor CSC remote-as 12345
         address-family ipv4
          neighbor CSC send-community both
        !
        """
    ).strip()
    bgp_no_rm_exclude_str = dedent(
        """
        no platform punt-keepalive disable-kernel-core
        !
        no service pad
        !
        router bgp 64512
         neighbor CSC peer-group
         neighbor CSC remote-as 12345
         address-family ipv4
          neighbor CSC send-community both
        !
        """
    ).strip()
    tagging_rules: list[dict[str, str | list[str]]] = [
        {"regex": r"^router bgp .* neighbor (\S+) route-map (\S+) (?:in|out)", "tags": ["rm-attach"]},
        {"regex": r"^router bgp \d+$", "tags": ["bgp"]},
    ]
    parser = CTreeParser(Vendor.CISCO, TaggingRulesDict({Vendor.CISCO: tagging_rules}))
    root = parser.parse(config_str)

    # c "neighbor CSC route-map rm_CSC_PE_in in", встречаем bgp секцию и помещаем
    # этот узел в результат со всеми его потомками, без проверки на их теги
    bgp_all = CTreeSearcher.search(
        root,
        include_tags=["bgp"],
        include_children=True,
    )
    assert bgp_all.config == bgp_all_str

    # без "neighbor CSC route-map rm_CSC_PE_in in", а тут уже проверяем теги каждого
    # потомка, поэтому строка не попадает в результат
    bgp_no_rm = CTreeSearcher.search(
        root,
        include_tags=["bgp"],
    )
    assert bgp_no_rm.config == bgp_no_rm_str

    bgp_rm_attach = CTreeSearcher.search(
        root,
        include_tags=["rm-attach"],
    )
    assert bgp_rm_attach.config == bgp_rm_attach_str

    bgp_no_rm_exclude = CTreeSearcher.search(
        root,
        exclude_tags=["rm-attach"],
    )
    assert bgp_no_rm_exclude.config == bgp_no_rm_exclude_str


def test_wrong_tag_include_mode() -> None:
    config = dedent(
        """
        interface Ethernet1
         load-interval 30
        !
        """
    )

    tagging_rules: list[dict[str, str | list[str]]] = [
        {"regex": r"^interface (\S+)", "tags": ["eth"]},
    ]
    parser = CTreeParser(Vendor.CISCO, TaggingRulesDict({Vendor.CISCO: tagging_rules}))
    root = parser.parse(config)

    with pytest.raises(ValueError) as exc:
        _ = CTreeSearcher.search(
            root,
            include_tags=["Ethernet1"],
            include_mode="wrong",  # type: ignore[arg-type]
        )
    assert str(exc.value) == "incorrect include_mode, 'or' or 'and' are allowed."


@pytest.mark.parametrize(
    "include_tags, include_mode, exclude_tags, expected",
    [
        ([r"Ethernet123"], "or", [], ""),
        ([r"re:Ethernet\d+", "eth", "fake"], "and", [], ""),
        (
            ["re:Ethernet1"],
            "or",
            [],
            dedent(
                """
                interface Ethernet1
                 load-interval 30
                !
                """
            ).strip(),
        ),
        (
            [r"re:Ethernet(?:1|3)"],
            "or",
            [],
            dedent(
                """
                interface Ethernet1
                 load-interval 30
                !
                interface Ethernet3
                 load-interval 30
                !
                """
            ).strip(),
        ),
        (
            [r"re:(?:Gigabit)?Ethernet1"],
            "or",
            [],
            dedent(
                """
                interface Ethernet1
                 load-interval 30
                !
                interface GigabitEthernet1
                 load-interval 30
                !
                """
            ).strip(),
        ),
        (
            [r"re:(?:Gigabit)?Ethernet1", "Ethernet2"],
            "or",
            [],
            dedent(
                """
                interface Ethernet1
                 load-interval 30
                !
                interface Ethernet2
                 load-interval 30
                !
                interface GigabitEthernet1
                 load-interval 30
                !
                """
            ).strip(),
        ),
        (
            [r"re:Ethernet\d+", "eth"],
            "and",
            [],
            dedent(
                """
                interface Ethernet1
                 load-interval 30
                !
                interface Ethernet2
                 load-interval 30
                !
                interface Ethernet3
                 load-interval 30
                !
                """
            ).strip(),
        ),
        (
            [r"re:Ethernet\d+", "e2"],
            "and",
            [],
            dedent(
                """
                interface Ethernet2
                 load-interval 30
                !
                """
            ).strip(),
        ),
        (
            [r"re:Ethernet\d+", "eth"],
            "and",
            ["e2"],
            dedent(
                """
                interface Ethernet1
                 load-interval 30
                !
                interface Ethernet3
                 load-interval 30
                !
                """
            ).strip(),
        ),
        (
            [r"re:(?:Gigabit)?Ethernet\d+"],
            "or",
            [r"re:e(?:2|3)"],
            dedent(
                """
                interface Ethernet1
                 load-interval 30
                !
                interface GigabitEthernet1
                 load-interval 30
                !
                """
            ).strip(),
        ),
        (
            [r"re:Ethernet\d+", r"re:e(?:1|2|3)"],
            "and",
            [r"re:e(?:3|4)"],
            dedent(
                """
                interface Ethernet2
                 load-interval 30
                !
                """
            ).strip(),
        ),
    ],
)
def test_regex_include_tag(
    include_tags: list[str],
    include_mode: Literal["or", "and"],
    exclude_tags: list[str],
    expected: str,
) -> None:
    config = dedent(
        """
        interface Ethernet1
         load-interval 30
        !
        interface Ethernet2
         load-interval 30
        !
        interface Ethernet3
         load-interval 30
        !
        interface GigabitEthernet1
         load-interval 30
        !
        interface GigabitEthernet2
         load-interval 30
        !
        interface GigabitEthernet3
         load-interval 30
        !
        """
    )

    tagging_rules: list[dict[str, str | list[str]]] = [
        {"regex": r"^interface ((?:Gigabit)?Ethernet2)", "tags": ["eth", "e2"]},
        {"regex": r"^interface ((?:Gigabit)?Ethernet3)", "tags": ["eth", "e3"]},
        {"regex": r"^interface (\S+)", "tags": ["eth"]},
    ]
    parser = CTreeParser(Vendor.CISCO, TaggingRulesDict({Vendor.CISCO: tagging_rules}))
    root = parser.parse(config)

    filtered = CTreeSearcher.search(
        ct=root,
        include_tags=include_tags,
        include_mode=include_mode,
        exclude_tags=exclude_tags,
    )
    assert filtered.config == expected


def test_regex_with_no_regex_include() -> None:
    config = dedent(
        """
        interface Ethernet1+2
         load-interval 30
        !
        interface Ethernet112
         load-interval 30
        !
        interface Ethernet1112
         load-interval 30
        !
        """
    )
    expected = dedent(
        """
        interface Ethernet1+2
         load-interval 30
        !
        interface Ethernet1112
         load-interval 30
        !
        """
    ).strip()
    tagging_rules: list[dict[str, str | list[str]]] = [
        {
            "regex": r"^interface (\S+)",
            "tags": ["eth"],
        },
    ]
    parser = CTreeParser(Vendor.CISCO, TaggingRulesDict({Vendor.CISCO: tagging_rules}))
    root = parser.parse(config)
    filtered = CTreeSearcher.search(ct=root, include_tags=["Ethernet1+2", r"re:Ethernet1{3}2"])
    assert filtered.config == expected


def test_regex_with_no_regex_exclude() -> None:
    config = dedent(
        """
        interface Ethernet1+2
         load-interval 30
        !
        interface Ethernet112
         load-interval 30
        !
        interface Ethernet1112
         load-interval 30
        !
        """
    )
    expected = dedent(
        """
        interface Ethernet112
         load-interval 30
        !
        """
    ).strip()
    tagging_rules: list[dict[str, str | list[str]]] = [
        {
            "regex": r"^interface (\S+)",
            "tags": ["eth"],
        },
    ]
    parser = CTreeParser(Vendor.CISCO, TaggingRulesDict({Vendor.CISCO: tagging_rules}))
    root = parser.parse(config)
    filtered = CTreeSearcher.search(ct=root, exclude_tags=["Ethernet1+2", r"re:Ethernet1{3}2"])
    assert filtered.config == expected
