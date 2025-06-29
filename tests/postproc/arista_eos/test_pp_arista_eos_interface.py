from textwrap import dedent

import pytest

from ctreepo import CTreeDiffer, CTreeParser, Platform
from ctreepo.postproc.arista_eos import AristaEOSInterface


@pytest.mark.parametrize(
    "current_config, target_config, raw_diff_config, pp_diff_config",
    [
        # базовый тест
        (
            dedent(
                """
                interface Ethernet1
                   description test
                   ip address 192.168.0.1/24
                """,
            ),
            dedent(
                """
                interface Ethernet1
                   description test
                   ip address 192.168.2.1/24 secondary
                   ip address 192.168.1.1/24
                """,
            ),
            dedent(
                """
                interface Ethernet1
                   no ip address 192.168.0.1/24
                   ip address 192.168.2.1/24 secondary
                   ip address 192.168.1.1/24
                !
                """,
            ).strip(),
            dedent(
                """
                interface Ethernet1
                   no ip address 192.168.0.1/24
                   ip address 192.168.1.1/24
                   ip address 192.168.2.1/24 secondary
                !
                """,
            ).strip(),
        ),
    ],
)
def test_pp_arista_eos_interface(
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

    pp_diff = CTreeDiffer.diff(current, target, post_proc_rules=[AristaEOSInterface])
    assert pp_diff.config == pp_diff_config
