from textwrap import dedent

import pytest

from ctreepo import TEMPLATES, CTreeDiffer, CTreeParser, Platform, settings


@pytest.mark.parametrize(
    "current_config, target_config, diff_config",
    [
        # пароль не меняется
        (
            dedent(
                """
                hwtacacs-server template tacacs_group
                 hwtacacs-server authentication 10.0.0.1 vpn-instance MGMT
                 hwtacacs-server authentication 10.0.0.2 vpn-instance MGMT secondary
                 hwtacacs-server authentication 10.0.0.3 vpn-instance MGMT third
                 hwtacacs-server shared-key cipher old_secret_hash
                #
                """,
            ),
            dedent(
                f"""
                hwtacacs-server template tacacs_group
                 hwtacacs-server authentication 10.0.0.1 vpn-instance MGMT
                 hwtacacs-server authentication 10.0.0.2 vpn-instance MGMT secondary
                 hwtacacs-server authentication 10.0.0.3 vpn-instance MGMT third
                 hwtacacs-server shared-key cipher {settings.NO_VALUE}
                #
                """,
            ),
            dedent("").strip(),
        ),
        # пароль меняется
        (
            dedent(
                """
                hwtacacs-server template tacacs_group
                 hwtacacs-server authentication 10.0.0.1 vpn-instance MGMT
                 hwtacacs-server authentication 10.0.0.2 vpn-instance MGMT secondary
                 hwtacacs-server authentication 10.0.0.3 vpn-instance MGMT third
                 hwtacacs-server shared-key cipher old_secret_hash
                #
                """,
            ),
            dedent(
                """
                hwtacacs-server template tacacs_group
                 hwtacacs-server authentication 10.0.0.1 vpn-instance MGMT
                 hwtacacs-server authentication 10.0.0.2 vpn-instance MGMT secondary
                 hwtacacs-server authentication 10.0.0.3 vpn-instance MGMT third
                 hwtacacs-server shared-key cipher new_secret_hash
                #
                """,
            ),
            dedent(
                """
                hwtacacs-server template tacacs_group
                 hwtacacs-server shared-key cipher new_secret_hash
                #
                """,
            ).strip(),
        ),
        # пароль удаляется
        (
            dedent(
                """
                hwtacacs-server template tacacs_group
                 hwtacacs-server authentication 10.0.0.1 vpn-instance MGMT
                 hwtacacs-server authentication 10.0.0.2 vpn-instance MGMT secondary
                 hwtacacs-server authentication 10.0.0.3 vpn-instance MGMT third
                 hwtacacs-server shared-key cipher old_secret_hash
                #
                """,
            ),
            dedent(
                """
                hwtacacs-server template tacacs_group
                 hwtacacs-server authentication 10.0.0.1 vpn-instance MGMT
                 hwtacacs-server authentication 10.0.0.2 vpn-instance MGMT secondary
                 hwtacacs-server authentication 10.0.0.3 vpn-instance MGMT third
                #
                """,
            ),
            dedent(
                """
                hwtacacs-server template tacacs_group
                 undo hwtacacs-server shared-key
                #
                """,
            ).strip(),
        ),
    ],
)
def test_case_huawei_vrp_tacacs_password(
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
