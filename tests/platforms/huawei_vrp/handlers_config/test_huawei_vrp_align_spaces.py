from textwrap import dedent

import pytest

from ctreepo.platforms.huawei_vrp import align_spaces


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        # ничего не нужно двигать, удаляем пустые строки
        (
            dedent(
                """
                grpc
                 #
                 grpc server
                  source-ip 1.1.1.1 vpn-instance MGMT
                  server enable
                #

                ike peer ike_peer_name
                 version 2
                 pre-shared-key cipher ike-secret-key
                 local-id-type fqdn
                #
                """,
            ).strip(),
            dedent(
                """
                grpc
                 #
                 grpc server
                  source-ip 1.1.1.1 vpn-instance MGMT
                  server enable
                #
                ike peer ike_peer_name
                 version 2
                 pre-shared-key cipher ike-secret-key
                 local-id-type fqdn
                #
                """,
            ).strip(),
        ),
        # меняем в середине
        (
            dedent(
                """
                grpc
                 #
                 grpc server
                  source-ip 1.1.1.1 vpn-instance MGMT
                  server enable
                #
                  snmp-agent community read cipher snmp-secret-key mib-view iso-view
                  ssh server-source -i all
                #
                ike peer ike_peer_name
                 version 2
                 pre-shared-key cipher ike-secret-key
                 local-id-type fqdn
                #
                """,
            ).strip(),
            dedent(
                """
                grpc
                 #
                 grpc server
                  source-ip 1.1.1.1 vpn-instance MGMT
                  server enable
                #
                snmp-agent community read cipher snmp-secret-key mib-view iso-view
                ssh server-source -i all
                #
                ike peer ike_peer_name
                 version 2
                 pre-shared-key cipher ike-secret-key
                 local-id-type fqdn
                #
                """,
            ).strip(),
        ),
        # меняем в начале
        (
            dedent(
                """
                #
                  snmp-agent community read cipher snmp-secret-key mib-view iso-view
                  ssh server-source -i all
                #
                ike peer ike_peer_name
                 version 2
                 pre-shared-key cipher ike-secret-key
                 local-id-type fqdn
                #
                """,
            ).strip(),
            dedent(
                """
                #
                snmp-agent community read cipher snmp-secret-key mib-view iso-view
                ssh server-source -i all
                #
                ike peer ike_peer_name
                 version 2
                 pre-shared-key cipher ike-secret-key
                 local-id-type fqdn
                #
                """,
            ).strip(),
        ),
        # меняем в конце
        (
            dedent(
                """
                #
                ike peer ike_peer_name
                 version 2
                 pre-shared-key cipher ike-secret-key
                 local-id-type fqdn
                #
                  snmp-agent community read cipher snmp-secret-key mib-view iso-view
                  ssh server-source -i all
                #
                """,
            ).strip(),
            dedent(
                """
                #
                ike peer ike_peer_name
                 version 2
                 pre-shared-key cipher ike-secret-key
                 local-id-type fqdn
                #
                snmp-agent community read cipher snmp-secret-key mib-view iso-view
                ssh server-source -i all
                #
                """,
            ).strip(),
        ),
        # комбинация
        (
            dedent(
                """
                #
                  snmp-agent community read cipher snmp-secret-key mib-view iso-view
                  ssh server-source -i all
                #
                ike peer ike_peer_name
                 version 2
                 pre-shared-key cipher ike-secret-key
                 local-id-type fqdn

                #
                 ntp-service server disable
                 ntp-service source-interface LoopBack0
                 ntp-service unicast-server 1.2.3.4
                #
                """,
            ).strip(),
            dedent(
                """
                #
                snmp-agent community read cipher snmp-secret-key mib-view iso-view
                ssh server-source -i all
                #
                ike peer ike_peer_name
                 version 2
                 pre-shared-key cipher ike-secret-key
                 local-id-type fqdn
                #
                ntp-service server disable
                ntp-service source-interface LoopBack0
                ntp-service unicast-server 1.2.3.4
                #
                """,
            ).strip(),
        ),
    ],
)
def test_huawei_vrp_align_spaces(config: str, expected: str) -> None:
    result = align_spaces(config)
    assert result == expected
