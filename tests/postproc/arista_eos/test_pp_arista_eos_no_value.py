from textwrap import dedent

import pytest

from ctreepo import CTreeDiffer, CTreeParser, Platform, settings
from ctreepo.postproc.arista_eos import AristaEOSNoValue


@pytest.mark.parametrize(
    "current_config, target_config, raw_diff_config, pp_diff_config",
    [
        (
            dedent(
                """
                snmp-server community public12345 ro
                """,
            ),
            dedent(
                f"""
                snmp-server community {settings.NO_VALUE} ro
                """,
            ),
            dedent(
                f"""
                snmp-server community {settings.NO_VALUE} ro
                !
                no snmp-server community public12345 ro
                !
                """,
            ).strip(),
            "",
        ),
        (
            dedent(
                """
                snmp-server host 192.168.0.1 public12345 snmp bgp
                snmp-server host 192.168.0.2 public12345 snmp bgp
                snmp-server host 192.168.0.3 public12345 snmp bgp
                """,
            ),
            dedent(
                f"""
                snmp-server host 192.168.0.1 public12345 snmp bgp
                snmp-server host 192.168.0.2 {settings.NO_VALUE} snmp bgp
                """,
            ),
            dedent(
                f"""
                snmp-server host 192.168.0.2 {settings.NO_VALUE} snmp bgp
                !
                no snmp-server host 192.168.0.2 public12345 snmp bgp
                !
                no snmp-server host 192.168.0.3 public12345 snmp bgp
                !
                """,
            ).strip(),
            dedent(
                """
                no snmp-server host 192.168.0.3 public12345 snmp bgp
                !
                """,
            ).strip(),
        ),
        (
            dedent(
                """
                enable secret some-secret-hash
                aaa group server tacacs+ TACACS-GROUP
                   server-private 1.2.3.4 key 7 secret-key
                   ip tacacs source-interface Loopback0
                """,
            ),
            dedent(
                f"""
                enable secret {settings.NO_VALUE}
                aaa group server tacacs+ TACACS-GROUP
                   server-private 1.2.3.4 key 7 {settings.NO_VALUE}
                   ip tacacs source-interface Loopback0
                """,
            ),
            dedent(
                f"""
                aaa group server tacacs+ TACACS-GROUP
                   no server-private 1.2.3.4 key 7 secret-key
                   server-private 1.2.3.4 key 7 {settings.NO_VALUE}
                !
                enable secret {settings.NO_VALUE}
                !
                no enable secret some-secret-hash
                !
                """,
            ).strip(),
            "",
        ),
    ],
)
def test_pp_arista_eos_no_value(
    current_config: str,
    target_config: str,
    raw_diff_config: str,
    pp_diff_config: str,
) -> None:
    parser = CTreeParser(platform=Platform.ARISTA_EOS)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    raw_diff = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert raw_diff.config == raw_diff_config

    pp_diff = CTreeDiffer.diff(current, target, post_proc_rules=[AristaEOSNoValue])
    assert pp_diff.config == pp_diff_config
