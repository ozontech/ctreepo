from textwrap import dedent

from ctreepo.parser import CTreeParser
from ctreepo.spec.config_handler_registry import PreConfigHandlerRegistry


def test_pre_config_handler_registry_apply() -> None:
    config = dedent(
        """
        ssl policy policy-name
         diffie-hellman modulus 2048
        #
         snmp-agent community read cipher snmp-secret-key mib-view iso-view
        #
        ike peer ike_peer_name
         version 2
        #
        """,
    ).strip()
    expected = dedent(
        """
        ssl policy policy-name
         diffie-hellman modulus 2048
        #
        snmp-agent community read cipher snmp-secret-key mib-view iso-view
        #
        ike peer ike_peer_name
         version 2
        #
        """,
    ).strip()
    parser = CTreeParser("huawei_vrp")
    root = parser.parse(config)
    assert root.config == expected


def test_pre_config_handler_registry_reset() -> None:
    config = dedent(
        """
        ssl policy policy-name
         diffie-hellman modulus 2048
        #
         snmp-agent community read cipher snmp-secret-key mib-view iso-view
        #
        ike peer ike_peer_name
         version 2
        #
        """,
    ).strip()
    expected = dedent(
        """
        ssl policy policy-name
         diffie-hellman modulus 2048
         snmp-agent community read cipher snmp-secret-key mib-view iso-view
        #
        ike peer ike_peer_name
         version 2
        #
        """,
    ).strip()
    parser = CTreeParser("huawei_vrp")
    PreConfigHandlerRegistry.reset("huawei_vrp")
    root = parser.parse(config)
    assert root.config == expected
