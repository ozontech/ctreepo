from textwrap import dedent

import pytest

from ctreepo.platforms.huawei_vrp import expand_vty


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        (
            dedent(
                """
                user-interface con 0
                 authentication-mode password
                 idle-timeout 30 0
                user-interface vty 0 2
                 authentication-mode aaa
                 idle-timeout 30 0
                user-interface vty 10
                 authentication-mode aaa
                 idle-timeout 60 0
                user-interface vty 16 18
                 authentication-mode aaa
                 idle-timeout 30 0
                #
                """,
            ).strip(),
            dedent(
                """
                user-interface con 0
                 authentication-mode password
                 idle-timeout 30 0
                user-interface vty 0
                 authentication-mode aaa
                 idle-timeout 30 0
                user-interface vty 1
                 authentication-mode aaa
                 idle-timeout 30 0
                user-interface vty 2
                 authentication-mode aaa
                 idle-timeout 30 0
                user-interface vty 10
                 authentication-mode aaa
                 idle-timeout 60 0
                user-interface vty 16
                 authentication-mode aaa
                 idle-timeout 30 0
                user-interface vty 17
                 authentication-mode aaa
                 idle-timeout 30 0
                user-interface vty 18
                 authentication-mode aaa
                 idle-timeout 30 0
                #
                """,
            ).strip(),
        ),
        (
            dedent(
                """
                user-interface vty 0 2
                 authentication-mode aaa
                 idle-timeout 30 0
                #
                """,
            ).strip(),
            dedent(
                """
                user-interface vty 0
                 authentication-mode aaa
                 idle-timeout 30 0
                user-interface vty 1
                 authentication-mode aaa
                 idle-timeout 30 0
                user-interface vty 2
                 authentication-mode aaa
                 idle-timeout 30 0
                #
                """,
            ).strip(),
        ),
        (
            dedent(
                """
                interface 25GE1/0/1
                 port link-type trunk
                #
                user-interface vty 0 2
                 authentication-mode aaa
                 idle-timeout 30 0
                #
                """,
            ).strip(),
            dedent(
                """
                interface 25GE1/0/1
                 port link-type trunk
                #
                user-interface vty 0
                 authentication-mode aaa
                 idle-timeout 30 0
                user-interface vty 1
                 authentication-mode aaa
                 idle-timeout 30 0
                user-interface vty 2
                 authentication-mode aaa
                 idle-timeout 30 0
                #
                """,
            ).strip(),
        ),
    ],
)
def test_huawei_vrp_expand_vty(config: str, expected: str) -> None:
    result = expand_vty(config)
    assert result == expected
