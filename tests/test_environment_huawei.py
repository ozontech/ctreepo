from textwrap import dedent
from typing import cast

import pytest

from ctreepo import CTreeEnv, Platform
from ctreepo.platforms import HuaweiVRP


@pytest.fixture(scope="function")
def env_root() -> tuple[CTreeEnv, HuaweiVRP]:
    config_str = dedent(
        """
        !Software Version abcdef
        !Last configuration was updated at now by me
        #
        telnet server disable
        telnet ipv6 server disable
        undo telnet server-source all-interface
        undo telnet ipv6 server-source all-interface
        #
        diffserv domain default
        #
        ip vpn-instance LAN
         ipv4-family
          route-distinguisher 1.2.3.4:5678
          vpn-target 100:5678 export-extcommunity evpn
          vpn-target 100:5678 import-extcommunity evpn
         vxlan vni 5678
        #
        interface 25GE1/0/1
         port link-type trunk
         undo port trunk allow-pass vlan 1
         stp edged-port enable
         storm suppression broadcast packets 100
         storm suppression multicast packets 100
        #
        interface 25GE1/0/1.123 mode l2
         encapsulation dot1q vid 123
         bridge-domain 123
         statistics enable
        #
        interface 100GE1/0/1
         undo portswitch
         mtu 9216
         description peer-switch
         ip address 4.3.2.1 255.255.255.254
         qos queue 5 shaping percent cir 10
         qos queue 6 shaping percent cir 20
         qos queue 7 shaping percent cir 30
         qos drr 0 to 4
         qos queue 0 drr weight 10
         qos queue 1 drr weight 20
         qos queue 2 drr weight 30
         qos queue 3 drr weight 40
         qos queue 4 drr weight 50
         qos queue 1 ecn
        #
        interface LoopBack0
         description RID
         ip address 1.1.1.1 255.255.255.255
        #
        ip ip-prefix PL_LOOPBACK index 10 permit 1.1.1.0 24 greater-equal 32 less-equal 32
        #
        route-policy RP_LOOPBACKS permit node 10
         if-match ip-prefix PL_LOOPBACK
        #
        route-policy RP_DENY deny node 10
        #
        grpc
         #
         grpc server
          source-ip 1.1.1.1 vpn-instance MGMT
          server enable
        #
        aaa
         authentication-scheme default
         authentication-scheme local
          authentication-mode local
         authorization-scheme default
          authorization-mode local
         authorization-scheme local
         accounting-scheme default
         domain default
         domain local
          authentication-scheme local
         local-user admin@local password irreversible-cipher admin-secret-key
         local-user admin@local privilege level 3
         local-user admin@local service-type terminal ssh
        #
        hwtacacs-server template template-name
         hwtacacs-server authentication 5.5.5.5 vpn-instance MGMT
         hwtacacs-server authentication 6.6.6.6 vpn-instance MGMT secondary
         hwtacacs-server shared-key cipher tacacs-secret-key
        #
        ssl policy policy-name
         diffie-hellman modulus 2048
         certificate load pem-cert cert.cer key-pair rsa key-file cert.key.pem auth-code cipher cert-secret-key
        #
          snmp-agent community read cipher snmp-secret-key mib-view iso-view
        #
        ike peer ike_peer_name
         version 2
         pre-shared-key cipher ike-secret-key
         local-id-type fqdn
        #
        interface Tunnel0/0/0
         mtu 1300
         source LoopBack0
         gre key cipher gre-secret-key
         nhrp authentication cipher nhrp-secret-key
        #
        user-interface con 0
         authentication-mode password
         set authentication password cipher console-secret-key
        #
        wlan ac
         security-profile name default
          security wpa2 psk pass-phrase psk-secret-key aes
        #
        xpl extcommunity-list soo CL_SOO_1
         123:123
         end-list
        #
        xpl community-list CL_NAME_1
         12345:12345
         end-list
        #
        xpl ip-prefix-list PL_DEFAULT
         0.0.0.0 0,
         0.0.0.0 1,
         128.0.0.0 1
        #
        xpl route-filter RF_NAME_1
         if ip route-destination in PL_DEFAULT then
          ! -- default routes --
          refuse
         elseif community matches-any CL_NAME_1 then
          ! -- matching by community --
          approve
         endif
         end-filter
        #
        return
        """,
    )
    tagging_rules: list[dict[str, str | list[str]]] = [
        {"regex": r"^interface (LoopBack\d+)$", "tags": ["interface", "loopback"]},
        {"regex": r"^interface (\S+)$", "tags": ["interface"]},
        {"regex": r"^interface (\S+) mode l2$", "tags": ["interface", "sub"]},
        {"regex": r"^interface (\S+) / qos .*", "tags": ["interface", "qos"]},
        {"regex": r"^diffserv .*", "tags": ["qos"]},
        {"regex": r"^(?:undo )?telnet .*", "tags": ["mgmt", "telnet"]},
        {"regex": r"^aaa$", "tags": ["aaa"]},
        {"regex": r"^aaa / local-user (\S+)@(\S+) .*", "tags": ["mgmt", "user"]},
        {"regex": r"^xpl .*", "tags": ["xpl"]},
        {"regex": r"^user-interface .*", "tags": ["mgmt"]},
        {"regex": r"^route-policy (\S+) (?:permit|deny) node \d+", "tags": ["route-policy"]},
        {"regex": r"^ip ip-prefix (\S+) index \d+ .*", "tags": ["prefix-list"]},
        {"regex": r"^ip vpn-instance (\S+)$", "tags": ["vrf"]},
        {"regex": r"^grpc$", "tags": ["mgmt", "gnmi"]},
    ]

    env = CTreeEnv(
        platform=Platform.HUAWEI_VRP,
        tagging_rules=tagging_rules,
    )
    root = env.parse(config_str)
    root = cast(HuaweiVRP, root)
    return env, root


def test_config(env_root: tuple[CTreeEnv, HuaweiVRP]) -> None:
    config = dedent(
        """
        telnet server disable
        #
        telnet ipv6 server disable
        #
        undo telnet server-source all-interface
        #
        undo telnet ipv6 server-source all-interface
        #
        diffserv domain default
        #
        ip vpn-instance LAN
         ipv4-family
          route-distinguisher 1.2.3.4:5678
          vpn-target 100:5678 export-extcommunity evpn
          vpn-target 100:5678 import-extcommunity evpn
         vxlan vni 5678
        #
        interface 25GE1/0/1
         port link-type trunk
         undo port trunk allow-pass vlan 1
         stp edged-port enable
         storm suppression broadcast packets 100
         storm suppression multicast packets 100
        #
        interface 25GE1/0/1.123 mode l2
         encapsulation dot1q vid 123
         bridge-domain 123
         statistics enable
        #
        interface 100GE1/0/1
         undo portswitch
         mtu 9216
         description peer-switch
         ip address 4.3.2.1 255.255.255.254
         qos queue 5 shaping percent cir 10
         qos queue 6 shaping percent cir 20
         qos queue 7 shaping percent cir 30
         qos drr 0 to 4
         qos queue 0 drr weight 10
         qos queue 1 drr weight 20
         qos queue 2 drr weight 30
         qos queue 3 drr weight 40
         qos queue 4 drr weight 50
         qos queue 1 ecn
        #
        interface LoopBack0
         description RID
         ip address 1.1.1.1 255.255.255.255
        #
        ip ip-prefix PL_LOOPBACK index 10 permit 1.1.1.0 24 greater-equal 32 less-equal 32
        #
        route-policy RP_LOOPBACKS permit node 10
         if-match ip-prefix PL_LOOPBACK
        #
        route-policy RP_DENY deny node 10
        #
        grpc
         grpc server
          source-ip 1.1.1.1 vpn-instance MGMT
          server enable
        #
        aaa
         authentication-scheme default
         authentication-scheme local
          authentication-mode local
         authorization-scheme default
          authorization-mode local
         authorization-scheme local
         accounting-scheme default
         domain default
         domain local
          authentication-scheme local
         local-user admin@local password irreversible-cipher admin-secret-key
         local-user admin@local privilege level 3
         local-user admin@local service-type terminal ssh
        #
        hwtacacs-server template template-name
         hwtacacs-server authentication 5.5.5.5 vpn-instance MGMT
         hwtacacs-server authentication 6.6.6.6 vpn-instance MGMT secondary
         hwtacacs-server shared-key cipher tacacs-secret-key
        #
        ssl policy policy-name
         diffie-hellman modulus 2048
         certificate load pem-cert cert.cer key-pair rsa key-file cert.key.pem auth-code cipher cert-secret-key
        #
        snmp-agent community read cipher snmp-secret-key mib-view iso-view
        #
        ike peer ike_peer_name
         version 2
         pre-shared-key cipher ike-secret-key
         local-id-type fqdn
        #
        interface Tunnel0/0/0
         mtu 1300
         source LoopBack0
         gre key cipher gre-secret-key
         nhrp authentication cipher nhrp-secret-key
        #
        user-interface con 0
         authentication-mode password
         set authentication password cipher console-secret-key
        #
        wlan ac
         security-profile name default
          security wpa2 psk pass-phrase psk-secret-key aes
        #
        xpl extcommunity-list soo CL_SOO_1
         123:123
         end-list
        #
        xpl community-list CL_NAME_1
         12345:12345
         end-list
        #
        xpl ip-prefix-list PL_DEFAULT
         0.0.0.0 0,
         0.0.0.0 1,
         128.0.0.0 1
        #
        xpl route-filter RF_NAME_1
         if ip route-destination in PL_DEFAULT then
          ! -- default routes --
          refuse
         elseif community matches-any CL_NAME_1 then
          ! -- matching by community --
          approve
         endif
         end-filter
        #
        """,
    ).strip()
    assert env_root[1].config == config


def test_patch(env_root: tuple[CTreeEnv, HuaweiVRP]) -> None:
    patch = dedent(
        """
        telnet server disable
        telnet ipv6 server disable
        undo telnet server-source all-interface
        undo telnet ipv6 server-source all-interface
        diffserv domain default
        ip vpn-instance LAN
        ipv4-family
        route-distinguisher 1.2.3.4:5678
        vpn-target 100:5678 export-extcommunity evpn
        vpn-target 100:5678 import-extcommunity evpn
        quit
        vxlan vni 5678
        quit
        interface 25GE1/0/1
        port link-type trunk
        undo port trunk allow-pass vlan 1
        stp edged-port enable
        storm suppression broadcast packets 100
        storm suppression multicast packets 100
        quit
        interface 25GE1/0/1.123 mode l2
        encapsulation dot1q vid 123
        bridge-domain 123
        statistics enable
        quit
        interface 100GE1/0/1
        undo portswitch
        mtu 9216
        description peer-switch
        ip address 4.3.2.1 255.255.255.254
        qos queue 5 shaping percent cir 10
        qos queue 6 shaping percent cir 20
        qos queue 7 shaping percent cir 30
        qos drr 0 to 4
        qos queue 0 drr weight 10
        qos queue 1 drr weight 20
        qos queue 2 drr weight 30
        qos queue 3 drr weight 40
        qos queue 4 drr weight 50
        qos queue 1 ecn
        quit
        interface LoopBack0
        description RID
        ip address 1.1.1.1 255.255.255.255
        quit
        ip ip-prefix PL_LOOPBACK index 10 permit 1.1.1.0 24 greater-equal 32 less-equal 32
        route-policy RP_LOOPBACKS permit node 10
        if-match ip-prefix PL_LOOPBACK
        quit
        route-policy RP_DENY deny node 10
        quit
        grpc
        grpc server
        source-ip 1.1.1.1 vpn-instance MGMT
        server enable
        quit
        quit
        aaa
        authentication-scheme default
        quit
        authentication-scheme local
        authentication-mode local
        quit
        authorization-scheme default
        authorization-mode local
        quit
        authorization-scheme local
        quit
        accounting-scheme default
        quit
        domain default
        quit
        domain local
        authentication-scheme local
        quit
        local-user admin@local password irreversible-cipher admin-secret-key
        local-user admin@local privilege level 3
        local-user admin@local service-type terminal ssh
        quit
        hwtacacs-server template template-name
        hwtacacs-server authentication 5.5.5.5 vpn-instance MGMT
        hwtacacs-server authentication 6.6.6.6 vpn-instance MGMT secondary
        hwtacacs-server shared-key cipher tacacs-secret-key
        quit
        ssl policy policy-name
        diffie-hellman modulus 2048
        certificate load pem-cert cert.cer key-pair rsa key-file cert.key.pem auth-code cipher cert-secret-key
        quit
        snmp-agent community read cipher snmp-secret-key mib-view iso-view
        ike peer ike_peer_name
        version 2
        pre-shared-key cipher ike-secret-key
        local-id-type fqdn
        quit
        interface Tunnel0/0/0
        mtu 1300
        source LoopBack0
        gre key cipher gre-secret-key
        nhrp authentication cipher nhrp-secret-key
        quit
        user-interface con 0
        authentication-mode password
        set authentication password cipher console-secret-key
        quit
        wlan ac
        security-profile name default
        security wpa2 psk pass-phrase psk-secret-key aes
        quit
        quit
        xpl extcommunity-list soo CL_SOO_1
        123:123
        end-list
        xpl community-list CL_NAME_1
        12345:12345
        end-list
        xpl ip-prefix-list PL_DEFAULT
        0.0.0.0 0,
        0.0.0.0 1,
        128.0.0.0 1
        xpl route-filter RF_NAME_1
        if ip route-destination in PL_DEFAULT then
        ! -- default routes --
        refuse
        elseif community matches-any CL_NAME_1 then
        ! -- matching by community --
        approve
        endif
        end-filter
        """,
    ).strip()
    assert env_root[1].patch == patch


def test_to_dict(env_root: tuple[CTreeEnv, HuaweiVRP]) -> None:
    dst = {
        "line": "",
        "tags": [],
        "template": "",
        "undo_line": "",
        "children": {
            "telnet server disable": {
                "line": "telnet server disable",
                "tags": ["mgmt", "telnet"],
                "template": "",
                "undo_line": "",
                "children": {},
            },
            "telnet ipv6 server disable": {
                "line": "telnet ipv6 server disable",
                "tags": ["mgmt", "telnet"],
                "template": "",
                "undo_line": "",
                "children": {},
            },
            "undo telnet server-source all-interface": {
                "line": "undo telnet server-source all-interface",
                "tags": ["mgmt", "telnet"],
                "template": "",
                "undo_line": "",
                "children": {},
            },
            "undo telnet ipv6 server-source all-interface": {
                "line": "undo telnet ipv6 server-source all-interface",
                "tags": ["mgmt", "telnet"],
                "template": "",
                "undo_line": "",
                "children": {},
            },
            "diffserv domain default": {
                "line": "diffserv domain default",
                "tags": ["qos"],
                "template": "",
                "undo_line": "",
                "children": {},
            },
            "ip vpn-instance LAN": {
                "line": "ip vpn-instance LAN",
                "tags": ["vrf", "LAN"],
                "template": "",
                "undo_line": "",
                "children": {
                    "ipv4-family": {
                        "line": "ipv4-family",
                        "tags": ["vrf", "LAN"],
                        "template": "",
                        "undo_line": "",
                        "children": {
                            "route-distinguisher 1.2.3.4:5678": {
                                "line": "route-distinguisher 1.2.3.4:5678",
                                "tags": ["vrf", "LAN"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                            "vpn-target 100:5678 export-extcommunity evpn": {
                                "line": "vpn-target 100:5678 export-extcommunity evpn",
                                "tags": ["vrf", "LAN"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                            "vpn-target 100:5678 import-extcommunity evpn": {
                                "line": "vpn-target 100:5678 import-extcommunity evpn",
                                "tags": ["vrf", "LAN"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                        },
                    },
                    "vxlan vni 5678": {
                        "line": "vxlan vni 5678",
                        "tags": ["vrf", "LAN"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "interface 25GE1/0/1": {
                "line": "interface 25GE1/0/1",
                "tags": ["interface", "25GE1/0/1"],
                "template": "",
                "undo_line": "",
                "children": {
                    "port link-type trunk": {
                        "line": "port link-type trunk",
                        "tags": ["interface", "25GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "undo port trunk allow-pass vlan 1": {
                        "line": "undo port trunk allow-pass vlan 1",
                        "tags": ["interface", "25GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "stp edged-port enable": {
                        "line": "stp edged-port enable",
                        "tags": ["interface", "25GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "storm suppression broadcast packets 100": {
                        "line": "storm suppression broadcast packets 100",
                        "tags": ["interface", "25GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "storm suppression multicast packets 100": {
                        "line": "storm suppression multicast packets 100",
                        "tags": ["interface", "25GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "interface 25GE1/0/1.123 mode l2": {
                "line": "interface 25GE1/0/1.123 mode l2",
                "tags": ["interface", "sub", "25GE1/0/1.123"],
                "template": "",
                "undo_line": "",
                "children": {
                    "encapsulation dot1q vid 123": {
                        "line": "encapsulation dot1q vid 123",
                        "tags": ["interface", "sub", "25GE1/0/1.123"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "bridge-domain 123": {
                        "line": "bridge-domain 123",
                        "tags": ["interface", "sub", "25GE1/0/1.123"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "statistics enable": {
                        "line": "statistics enable",
                        "tags": ["interface", "sub", "25GE1/0/1.123"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "interface 100GE1/0/1": {
                "line": "interface 100GE1/0/1",
                "tags": ["interface", "100GE1/0/1"],
                "template": "",
                "undo_line": "",
                "children": {
                    "undo portswitch": {
                        "line": "undo portswitch",
                        "tags": ["interface", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "mtu 9216": {
                        "line": "mtu 9216",
                        "tags": ["interface", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "description peer-switch": {
                        "line": "description peer-switch",
                        "tags": ["interface", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "ip address 4.3.2.1 255.255.255.254": {
                        "line": "ip address 4.3.2.1 255.255.255.254",
                        "tags": ["interface", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 5 shaping percent cir 10": {
                        "line": "qos queue 5 shaping percent cir 10",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 6 shaping percent cir 20": {
                        "line": "qos queue 6 shaping percent cir 20",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 7 shaping percent cir 30": {
                        "line": "qos queue 7 shaping percent cir 30",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos drr 0 to 4": {
                        "line": "qos drr 0 to 4",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 0 drr weight 10": {
                        "line": "qos queue 0 drr weight 10",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 1 drr weight 20": {
                        "line": "qos queue 1 drr weight 20",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 2 drr weight 30": {
                        "line": "qos queue 2 drr weight 30",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 3 drr weight 40": {
                        "line": "qos queue 3 drr weight 40",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 4 drr weight 50": {
                        "line": "qos queue 4 drr weight 50",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 1 ecn": {
                        "line": "qos queue 1 ecn",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "interface LoopBack0": {
                "line": "interface LoopBack0",
                "tags": ["interface", "loopback", "LoopBack0"],
                "template": "",
                "undo_line": "",
                "children": {
                    "description RID": {
                        "line": "description RID",
                        "tags": ["interface", "loopback", "LoopBack0"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "ip address 1.1.1.1 255.255.255.255": {
                        "line": "ip address 1.1.1.1 255.255.255.255",
                        "tags": ["interface", "loopback", "LoopBack0"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "ip ip-prefix PL_LOOPBACK index 10 permit 1.1.1.0 24 greater-equal 32 less-equal 32": {
                "line": "ip ip-prefix PL_LOOPBACK index 10 permit 1.1.1.0 24 greater-equal 32 less-equal 32",
                "tags": ["prefix-list", "PL_LOOPBACK"],
                "template": "",
                "undo_line": "",
                "children": {},
            },
            "route-policy RP_LOOPBACKS permit node 10": {
                "line": "route-policy RP_LOOPBACKS permit node 10",
                "tags": ["route-policy", "RP_LOOPBACKS"],
                "template": "",
                "undo_line": "",
                "children": {
                    "if-match ip-prefix PL_LOOPBACK": {
                        "line": "if-match ip-prefix PL_LOOPBACK",
                        "tags": ["route-policy", "RP_LOOPBACKS"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "route-policy RP_DENY deny node 10": {
                "line": "route-policy RP_DENY deny node 10",
                "tags": ["route-policy", "RP_DENY"],
                "template": "",
                "undo_line": "",
                "children": {},
            },
            "grpc": {
                "line": "grpc",
                "tags": ["mgmt", "gnmi"],
                "template": "",
                "undo_line": "",
                "children": {
                    "grpc server": {
                        "line": "grpc server",
                        "tags": ["mgmt", "gnmi"],
                        "template": "",
                        "undo_line": "",
                        "children": {
                            "source-ip 1.1.1.1 vpn-instance MGMT": {
                                "line": "source-ip 1.1.1.1 vpn-instance MGMT",
                                "tags": ["mgmt", "gnmi"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                            "server enable": {
                                "line": "server enable",
                                "tags": ["mgmt", "gnmi"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                        },
                    },
                },
            },
            "aaa": {
                "line": "aaa",
                "tags": ["aaa"],
                "template": "",
                "undo_line": "",
                "children": {
                    "authentication-scheme default": {
                        "line": "authentication-scheme default",
                        "tags": ["aaa"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "authentication-scheme local": {
                        "line": "authentication-scheme local",
                        "tags": ["aaa"],
                        "template": "",
                        "undo_line": "",
                        "children": {
                            "authentication-mode local": {
                                "line": "authentication-mode local",
                                "tags": ["aaa"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                        },
                    },
                    "authorization-scheme default": {
                        "line": "authorization-scheme default",
                        "tags": ["aaa"],
                        "template": "",
                        "undo_line": "",
                        "children": {
                            "authorization-mode local": {
                                "line": "authorization-mode local",
                                "tags": ["aaa"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                        },
                    },
                    "authorization-scheme local": {
                        "line": "authorization-scheme local",
                        "tags": ["aaa"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "accounting-scheme default": {
                        "line": "accounting-scheme default",
                        "tags": ["aaa"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "domain default": {
                        "line": "domain default",
                        "tags": ["aaa"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "domain local": {
                        "line": "domain local",
                        "tags": ["aaa"],
                        "template": "",
                        "undo_line": "",
                        "children": {
                            "authentication-scheme local": {
                                "line": "authentication-scheme local",
                                "tags": ["aaa"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                        },
                    },
                    "local-user admin@local password irreversible-cipher admin-secret-key": {
                        "line": "local-user admin@local password irreversible-cipher admin-secret-key",
                        "tags": ["mgmt", "user", "admin", "local"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "local-user admin@local privilege level 3": {
                        "line": "local-user admin@local privilege level 3",
                        "tags": ["mgmt", "user", "admin", "local"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "local-user admin@local service-type terminal ssh": {
                        "line": "local-user admin@local service-type terminal ssh",
                        "tags": ["mgmt", "user", "admin", "local"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "hwtacacs-server template template-name": {
                "line": "hwtacacs-server template template-name",
                "tags": [],
                "template": "",
                "undo_line": "",
                "children": {
                    "hwtacacs-server authentication 5.5.5.5 vpn-instance MGMT": {
                        "line": "hwtacacs-server authentication 5.5.5.5 vpn-instance MGMT",
                        "tags": [],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "hwtacacs-server authentication 6.6.6.6 vpn-instance MGMT secondary": {
                        "line": "hwtacacs-server authentication 6.6.6.6 vpn-instance MGMT secondary",
                        "tags": [],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "hwtacacs-server shared-key cipher tacacs-secret-key": {
                        "line": "hwtacacs-server shared-key cipher tacacs-secret-key",
                        "tags": [],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "ssl policy policy-name": {
                "line": "ssl policy policy-name",
                "tags": [],
                "template": "",
                "undo_line": "",
                "children": {
                    "diffie-hellman modulus 2048": {
                        "line": "diffie-hellman modulus 2048",
                        "tags": [],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    (
                        "certificate load pem-cert cert.cer key-pair rsa key-file "
                        "cert.key.pem auth-code cipher cert-secret-key"
                    ): {
                        "line": (
                            "certificate load pem-cert cert.cer key-pair rsa key-file "
                            "cert.key.pem auth-code cipher cert-secret-key"
                        ),
                        "tags": [],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "snmp-agent community read cipher snmp-secret-key mib-view iso-view": {
                "line": "snmp-agent community read cipher snmp-secret-key mib-view iso-view",
                "tags": [],
                "template": "",
                "undo_line": "",
                "children": {},
            },
            "ike peer ike_peer_name": {
                "line": "ike peer ike_peer_name",
                "tags": [],
                "template": "",
                "undo_line": "",
                "children": {
                    "version 2": {"line": "version 2", "tags": [], "template": "", "undo_line": "", "children": {}},
                    "pre-shared-key cipher ike-secret-key": {
                        "line": "pre-shared-key cipher ike-secret-key",
                        "tags": [],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "local-id-type fqdn": {
                        "line": "local-id-type fqdn",
                        "tags": [],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "interface Tunnel0/0/0": {
                "line": "interface Tunnel0/0/0",
                "tags": ["interface", "Tunnel0/0/0"],
                "template": "",
                "undo_line": "",
                "children": {
                    "mtu 1300": {
                        "line": "mtu 1300",
                        "tags": ["interface", "Tunnel0/0/0"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "source LoopBack0": {
                        "line": "source LoopBack0",
                        "tags": ["interface", "Tunnel0/0/0"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "gre key cipher gre-secret-key": {
                        "line": "gre key cipher gre-secret-key",
                        "tags": ["interface", "Tunnel0/0/0"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "nhrp authentication cipher nhrp-secret-key": {
                        "line": "nhrp authentication cipher nhrp-secret-key",
                        "tags": ["interface", "Tunnel0/0/0"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "user-interface con 0": {
                "line": "user-interface con 0",
                "tags": ["mgmt"],
                "template": "",
                "undo_line": "",
                "children": {
                    "authentication-mode password": {
                        "line": "authentication-mode password",
                        "tags": ["mgmt"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "set authentication password cipher console-secret-key": {
                        "line": "set authentication password cipher console-secret-key",
                        "tags": ["mgmt"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "wlan ac": {
                "line": "wlan ac",
                "tags": [],
                "template": "",
                "undo_line": "",
                "children": {
                    "security-profile name default": {
                        "line": "security-profile name default",
                        "tags": [],
                        "template": "",
                        "undo_line": "",
                        "children": {
                            "security wpa2 psk pass-phrase psk-secret-key aes": {
                                "line": "security wpa2 psk pass-phrase psk-secret-key aes",
                                "tags": [],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                        },
                    },
                },
            },
            "xpl extcommunity-list soo CL_SOO_1": {
                "line": "xpl extcommunity-list soo CL_SOO_1",
                "tags": ["xpl"],
                "template": "",
                "undo_line": "",
                "children": {
                    "123:123": {"line": "123:123", "tags": ["xpl"], "template": "", "undo_line": "", "children": {}},
                    "end-list": {"line": "end-list", "tags": ["xpl"], "template": "", "undo_line": "", "children": {}},
                },
            },
            "xpl community-list CL_NAME_1": {
                "line": "xpl community-list CL_NAME_1",
                "tags": ["xpl"],
                "template": "",
                "undo_line": "",
                "children": {
                    "12345:12345": {
                        "line": "12345:12345",
                        "tags": ["xpl"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "end-list": {"line": "end-list", "tags": ["xpl"], "template": "", "undo_line": "", "children": {}},
                },
            },
            "xpl ip-prefix-list PL_DEFAULT": {
                "line": "xpl ip-prefix-list PL_DEFAULT",
                "tags": ["xpl"],
                "template": "",
                "undo_line": "",
                "children": {
                    "0.0.0.0 0,": {
                        "line": "0.0.0.0 0,",
                        "tags": ["xpl"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "0.0.0.0 1,": {
                        "line": "0.0.0.0 1,",
                        "tags": ["xpl"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "128.0.0.0 1": {
                        "line": "128.0.0.0 1",
                        "tags": ["xpl"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "xpl route-filter RF_NAME_1": {
                "line": "xpl route-filter RF_NAME_1",
                "tags": ["xpl"],
                "template": "",
                "undo_line": "",
                "children": {
                    "if ip route-destination in PL_DEFAULT then": {
                        "line": "if ip route-destination in PL_DEFAULT then",
                        "tags": ["xpl"],
                        "template": "",
                        "undo_line": "",
                        "children": {
                            "! -- default routes --": {
                                "line": "! -- default routes --",
                                "tags": ["xpl"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                            "refuse": {
                                "line": "refuse",
                                "tags": ["xpl"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                        },
                    },
                    "elseif community matches-any CL_NAME_1 then": {
                        "line": "elseif community matches-any CL_NAME_1 then",
                        "tags": ["xpl"],
                        "template": "",
                        "undo_line": "",
                        "children": {
                            "! -- matching by community --": {
                                "line": "! -- matching by community --",
                                "tags": ["xpl"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                            "approve": {
                                "line": "approve",
                                "tags": ["xpl"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                        },
                    },
                    "endif": {"line": "endif", "tags": ["xpl"], "template": "", "undo_line": "", "children": {}},
                    "end-filter": {
                        "line": "end-filter",
                        "tags": ["xpl"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
        },
    }
    serialized = env_root[0].to_dict(env_root[1])
    assert dst == serialized


def test_from_dict(env_root: tuple[CTreeEnv, HuaweiVRP]) -> None:
    src = {
        "line": "",
        "tags": [],
        "template": "",
        "undo_line": "",
        "children": {
            "telnet server disable": {
                "line": "telnet server disable",
                "tags": ["mgmt", "telnet"],
                "template": "",
                "undo_line": "",
                "children": {},
            },
            "telnet ipv6 server disable": {
                "line": "telnet ipv6 server disable",
                "tags": ["mgmt", "telnet"],
                "template": "",
                "undo_line": "",
                "children": {},
            },
            "undo telnet server-source all-interface": {
                "line": "undo telnet server-source all-interface",
                "tags": ["mgmt", "telnet"],
                "template": "",
                "undo_line": "",
                "children": {},
            },
            "undo telnet ipv6 server-source all-interface": {
                "line": "undo telnet ipv6 server-source all-interface",
                "tags": ["mgmt", "telnet"],
                "template": "",
                "undo_line": "",
                "children": {},
            },
            "diffserv domain default": {
                "line": "diffserv domain default",
                "tags": ["qos"],
                "template": "",
                "undo_line": "",
                "children": {},
            },
            "ip vpn-instance LAN": {
                "line": "ip vpn-instance LAN",
                "tags": ["vrf", "LAN"],
                "template": "",
                "undo_line": "",
                "children": {
                    "ipv4-family": {
                        "line": "ipv4-family",
                        "tags": ["vrf", "LAN"],
                        "template": "",
                        "undo_line": "",
                        "children": {
                            "route-distinguisher 1.2.3.4:5678": {
                                "line": "route-distinguisher 1.2.3.4:5678",
                                "tags": ["vrf", "LAN"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                            "vpn-target 100:5678 export-extcommunity evpn": {
                                "line": "vpn-target 100:5678 export-extcommunity evpn",
                                "tags": ["vrf", "LAN"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                            "vpn-target 100:5678 import-extcommunity evpn": {
                                "line": "vpn-target 100:5678 import-extcommunity evpn",
                                "tags": ["vrf", "LAN"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                        },
                    },
                    "vxlan vni 5678": {
                        "line": "vxlan vni 5678",
                        "tags": ["vrf", "LAN"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "interface 25GE1/0/1": {
                "line": "interface 25GE1/0/1",
                "tags": ["interface", "25GE1/0/1"],
                "template": "",
                "undo_line": "",
                "children": {
                    "port link-type trunk": {
                        "line": "port link-type trunk",
                        "tags": ["interface", "25GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "undo port trunk allow-pass vlan 1": {
                        "line": "undo port trunk allow-pass vlan 1",
                        "tags": ["interface", "25GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "stp edged-port enable": {
                        "line": "stp edged-port enable",
                        "tags": ["interface", "25GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "storm suppression broadcast packets 100": {
                        "line": "storm suppression broadcast packets 100",
                        "tags": ["interface", "25GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "storm suppression multicast packets 100": {
                        "line": "storm suppression multicast packets 100",
                        "tags": ["interface", "25GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "interface 25GE1/0/1.123 mode l2": {
                "line": "interface 25GE1/0/1.123 mode l2",
                "tags": ["interface", "sub", "25GE1/0/1.123"],
                "template": "",
                "undo_line": "",
                "children": {
                    "encapsulation dot1q vid 123": {
                        "line": "encapsulation dot1q vid 123",
                        "tags": ["interface", "sub", "25GE1/0/1.123"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "bridge-domain 123": {
                        "line": "bridge-domain 123",
                        "tags": ["interface", "sub", "25GE1/0/1.123"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "statistics enable": {
                        "line": "statistics enable",
                        "tags": ["interface", "sub", "25GE1/0/1.123"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "interface 100GE1/0/1": {
                "line": "interface 100GE1/0/1",
                "tags": ["interface", "100GE1/0/1"],
                "template": "",
                "undo_line": "",
                "children": {
                    "undo portswitch": {
                        "line": "undo portswitch",
                        "tags": ["interface", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "mtu 9216": {
                        "line": "mtu 9216",
                        "tags": ["interface", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "description peer-switch": {
                        "line": "description peer-switch",
                        "tags": ["interface", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "ip address 4.3.2.1 255.255.255.254": {
                        "line": "ip address 4.3.2.1 255.255.255.254",
                        "tags": ["interface", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 5 shaping percent cir 10": {
                        "line": "qos queue 5 shaping percent cir 10",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 6 shaping percent cir 20": {
                        "line": "qos queue 6 shaping percent cir 20",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 7 shaping percent cir 30": {
                        "line": "qos queue 7 shaping percent cir 30",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos drr 0 to 4": {
                        "line": "qos drr 0 to 4",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 0 drr weight 10": {
                        "line": "qos queue 0 drr weight 10",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 1 drr weight 20": {
                        "line": "qos queue 1 drr weight 20",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 2 drr weight 30": {
                        "line": "qos queue 2 drr weight 30",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 3 drr weight 40": {
                        "line": "qos queue 3 drr weight 40",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 4 drr weight 50": {
                        "line": "qos queue 4 drr weight 50",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "qos queue 1 ecn": {
                        "line": "qos queue 1 ecn",
                        "tags": ["interface", "qos", "100GE1/0/1"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "interface LoopBack0": {
                "line": "interface LoopBack0",
                "tags": ["interface", "loopback", "LoopBack0"],
                "template": "",
                "undo_line": "",
                "children": {
                    "description RID": {
                        "line": "description RID",
                        "tags": ["interface", "loopback", "LoopBack0"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "ip address 1.1.1.1 255.255.255.255": {
                        "line": "ip address 1.1.1.1 255.255.255.255",
                        "tags": ["interface", "loopback", "LoopBack0"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "ip ip-prefix PL_LOOPBACK index 10 permit 1.1.1.0 24 greater-equal 32 less-equal 32": {
                "line": "ip ip-prefix PL_LOOPBACK index 10 permit 1.1.1.0 24 greater-equal 32 less-equal 32",
                "tags": ["prefix-list", "PL_LOOPBACK"],
                "template": "",
                "undo_line": "",
                "children": {},
            },
            "route-policy RP_LOOPBACKS permit node 10": {
                "line": "route-policy RP_LOOPBACKS permit node 10",
                "tags": ["route-policy", "RP_LOOPBACKS"],
                "template": "",
                "undo_line": "",
                "children": {
                    "if-match ip-prefix PL_LOOPBACK": {
                        "line": "if-match ip-prefix PL_LOOPBACK",
                        "tags": ["route-policy", "RP_LOOPBACKS"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "route-policy RP_DENY deny node 10": {
                "line": "route-policy RP_DENY deny node 10",
                "tags": ["route-policy", "RP_DENY"],
                "template": "",
                "undo_line": "",
                "children": {},
            },
            "grpc": {
                "line": "grpc",
                "tags": ["mgmt", "gnmi"],
                "template": "",
                "undo_line": "",
                "children": {
                    "grpc server": {
                        "line": "grpc server",
                        "tags": ["mgmt", "gnmi"],
                        "template": "",
                        "undo_line": "",
                        "children": {
                            "source-ip 1.1.1.1 vpn-instance MGMT": {
                                "line": "source-ip 1.1.1.1 vpn-instance MGMT",
                                "tags": ["mgmt", "gnmi"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                            "server enable": {
                                "line": "server enable",
                                "tags": ["mgmt", "gnmi"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                        },
                    },
                },
            },
            "aaa": {
                "line": "aaa",
                "tags": ["aaa"],
                "template": "",
                "undo_line": "",
                "children": {
                    "authentication-scheme default": {
                        "line": "authentication-scheme default",
                        "tags": ["aaa"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "authentication-scheme local": {
                        "line": "authentication-scheme local",
                        "tags": ["aaa"],
                        "template": "",
                        "undo_line": "",
                        "children": {
                            "authentication-mode local": {
                                "line": "authentication-mode local",
                                "tags": ["aaa"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                        },
                    },
                    "authorization-scheme default": {
                        "line": "authorization-scheme default",
                        "tags": ["aaa"],
                        "template": "",
                        "undo_line": "",
                        "children": {
                            "authorization-mode local": {
                                "line": "authorization-mode local",
                                "tags": ["aaa"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                        },
                    },
                    "authorization-scheme local": {
                        "line": "authorization-scheme local",
                        "tags": ["aaa"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "accounting-scheme default": {
                        "line": "accounting-scheme default",
                        "tags": ["aaa"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "domain default": {
                        "line": "domain default",
                        "tags": ["aaa"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "domain local": {
                        "line": "domain local",
                        "tags": ["aaa"],
                        "template": "",
                        "undo_line": "",
                        "children": {
                            "authentication-scheme local": {
                                "line": "authentication-scheme local",
                                "tags": ["aaa"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                        },
                    },
                    "local-user admin@local password irreversible-cipher admin-secret-key": {
                        "line": "local-user admin@local password irreversible-cipher admin-secret-key",
                        "tags": ["mgmt", "user", "admin", "local"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "local-user admin@local privilege level 3": {
                        "line": "local-user admin@local privilege level 3",
                        "tags": ["mgmt", "user", "admin", "local"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "local-user admin@local service-type terminal ssh": {
                        "line": "local-user admin@local service-type terminal ssh",
                        "tags": ["mgmt", "user", "admin", "local"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "hwtacacs-server template template-name": {
                "line": "hwtacacs-server template template-name",
                "tags": [],
                "template": "",
                "undo_line": "",
                "children": {
                    "hwtacacs-server authentication 5.5.5.5 vpn-instance MGMT": {
                        "line": "hwtacacs-server authentication 5.5.5.5 vpn-instance MGMT",
                        "tags": [],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "hwtacacs-server authentication 6.6.6.6 vpn-instance MGMT secondary": {
                        "line": "hwtacacs-server authentication 6.6.6.6 vpn-instance MGMT secondary",
                        "tags": [],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "hwtacacs-server shared-key cipher tacacs-secret-key": {
                        "line": "hwtacacs-server shared-key cipher tacacs-secret-key",
                        "tags": [],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "ssl policy policy-name": {
                "line": "ssl policy policy-name",
                "tags": [],
                "template": "",
                "undo_line": "",
                "children": {
                    "diffie-hellman modulus 2048": {
                        "line": "diffie-hellman modulus 2048",
                        "tags": [],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    (
                        "certificate load pem-cert cert.cer key-pair rsa key-file "
                        "cert.key.pem auth-code cipher cert-secret-key"
                    ): {
                        "line": (
                            "certificate load pem-cert cert.cer key-pair rsa key-file "
                            "cert.key.pem auth-code cipher cert-secret-key"
                        ),
                        "tags": [],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "snmp-agent community read cipher snmp-secret-key mib-view iso-view": {
                "line": "snmp-agent community read cipher snmp-secret-key mib-view iso-view",
                "tags": [],
                "template": "",
                "undo_line": "",
                "children": {},
            },
            "ike peer ike_peer_name": {
                "line": "ike peer ike_peer_name",
                "tags": [],
                "template": "",
                "undo_line": "",
                "children": {
                    "version 2": {"line": "version 2", "tags": [], "template": "", "undo_line": "", "children": {}},
                    "pre-shared-key cipher ike-secret-key": {
                        "line": "pre-shared-key cipher ike-secret-key",
                        "tags": [],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "local-id-type fqdn": {
                        "line": "local-id-type fqdn",
                        "tags": [],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "interface Tunnel0/0/0": {
                "line": "interface Tunnel0/0/0",
                "tags": ["interface", "Tunnel0/0/0"],
                "template": "",
                "undo_line": "",
                "children": {
                    "mtu 1300": {
                        "line": "mtu 1300",
                        "tags": ["interface", "Tunnel0/0/0"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "source LoopBack0": {
                        "line": "source LoopBack0",
                        "tags": ["interface", "Tunnel0/0/0"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "gre key cipher gre-secret-key": {
                        "line": "gre key cipher gre-secret-key",
                        "tags": ["interface", "Tunnel0/0/0"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "nhrp authentication cipher nhrp-secret-key": {
                        "line": "nhrp authentication cipher nhrp-secret-key",
                        "tags": ["interface", "Tunnel0/0/0"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "user-interface con 0": {
                "line": "user-interface con 0",
                "tags": ["mgmt"],
                "template": "",
                "undo_line": "",
                "children": {
                    "authentication-mode password": {
                        "line": "authentication-mode password",
                        "tags": ["mgmt"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "set authentication password cipher console-secret-key": {
                        "line": "set authentication password cipher console-secret-key",
                        "tags": ["mgmt"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "wlan ac": {
                "line": "wlan ac",
                "tags": [],
                "template": "",
                "undo_line": "",
                "children": {
                    "security-profile name default": {
                        "line": "security-profile name default",
                        "tags": [],
                        "template": "",
                        "undo_line": "",
                        "children": {
                            "security wpa2 psk pass-phrase psk-secret-key aes": {
                                "line": "security wpa2 psk pass-phrase psk-secret-key aes",
                                "tags": [],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                        },
                    },
                },
            },
            "xpl extcommunity-list soo CL_SOO_1": {
                "line": "xpl extcommunity-list soo CL_SOO_1",
                "tags": ["xpl"],
                "template": "",
                "undo_line": "",
                "children": {
                    "123:123": {"line": "123:123", "tags": ["xpl"], "template": "", "undo_line": "", "children": {}},
                    "end-list": {"line": "end-list", "tags": ["xpl"], "template": "", "undo_line": "", "children": {}},
                },
            },
            "xpl community-list CL_NAME_1": {
                "line": "xpl community-list CL_NAME_1",
                "tags": ["xpl"],
                "template": "",
                "undo_line": "",
                "children": {
                    "12345:12345": {
                        "line": "12345:12345",
                        "tags": ["xpl"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "end-list": {"line": "end-list", "tags": ["xpl"], "template": "", "undo_line": "", "children": {}},
                },
            },
            "xpl ip-prefix-list PL_DEFAULT": {
                "line": "xpl ip-prefix-list PL_DEFAULT",
                "tags": ["xpl"],
                "template": "",
                "undo_line": "",
                "children": {
                    "0.0.0.0 0,": {
                        "line": "0.0.0.0 0,",
                        "tags": ["xpl"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "0.0.0.0 1,": {
                        "line": "0.0.0.0 1,",
                        "tags": ["xpl"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                    "128.0.0.0 1": {
                        "line": "128.0.0.0 1",
                        "tags": ["xpl"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
            "xpl route-filter RF_NAME_1": {
                "line": "xpl route-filter RF_NAME_1",
                "tags": ["xpl"],
                "template": "",
                "undo_line": "",
                "children": {
                    "if ip route-destination in PL_DEFAULT then": {
                        "line": "if ip route-destination in PL_DEFAULT then",
                        "tags": ["xpl"],
                        "template": "",
                        "undo_line": "",
                        "children": {
                            "! -- default routes --": {
                                "line": "! -- default routes --",
                                "tags": ["xpl"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                            "refuse": {
                                "line": "refuse",
                                "tags": ["xpl"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                        },
                    },
                    "elseif community matches-any CL_NAME_1 then": {
                        "line": "elseif community matches-any CL_NAME_1 then",
                        "tags": ["xpl"],
                        "template": "",
                        "undo_line": "",
                        "children": {
                            "! -- matching by community --": {
                                "line": "! -- matching by community --",
                                "tags": ["xpl"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                            "approve": {
                                "line": "approve",
                                "tags": ["xpl"],
                                "template": "",
                                "undo_line": "",
                                "children": {},
                            },
                        },
                    },
                    "endif": {"line": "endif", "tags": ["xpl"], "template": "", "undo_line": "", "children": {}},
                    "end-filter": {
                        "line": "end-filter",
                        "tags": ["xpl"],
                        "template": "",
                        "undo_line": "",
                        "children": {},
                    },
                },
            },
        },
    }
    env, ct = env_root
    deserialized = env.from_dict(src)
    assert ct == deserialized

    src["children"]["telnet server disable"]["tags"].append("changed")  # type: ignore[index]
    deserialized = env.from_dict(src)
    assert ct != deserialized


def test_masked_config(env_root: tuple[CTreeEnv, HuaweiVRP]) -> None:
    masked_config = dedent(
        f"""
        telnet server disable
        #
        telnet ipv6 server disable
        #
        undo telnet server-source all-interface
        #
        undo telnet ipv6 server-source all-interface
        #
        diffserv domain default
        #
        ip vpn-instance LAN
         ipv4-family
          route-distinguisher 1.2.3.4:5678
          vpn-target 100:5678 export-extcommunity evpn
          vpn-target 100:5678 import-extcommunity evpn
         vxlan vni 5678
        #
        interface 25GE1/0/1
         port link-type trunk
         undo port trunk allow-pass vlan 1
         stp edged-port enable
         storm suppression broadcast packets 100
         storm suppression multicast packets 100
        #
        interface 25GE1/0/1.123 mode l2
         encapsulation dot1q vid 123
         bridge-domain 123
         statistics enable
        #
        interface 100GE1/0/1
         undo portswitch
         mtu 9216
         description peer-switch
         ip address 4.3.2.1 255.255.255.254
         qos queue 5 shaping percent cir 10
         qos queue 6 shaping percent cir 20
         qos queue 7 shaping percent cir 30
         qos drr 0 to 4
         qos queue 0 drr weight 10
         qos queue 1 drr weight 20
         qos queue 2 drr weight 30
         qos queue 3 drr weight 40
         qos queue 4 drr weight 50
         qos queue 1 ecn
        #
        interface LoopBack0
         description RID
         ip address 1.1.1.1 255.255.255.255
        #
        ip ip-prefix PL_LOOPBACK index 10 permit 1.1.1.0 24 greater-equal 32 less-equal 32
        #
        route-policy RP_LOOPBACKS permit node 10
         if-match ip-prefix PL_LOOPBACK
        #
        route-policy RP_DENY deny node 10
        #
        grpc
         grpc server
          source-ip 1.1.1.1 vpn-instance MGMT
          server enable
        #
        aaa
         authentication-scheme default
         authentication-scheme local
          authentication-mode local
         authorization-scheme default
          authorization-mode local
         authorization-scheme local
         accounting-scheme default
         domain default
         domain local
          authentication-scheme local
         local-user admin@local password irreversible-cipher {HuaweiVRP.masking_string}
         local-user admin@local privilege level 3
         local-user admin@local service-type terminal ssh
        #
        hwtacacs-server template template-name
         hwtacacs-server authentication 5.5.5.5 vpn-instance MGMT
         hwtacacs-server authentication 6.6.6.6 vpn-instance MGMT secondary
         hwtacacs-server shared-key cipher {HuaweiVRP.masking_string}
        #
        ssl policy policy-name
         diffie-hellman modulus 2048
         certificate load pem-cert cert.cer key-pair rsa key-file \
cert.key.pem auth-code cipher {HuaweiVRP.masking_string}
        #
        snmp-agent community read cipher {HuaweiVRP.masking_string} mib-view iso-view
        #
        ike peer ike_peer_name
         version 2
         pre-shared-key cipher {HuaweiVRP.masking_string}
         local-id-type fqdn
        #
        interface Tunnel0/0/0
         mtu 1300
         source LoopBack0
         gre key cipher {HuaweiVRP.masking_string}
         nhrp authentication cipher {HuaweiVRP.masking_string}
        #
        user-interface con 0
         authentication-mode password
         set authentication password cipher {HuaweiVRP.masking_string}
        #
        wlan ac
         security-profile name default
          security wpa2 psk pass-phrase {HuaweiVRP.masking_string} aes
        #
        xpl extcommunity-list soo CL_SOO_1
         123:123
         end-list
        #
        xpl community-list CL_NAME_1
         12345:12345
         end-list
        #
        xpl ip-prefix-list PL_DEFAULT
         0.0.0.0 0,
         0.0.0.0 1,
         128.0.0.0 1
        #
        xpl route-filter RF_NAME_1
         if ip route-destination in PL_DEFAULT then
          ! -- default routes --
          refuse
         elseif community matches-any CL_NAME_1 then
          ! -- matching by community --
          approve
         endif
         end-filter
        #
        """,
    ).strip()
    assert env_root[1].masked_config == masked_config


def test_masked_patch(env_root: tuple[CTreeEnv, HuaweiVRP]) -> None:
    masked_patch = dedent(
        f"""
        telnet server disable
        telnet ipv6 server disable
        undo telnet server-source all-interface
        undo telnet ipv6 server-source all-interface
        diffserv domain default
        ip vpn-instance LAN
        ipv4-family
        route-distinguisher 1.2.3.4:5678
        vpn-target 100:5678 export-extcommunity evpn
        vpn-target 100:5678 import-extcommunity evpn
        quit
        vxlan vni 5678
        quit
        interface 25GE1/0/1
        port link-type trunk
        undo port trunk allow-pass vlan 1
        stp edged-port enable
        storm suppression broadcast packets 100
        storm suppression multicast packets 100
        quit
        interface 25GE1/0/1.123 mode l2
        encapsulation dot1q vid 123
        bridge-domain 123
        statistics enable
        quit
        interface 100GE1/0/1
        undo portswitch
        mtu 9216
        description peer-switch
        ip address 4.3.2.1 255.255.255.254
        qos queue 5 shaping percent cir 10
        qos queue 6 shaping percent cir 20
        qos queue 7 shaping percent cir 30
        qos drr 0 to 4
        qos queue 0 drr weight 10
        qos queue 1 drr weight 20
        qos queue 2 drr weight 30
        qos queue 3 drr weight 40
        qos queue 4 drr weight 50
        qos queue 1 ecn
        quit
        interface LoopBack0
        description RID
        ip address 1.1.1.1 255.255.255.255
        quit
        ip ip-prefix PL_LOOPBACK index 10 permit 1.1.1.0 24 greater-equal 32 less-equal 32
        route-policy RP_LOOPBACKS permit node 10
        if-match ip-prefix PL_LOOPBACK
        quit
        route-policy RP_DENY deny node 10
        quit
        grpc
        grpc server
        source-ip 1.1.1.1 vpn-instance MGMT
        server enable
        quit
        quit
        aaa
        authentication-scheme default
        quit
        authentication-scheme local
        authentication-mode local
        quit
        authorization-scheme default
        authorization-mode local
        quit
        authorization-scheme local
        quit
        accounting-scheme default
        quit
        domain default
        quit
        domain local
        authentication-scheme local
        quit
        local-user admin@local password irreversible-cipher {HuaweiVRP.masking_string}
        local-user admin@local privilege level 3
        local-user admin@local service-type terminal ssh
        quit
        hwtacacs-server template template-name
        hwtacacs-server authentication 5.5.5.5 vpn-instance MGMT
        hwtacacs-server authentication 6.6.6.6 vpn-instance MGMT secondary
        hwtacacs-server shared-key cipher {HuaweiVRP.masking_string}
        quit
        ssl policy policy-name
        diffie-hellman modulus 2048
        certificate load pem-cert cert.cer key-pair rsa key-file \
cert.key.pem auth-code cipher {HuaweiVRP.masking_string}
        quit
        snmp-agent community read cipher {HuaweiVRP.masking_string} mib-view iso-view
        ike peer ike_peer_name
        version 2
        pre-shared-key cipher {HuaweiVRP.masking_string}
        local-id-type fqdn
        quit
        interface Tunnel0/0/0
        mtu 1300
        source LoopBack0
        gre key cipher {HuaweiVRP.masking_string}
        nhrp authentication cipher {HuaweiVRP.masking_string}
        quit
        user-interface con 0
        authentication-mode password
        set authentication password cipher {HuaweiVRP.masking_string}
        quit
        wlan ac
        security-profile name default
        security wpa2 psk pass-phrase {HuaweiVRP.masking_string} aes
        quit
        quit
        xpl extcommunity-list soo CL_SOO_1
        123:123
        end-list
        xpl community-list CL_NAME_1
        12345:12345
        end-list
        xpl ip-prefix-list PL_DEFAULT
        0.0.0.0 0,
        0.0.0.0 1,
        128.0.0.0 1
        xpl route-filter RF_NAME_1
        if ip route-destination in PL_DEFAULT then
        ! -- default routes --
        refuse
        elseif community matches-any CL_NAME_1 then
        ! -- matching by community --
        approve
        endif
        end-filter
        """,
    ).strip()  # noqa: F501
    assert env_root[1].masked_patch == masked_patch


def test_searcher(env_root: tuple[CTreeEnv, HuaweiVRP]) -> None:
    qos_config = dedent(
        """
        diffserv domain default
        #
        interface 100GE1/0/1
         qos queue 5 shaping percent cir 10
         qos queue 6 shaping percent cir 20
         qos queue 7 shaping percent cir 30
         qos drr 0 to 4
         qos queue 0 drr weight 10
         qos queue 1 drr weight 20
         qos queue 2 drr weight 30
         qos queue 3 drr weight 40
         qos queue 4 drr weight 50
         qos queue 1 ecn
        #
        """,
    ).strip()
    interface_or_qos_config = dedent(
        """
        diffserv domain default
        #
        interface 25GE1/0/1
         port link-type trunk
         undo port trunk allow-pass vlan 1
         stp edged-port enable
         storm suppression broadcast packets 100
         storm suppression multicast packets 100
        #
        interface 25GE1/0/1.123 mode l2
         encapsulation dot1q vid 123
         bridge-domain 123
         statistics enable
        #
        interface 100GE1/0/1
         undo portswitch
         mtu 9216
         description peer-switch
         ip address 4.3.2.1 255.255.255.254
         qos queue 5 shaping percent cir 10
         qos queue 6 shaping percent cir 20
         qos queue 7 shaping percent cir 30
         qos drr 0 to 4
         qos queue 0 drr weight 10
         qos queue 1 drr weight 20
         qos queue 2 drr weight 30
         qos queue 3 drr weight 40
         qos queue 4 drr weight 50
         qos queue 1 ecn
        #
        interface LoopBack0
         description RID
         ip address 1.1.1.1 255.255.255.255
        #
        interface Tunnel0/0/0
         mtu 1300
         source LoopBack0
         gre key cipher gre-secret-key
         nhrp authentication cipher nhrp-secret-key
        #
        """,
    ).strip()
    interface_and_qos_config = dedent(
        """
        interface 100GE1/0/1
         qos queue 5 shaping percent cir 10
         qos queue 6 shaping percent cir 20
         qos queue 7 shaping percent cir 30
         qos drr 0 to 4
         qos queue 0 drr weight 10
         qos queue 1 drr weight 20
         qos queue 2 drr weight 30
         qos queue 3 drr weight 40
         qos queue 4 drr weight 50
         qos queue 1 ecn
        #
        """,
    ).strip()

    env, ct = env_root
    qos = env.search(ct=ct, include_tags=["qos"])
    interface_or_qos = env.search(ct=ct, include_tags=["qos", "interface"])
    interface_and_qos = env.search(ct=ct, include_tags=["qos", "interface"], include_mode="and")
    assert qos.config == qos_config
    assert interface_or_qos.config == interface_or_qos_config
    assert interface_and_qos.config == interface_and_qos_config


def test_tagging_rules(env_root: tuple[CTreeEnv, HuaweiVRP]) -> None:
    env_dict, _ = env_root
    env_file = CTreeEnv(platform=Platform.HUAWEI_VRP, tagging_rules="./tests/test_environment_huawei.yaml")
    assert env_dict._parser.tagging_rules == env_file._parser.tagging_rules


def test_diff(env_root: tuple[CTreeEnv, HuaweiVRP]) -> None:
    target_str = dedent(
        """
        !Software Version abcdef
        !Last configuration was updated at now by me
        #
        telnet server disable
        telnet ipv6 server disable
        undo telnet server-source all-interface
        undo telnet ipv6 server-source all-interface
        #
        diffserv domain default
        #
        ip vpn-instance LAN
         ipv4-family
          route-distinguisher 1.2.3.4:5678
          vpn-target 100:5678 export-extcommunity evpn
          vpn-target 100:5678 import-extcommunity evpn
         vxlan vni 5678
        #
        interface 25GE1/0/1
         port link-type trunk
         undo port trunk allow-pass vlan 1
         stp edged-port enable
         storm suppression broadcast packets 100
         storm suppression multicast packets 100
        #
        interface 25GE1/0/1.123 mode l2
         encapsulation dot1q vid 123
         bridge-domain 123
         statistics enable
        #
        interface 100GE1/0/1
         undo portswitch
         description peer-switch
         ip address 4.3.2.1 255.255.255.254
         qos queue 5 shaping percent cir 10
         qos queue 6 shaping percent cir 20
         qos queue 7 shaping percent cir 30
         qos drr 0 to 4
         qos queue 0 drr weight 10
         qos queue 1 drr weight 20
         qos queue 2 drr weight 30
         qos queue 3 drr weight 40
         qos queue 4 drr weight 50
         qos queue 1 ecn
        #
        interface LoopBack0
         description RID-TEST
         ip address 1.1.1.1 255.255.255.255
        #
        ip ip-prefix PL_LOOPBACK index 10 permit 1.1.1.0 24 greater-equal 32 less-equal 32
        ip ip-prefix PL_LOOPBACK index 10 permit 2.2.2.0 24 greater-equal 32 less-equal 32
        #
        route-policy RP_LOOPBACKS permit node 10
         if-match ip-prefix PL_LOOPBACK
        #
        route-policy RP_DENY deny node 10
        #
        grpc
         #
         grpc server
          source-ip 1.1.1.1 vpn-instance MGMT
          server enable
        #
        aaa
         authentication-scheme default
         authentication-scheme local
          authentication-mode local
         authorization-scheme default
          authorization-mode local
         authorization-scheme local
         accounting-scheme default
         domain default
         domain local
          authentication-scheme local
         local-user admin@local password irreversible-cipher admin-secret-key
         local-user admin@local privilege level 3
         local-user admin@local service-type terminal ssh
        #
        hwtacacs-server template template-name
         hwtacacs-server authentication 5.5.5.5 vpn-instance MGMT
         hwtacacs-server authentication 6.6.6.6 vpn-instance MGMT secondary
         hwtacacs-server shared-key cipher tacacs-secret-key
        #
        ssl policy policy-name
         diffie-hellman modulus 2048
         certificate load pem-cert cert.cer key-pair rsa key-file cert.key.pem auth-code cipher cert-secret-key
        #
          snmp-agent community read cipher snmp-secret-key mib-view iso-view
        #
        ike peer ike_peer_name
         version 2
         pre-shared-key cipher ike-secret-key
         local-id-type fqdn
        #
        interface Tunnel0/0/0
         mtu 1300
         source LoopBack0
         gre key cipher gre-secret-key
         nhrp authentication cipher nhrp-secret-key
        #
        user-interface con 0
         authentication-mode password
         set authentication password cipher console-secret-key
        #
        wlan ac
         security-profile name default
          security wpa2 psk pass-phrase psk-secret-key aes
        #
        xpl extcommunity-list soo CL_SOO_1
         123:123
         end-list
        #
        xpl community-list CL_NAME_1
         12345:12345
         end-list
        #
        xpl ip-prefix-list PL_DEFAULT
         0.0.0.0 0,
         0.0.0.0 1,
         128.0.0.0 1
        #
        xpl route-filter RF_NAME_1
         if ip route-destination in PL_DEFAULT then
          ! -- default routes --
          refuse
         elseif community matches-any CL_NAME_1_NEW then
          ! -- matching by community --
          approve
         endif
         end-filter
        #
        return
        """,
    )
    diff_str_raw = dedent(
        """
        interface 100GE1/0/1
         undo mtu
        #
        interface LoopBack0
         undo description RID
         description RID-TEST
        #
        xpl route-filter RF_NAME_1
         undo elseif community matches-any CL_NAME_1 then
         elseif community matches-any CL_NAME_1_NEW then
          ! -- matching by community --
          approve
        #
        ip ip-prefix PL_LOOPBACK index 10 permit 2.2.2.0 24 greater-equal 32 less-equal 32
        #
        """,
    ).strip()
    diff_str_no_diff_section = dedent(
        """
        interface 100GE1/0/1
         undo mtu
        #
        interface LoopBack0
         undo description RID
         description RID-TEST
        #
        ip ip-prefix PL_LOOPBACK index 10 permit 2.2.2.0 24 greater-equal 32 less-equal 32
        #
        xpl route-filter RF_NAME_1
         if ip route-destination in PL_DEFAULT then
          ! -- default routes --
          refuse
         elseif community matches-any CL_NAME_1_NEW then
          ! -- matching by community --
          approve
         endif
         end-filter
        #
        """,
    ).strip()
    env, current = env_root
    target = env.parse(target_str)
    diff = env.diff(a=current, b=target)

    env_no_diff = CTreeEnv(
        platform=Platform.HUAWEI_VRP,
        no_diff_sections=[r"^xpl \S+ \S+$"],
    )
    diff_no_diff = env_no_diff.diff(a=current, b=target)
    assert diff.config == diff_str_raw
    assert diff_no_diff.config == diff_str_no_diff_section
