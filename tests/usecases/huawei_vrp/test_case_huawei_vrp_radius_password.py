from textwrap import dedent

import pytest

from ctreepo import TEMPLATES, CTreeDiffer, CTreeParser, Platform, settings


@pytest.mark.parametrize(
    ("current_config", "target_config", "diff_config"),
    [
        # пароль не меняется
        (
            dedent(
                """
                radius-server template my_radius_template
                 radius-server shared-key cipher old_hash_1
                 radius-server accounting 1.2.3.4 1813 source Vlanif 123 weight 123
                #
                """,
            ),
            dedent(
                f"""
                radius-server template my_radius_template
                 radius-server shared-key cipher {settings.NO_VALUE}
                 radius-server accounting 1.2.3.4 1813 source Vlanif 123 weight 123
                #
                """,
            ),
            dedent("").strip(),
        ),
        # пароль меняется
        (
            dedent(
                """
                radius-server template my_radius_template
                 radius-server shared-key cipher old_hash_1
                 radius-server accounting 1.2.3.4 1813 source Vlanif 123 weight 123
                #
                """,
            ),
            dedent(
                """
                radius-server template my_radius_template
                 radius-server shared-key cipher new_hash_1
                 radius-server accounting 1.2.3.4 1813 source Vlanif 123 weight 123
                #
                """,
            ),
            dedent(
                """
                radius-server template my_radius_template
                 radius-server shared-key cipher new_hash_1
                #
                """,
            ).strip(),
        ),
        # пароль удаляется
        (
            dedent(
                """
                radius-server template my_radius_template
                 radius-server shared-key cipher old_hash_1
                 radius-server accounting 1.2.3.4 1813 source Vlanif 123 weight 123
                #
                """,
            ),
            dedent(
                """
                radius-server template my_radius_template
                 radius-server accounting 1.2.3.4 1813 source Vlanif 123 weight 123
                #
                """,
            ),
            dedent(
                """
                radius-server template my_radius_template
                 undo radius-server shared-key
                #
                """,
            ).strip(),
        ),
    ],
)
def test_case_huawei_vrp_radius_password(
    current_config: str,
    target_config: str,
    diff_config: str,
) -> None:
    platform = Platform.HUAWEI_VRP

    parser = CTreeParser(platform=platform)
    template = parser.parse(TEMPLATES.get(platform, ""))
    current = parser.parse(current_config, template=template)
    target = parser.parse(target_config, template=template)

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
