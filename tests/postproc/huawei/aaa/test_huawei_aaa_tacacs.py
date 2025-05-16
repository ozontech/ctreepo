from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Platform


def test_huawei_aaa_tacacs_case_1() -> None:
    """Если пароль пустой (не меняется), то undo и узел с пустым паролем нужно удалить."""
    current_config = dedent(
        """
        hwtacacs-server template group-name
         hwtacacs-server authentication 10.0.0.1 vpn-instance MGMT
         hwtacacs-server authentication 10.0.0.2 vpn-instance MGMT secondary
         hwtacacs-server authentication 10.0.0.3 vpn-instance MGMT third
         undo hwtacacs-server user-name domain-included
         hwtacacs-server shared-key cipher old_secret_hash
        #
        """,
    )
    target_config = dedent(
        """
        hwtacacs-server template group-name
         hwtacacs-server authentication 10.0.0.1 vpn-instance MGMT
         hwtacacs-server authentication 10.0.0.2 vpn-instance MGMT secondary
         hwtacacs-server authentication 10.0.0.3 vpn-instance MGMT third
         undo hwtacacs-server user-name domain-included
         hwtacacs-server shared-key cipher
        #
        """,
    )
    diff_raw = dedent(
        """
        hwtacacs-server template group-name
         undo hwtacacs-server shared-key cipher old_secret_hash
         hwtacacs-server shared-key cipher
        #
        """,
    ).strip()
    diff_processed = ""

    parser = CTreeParser(Platform.HUAWEI_VRP)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff.config == diff_raw

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_processed


def test_huawei_aaa_tacacs_case_2() -> None:
    """Изменение пароля без undo команды, новый пароль перепишет старый.

    Это через маску так же можно сделать, но осталось как legacy.
    """
    current_config = dedent(
        """
        hwtacacs-server template group-name
         hwtacacs-server authentication 10.0.0.1 vpn-instance MGMT
         hwtacacs-server authentication 10.0.0.2 vpn-instance MGMT secondary
         hwtacacs-server authentication 10.0.0.3 vpn-instance MGMT third
         undo hwtacacs-server user-name domain-included
         hwtacacs-server shared-key cipher old_secret_hash
        #
        """,
    )
    target_config = dedent(
        """
        hwtacacs-server template group-name
         hwtacacs-server authentication 10.0.0.1 vpn-instance MGMT
         hwtacacs-server authentication 10.0.0.2 vpn-instance MGMT secondary
         hwtacacs-server authentication 10.0.0.3 vpn-instance MGMT third
         undo hwtacacs-server user-name domain-included
         hwtacacs-server shared-key cipher new_secret_hash
        #
        """,
    )
    diff_raw = dedent(
        """
        hwtacacs-server template group-name
         undo hwtacacs-server shared-key cipher old_secret_hash
         hwtacacs-server shared-key cipher new_secret_hash
        #
        """,
    ).strip()
    diff_processed = dedent(
        """
        hwtacacs-server template group-name
         hwtacacs-server shared-key cipher new_secret_hash
        #
        """,
    ).strip()

    parser = CTreeParser(Platform.HUAWEI_VRP)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff.config == diff_raw

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_processed
