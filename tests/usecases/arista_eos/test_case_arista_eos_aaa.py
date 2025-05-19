from textwrap import dedent

import pytest

from ctreepo import TEMPLATES, CTreeDiffer, CTreeParser, Platform

# AAA_MASK = """
# aaa authentication (?:login|enable) (?P<METHOD>.*)
# """


@pytest.mark.parametrize(
    "current_config, target_config, diff_config",
    [
        (
            dedent(
                """
                aaa authentication login default group group1 local
                aaa authentication login console local
                aaa authentication enable default none
                aaa authentication policy on-success log
                """,
            ),
            dedent(
                """
                aaa authentication login default group group2 local
                aaa authentication login console none
                aaa authentication enable default none
                """,
            ),
            dedent(
                """
                aaa authentication login default group group2 local
                !
                aaa authentication login console none
                !
                no aaa authentication policy on-success log
                !
                """,
            ).strip(),
        ),
    ],
)
def test_case_arista_eos_aaa(
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
