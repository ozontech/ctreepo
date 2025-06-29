from textwrap import dedent

import pytest

from ctreepo import TEMPLATES, CTreeDiffer, CTreeParser, Platform, settings


@pytest.mark.parametrize(
    "current_config, target_config, diff_config",
    [
        # удаление записей
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
                no ip prefix-list TEST_PL_1 seq 20
                !
                no ip prefix-list TEST_PL_2 seq 10
                !
                """,
            ).strip(),
        ),
        # изменение одной записи
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
                no ip prefix-list TEST_PL_1 seq 20
                !
                ip prefix-list TEST_PL_1 seq 20 permit 10.1.131.0/24 eq 32
                !
                no ip prefix-list TEST_PL_2 seq 10
                !
                """,
            ).strip(),
        ),
        # изменение нескольких записей
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
                no ip prefix-list TEST_PL_1 seq 10
                !
                ip prefix-list TEST_PL_1 seq 10 permit 10.1.130.0/24 eq 32
                !
                no ip prefix-list TEST_PL_2 seq 10
                !
                ip prefix-list TEST_PL_2 seq 10 permit 10.1.133.0/24
                !
                """,
            ).strip(),
        ),
    ],
)
def test_case_arista_eos_prefix_list(
    current_config: str,
    target_config: str,
    diff_config: str,
) -> None:
    platform = Platform.ARISTA_EOS

    parser = CTreeParser(platform=platform)
    template = parser.parse(TEMPLATES.get(platform, ""))
    current = parser.parse(current_config, template=template)
    target = parser.parse(target_config, template=template)

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
    for node in diff.children.values():
        assert settings.TAG_ON_UNDO not in node.tags
