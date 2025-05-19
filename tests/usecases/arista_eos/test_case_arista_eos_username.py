from textwrap import dedent

import pytest

from ctreepo import TEMPLATES, CTreeDiffer, CTreeParser, Platform, settings


@pytest.mark.parametrize(
    "current_config, target_config, diff_config",
    [
        # не меняем пароль для пользователей user1/user2, состав пользователей совпадает
        (
            dedent(
                """
                username user1 privilege 15 role network-admin secret sha512 old_hash_1
                username user2 privilege 15 role network-admin secret sha512 old_hash_2
                """,
            ),
            dedent(
                f"""
                username user1 privilege 15 role network-admin secret {settings.NO_VALUE}
                username user2 privilege 15 role network-admin secret {settings.NO_VALUE}
                """,
            ),
            dedent("").strip(),
        ),
        # меняем пароль для user1, не меняем для user2, состав пользователей совпадает
        (
            dedent(
                """
                username user1 privilege 15 role network-admin secret sha512 old_hash_1
                username user2 privilege 15 role network-admin secret sha512 old_hash_2
                """,
            ),
            dedent(
                f"""
                username user1 privilege 15 role network-admin secret new_password_1
                username user2 privilege 15 role network-admin secret {settings.NO_VALUE}
                """,
            ),
            dedent(
                """
                username user1 privilege 15 role network-admin secret new_password_1
                !
                """,
            ).strip(),
        ),
        # меняем пароль для user1, не меняем для user2, на устройстве лишний пользователь
        (
            dedent(
                """
                username user1 privilege 15 role network-admin secret sha512 old_hash_1
                username user2 privilege 15 role network-admin secret sha512 old_hash_2
                username user3 privilege 15 role network-admin secret sha512 old_hash_3
                """,
            ),
            dedent(
                f"""
                username user1 privilege 15 role network-admin secret new_password_1
                username user2 privilege 15 role network-admin secret {settings.NO_VALUE}
                """,
            ),
            dedent(
                """
                username user1 privilege 15 role network-admin secret new_password_1
                !
                no username user3
                !
                """,
            ).strip(),
        ),
        # меняем пароль для user1, не меняем для user2, на устройстве не хватает пользователя и один лишний
        (
            dedent(
                """
                username user1 privilege 15 role network-admin secret sha512 old_hash_1
                username user2 privilege 15 role network-admin secret sha512 old_hash_2
                username user3 privilege 15 role network-admin secret sha512 old_hash_3
                """,
            ),
            dedent(
                f"""
                username user1 privilege 15 role network-admin secret new_password_1
                username user2 privilege 15 role network-admin secret {settings.NO_VALUE}
                username user4 privilege 15 role network-admin secret new_password_4
                """,
            ),
            dedent(
                """
                username user1 privilege 15 role network-admin secret new_password_1
                !
                username user4 privilege 15 role network-admin secret new_password_4
                !
                no username user3
                !
                """,
            ).strip(),
        ),
    ],
)
def test_case_arista_eos_username(current_config: str, target_config: str, diff_config: str) -> None:
    platform = Platform.ARISTA_EOS

    parser = CTreeParser(platform)
    template = parser.parse(TEMPLATES.get(platform, ""))
    current = parser.parse(current_config, template=template)
    target = parser.parse(target_config, template=template)

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
