from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Platform
from ctreepo.parser import TaggingRulesDict


def test_arista_interface_post_processing() -> None:
    current_config = dedent(
        """
        interface 25GE1/0/1
         port link-type trunk
         undo port trunk allow-pass vlan 1
         stp edged-port enable
         storm suppression multicast packets 50
         storm suppression broadcast packets 200
         sflow sampling collector 1
         sflow sampling inbound
         device transceiver 25GBASE-COPPER
        #
        interface 25GE1/0/1.1234 mode l2
         encapsulation untag
         bridge-domain 1234
         statistics enable
        #
        interface 25GE1/0/2
         port link-type trunk
         undo port trunk allow-pass vlan 1
         stp edged-port enable
         storm suppression multicast packets 50
         storm suppression broadcast packets 200
         sflow sampling collector 1
         sflow sampling inbound
         device transceiver 25GBASE-COPPER
        #
        interface 25GE1/0/2.1234 mode l2
         encapsulation untag
         bridge-domain 1234
         statistics enable
        #
        """,
    ).strip()

    target_config = dedent(
        """
        #
        interface 25GE1/0/2
         port link-type trunk
         undo port trunk allow-pass vlan 1
         stp edged-port enable
         storm suppression multicast packets 50
         storm suppression broadcast packets 200
         sflow sampling collector 1
         sflow sampling inbound
         description test
         device transceiver 25GBASE-COPPER
        #
        interface 25GE1/0/2.1234 mode l2
         encapsulation untag
         bridge-domain 1234
         statistics enable
        #
        """,
    ).strip()
    diff_config = dedent(
        """
        interface 25GE1/0/2
           description test
        !
        no interface 25GE1/0/1
        !
        no interface 25GE1/0/1.1234 mode l2
        !
        """,
    ).strip()
    diff_patch = dedent(
        """
        interface 25GE1/0/2
        description test
        exit
        no interface 25GE1/0/1
        no interface 25GE1/0/1.1234 mode l2
        """,
    ).strip()
    parser = CTreeParser(Platform.ARISTA_EOS)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_arista_route_policy_post_processing() -> None:
    current_config = dedent(
        """
        route-map RM_NAME_1 permit 10
         if-match ip-prefix PL_NAME_1
         if-match ip next-hop ip-prefix PL_NHOP_NAME_1
         apply community community-list CL_NAME_1 additive
        #
        route-map RM_NAME_1 permit 20
         if-match ip-prefix ANYCAST_NETWORK
         apply community community-list CL_NAME_1 additive
        #
        route-map RM_NAME_1 permit 30
         if-match ip-prefix PL_NAME_1
         if-match ip next-hop ip-prefix PL_NHOP_NAME_1_1
         apply community community-list CL_NAME_1 additive
        #
        route-map RM_NAME_1 permit 40
         if-match ip-prefix PL_NAME_1
         if-match ip next-hop ip-prefix PL_NHOP_NAME_1_2
         apply community community-list CL_NAME_1 additive
        #
        route-map RM_NAME_1 permit 50
         if-match ip-prefix PL_NAME_2
         apply community community-list CL_NAME_1 additive
        #
        route-map RM_NAME_1 permit 70
         if-match ip-prefix PL_NAME_3
         apply community community-list CL_NAME_1 additive
        #
        route-map RM_NAME_1 permit 80
         if-match ip-prefix PL_NAME_4
         apply community community-list CL_NAME_1 additive
        #
        route-map RM_NAME_1 permit 90
         if-match ip-prefix PL_NAME_5
         apply community community-list CL_NAME_1 additive
        #
        route-map RM_NAME_1 permit 100
         if-match ip-prefix PL_NAME_6
         if-match ip next-hop ip-prefix PL_NHOP_NAME_6
         apply community community-list CL_NAME_1 additive
        #
        route-map RM_NAME_2 permit 10
         if-match ip-prefix PL_NAME_7
        #
        route-map RM_NAME_2 permit 20
         if-match ip-prefix PL_NAME_8
        #
        route-map DIRECT_IN permit 5
         apply community community-list CL_NAME_1 additive
        #
        """,
    ).strip()
    target_config = dedent(
        """
        route-map RM_NAME_1 permit 10
         if-match ip-prefix PL_NAME_1
         if-match ip next-hop ip-prefix PL_NHOP_NAME_1
         apply community community-list CL_NAME_1 additive
        #
        route-map RM_NAME_1 permit 30
         if-match ip-prefix PL_NAME_1
         apply community community-list CL_NAME_1 additive
        #
        route-map RM_NAME_1 permit 40
         if-match ip-prefix PL_NAME_1
         if-match ip next-hop ip-prefix PL_NHOP_NAME_1_2
         apply community community-list CL_NAME_1 additive
        #
        route-map RM_NAME_1 permit 50
         if-match ip-prefix PL_NAME_2
         apply community community-list CL_NAME_1 additive
        #
        route-map RM_NAME_1 permit 70
         if-match ip-prefix PL_NAME_3
         apply community community-list CL_NAME_1 additive
        #
        route-map RM_NAME_1 permit 80
         if-match ip-prefix PL_NAME_4
         apply community community-list CL_NAME_1 additive
        #
        route-map RM_NAME_1 permit 90
         if-match ip-prefix PL_NAME_5
         apply community community-list CL_NAME_1 additive
        #
        route-map RM_NAME_1 permit 100
         if-match ip-prefix PL_NAME_6
         if-match ip next-hop ip-prefix PL_NHOP_NAME_6
         apply community community-list CL_NAME_1 additive
        #
        route-map RP_BLOCK deny 10
        #
        route-map DIRECT_IN permit 5
         apply community community-list CL_NAME_1 additive
        #
        """,
    ).strip()
    diff_config = dedent(
        """
        route-map RM_NAME_1 permit 30
           no if-match ip next-hop ip-prefix PL_NHOP_NAME_1_1
        !
        route-map RP_BLOCK deny 10
        !
        no route-map RM_NAME_1 permit 20
        !
        no route-map RM_NAME_2 permit 10
        !
        no route-map RM_NAME_2 permit 20
        !
        """,
    ).strip()
    diff_patch = dedent(
        """
        route-map RM_NAME_1 permit 30
        no if-match ip next-hop ip-prefix PL_NHOP_NAME_1_1
        exit
        route-map RP_BLOCK deny 10
        exit
        no route-map RM_NAME_1 permit 20
        no route-map RM_NAME_2 permit 10
        no route-map RM_NAME_2 permit 20
        """,
    ).strip()
    parser = CTreeParser(platform=Platform.ARISTA_EOS)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_arista_prefix_list_post_processing() -> None:
    current_config = dedent(
        """
        ip prefix-list TEST_PL_1 seq 10 permit 10.1.30.0/24 eq 32
        ip prefix-list TEST_PL_1 seq 20 permit 10.1.31.0/24 eq 32
        ip prefix-list TEST_PL_1 seq 30 permit 10.1.32.0/24 eq 32
        ip prefix-list TEST_PL_2 seq 10 permit 10.1.33.0/24
        ip prefix-list TEST_PL_3 seq 10 permit 10.1.34.0/24 ge 25 le 26
        """,
    ).strip()
    target_config = dedent(
        """
        ip prefix-list TEST_PL_1 seq 10 permit 10.1.30.0/24 eq 32
        ip prefix-list TEST_PL_1 seq 30 permit 10.1.32.0/24 eq 32
        ip prefix-list TEST_PL_3 seq 10 permit 10.0.36.0/24
        """,
    ).strip()
    diff_config = dedent(
        """
        no ip prefix-list TEST_PL_3 seq 10
        !
        ip prefix-list TEST_PL_3 seq 10 permit 10.0.36.0/24
        !
        no ip prefix-list TEST_PL_1 seq 20
        !
        no ip prefix-list TEST_PL_2 seq 10
        !
        """,
    ).strip()

    diff_patch = dedent(
        """
        no ip prefix-list TEST_PL_3 seq 10
        ip prefix-list TEST_PL_3 seq 10 permit 10.0.36.0/24
        no ip prefix-list TEST_PL_1 seq 20
        no ip prefix-list TEST_PL_2 seq 10
        """,
    ).strip()
    parser = CTreeParser(platform=Platform.ARISTA_EOS)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target)

    assert diff.config == diff_config
    assert diff.patch == diff_patch
    assert "post" not in diff.children["no ip prefix-list TEST_PL_3 seq 10"].tags
    assert (
        diff.children["no ip prefix-list TEST_PL_3 seq 10"].tags
        == target.children["ip prefix-list TEST_PL_3 seq 10 permit 10.0.36.0/24"].tags
    )


def test_arista_user_post_processing_1() -> None:
    # случай 1: не меняем пароль для пользователей user1/user2, состав пользователей совпадает
    target_config = dedent(
        """
        username user1 privilege 15 role network-admin secret
        username user2 privilege 15 role network-admin secret
        """,
    ).strip()
    current_config = dedent(
        """
        username user1 privilege 15 role network-admin secret sha512 some_password_hash_1
        username user2 privilege 15 role network-admin secret sha512 some_password_hash_2
        """,
    ).strip()
    diff_config_raw = dedent(
        """
        username user1 privilege 15 role network-admin secret
        !
        username user2 privilege 15 role network-admin secret
        !
        no username user1 privilege 15 role network-admin secret sha512 some_password_hash_1
        !
        no username user2 privilege 15 role network-admin secret sha512 some_password_hash_2
        !
        """,
    ).strip()
    diff_config_processed = ""
    parser = CTreeParser(Platform.ARISTA_EOS)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw

    diff_processed = CTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed


def test_arista_user_post_processing_2() -> None:
    # случай 2: меняем пароль для user1, не меняем для user2, состав пользователей совпадает
    target_config = dedent(
        """
        username user1 privilege 15 role network-admin secret P@ssw0rd
        username user2 privilege 15 role network-admin secret
        """,
    ).strip()
    current_config = dedent(
        """
        username user1 privilege 15 role network-admin secret sha512 some_password_hash_1
        username user2 privilege 15 role network-admin secret sha512 some_password_hash_2
        """,
    ).strip()
    diff_config_raw = dedent(
        """
        username user1 privilege 15 role network-admin secret P@ssw0rd
        !
        username user2 privilege 15 role network-admin secret
        !
        no username user1 privilege 15 role network-admin secret sha512 some_password_hash_1
        !
        no username user2 privilege 15 role network-admin secret sha512 some_password_hash_2
        !
        """,
    ).strip()
    diff_config_processed = dedent(
        """
        username user1 privilege 15 role network-admin secret P@ssw0rd
        !
        """,
    ).strip()
    parser = CTreeParser(Platform.ARISTA_EOS)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw

    diff_processed = CTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed


def test_arista_user_post_processing_3() -> None:
    # случай 3: меняем пароль для user1, не меняем для user2, на устройстве лишний пользователь
    target_config = dedent(
        """
        username user1 privilege 15 role network-admin secret P@ssw0rd
        username user2 privilege 15 role network-admin secret
        """,
    ).strip()
    current_config = dedent(
        """
        username user1 privilege 15 role network-admin secret sha512 some_password_hash_1
        username user2 privilege 15 role network-admin secret sha512 some_password_hash_2
        username user3 privilege 15 role network-admin secret sha512 some_password_hash_3
        username user3 description some-test
        """,
    ).strip()
    diff_config_raw = dedent(
        """
        username user1 privilege 15 role network-admin secret P@ssw0rd
        !
        username user2 privilege 15 role network-admin secret
        !
        no username user1 privilege 15 role network-admin secret sha512 some_password_hash_1
        !
        no username user2 privilege 15 role network-admin secret sha512 some_password_hash_2
        !
        no username user3 privilege 15 role network-admin secret sha512 some_password_hash_3
        !
        no username user3 description some-test
        !
        """,
    ).strip()
    diff_config_processed = dedent(
        """
        username user1 privilege 15 role network-admin secret P@ssw0rd
        !
        no username user3
        !
        """,
    ).strip()
    parser = CTreeParser(Platform.ARISTA_EOS)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw

    diff_processed = CTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed


def test_arista_user_post_processing_4() -> None:
    # случай 4: меняем пароль для user1, не меняем для user2, на устройстве не хватает пользователя и один лишний
    target_config = dedent(
        """
        username user1 privilege 15 role network-admin secret P@ssw0rd
        username user2 privilege 15 role network-admin secret
        username user4 privilege 15 role network-admin secret P@ssw0rd
        """,
    ).strip()
    current_config = dedent(
        """
        username user1 privilege 15 role network-admin secret sha512 some_password_hash_1
        username user2 privilege 15 role network-admin secret sha512 some_password_hash_2
        username user3 privilege 15 role network-admin secret sha512 some_password_hash_3
        """,
    ).strip()
    diff_config_raw = dedent(
        """
        username user1 privilege 15 role network-admin secret P@ssw0rd
        !
        username user2 privilege 15 role network-admin secret
        !
        username user4 privilege 15 role network-admin secret P@ssw0rd
        !
        no username user1 privilege 15 role network-admin secret sha512 some_password_hash_1
        !
        no username user2 privilege 15 role network-admin secret sha512 some_password_hash_2
        !
        no username user3 privilege 15 role network-admin secret sha512 some_password_hash_3
        !
        """,
    ).strip()
    diff_config_processed = dedent(
        """
        username user1 privilege 15 role network-admin secret P@ssw0rd
        !
        username user4 privilege 15 role network-admin secret P@ssw0rd
        !
        no username user3
        !
        """,
    ).strip()
    parser = CTreeParser(Platform.ARISTA_EOS)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw

    diff_processed = CTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed


def test_arista_postproc_bgp_1() -> None:
    current_config = ""
    target_config = dedent(
        """
        route-map RM_TEST permit 10
           match ip address prefix-list PL_TEST
        !
        router bgp 12345
           router-id 1.2.3.4
           no bgp default ipv4-unicast
           maximum-paths 4 ecmp 64
           address-family ipv4
              neighbor PEER_GROUP_1 activate
              neighbor PEER_GROUP_2 activate
           vrf VRF_NAME_1
              router-id 1.2.3.4
              rd 1.2.3.4:123
              route-target import evpn 123:456
              route-target export evpn 123:456
              bgp listen range 1.2.3.0/24 peer-group PEER_GROUP_1 peer-filter AS12345
           address-family evpn
              neighbor PEER_GROUP_3 activate
           neighbor PEER_GROUP_1 peer group
           neighbor PEER_GROUP_1 bfd
           neighbor PEER_GROUP_2 peer group
           neighbor PEER_GROUP_3 peer group
           neighbor 192.168.0.1 peer group PEER_GROUP_1
           neighbor 192.168.0.1 remote-as 12345
           neighbor 192.168.0.2 peer group PEER_GROUP_2
           neighbor 192.168.0.2 remote-as 12345
           neighbor 192.168.0.3 peer group PEER_GROUP_3
           neighbor 192.168.0.3 remote-as 12345
        !
        """,
    ).strip()
    diff_config = dedent(
        """
        route-map RM_TEST permit 10
           match ip address prefix-list PL_TEST
        !
        router bgp 12345
           router-id 1.2.3.4
           no bgp default ipv4-unicast
           maximum-paths 4 ecmp 64
           neighbor PEER_GROUP_1 peer group
           neighbor PEER_GROUP_1 bfd
           neighbor PEER_GROUP_2 peer group
           neighbor PEER_GROUP_3 peer group
           neighbor 192.168.0.1 peer group PEER_GROUP_1
           neighbor 192.168.0.1 remote-as 12345
           neighbor 192.168.0.2 peer group PEER_GROUP_2
           neighbor 192.168.0.2 remote-as 12345
           neighbor 192.168.0.3 peer group PEER_GROUP_3
           neighbor 192.168.0.3 remote-as 12345
           address-family ipv4
              neighbor PEER_GROUP_1 activate
              neighbor PEER_GROUP_2 activate
           vrf VRF_NAME_1
              router-id 1.2.3.4
              rd 1.2.3.4:123
              route-target import evpn 123:456
              route-target export evpn 123:456
              bgp listen range 1.2.3.0/24 peer-group PEER_GROUP_1 peer-filter AS12345
           address-family evpn
              neighbor PEER_GROUP_3 activate
        !
        """,
    ).strip()
    diff_patch = dedent(
        """
        route-map RM_TEST permit 10
        match ip address prefix-list PL_TEST
        exit
        router bgp 12345
        router-id 1.2.3.4
        no bgp default ipv4-unicast
        maximum-paths 4 ecmp 64
        neighbor PEER_GROUP_1 peer group
        neighbor PEER_GROUP_1 bfd
        neighbor PEER_GROUP_2 peer group
        neighbor PEER_GROUP_3 peer group
        neighbor 192.168.0.1 peer group PEER_GROUP_1
        neighbor 192.168.0.1 remote-as 12345
        neighbor 192.168.0.2 peer group PEER_GROUP_2
        neighbor 192.168.0.2 remote-as 12345
        neighbor 192.168.0.3 peer group PEER_GROUP_3
        neighbor 192.168.0.3 remote-as 12345
        address-family ipv4
        neighbor PEER_GROUP_1 activate
        neighbor PEER_GROUP_2 activate
        exit
        vrf VRF_NAME_1
        router-id 1.2.3.4
        rd 1.2.3.4:123
        route-target import evpn 123:456
        route-target export evpn 123:456
        bgp listen range 1.2.3.0/24 peer-group PEER_GROUP_1 peer-filter AS12345
        exit
        address-family evpn
        neighbor PEER_GROUP_3 activate
        exit
        exit
        """,
    ).strip()

    parser = CTreeParser(Platform.ARISTA_EOS)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_arista_postproc_bgp_2() -> None:
    current_config = dedent(
        """
        router bgp 12345
           router-id 1.1.1.1
           neighbor GROUP-PEER peer group
           neighbor GROUP-PEER remote-as 54321
           neighbor GROUP-PEER route-map RM-IN in
           neighbor GROUP-PEER route-map RM-OUT out
           neighbor GROUP-PEER maximum-routes 200
           neighbor GROUP-PEER maximum-accepted-routes 100
           address-family ipv4
              neighbor 1
              neighbor GROUP-PEER activate
           vrf LAN
              neighbor 1
              neighbor 1.2.3.4 peer group GROUP-PEER
              neighbor 1.2.3.4 shutdown
        !
        """,
    )
    target_config = dedent(
        """
        router bgp 12345
           router-id 1.1.1.1
           address-family ipv4
              neighbor 1
           vrf LAN
              neighbor 1
        !
        """,
    ).strip()
    diff_config_raw = dedent(
        """
        router bgp 12345
           no neighbor GROUP-PEER peer group
           no neighbor GROUP-PEER remote-as 54321
           no neighbor GROUP-PEER route-map RM-IN in
           no neighbor GROUP-PEER route-map RM-OUT out
           no neighbor GROUP-PEER maximum-routes 200
           no neighbor GROUP-PEER maximum-accepted-routes 100
           address-family ipv4
              no neighbor GROUP-PEER activate
           vrf LAN
              no neighbor 1.2.3.4 peer group GROUP-PEER
              no neighbor 1.2.3.4 shutdown
        !
        """,
    ).strip()
    diff_config = dedent(
        """
        router bgp 12345
           no neighbor GROUP-PEER peer group
           vrf LAN
              no neighbor 1.2.3.4 peer group GROUP-PEER
              no neighbor 1.2.3.4 shutdown
        !
        """,
    ).strip()

    parser = CTreeParser(Platform.ARISTA_EOS)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff_raw = CTreeDiffer.diff(current, target, post_proc_rules=[])
    diff = CTreeDiffer.diff(current, target)
    assert diff_raw.config == diff_config_raw
    assert diff.config == diff_config


def test_arista_postproc_tacacs_key_1() -> None:
    target_config = dedent(
        """
        tacacs-server timeout 3
        tacacs-server key
        tacacs-server host 1.2.3.4 vrf MGMT
        """,
    ).strip()
    current_config = dedent(
        """
        tacacs-server timeout 3
        tacacs-server key 7 secret_hash
        tacacs-server host 1.2.3.4 vrf MGMT
        """,
    ).strip()
    diff_config_raw = dedent(
        """
        tacacs-server key
        !
        no tacacs-server key 7 secret_hash
        !
        """,
    ).strip()
    diff_config_processed = ""
    parser = CTreeParser(Platform.ARISTA_EOS)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw, "diff_config_raw"

    diff_processed = CTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed, "diff_config_processed"


def test_arista_postproc_tacacs_key_2() -> None:
    target_config = dedent(
        """
        tacacs-server timeout 3
        tacacs-server key P@ssw0rd
        tacacs-server host 1.2.3.4 vrf MGMT
        """,
    ).strip()
    current_config = dedent(
        """
        tacacs-server timeout 3
        tacacs-server key 7 secret_hash
        tacacs-server host 1.2.3.4 vrf MGMT
        """,
    ).strip()
    diff_config_raw = dedent(
        """
        tacacs-server key P@ssw0rd
        !
        no tacacs-server key 7 secret_hash
        !
        """,
    ).strip()
    diff_config_processed = dedent(
        """
        tacacs-server key P@ssw0rd
        !
        """,
    ).strip()
    parser = CTreeParser(Platform.ARISTA_EOS)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw, "diff_config_raw"

    diff_processed = CTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed, "diff_config_processed"


def test_arista_postproc_aaa() -> None:
    target_config = dedent(
        """
        aaa authentication login default group group2 local
        aaa authentication login console none
        aaa authentication enable default none
        """,
    ).strip()
    current_config = dedent(
        """
        aaa authentication login default group group1 local
        aaa authentication login console local
        aaa authentication enable default none
        aaa authentication policy on-success log
        """,
    ).strip()
    diff_config_raw = dedent(
        """
        aaa authentication login default group group2 local
        !
        aaa authentication login console none
        !
        no aaa authentication login default group group1 local
        !
        no aaa authentication login console local
        !
        no aaa authentication policy on-success log
        !
        """,
    ).strip()
    diff_config_processed = dedent(
        """
        aaa authentication login default group group2 local
        !
        aaa authentication login console none
        !
        no aaa authentication policy on-success log
        !
        """,
    ).strip()
    parser = CTreeParser(Platform.ARISTA_EOS)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw, "diff_config_raw"

    diff_processed = CTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed, "diff_config_processed"


def test_huawei_interface_post_processing_1() -> None:
    # secondary ip
    current_config = dedent(
        """
        interface Ethernet1
           description test
           ip address 192.168.0.1/24
        !
        """,
    ).strip()
    target_config = dedent(
        """
        interface Ethernet1
           description test
           ip address 192.168.2.1/24 secondary
           ip address 192.168.1.1/24
        !
        """,
    ).strip()
    diff_config = dedent(
        """
        interface Ethernet1
           no ip address 192.168.0.1/24
           ip address 192.168.1.1/24
           ip address 192.168.2.1/24 secondary
        !
        """,
    ).strip()

    parser = CTreeParser(Platform.ARISTA_EOS)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config


def test_arista_postproc_snmp_1() -> None:
    # no с тегом pre до добавления community
    current_config = dedent(
        """
        snmp-server community public12345 ro
        snmp-server vrf MGMT
        """,
    )
    target_config = dedent(
        """
        snmp-server community public54321 ro
        snmp-server vrf MGMT
        """,
    )
    diff_config = dedent(
        """
        no snmp-server community public12345 ro
        !
        snmp-server community public54321 ro
        !
        """,
    ).strip()

    tagging_rules = TaggingRulesDict(
        {Platform.ARISTA_EOS: [{"regex": r"^(?:no )?snmp-server\s+", "tags": ["snmp"]}]},
    )

    parser = CTreeParser(Platform.ARISTA_EOS, tagging_rules=tagging_rules)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target)
    diff.reorder(["pre", "post"])
    assert list(diff.children.values())[0].tags == ["snmp", "pre"]
    assert list(diff.children.values())[1].tags == ["snmp"]
    assert diff.config == diff_config


def test_arista_postproc_snmp_2() -> None:
    # удалить узлы с нулевым community
    current_config = dedent(
        """
        snmp-server community public12345 ro
        snmp-server vrf MGMT
        """,
    )
    target_config = dedent(
        """
        snmp-server community  ro
        snmp-server community private12345 rw
        snmp-server vrf MGMT
        """,
    )
    diff_config = dedent(
        """
        snmp-server community private12345 rw
        !
        """,
    ).strip()

    parser = CTreeParser(Platform.ARISTA_EOS)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config


def test_arista_enable_password_post_processing() -> None:
    current_config = "enable password sha512 secret-string"
    target_config_1 = "enable password"
    target_config_2 = "enable password new-password"
    diff_patch_1 = ""
    diff_patch_2 = "enable password new-password"

    parser = CTreeParser(platform=Platform.ARISTA_EOS)

    current = parser.parse(current_config)
    target_1 = parser.parse(target_config_1)
    target_2 = parser.parse(target_config_2)

    diff_1 = CTreeDiffer.diff(current, target_1)
    diff_2 = CTreeDiffer.diff(current, target_2)

    assert diff_1.patch == diff_patch_1
    assert diff_2.patch == diff_patch_2
