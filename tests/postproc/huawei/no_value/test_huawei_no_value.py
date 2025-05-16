from textwrap import dedent

import pytest

from ctreepo import CTreeDiffer, CTreeParser, Platform


@pytest.mark.parametrize(
    "current_config, target_config, diff_config",
    [
        (
            dedent(
                """
                snmp-agent
                snmp-agent sys-info version v2c v3
                snmp-agent community read public12345 mib-view device42 acl 1234
                """,
            ),
            dedent(
                """
                snmp-agent
                snmp-agent sys-info version v2c v3
                snmp-agent community read <<no-value>> mib-view device42 acl 1234
                """,
            ),
            "",
        ),
        (
            dedent(
                """
                snmp-agent
                snmp-agent sys-info version v2c v3
                snmp-agent community read public12345 mib-view device42 acl 1234
                snmp-agent community read 12345public mib-view device42 acl 5432
                """,
            ),
            dedent(
                """
                snmp-agent
                snmp-agent sys-info version v2c v3
                snmp-agent community read <<no-value>> mib-view device42 acl 1234
                """,
            ),
            dedent(
                """
                undo snmp-agent community read 12345public mib-view device42 acl 5432
                #
                """,
            ).strip(),
        ),
        (
            dedent(
                """
                hwtacacs-server template tacacs-group
                 hwtacacs-server shared-key cipher tacacs-password
                 hwtacacs-server timer response-timeout 4
                """,
            ),
            dedent(
                """
                hwtacacs-server template tacacs-group
                 hwtacacs-server shared-key cipher <<no-value>>
                 hwtacacs-server timer response-timeout 5
                """,
            ),
            dedent(
                """
                hwtacacs-server template tacacs-group
                 undo hwtacacs-server timer response-timeout 4
                 hwtacacs-server timer response-timeout 5
                #
                """,
            ).strip(),
        ),
        (
            dedent(
                """
                hwtacacs-server template tacacs-group
                 hwtacacs-server shared-key cipher tacacs-password
                 hwtacacs-server timer response-timeout 4
                """,
            ),
            dedent(
                """
                hwtacacs-server template tacacs-group
                 hwtacacs-server shared-key cipher <<no-value>>
                 hwtacacs-server timer response-timeout 4
                """,
            ),
            "",
        ),
        (
            dedent(
                """
                sysname router1
                #
                snmp-agent
                snmp-agent sys-info version v2c v3
                snmp-agent community read public12345 mib-view device42 acl 1234
                #
                hwtacacs-server template tacacs-group
                 hwtacacs-server shared-key cipher tacacs-password
                 hwtacacs-server timer response-timeout 4
                """,
            ),
            dedent(
                """
                sysname router1
                #
                snmp-agent
                snmp-agent sys-info version v2c v3
                snmp-agent community read <<no-value>> mib-view device42 acl 1234
                #
                hwtacacs-server template tacacs-group
                 hwtacacs-server shared-key cipher <<no-value>>
                 hwtacacs-server timer response-timeout 4
                """,
            ),
            "",
        ),
        (
            dedent(
                """
                sysname router1
                #
                snmp-agent
                snmp-agent sys-info version v2c v3
                snmp-agent community read public12345 mib-view device42 acl 1234
                #
                hwtacacs-server template tacacs-group
                 hwtacacs-server shared-key cipher tacacs-password
                 hwtacacs-server timer response-timeout 4
                """,
            ),
            dedent(
                """
                sysname router1
                #
                snmp-agent
                snmp-agent sys-info version v2c v3
                snmp-agent community read <<no-value>> mib-view device42 acl 4321
                #
                hwtacacs-server template tacacs-group
                 hwtacacs-server shared-key cipher <<no-value>>
                 hwtacacs-server timer response-timeout 4
                """,
            ),
            dedent(
                """
                undo snmp-agent community read public12345 mib-view device42 acl 1234
                #
                """,
            ).strip(),
        ),
    ],
)
def test_huawei_no_value_case_1(current_config: str, target_config: str, diff_config: str) -> None:
    parser = CTreeParser(platform=Platform.HUAWEI_VRP)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
