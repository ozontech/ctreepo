from textwrap import dedent

import pytest

from ctreepo import CTree, CTreeParser, CTreeSearcher, CTreeSerializer, Vendor
from ctreepo.parser import TaggingRulesDict
from ctreepo.vendors import CiscoCT


@pytest.fixture(scope="function")
def root() -> CTree:
    config_str = dedent(
        """
        Building configuration...

        Current configuration : 2688 bytes
        !
        ! Last configuration change at now by admin
        !
        version 17.3
        service timestamps debug datetime msec
        service timestamps log datetime msec
        ! Call-home is enabled by Smart-Licensing.
        service call-home
        platform qfp utilization monitor load 80
        platform punt-keepalive disable-kernel-core
        platform console serial
        !
        boot-start-marker
        boot-end-marker
        !
        !
        vrf definition MGMT
         !
         address-family ipv4
         exit-address-family
        !
        !
        aaa new-model
        !
        !
        aaa authentication login default local
        aaa authorization exec default local
        !
        spanning-tree extend system-id
        !
        username admin privilege 15 secret 9 admin-secret-key
        !
        crypto pki certificate chain TP_NAME_1
         certificate ca 1234ABCD
          30820378 30820260 A0030201 02021017 16449497 577B9F48 1ED1DB4F 4D01F430
          0D06092A 864886F7 0D010105 0500303C 310B3009 06035504 06130252 55311230
          A2D15C91 CF6CAF3F 58C08402 2992CC76 E7A29BF3 5BC7936D 1849E655
                quit
        crypto pki certificate chain TP_NAME_2
         certificate ABCD1234
          308207AE 30820696 A0030201 02020A7E 0C784200 02007AB8 A3300D06 092A8648
          86F70D01 01050500 3040310B 30090603 55040613 02525531 12301006 0355040A
          33EFC68A EEA18FCF BA0859C2 CEDAB304 0872
                quit
         certificate ca 4321DCBA
          30820674 3082055C A0030201 02020A61 4FBE3E00 01000000 08300D06 092A8648
          86F70D01 01050500 303C310B 30090603 55040613 02525531 12301006 0355040A
          17FAA91A 09D647FD 1754D09D 8F185225 EB45ACE8 9987F7DF
                quit
        !
        interface Loopback0
         description -= RID =-
         ip address 2.3.4.5 255.255.255.255
        !
        interface GigabitEthernet1
         vrf forwarding mgmt
         ip address 1.2.3.4 255.255.255.0
         negotiation auto
         no mop enabled
         no mop sysid
         service-policy output PL_NAME_1
        !
        class-map match-all CM_NAME_1
          match  dscp af41
        class-map match-all CM_NAME_2
          match  dscp ef
        !
        policy-map PL_NAME_1
          class CM_NAME_1
            bandwidth percent 10
          class CM_NAME_2
            priority percent 20
          class CM_NAME_3
            priority percent 30
          class CM_NAME_4
            bandwidth percent 40
          class CM_NAME_5
            bandwidth percent 50
            fair-queue
          class CM_NAME_6
            bandwidth percent 60
        !
        ip ssh rsa keypair-name SSH
        ip ssh version 2
        !
        ip access-list extended ACL_NAME_1
         10 permit icmp any any
         20 permit tcp any range 22 telnet host 1.2.3.4
        !
        route-map RM_DENY deny 10
        !
        route-map RM_NAME_1 permit 10
         match ip address ACL_NAME_1
         set ip next-hop 4.4.4.4
        !
        banner motd ^C
        =============================================
                    multiline motd banner
        =============================================

        $(hostname).$(domain), line $(line)
        ^C
        !
        banner exec $$
        =============================================
                   multiline exec banner
        =============================================

        $(hostname).$(domain), line $(line)
        $$
        !
        banner login # $(hostname).$(domain) at line $(line) #
        !
        line con 0
         stopbits 1
        line vty 0 4
         transport input all
        line vty 5 15
         transport input all
        !
        !
        end
        """
    )
    tagging_rules_dict = {
        Vendor.CISCO: [
            {"regex": r"^interface (Loopback\d+)$", "tags": ["interface", "loopback"]},
            {"regex": r"^interface (\S+)$", "tags": ["interface"]},
            {"regex": r"^interface (\S+) / service-policy (?:input|output) (\S+)$", "tags": ["interface", "qos"]},
            {"regex": r"^interface (\S+) / vrf forwarding (\S+)$", "tags": ["interface", "vrf"]},
            {"regex": r"^class-map \S+ (\S+)$", "tags": ["qos"]},
            {"regex": r"^policy-map (\S+)$", "tags": ["qos"]},
            {"regex": r"^ip ssh .*", "tags": ["mgmt", "ssh"]},
            {"regex": r"^route-map (\S+) (?:permit|deny) \d+$", "tags": ["route-map"]},
            {"regex": r"^ip access-list extended (\S+)$", "tags": ["access-list"]},
            {"regex": r"^banner (motd|login|exec) .*", "tags": ["banner"]},
            {"regex": r"^username (\S+) privilege .*", "tags": ["mgmt", "user"]},
            {"regex": r"^aaa .*", "tags": ["mgmt", "aaa"]},
            {"regex": r"^vrf definition (\S+)$", "tags": ["vrf"]},
        ],
    }
    loader = TaggingRulesDict(tagging_rules_dict)  # type: ignore[arg-type]
    parser = CTreeParser(
        vendor=Vendor.CISCO,
        tagging_rules=loader,
    )
    root: CTree = parser.parse(config_str)
    return root


def test_config(root: CTree) -> None:
    config = dedent(
        """
        service timestamps debug datetime msec
        !
        service timestamps log datetime msec
        !
        service call-home
        !
        platform qfp utilization monitor load 80
        !
        platform punt-keepalive disable-kernel-core
        !
        platform console serial
        !
        boot-start-marker
        !
        boot-end-marker
        !
        vrf definition MGMT
         address-family ipv4
        !
        aaa new-model
        !
        aaa authentication login default local
        !
        aaa authorization exec default local
        !
        spanning-tree extend system-id
        !
        username admin privilege 15 secret 9 admin-secret-key
        !
        crypto pki certificate chain TP_NAME_1
         certificate ca 1234ABCD
          30820378 30820260 A0030201 02021017 16449497 577B9F48 1ED1DB4F 4D01F430
          0D06092A 864886F7 0D010105 0500303C 310B3009 06035504 06130252 55311230
          A2D15C91 CF6CAF3F 58C08402 2992CC76 E7A29BF3 5BC7936D 1849E655
                quit
        !
        crypto pki certificate chain TP_NAME_2
         certificate ABCD1234
          308207AE 30820696 A0030201 02020A7E 0C784200 02007AB8 A3300D06 092A8648
          86F70D01 01050500 3040310B 30090603 55040613 02525531 12301006 0355040A
          33EFC68A EEA18FCF BA0859C2 CEDAB304 0872
                quit
         certificate ca 4321DCBA
          30820674 3082055C A0030201 02020A61 4FBE3E00 01000000 08300D06 092A8648
          86F70D01 01050500 303C310B 30090603 55040613 02525531 12301006 0355040A
          17FAA91A 09D647FD 1754D09D 8F185225 EB45ACE8 9987F7DF
                quit
        !
        interface Loopback0
         description -= RID =-
         ip address 2.3.4.5 255.255.255.255
        !
        interface GigabitEthernet1
         vrf forwarding mgmt
         ip address 1.2.3.4 255.255.255.0
         negotiation auto
         no mop enabled
         no mop sysid
         service-policy output PL_NAME_1
        !
        class-map match-all CM_NAME_1
         match  dscp af41
        !
        class-map match-all CM_NAME_2
         match  dscp ef
        !
        policy-map PL_NAME_1
         class CM_NAME_1
          bandwidth percent 10
         class CM_NAME_2
          priority percent 20
         class CM_NAME_3
          priority percent 30
         class CM_NAME_4
          bandwidth percent 40
         class CM_NAME_5
          bandwidth percent 50
          fair-queue
         class CM_NAME_6
          bandwidth percent 60
        !
        ip ssh rsa keypair-name SSH
        !
        ip ssh version 2
        !
        ip access-list extended ACL_NAME_1
         10 permit icmp any any
         20 permit tcp any range 22 telnet host 1.2.3.4
        !
        route-map RM_DENY deny 10
        !
        route-map RM_NAME_1 permit 10
         match ip address ACL_NAME_1
         set ip next-hop 4.4.4.4
        !
        banner motd ^C
        =============================================
                    multiline motd banner
        =============================================

        $(hostname).$(domain), line $(line)
        ^C
        !
        banner exec $$
        =============================================
                   multiline exec banner
        =============================================

        $(hostname).$(domain), line $(line)
        $$
        !
        banner login # $(hostname).$(domain) at line $(line) #
        !
        line con 0
         stopbits 1
        !
        line vty 0 4
         transport input all
        !
        line vty 5 15
         transport input all
        !
        """
    ).strip()
    assert root.config == config


def test_patch(root: CTree) -> None:
    patch = dedent(
        """
        service timestamps debug datetime msec
        service timestamps log datetime msec
        service call-home
        platform qfp utilization monitor load 80
        platform punt-keepalive disable-kernel-core
        platform console serial
        boot-start-marker
        boot-end-marker
        vrf definition MGMT
        address-family ipv4
        exit
        aaa new-model
        aaa authentication login default local
        aaa authorization exec default local
        spanning-tree extend system-id
        username admin privilege 15 secret 9 admin-secret-key
        crypto pki certificate chain TP_NAME_1
        certificate ca 1234ABCD
        30820378 30820260 A0030201 02021017 16449497 577B9F48 1ED1DB4F 4D01F430
          0D06092A 864886F7 0D010105 0500303C 310B3009 06035504 06130252 55311230
          A2D15C91 CF6CAF3F 58C08402 2992CC76 E7A29BF3 5BC7936D 1849E655
                quit
        exit
        crypto pki certificate chain TP_NAME_2
        certificate ABCD1234
        308207AE 30820696 A0030201 02020A7E 0C784200 02007AB8 A3300D06 092A8648
          86F70D01 01050500 3040310B 30090603 55040613 02525531 12301006 0355040A
          33EFC68A EEA18FCF BA0859C2 CEDAB304 0872
                quit
        certificate ca 4321DCBA
        30820674 3082055C A0030201 02020A61 4FBE3E00 01000000 08300D06 092A8648
          86F70D01 01050500 303C310B 30090603 55040613 02525531 12301006 0355040A
          17FAA91A 09D647FD 1754D09D 8F185225 EB45ACE8 9987F7DF
                quit
        exit
        interface Loopback0
        description -= RID =-
        ip address 2.3.4.5 255.255.255.255
        exit
        interface GigabitEthernet1
        vrf forwarding mgmt
        ip address 1.2.3.4 255.255.255.0
        negotiation auto
        no mop enabled
        no mop sysid
        service-policy output PL_NAME_1
        exit
        class-map match-all CM_NAME_1
        match  dscp af41
        exit
        class-map match-all CM_NAME_2
        match  dscp ef
        exit
        policy-map PL_NAME_1
        class CM_NAME_1
        bandwidth percent 10
        exit
        class CM_NAME_2
        priority percent 20
        exit
        class CM_NAME_3
        priority percent 30
        exit
        class CM_NAME_4
        bandwidth percent 40
        exit
        class CM_NAME_5
        bandwidth percent 50
        fair-queue
        exit
        class CM_NAME_6
        bandwidth percent 60
        exit
        exit
        ip ssh rsa keypair-name SSH
        ip ssh version 2
        ip access-list extended ACL_NAME_1
        10 permit icmp any any
        20 permit tcp any range 22 telnet host 1.2.3.4
        exit
        route-map RM_DENY deny 10
        exit
        route-map RM_NAME_1 permit 10
        match ip address ACL_NAME_1
        set ip next-hop 4.4.4.4
        exit
        banner motd ^C
        =============================================
                    multiline motd banner
        =============================================

        $(hostname).$(domain), line $(line)
        ^C
        banner exec $$
        =============================================
                   multiline exec banner
        =============================================

        $(hostname).$(domain), line $(line)
        $$
        banner login # $(hostname).$(domain) at line $(line) #
        line con 0
        stopbits 1
        exit
        line vty 0 4
        transport input all
        exit
        line vty 5 15
        transport input all
        exit
        """
    ).strip()
    assert root.patch == patch


def test_to_dict(root: CTree) -> None:
    dst = {
        "line": "",
        "tags": [],
        "template": "",
        "children": {
            "service timestamps debug datetime msec": {
                "line": "service timestamps debug datetime msec",
                "tags": [],
                "template": "",
                "children": {},
            },
            "service timestamps log datetime msec": {
                "line": "service timestamps log datetime msec",
                "tags": [],
                "template": "",
                "children": {},
            },
            "service call-home": {"line": "service call-home", "tags": [], "template": "", "children": {}},
            "platform qfp utilization monitor load 80": {
                "line": "platform qfp utilization monitor load 80",
                "tags": [],
                "template": "",
                "children": {},
            },
            "platform punt-keepalive disable-kernel-core": {
                "line": "platform punt-keepalive disable-kernel-core",
                "tags": [],
                "template": "",
                "children": {},
            },
            "platform console serial": {"line": "platform console serial", "tags": [], "template": "", "children": {}},
            "boot-start-marker": {"line": "boot-start-marker", "tags": [], "template": "", "children": {}},
            "boot-end-marker": {"line": "boot-end-marker", "tags": [], "template": "", "children": {}},
            "vrf definition MGMT": {
                "line": "vrf definition MGMT",
                "tags": ["vrf", "MGMT"],
                "template": "",
                "children": {
                    "address-family ipv4": {
                        "line": "address-family ipv4",
                        "tags": ["vrf", "MGMT"],
                        "template": "",
                        "children": {},
                    }
                },
            },
            "aaa new-model": {"line": "aaa new-model", "tags": ["mgmt", "aaa"], "template": "", "children": {}},
            "aaa authentication login default local": {
                "line": "aaa authentication login default local",
                "tags": ["mgmt", "aaa"],
                "template": "",
                "children": {},
            },
            "aaa authorization exec default local": {
                "line": "aaa authorization exec default local",
                "tags": ["mgmt", "aaa"],
                "template": "",
                "children": {},
            },
            "spanning-tree extend system-id": {
                "line": "spanning-tree extend system-id",
                "tags": [],
                "template": "",
                "children": {},
            },
            "username admin privilege 15 secret 9 admin-secret-key": {
                "line": ("username admin privilege 15 secret 9 " "admin-secret-key"),
                "tags": ["mgmt", "user", "admin"],
                "template": "",
                "children": {},
            },
            "crypto pki certificate chain TP_NAME_1": {
                "line": "crypto pki certificate chain TP_NAME_1",
                "tags": [],
                "template": "",
                "children": {
                    "certificate ca 1234ABCD": {
                        "line": "certificate ca 1234ABCD",
                        "tags": [],
                        "template": "",
                        "children": {
                            (
                                "30820378 30820260 A0030201 02021017 16449497 577B9F48 1ED1DB4F 4D01F430\n  "
                                "0D06092A 864886F7 0D010105 0500303C 310B3009 06035504 06130252 55311230\n  "
                                "A2D15C91 CF6CAF3F 58C08402 2992CC76 E7A29BF3 5BC7936D 1849E655\n        quit"
                            ): {
                                "line": (
                                    "30820378 30820260 A0030201 02021017 16449497 577B9F48 1ED1DB4F 4D01F430\n  "
                                    "0D06092A 864886F7 0D010105 0500303C 310B3009 06035504 06130252 55311230\n  "
                                    "A2D15C91 CF6CAF3F 58C08402 2992CC76 E7A29BF3 5BC7936D 1849E655\n        quit"
                                ),
                                "tags": [],
                                "template": "",
                                "children": {},
                            }
                        },
                    }
                },
            },
            "crypto pki certificate chain TP_NAME_2": {
                "line": "crypto pki certificate chain TP_NAME_2",
                "tags": [],
                "template": "",
                "children": {
                    "certificate ABCD1234": {
                        "line": "certificate ABCD1234",
                        "tags": [],
                        "template": "",
                        "children": {
                            (
                                "308207AE 30820696 A0030201 02020A7E 0C784200 02007AB8 A3300D06 092A8648\n  "
                                "86F70D01 01050500 3040310B 30090603 55040613 02525531 12301006 0355040A\n  "
                                "33EFC68A EEA18FCF BA0859C2 CEDAB304 0872\n        quit"
                            ): {
                                "line": (
                                    "308207AE 30820696 A0030201 02020A7E 0C784200 02007AB8 A3300D06 092A8648\n  "
                                    "86F70D01 01050500 3040310B 30090603 55040613 02525531 12301006 0355040A\n  "
                                    "33EFC68A EEA18FCF BA0859C2 CEDAB304 0872\n        quit"
                                ),
                                "tags": [],
                                "template": "",
                                "children": {},
                            }
                        },
                    },
                    "certificate ca 4321DCBA": {
                        "line": "certificate ca 4321DCBA",
                        "tags": [],
                        "template": "",
                        "children": {
                            (
                                "30820674 3082055C A0030201 02020A61 4FBE3E00 01000000 08300D06 092A8648\n"
                                "  86F70D01 01050500 303C310B 30090603 55040613 02525531 12301006 0355040A\n"
                                "  17FAA91A 09D647FD 1754D09D 8F185225 EB45ACE8 9987F7DF\n        quit"
                            ): {
                                "line": (
                                    "30820674 3082055C A0030201 02020A61 4FBE3E00 01000000 08300D06 092A8648\n"
                                    "  86F70D01 01050500 303C310B 30090603 55040613 02525531 12301006 0355040A\n"
                                    "  17FAA91A 09D647FD 1754D09D 8F185225 EB45ACE8 9987F7DF\n        quit"
                                ),
                                "tags": [],
                                "template": "",
                                "children": {},
                            }
                        },
                    },
                },
            },
            "interface Loopback0": {
                "line": "interface Loopback0",
                "tags": ["interface", "loopback", "Loopback0"],
                "template": "",
                "children": {
                    "description -= RID =-": {
                        "line": "description -= RID =-",
                        "tags": ["interface", "loopback", "Loopback0"],
                        "template": "",
                        "children": {},
                    },
                    "ip address 2.3.4.5 255.255.255.255": {
                        "line": "ip address 2.3.4.5 255.255.255.255",
                        "tags": ["interface", "loopback", "Loopback0"],
                        "template": "",
                        "children": {},
                    },
                },
            },
            "interface GigabitEthernet1": {
                "line": "interface GigabitEthernet1",
                "tags": ["interface", "GigabitEthernet1"],
                "template": "",
                "children": {
                    "vrf forwarding mgmt": {
                        "line": "vrf forwarding mgmt",
                        "tags": ["interface", "vrf", "GigabitEthernet1", "mgmt"],
                        "template": "",
                        "children": {},
                    },
                    "ip address 1.2.3.4 255.255.255.0": {
                        "line": "ip address 1.2.3.4 255.255.255.0",
                        "tags": ["interface", "GigabitEthernet1"],
                        "template": "",
                        "children": {},
                    },
                    "negotiation auto": {
                        "line": "negotiation auto",
                        "tags": ["interface", "GigabitEthernet1"],
                        "template": "",
                        "children": {},
                    },
                    "no mop enabled": {
                        "line": "no mop enabled",
                        "tags": ["interface", "GigabitEthernet1"],
                        "template": "",
                        "children": {},
                    },
                    "no mop sysid": {
                        "line": "no mop sysid",
                        "tags": ["interface", "GigabitEthernet1"],
                        "template": "",
                        "children": {},
                    },
                    "service-policy output PL_NAME_1": {
                        "line": "service-policy output PL_NAME_1",
                        "tags": ["interface", "qos", "GigabitEthernet1", "PL_NAME_1"],
                        "template": "",
                        "children": {},
                    },
                },
            },
            "class-map match-all CM_NAME_1": {
                "line": "class-map match-all CM_NAME_1",
                "tags": ["qos", "CM_NAME_1"],
                "template": "",
                "children": {
                    "match  dscp af41": {
                        "line": "match  dscp af41",
                        "tags": ["qos", "CM_NAME_1"],
                        "template": "",
                        "children": {},
                    }
                },
            },
            "class-map match-all CM_NAME_2": {
                "line": "class-map match-all CM_NAME_2",
                "tags": ["qos", "CM_NAME_2"],
                "template": "",
                "children": {
                    "match  dscp ef": {
                        "line": "match  dscp ef",
                        "tags": ["qos", "CM_NAME_2"],
                        "template": "",
                        "children": {},
                    }
                },
            },
            "policy-map PL_NAME_1": {
                "line": "policy-map PL_NAME_1",
                "tags": ["qos", "PL_NAME_1"],
                "template": "",
                "children": {
                    "class CM_NAME_1": {
                        "line": "class CM_NAME_1",
                        "tags": ["qos", "PL_NAME_1"],
                        "template": "",
                        "children": {
                            "bandwidth percent 10": {
                                "line": "bandwidth percent 10",
                                "tags": ["qos", "PL_NAME_1"],
                                "template": "",
                                "children": {},
                            }
                        },
                    },
                    "class CM_NAME_2": {
                        "line": "class CM_NAME_2",
                        "tags": ["qos", "PL_NAME_1"],
                        "template": "",
                        "children": {
                            "priority percent 20": {
                                "line": "priority percent 20",
                                "tags": ["qos", "PL_NAME_1"],
                                "template": "",
                                "children": {},
                            }
                        },
                    },
                    "class CM_NAME_3": {
                        "line": "class CM_NAME_3",
                        "tags": ["qos", "PL_NAME_1"],
                        "template": "",
                        "children": {
                            "priority percent 30": {
                                "line": "priority percent 30",
                                "tags": ["qos", "PL_NAME_1"],
                                "template": "",
                                "children": {},
                            }
                        },
                    },
                    "class CM_NAME_4": {
                        "line": "class CM_NAME_4",
                        "tags": ["qos", "PL_NAME_1"],
                        "template": "",
                        "children": {
                            "bandwidth percent 40": {
                                "line": "bandwidth percent 40",
                                "tags": ["qos", "PL_NAME_1"],
                                "template": "",
                                "children": {},
                            }
                        },
                    },
                    "class CM_NAME_5": {
                        "line": "class CM_NAME_5",
                        "tags": ["qos", "PL_NAME_1"],
                        "template": "",
                        "children": {
                            "bandwidth percent 50": {
                                "line": "bandwidth percent 50",
                                "tags": ["qos", "PL_NAME_1"],
                                "template": "",
                                "children": {},
                            },
                            "fair-queue": {
                                "line": "fair-queue",
                                "tags": ["qos", "PL_NAME_1"],
                                "template": "",
                                "children": {},
                            },
                        },
                    },
                    "class CM_NAME_6": {
                        "line": "class CM_NAME_6",
                        "tags": ["qos", "PL_NAME_1"],
                        "template": "",
                        "children": {
                            "bandwidth percent 60": {
                                "line": "bandwidth percent 60",
                                "tags": ["qos", "PL_NAME_1"],
                                "template": "",
                                "children": {},
                            }
                        },
                    },
                },
            },
            "ip ssh rsa keypair-name SSH": {
                "line": "ip ssh rsa keypair-name SSH",
                "tags": ["mgmt", "ssh"],
                "template": "",
                "children": {},
            },
            "ip ssh version 2": {"line": "ip ssh version 2", "tags": ["mgmt", "ssh"], "template": "", "children": {}},
            "ip access-list extended ACL_NAME_1": {
                "line": "ip access-list extended ACL_NAME_1",
                "tags": ["access-list", "ACL_NAME_1"],
                "template": "",
                "children": {
                    "10 permit icmp any any": {
                        "line": "10 permit icmp any any",
                        "tags": ["access-list", "ACL_NAME_1"],
                        "template": "",
                        "children": {},
                    },
                    "20 permit tcp any range 22 telnet host 1.2.3.4": {
                        "line": "20 permit tcp any range 22 telnet host 1.2.3.4",
                        "tags": ["access-list", "ACL_NAME_1"],
                        "template": "",
                        "children": {},
                    },
                },
            },
            "route-map RM_DENY deny 10": {
                "line": "route-map RM_DENY deny 10",
                "tags": ["route-map", "RM_DENY"],
                "template": "",
                "children": {},
            },
            "route-map RM_NAME_1 permit 10": {
                "line": "route-map RM_NAME_1 permit 10",
                "tags": ["route-map", "RM_NAME_1"],
                "template": "",
                "children": {
                    "match ip address ACL_NAME_1": {
                        "line": "match ip address ACL_NAME_1",
                        "tags": ["route-map", "RM_NAME_1"],
                        "template": "",
                        "children": {},
                    },
                    "set ip next-hop 4.4.4.4": {
                        "line": "set ip next-hop 4.4.4.4",
                        "tags": ["route-map", "RM_NAME_1"],
                        "template": "",
                        "children": {},
                    },
                },
            },
            (
                "banner motd ^C\n=============================================\n            multiline motd banner\n"
                "=============================================\n\n$(hostname).$(domain), line $(line)\n^C"
            ): {
                "line": (
                    "banner motd ^C\n=============================================\n            multiline motd banner\n"
                    "=============================================\n\n$(hostname).$(domain), line $(line)\n^C"
                ),
                "tags": ["banner", "motd"],
                "template": "",
                "children": {},
            },
            (
                "banner exec $$\n=============================================\n           multiline exec banner\n"
                "=============================================\n\n$(hostname).$(domain), line $(line)\n$$"
            ): {
                "line": (
                    "banner exec $$\n=============================================\n           multiline exec banner\n"
                    "=============================================\n\n$(hostname).$(domain), line $(line)\n$$"
                ),
                "tags": ["banner", "exec"],
                "template": "",
                "children": {},
            },
            "banner login # $(hostname).$(domain) at line $(line) #": {
                "line": "banner login # $(hostname).$(domain) at line $(line) #",
                "tags": ["banner", "login"],
                "template": "",
                "children": {},
            },
            "line con 0": {
                "line": "line con 0",
                "tags": [],
                "template": "",
                "children": {"stopbits 1": {"line": "stopbits 1", "tags": [], "template": "", "children": {}}},
            },
            "line vty 0 4": {
                "line": "line vty 0 4",
                "tags": [],
                "template": "",
                "children": {
                    "transport input all": {"line": "transport input all", "tags": [], "template": "", "children": {}}
                },
            },
            "line vty 5 15": {
                "line": "line vty 5 15",
                "tags": [],
                "template": "",
                "children": {
                    "transport input all": {"line": "transport input all", "tags": [], "template": "", "children": {}}
                },
            },
        },
    }
    serialized = CTreeSerializer.to_dict(root)
    assert dst == serialized


def test_from_dict(root: CTree) -> None:
    src = {
        "line": "",
        "tags": [],
        "template": "",
        "children": {
            "service timestamps debug datetime msec": {
                "line": "service timestamps debug datetime msec",
                "tags": [],
                "template": "",
                "children": {},
            },
            "service timestamps log datetime msec": {
                "line": "service timestamps log datetime msec",
                "tags": [],
                "template": "",
                "children": {},
            },
            "service call-home": {"line": "service call-home", "tags": [], "template": "", "children": {}},
            "platform qfp utilization monitor load 80": {
                "line": "platform qfp utilization monitor load 80",
                "tags": [],
                "template": "",
                "children": {},
            },
            "platform punt-keepalive disable-kernel-core": {
                "line": "platform punt-keepalive disable-kernel-core",
                "tags": [],
                "template": "",
                "children": {},
            },
            "platform console serial": {"line": "platform console serial", "tags": [], "template": "", "children": {}},
            "boot-start-marker": {"line": "boot-start-marker", "tags": [], "template": "", "children": {}},
            "boot-end-marker": {"line": "boot-end-marker", "tags": [], "template": "", "children": {}},
            "vrf definition MGMT": {
                "line": "vrf definition MGMT",
                "tags": ["vrf", "MGMT"],
                "template": "",
                "children": {
                    "address-family ipv4": {
                        "line": "address-family ipv4",
                        "tags": ["vrf", "MGMT"],
                        "template": "",
                        "children": {},
                    }
                },
            },
            "aaa new-model": {"line": "aaa new-model", "tags": ["mgmt", "aaa"], "template": "", "children": {}},
            "aaa authentication login default local": {
                "line": "aaa authentication login default local",
                "tags": ["mgmt", "aaa"],
                "template": "",
                "children": {},
            },
            "aaa authorization exec default local": {
                "line": "aaa authorization exec default local",
                "tags": ["mgmt", "aaa"],
                "template": "",
                "children": {},
            },
            "spanning-tree extend system-id": {
                "line": "spanning-tree extend system-id",
                "tags": [],
                "template": "",
                "children": {},
            },
            "username admin privilege 15 secret 9 admin-secret-key": {
                "line": ("username admin privilege 15 secret 9 " "admin-secret-key"),
                "tags": ["mgmt", "user", "admin"],
                "template": "",
                "children": {},
            },
            "crypto pki certificate chain TP_NAME_1": {
                "line": "crypto pki certificate chain TP_NAME_1",
                "tags": [],
                "template": "",
                "children": {
                    "certificate ca 1234ABCD": {
                        "line": "certificate ca 1234ABCD",
                        "tags": [],
                        "template": "",
                        "children": {
                            (
                                "30820378 30820260 A0030201 02021017 16449497 577B9F48 1ED1DB4F 4D01F430\n  "
                                "0D06092A 864886F7 0D010105 0500303C 310B3009 06035504 06130252 55311230\n  "
                                "A2D15C91 CF6CAF3F 58C08402 2992CC76 E7A29BF3 5BC7936D 1849E655\n        quit"
                            ): {
                                "line": (
                                    "30820378 30820260 A0030201 02021017 16449497 577B9F48 1ED1DB4F 4D01F430\n  "
                                    "0D06092A 864886F7 0D010105 0500303C 310B3009 06035504 06130252 55311230\n  "
                                    "A2D15C91 CF6CAF3F 58C08402 2992CC76 E7A29BF3 5BC7936D 1849E655\n        quit"
                                ),
                                "tags": [],
                                "template": "",
                                "children": {},
                            }
                        },
                    }
                },
            },
            "crypto pki certificate chain TP_NAME_2": {
                "line": "crypto pki certificate chain TP_NAME_2",
                "tags": [],
                "template": "",
                "children": {
                    "certificate ABCD1234": {
                        "line": "certificate ABCD1234",
                        "tags": [],
                        "template": "",
                        "children": {
                            (
                                "308207AE 30820696 A0030201 02020A7E 0C784200 02007AB8 A3300D06 092A8648\n  "
                                "86F70D01 01050500 3040310B 30090603 55040613 02525531 12301006 0355040A\n  "
                                "33EFC68A EEA18FCF BA0859C2 CEDAB304 0872\n        quit"
                            ): {
                                "line": (
                                    "308207AE 30820696 A0030201 02020A7E 0C784200 02007AB8 A3300D06 092A8648\n  "
                                    "86F70D01 01050500 3040310B 30090603 55040613 02525531 12301006 0355040A\n  "
                                    "33EFC68A EEA18FCF BA0859C2 CEDAB304 0872\n        quit"
                                ),
                                "tags": [],
                                "template": "",
                                "children": {},
                            }
                        },
                    },
                    "certificate ca 4321DCBA": {
                        "line": "certificate ca 4321DCBA",
                        "tags": [],
                        "template": "",
                        "children": {
                            (
                                "30820674 3082055C A0030201 02020A61 4FBE3E00 01000000 08300D06 092A8648\n"
                                "  86F70D01 01050500 303C310B 30090603 55040613 02525531 12301006 0355040A\n"
                                "  17FAA91A 09D647FD 1754D09D 8F185225 EB45ACE8 9987F7DF\n        quit"
                            ): {
                                "line": (
                                    "30820674 3082055C A0030201 02020A61 4FBE3E00 01000000 08300D06 092A8648\n"
                                    "  86F70D01 01050500 303C310B 30090603 55040613 02525531 12301006 0355040A\n"
                                    "  17FAA91A 09D647FD 1754D09D 8F185225 EB45ACE8 9987F7DF\n        quit"
                                ),
                                "tags": [],
                                "template": "",
                                "children": {},
                            }
                        },
                    },
                },
            },
            "interface Loopback0": {
                "line": "interface Loopback0",
                "tags": ["interface", "loopback", "Loopback0"],
                "template": "",
                "children": {
                    "description -= RID =-": {
                        "line": "description -= RID =-",
                        "tags": ["interface", "loopback", "Loopback0"],
                        "template": "",
                        "children": {},
                    },
                    "ip address 2.3.4.5 255.255.255.255": {
                        "line": "ip address 2.3.4.5 255.255.255.255",
                        "tags": ["interface", "loopback", "Loopback0"],
                        "template": "",
                        "children": {},
                    },
                },
            },
            "interface GigabitEthernet1": {
                "line": "interface GigabitEthernet1",
                "tags": ["interface", "GigabitEthernet1"],
                "template": "",
                "children": {
                    "vrf forwarding mgmt": {
                        "line": "vrf forwarding mgmt",
                        "tags": ["interface", "vrf", "GigabitEthernet1", "mgmt"],
                        "template": "",
                        "children": {},
                    },
                    "ip address 1.2.3.4 255.255.255.0": {
                        "line": "ip address 1.2.3.4 255.255.255.0",
                        "tags": ["interface", "GigabitEthernet1"],
                        "template": "",
                        "children": {},
                    },
                    "negotiation auto": {
                        "line": "negotiation auto",
                        "tags": ["interface", "GigabitEthernet1"],
                        "template": "",
                        "children": {},
                    },
                    "no mop enabled": {
                        "line": "no mop enabled",
                        "tags": ["interface", "GigabitEthernet1"],
                        "template": "",
                        "children": {},
                    },
                    "no mop sysid": {
                        "line": "no mop sysid",
                        "tags": ["interface", "GigabitEthernet1"],
                        "template": "",
                        "children": {},
                    },
                    "service-policy output PL_NAME_1": {
                        "line": "service-policy output PL_NAME_1",
                        "tags": ["interface", "qos", "GigabitEthernet1", "PL_NAME_1"],
                        "template": "",
                        "children": {},
                    },
                },
            },
            "class-map match-all CM_NAME_1": {
                "line": "class-map match-all CM_NAME_1",
                "tags": ["qos", "CM_NAME_1"],
                "template": "",
                "children": {
                    "match  dscp af41": {
                        "line": "match  dscp af41",
                        "tags": ["qos", "CM_NAME_1"],
                        "template": "",
                        "children": {},
                    }
                },
            },
            "class-map match-all CM_NAME_2": {
                "line": "class-map match-all CM_NAME_2",
                "tags": ["qos", "CM_NAME_2"],
                "template": "",
                "children": {
                    "match  dscp ef": {
                        "line": "match  dscp ef",
                        "tags": ["qos", "CM_NAME_2"],
                        "template": "",
                        "children": {},
                    }
                },
            },
            "policy-map PL_NAME_1": {
                "line": "policy-map PL_NAME_1",
                "tags": ["qos", "PL_NAME_1"],
                "template": "",
                "children": {
                    "class CM_NAME_1": {
                        "line": "class CM_NAME_1",
                        "tags": ["qos", "PL_NAME_1"],
                        "template": "",
                        "children": {
                            "bandwidth percent 10": {
                                "line": "bandwidth percent 10",
                                "tags": ["qos", "PL_NAME_1"],
                                "template": "",
                                "children": {},
                            }
                        },
                    },
                    "class CM_NAME_2": {
                        "line": "class CM_NAME_2",
                        "tags": ["qos", "PL_NAME_1"],
                        "template": "",
                        "children": {
                            "priority percent 20": {
                                "line": "priority percent 20",
                                "tags": ["qos", "PL_NAME_1"],
                                "template": "",
                                "children": {},
                            }
                        },
                    },
                    "class CM_NAME_3": {
                        "line": "class CM_NAME_3",
                        "tags": ["qos", "PL_NAME_1"],
                        "template": "",
                        "children": {
                            "priority percent 30": {
                                "line": "priority percent 30",
                                "tags": ["qos", "PL_NAME_1"],
                                "template": "",
                                "children": {},
                            }
                        },
                    },
                    "class CM_NAME_4": {
                        "line": "class CM_NAME_4",
                        "tags": ["qos", "PL_NAME_1"],
                        "template": "",
                        "children": {
                            "bandwidth percent 40": {
                                "line": "bandwidth percent 40",
                                "tags": ["qos", "PL_NAME_1"],
                                "template": "",
                                "children": {},
                            }
                        },
                    },
                    "class CM_NAME_5": {
                        "line": "class CM_NAME_5",
                        "tags": ["qos", "PL_NAME_1"],
                        "template": "",
                        "children": {
                            "bandwidth percent 50": {
                                "line": "bandwidth percent 50",
                                "tags": ["qos", "PL_NAME_1"],
                                "template": "",
                                "children": {},
                            },
                            "fair-queue": {
                                "line": "fair-queue",
                                "tags": ["qos", "PL_NAME_1"],
                                "template": "",
                                "children": {},
                            },
                        },
                    },
                    "class CM_NAME_6": {
                        "line": "class CM_NAME_6",
                        "tags": ["qos", "PL_NAME_1"],
                        "template": "",
                        "children": {
                            "bandwidth percent 60": {
                                "line": "bandwidth percent 60",
                                "tags": ["qos", "PL_NAME_1"],
                                "template": "",
                                "children": {},
                            }
                        },
                    },
                },
            },
            "ip ssh rsa keypair-name SSH": {
                "line": "ip ssh rsa keypair-name SSH",
                "tags": ["mgmt", "ssh"],
                "template": "",
                "children": {},
            },
            "ip ssh version 2": {"line": "ip ssh version 2", "tags": ["mgmt", "ssh"], "template": "", "children": {}},
            "ip access-list extended ACL_NAME_1": {
                "line": "ip access-list extended ACL_NAME_1",
                "tags": ["access-list", "ACL_NAME_1"],
                "template": "",
                "children": {
                    "10 permit icmp any any": {
                        "line": "10 permit icmp any any",
                        "tags": ["access-list", "ACL_NAME_1"],
                        "template": "",
                        "children": {},
                    },
                    "20 permit tcp any range 22 telnet host 1.2.3.4": {
                        "line": "20 permit tcp any range 22 telnet host 1.2.3.4",
                        "tags": ["access-list", "ACL_NAME_1"],
                        "template": "",
                        "children": {},
                    },
                },
            },
            "route-map RM_DENY deny 10": {
                "line": "route-map RM_DENY deny 10",
                "tags": ["route-map", "RM_DENY"],
                "template": "",
                "children": {},
            },
            "route-map RM_NAME_1 permit 10": {
                "line": "route-map RM_NAME_1 permit 10",
                "tags": ["route-map", "RM_NAME_1"],
                "template": "",
                "children": {
                    "match ip address ACL_NAME_1": {
                        "line": "match ip address ACL_NAME_1",
                        "tags": ["route-map", "RM_NAME_1"],
                        "template": "",
                        "children": {},
                    },
                    "set ip next-hop 4.4.4.4": {
                        "line": "set ip next-hop 4.4.4.4",
                        "tags": ["route-map", "RM_NAME_1"],
                        "template": "",
                        "children": {},
                    },
                },
            },
            (
                "banner motd ^C\n=============================================\n            multiline motd banner\n"
                "=============================================\n\n$(hostname).$(domain), line $(line)\n^C"
            ): {
                "line": (
                    "banner motd ^C\n=============================================\n            multiline motd banner\n"
                    "=============================================\n\n$(hostname).$(domain), line $(line)\n^C"
                ),
                "tags": ["banner", "motd"],
                "template": "",
                "children": {},
            },
            (
                "banner exec $$\n=============================================\n           multiline exec banner\n"
                "=============================================\n\n$(hostname).$(domain), line $(line)\n$$"
            ): {
                "line": (
                    "banner exec $$\n=============================================\n           multiline exec banner\n"
                    "=============================================\n\n$(hostname).$(domain), line $(line)\n$$"
                ),
                "tags": ["banner", "exec"],
                "template": "",
                "children": {},
            },
            "banner login # $(hostname).$(domain) at line $(line) #": {
                "line": "banner login # $(hostname).$(domain) at line $(line) #",
                "tags": ["banner", "login"],
                "template": "",
                "children": {},
            },
            "line con 0": {
                "line": "line con 0",
                "tags": [],
                "template": "",
                "children": {"stopbits 1": {"line": "stopbits 1", "tags": [], "template": "", "children": {}}},
            },
            "line vty 0 4": {
                "line": "line vty 0 4",
                "tags": [],
                "template": "",
                "children": {
                    "transport input all": {"line": "transport input all", "tags": [], "template": "", "children": {}}
                },
            },
            "line vty 5 15": {
                "line": "line vty 5 15",
                "tags": [],
                "template": "",
                "children": {
                    "transport input all": {"line": "transport input all", "tags": [], "template": "", "children": {}}
                },
            },
        },
    }
    deserialized = CTreeSerializer.from_dict(Vendor.CISCO, src)
    assert root == deserialized

    src["children"]["line vty 5 15"]["tags"].append("changed")  # type: ignore[index]
    deserialized = CTreeSerializer.from_dict(Vendor.CISCO, src)
    assert root != deserialized


def test_masked_config(root: CTree) -> None:
    masked_config = dedent(
        f"""
        service timestamps debug datetime msec
        !
        service timestamps log datetime msec
        !
        service call-home
        !
        platform qfp utilization monitor load 80
        !
        platform punt-keepalive disable-kernel-core
        !
        platform console serial
        !
        boot-start-marker
        !
        boot-end-marker
        !
        vrf definition MGMT
         address-family ipv4
        !
        aaa new-model
        !
        aaa authentication login default local
        !
        aaa authorization exec default local
        !
        spanning-tree extend system-id
        !
        username admin privilege 15 secret 9 {CiscoCT.masking_string}
        !
        crypto pki certificate chain TP_NAME_1
         certificate ca 1234ABCD
          30820378 30820260 A0030201 02021017 16449497 577B9F48 1ED1DB4F 4D01F430
          0D06092A 864886F7 0D010105 0500303C 310B3009 06035504 06130252 55311230
          A2D15C91 CF6CAF3F 58C08402 2992CC76 E7A29BF3 5BC7936D 1849E655
                quit
        !
        crypto pki certificate chain TP_NAME_2
         certificate ABCD1234
          308207AE 30820696 A0030201 02020A7E 0C784200 02007AB8 A3300D06 092A8648
          86F70D01 01050500 3040310B 30090603 55040613 02525531 12301006 0355040A
          33EFC68A EEA18FCF BA0859C2 CEDAB304 0872
                quit
         certificate ca 4321DCBA
          30820674 3082055C A0030201 02020A61 4FBE3E00 01000000 08300D06 092A8648
          86F70D01 01050500 303C310B 30090603 55040613 02525531 12301006 0355040A
          17FAA91A 09D647FD 1754D09D 8F185225 EB45ACE8 9987F7DF
                quit
        !
        interface Loopback0
         description -= RID =-
         ip address 2.3.4.5 255.255.255.255
        !
        interface GigabitEthernet1
         vrf forwarding mgmt
         ip address 1.2.3.4 255.255.255.0
         negotiation auto
         no mop enabled
         no mop sysid
         service-policy output PL_NAME_1
        !
        class-map match-all CM_NAME_1
         match  dscp af41
        !
        class-map match-all CM_NAME_2
         match  dscp ef
        !
        policy-map PL_NAME_1
         class CM_NAME_1
          bandwidth percent 10
         class CM_NAME_2
          priority percent 20
         class CM_NAME_3
          priority percent 30
         class CM_NAME_4
          bandwidth percent 40
         class CM_NAME_5
          bandwidth percent 50
          fair-queue
         class CM_NAME_6
          bandwidth percent 60
        !
        ip ssh rsa keypair-name SSH
        !
        ip ssh version 2
        !
        ip access-list extended ACL_NAME_1
         10 permit icmp any any
         20 permit tcp any range 22 telnet host 1.2.3.4
        !
        route-map RM_DENY deny 10
        !
        route-map RM_NAME_1 permit 10
         match ip address ACL_NAME_1
         set ip next-hop 4.4.4.4
        !
        banner motd ^C
        =============================================
                    multiline motd banner
        =============================================

        $(hostname).$(domain), line $(line)
        ^C
        !
        banner exec $$
        =============================================
                   multiline exec banner
        =============================================

        $(hostname).$(domain), line $(line)
        $$
        !
        banner login # $(hostname).$(domain) at line $(line) #
        !
        line con 0
         stopbits 1
        !
        line vty 0 4
         transport input all
        !
        line vty 5 15
         transport input all
        !
        """
    ).strip()
    assert root.masked_config == masked_config


def test_masked_patch(root: CTree) -> None:
    masked_patch = dedent(
        f"""
        service timestamps debug datetime msec
        service timestamps log datetime msec
        service call-home
        platform qfp utilization monitor load 80
        platform punt-keepalive disable-kernel-core
        platform console serial
        boot-start-marker
        boot-end-marker
        vrf definition MGMT
        address-family ipv4
        exit
        aaa new-model
        aaa authentication login default local
        aaa authorization exec default local
        spanning-tree extend system-id
        username admin privilege 15 secret 9 {CiscoCT.masking_string}
        crypto pki certificate chain TP_NAME_1
        certificate ca 1234ABCD
        30820378 30820260 A0030201 02021017 16449497 577B9F48 1ED1DB4F 4D01F430
          0D06092A 864886F7 0D010105 0500303C 310B3009 06035504 06130252 55311230
          A2D15C91 CF6CAF3F 58C08402 2992CC76 E7A29BF3 5BC7936D 1849E655
                quit
        exit
        crypto pki certificate chain TP_NAME_2
        certificate ABCD1234
        308207AE 30820696 A0030201 02020A7E 0C784200 02007AB8 A3300D06 092A8648
          86F70D01 01050500 3040310B 30090603 55040613 02525531 12301006 0355040A
          33EFC68A EEA18FCF BA0859C2 CEDAB304 0872
                quit
        certificate ca 4321DCBA
        30820674 3082055C A0030201 02020A61 4FBE3E00 01000000 08300D06 092A8648
          86F70D01 01050500 303C310B 30090603 55040613 02525531 12301006 0355040A
          17FAA91A 09D647FD 1754D09D 8F185225 EB45ACE8 9987F7DF
                quit
        exit
        interface Loopback0
        description -= RID =-
        ip address 2.3.4.5 255.255.255.255
        exit
        interface GigabitEthernet1
        vrf forwarding mgmt
        ip address 1.2.3.4 255.255.255.0
        negotiation auto
        no mop enabled
        no mop sysid
        service-policy output PL_NAME_1
        exit
        class-map match-all CM_NAME_1
        match  dscp af41
        exit
        class-map match-all CM_NAME_2
        match  dscp ef
        exit
        policy-map PL_NAME_1
        class CM_NAME_1
        bandwidth percent 10
        exit
        class CM_NAME_2
        priority percent 20
        exit
        class CM_NAME_3
        priority percent 30
        exit
        class CM_NAME_4
        bandwidth percent 40
        exit
        class CM_NAME_5
        bandwidth percent 50
        fair-queue
        exit
        class CM_NAME_6
        bandwidth percent 60
        exit
        exit
        ip ssh rsa keypair-name SSH
        ip ssh version 2
        ip access-list extended ACL_NAME_1
        10 permit icmp any any
        20 permit tcp any range 22 telnet host 1.2.3.4
        exit
        route-map RM_DENY deny 10
        exit
        route-map RM_NAME_1 permit 10
        match ip address ACL_NAME_1
        set ip next-hop 4.4.4.4
        exit
        banner motd ^C
        =============================================
                    multiline motd banner
        =============================================

        $(hostname).$(domain), line $(line)
        ^C
        banner exec $$
        =============================================
                   multiline exec banner
        =============================================

        $(hostname).$(domain), line $(line)
        $$
        banner login # $(hostname).$(domain) at line $(line) #
        line con 0
        stopbits 1
        exit
        line vty 0 4
        transport input all
        exit
        line vty 5 15
        transport input all
        exit
        """
    ).strip()
    assert root.masked_patch == masked_patch


def test_searcher(root: CTree) -> None:
    qos_config = dedent(
        """
        interface GigabitEthernet1
         service-policy output PL_NAME_1
        !
        class-map match-all CM_NAME_1
         match  dscp af41
        !
        class-map match-all CM_NAME_2
         match  dscp ef
        !
        policy-map PL_NAME_1
         class CM_NAME_1
          bandwidth percent 10
         class CM_NAME_2
          priority percent 20
         class CM_NAME_3
          priority percent 30
         class CM_NAME_4
          bandwidth percent 40
         class CM_NAME_5
          bandwidth percent 50
          fair-queue
         class CM_NAME_6
          bandwidth percent 60
        !
        """
    ).strip()
    interface_or_qos_config = dedent(
        """
        interface Loopback0
         description -= RID =-
         ip address 2.3.4.5 255.255.255.255
        !
        interface GigabitEthernet1
         vrf forwarding mgmt
         ip address 1.2.3.4 255.255.255.0
         negotiation auto
         no mop enabled
         no mop sysid
         service-policy output PL_NAME_1
        !
        class-map match-all CM_NAME_1
         match  dscp af41
        !
        class-map match-all CM_NAME_2
         match  dscp ef
        !
        policy-map PL_NAME_1
         class CM_NAME_1
          bandwidth percent 10
         class CM_NAME_2
          priority percent 20
         class CM_NAME_3
          priority percent 30
         class CM_NAME_4
          bandwidth percent 40
         class CM_NAME_5
          bandwidth percent 50
          fair-queue
         class CM_NAME_6
          bandwidth percent 60
        !
        """
    ).strip()
    interface_and_qos_config = dedent(
        """
        interface GigabitEthernet1
         service-policy output PL_NAME_1
        !
        """
    ).strip()

    qos = CTreeSearcher.search(root, include_tags=["qos"])
    interface_or_qos = CTreeSearcher.search(root, include_tags=["qos", "interface"])
    interface_and_qos = CTreeSearcher.search(root, include_tags=["qos", "interface"], include_mode="and")
    assert qos.config == qos_config
    assert interface_or_qos.config == interface_or_qos_config
    assert interface_and_qos.config == interface_and_qos_config
