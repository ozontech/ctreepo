from textwrap import dedent

import pytest

from ctreepo import TEMPLATES, CTreeDiffer, CTreeParser, Platform, settings


@pytest.mark.parametrize(
    "current_config, target_config, diff_config",
    [
        # не меняем пароли для пользователей user1/user2, состав пользователей совпадает
        (
            dedent(
                """
                aaa
                 local-user user1@default password irreversible-cipher old_password_hash_1
                 local-user user1@default service-type terminal ssh
                 local-user user1@default level 3
                 local-user user2@default password irreversible-cipher old_password_hash_2
                 local-user user2@default service-type terminal ssh
                 local-user user2@default level 3
                #
                """,
            ),
            dedent(
                f"""
                aaa
                 local-user user1@default password irreversible-cipher {settings.NO_VALUE}
                 local-user user1@default service-type terminal ssh
                 local-user user1@default level 3
                 local-user user2@default password irreversible-cipher {settings.NO_VALUE}
                 local-user user2@default service-type terminal ssh
                 local-user user2@default level 3
                #
                """,
            ),
            dedent("").strip(),
        ),
        # меняем пароль для user1, не меняем для user2, состав пользователей совпадает
        (
            dedent(
                """
                aaa
                 local-user user1@default password irreversible-cipher old_password_hash_1
                 local-user user1@default service-type terminal ssh
                 local-user user1@default level 3
                 local-user user2@default password irreversible-cipher old_password_hash_2
                 local-user user2@default service-type terminal ssh
                 local-user user2@default level 3
                #
                """,
            ),
            dedent(
                f"""
                aaa
                 local-user user1@default password irreversible-cipher new_password_hash_1
                 local-user user1@default service-type terminal ssh
                 local-user user1@default level 3
                 local-user user2@default password irreversible-cipher {settings.NO_VALUE}
                 local-user user2@default service-type terminal ssh
                 local-user user2@default level 3
                #
                """,
            ),
            dedent(
                """
                aaa
                 local-user user1@default password irreversible-cipher new_password_hash_1
                #
                """,
            ).strip(),
        ),
        # меняем пароль для user1, не меняем для user2, на устройстве лишний пользователь
        (
            dedent(
                """
                aaa
                 local-user user1@default password irreversible-cipher old_password_hash_1
                 local-user user1@default service-type terminal ssh
                 local-user user1@default level 3
                 local-user user2@default password irreversible-cipher old_password_hash_2
                 local-user user2@default service-type terminal ssh
                 local-user user2@default level 3
                 local-user user3@default password irreversible-cipher old_password_hash_3
                 local-user user3@default service-type terminal ssh
                 local-user user3@default level 3
                #
                """,
            ),
            dedent(
                f"""
                aaa
                 local-user user1@default password irreversible-cipher new_password_hash_1
                 local-user user1@default service-type terminal ssh
                 local-user user1@default level 3
                 local-user user2@default password irreversible-cipher {settings.NO_VALUE}
                 local-user user2@default service-type terminal ssh
                 local-user user2@default level 3
                #
                """,
            ),
            dedent(
                """
                aaa
                 undo local-user user3@default
                 local-user user1@default password irreversible-cipher new_password_hash_1
                #
                """,
            ).strip(),
        ),
        # меняем пароль для user1, не меняем для user2, на устройстве не хватает пользователя и один лишний
        (
            dedent(
                """
                aaa
                 local-user user1@default password irreversible-cipher old_password_hash_1
                 local-user user1@default service-type terminal ssh
                 local-user user1@default level 3
                 local-user user2@default password irreversible-cipher old_password_hash_2
                 local-user user2@default service-type terminal ssh
                 local-user user2@default level 3
                 local-user user4@default password irreversible-cipher old_password_hash_4
                 local-user user4@default service-type terminal ssh
                 local-user user4@default level 3
                #
                """,
            ),
            dedent(
                f"""
                aaa
                 local-user user1@default password irreversible-cipher new_password_hash_1
                 local-user user1@default service-type terminal ssh
                 local-user user1@default level 3
                 local-user user2@default password irreversible-cipher {settings.NO_VALUE}
                 local-user user2@default service-type terminal ssh
                 local-user user2@default level 3
                 local-user user3@default password irreversible-cipher new_password_hash_3
                 local-user user3@default service-type terminal ssh
                 local-user user3@default level 3
                #
                """,
            ),
            dedent(
                """
                aaa
                 undo local-user user4@default
                 local-user user1@default password irreversible-cipher new_password_hash_1
                 local-user user3@default password irreversible-cipher new_password_hash_3
                 local-user user3@default service-type terminal ssh
                 local-user user3@default level 3
                #
                """,
            ).strip(),
        ),
        # меняем пароль для user1, не меняем для user2, меняем level для user2
        (
            dedent(
                """
                aaa
                 local-user user1@default password irreversible-cipher old_password_hash_1
                 local-user user1@default service-type terminal ssh
                 local-user user1@default level 3
                 local-user user2@default password irreversible-cipher old_password_hash_2
                 local-user user2@default service-type terminal ssh
                 local-user user2@default level 3
                #
                """,
            ),
            dedent(
                f"""
                aaa
                 local-user user1@default password irreversible-cipher new_password_hash_1
                 local-user user1@default service-type terminal ssh
                 local-user user1@default level 3
                 local-user user2@default password irreversible-cipher {settings.NO_VALUE}
                 local-user user2@default service-type terminal ssh
                 local-user user2@default level 2
                #
                """,
            ),
            dedent(
                """
                aaa
                 local-user user1@default password irreversible-cipher new_password_hash_1
                 local-user user2@default level 2
                #
                """,
            ).strip(),
        ),
    ],
)
def test_case_huawei_vrp_aaa_localuser(
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
