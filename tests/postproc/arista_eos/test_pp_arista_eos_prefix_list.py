from textwrap import dedent

import pytest

from ctreepo import CTreeDiffer, CTreeParser, Platform, settings
from ctreepo.postproc.arista_eos import AristaEOSPrefixList


@pytest.mark.parametrize(
    "current_config, target_config, raw_diff_config, pp_diff_config",
    [
        (
            dedent(
                """
                ip prefix-list TEST_PL_1 seq 10 permit 10.1.30.0/24 eq 32
                ip prefix-list TEST_PL_1 seq 20 permit 10.1.31.0/24 eq 32
                ip prefix-list TEST_PL_2 seq 10 permit 10.1.33.0/24
                """,
            ),
            dedent(
                """
                ip prefix-list TEST_PL_1 seq 10 permit 10.1.30.0/24 eq 32
                """,
            ),
            dedent(
                """
                no ip prefix-list TEST_PL_1 seq 20 permit 10.1.31.0/24 eq 32
                !
                no ip prefix-list TEST_PL_2 seq 10 permit 10.1.33.0/24
                !
                """,
            ).strip(),
            dedent(
                """
                no ip prefix-list TEST_PL_1 seq 20 permit 10.1.31.0/24 eq 32
                !
                no ip prefix-list TEST_PL_2 seq 10 permit 10.1.33.0/24
                !
                """,
            ).strip(),
        ),
        (
            dedent(
                """
                ip prefix-list TEST_PL_1 seq 10 permit 10.1.30.0/24 eq 32
                ip prefix-list TEST_PL_1 seq 20 permit 10.1.31.0/24 eq 32
                ip prefix-list TEST_PL_1 seq 30 permit 10.1.32.0/24 eq 32
                ip prefix-list TEST_PL_2 seq 10 permit 10.1.33.0/24
                ip prefix-list TEST_PL_3 seq 10 permit 10.1.34.0/24 ge 25 le 26
                """,
            ),
            dedent(
                """
                ip prefix-list TEST_PL_1 seq 10 permit 10.1.30.0/24 eq 32
                ip prefix-list TEST_PL_1 seq 20 permit 10.1.131.0/24 eq 32
                ip prefix-list TEST_PL_1 seq 30 permit 10.1.32.0/24 eq 32
                ip prefix-list TEST_PL_3 seq 10 permit 10.1.34.0/24 ge 25 le 26
                """,
            ),
            dedent(
                """
                ip prefix-list TEST_PL_1 seq 20 permit 10.1.131.0/24 eq 32
                !
                no ip prefix-list TEST_PL_1 seq 20 permit 10.1.31.0/24 eq 32
                !
                no ip prefix-list TEST_PL_2 seq 10 permit 10.1.33.0/24
                !
                """,
            ).strip(),
            dedent(
                """
                no ip prefix-list TEST_PL_1 seq 20 permit 10.1.31.0/24 eq 32
                !
                ip prefix-list TEST_PL_1 seq 20 permit 10.1.131.0/24 eq 32
                !
                no ip prefix-list TEST_PL_2 seq 10 permit 10.1.33.0/24
                !
                """,
            ).strip(),
        ),
        (
            dedent(
                """
                ip prefix-list TEST_PL_1 seq 10 permit 10.1.30.0/24 eq 32
                ip prefix-list TEST_PL_1 seq 20 permit 10.1.31.0/24 eq 32
                ip prefix-list TEST_PL_1 seq 30 permit 10.1.32.0/24 eq 32
                ip prefix-list TEST_PL_2 seq 10 permit 10.1.33.0/24
                ip prefix-list TEST_PL_3 seq 10 permit 10.1.34.0/24 ge 25 le 26
                """,
            ),
            dedent(
                """
                ip prefix-list TEST_PL_1 seq 10 permit 10.1.130.0/24 eq 32
                ip prefix-list TEST_PL_1 seq 20 permit 10.1.31.0/24 eq 32
                ip prefix-list TEST_PL_1 seq 30 permit 10.1.32.0/24 eq 32
                ip prefix-list TEST_PL_2 seq 10 permit 10.1.133.0/24
                ip prefix-list TEST_PL_3 seq 10 permit 10.1.34.0/24 ge 25 le 26
                """,
            ),
            dedent(
                """
                ip prefix-list TEST_PL_1 seq 10 permit 10.1.130.0/24 eq 32
                !
                ip prefix-list TEST_PL_2 seq 10 permit 10.1.133.0/24
                !
                no ip prefix-list TEST_PL_1 seq 10 permit 10.1.30.0/24 eq 32
                !
                no ip prefix-list TEST_PL_2 seq 10 permit 10.1.33.0/24
                !
                """,
            ).strip(),
            dedent(
                """
                no ip prefix-list TEST_PL_1 seq 10 permit 10.1.30.0/24 eq 32
                !
                ip prefix-list TEST_PL_1 seq 10 permit 10.1.130.0/24 eq 32
                !
                no ip prefix-list TEST_PL_2 seq 10 permit 10.1.33.0/24
                !
                ip prefix-list TEST_PL_2 seq 10 permit 10.1.133.0/24
                !
                """,
            ).strip(),
        ),
        (
            dedent(
                """
                ip prefix-list TEST_PL_1 seq 10 permit 10.1.30.0/24 eq 32
                ip prefix-list TEST_PL_1 seq 20 permit 10.1.31.0/24 eq 32
                ip prefix-list TEST_PL_1 seq 30 permit 10.1.32.0/24 eq 32
                ip prefix-list TEST_PL_2 seq 10 permit 10.1.33.0/24
                """,
            ),
            dedent(
                """
                ip prefix-list TEST_PL_1 seq 10 permit 10.1.30.0/24 eq 32
                ip prefix-list TEST_PL_1 seq 20 permit 10.1.131.0/24 eq 32
                ip prefix-list TEST_PL_2 seq 10 permit 10.1.33.0/24
                """,
            ),
            dedent(
                """
                ip prefix-list TEST_PL_1 seq 20 permit 10.1.131.0/24 eq 32
                !
                no ip prefix-list TEST_PL_1 seq 20 permit 10.1.31.0/24 eq 32
                !
                no ip prefix-list TEST_PL_1 seq 30 permit 10.1.32.0/24 eq 32
                !
                """,
            ).strip(),
            dedent(
                """
                no ip prefix-list TEST_PL_1 seq 20 permit 10.1.31.0/24 eq 32
                !
                ip prefix-list TEST_PL_1 seq 20 permit 10.1.131.0/24 eq 32
                !
                no ip prefix-list TEST_PL_1 seq 30 permit 10.1.32.0/24 eq 32
                !
                """,
            ).strip(),
        ),
    ],
)
def test_pp_arista_eos_prefix_list(
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
    for node in raw_diff.children.values():
        if node.line.startswith(node.undo):
            assert settings.TAG_ON_UNDO in node.tags
        else:
            assert settings.TAG_ON_UNDO not in node.tags

    pp_diff = CTreeDiffer.diff(current, target, post_proc_rules=[AristaEOSPrefixList])
    assert pp_diff.config == pp_diff_config
    for node in pp_diff.children.values():
        assert settings.TAG_ON_UNDO not in node.tags
