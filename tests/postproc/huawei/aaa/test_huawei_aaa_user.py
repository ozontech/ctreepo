from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Vendor


def test_huawei_aaa_user_case_1() -> None:
    # случай 1: не меняем пароль для пользователей user1/user2, состав пользователей совпадает
    target_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
        #
        """
    ).strip()
    current_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher some_password_hash_1
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher some_password_hash_2
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
        #
        """
    ).strip()
    diff_config_raw = dedent(
        """
        aaa
         undo local-user user1@default password irreversible-cipher some_password_hash_1
         undo local-user user2@default password irreversible-cipher some_password_hash_2
         local-user user1@default password irreversible-cipher
         local-user user2@default password irreversible-cipher
        #
        """
    ).strip()
    diff_config_processed = ""
    parser = CTreeParser(Vendor.HUAWEI)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw

    diff_processed = CTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed


def test_huawei_aaa_user_case_2() -> None:
    # случай 2: меняем пароль для user1, не меняем для user2, состав пользователей совпадает
    target_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
        #
        """
    ).strip()
    current_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher some_password_hash_1
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher some_password_hash_2
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
        #
        """
    ).strip()
    diff_config_raw = dedent(
        """
        aaa
         undo local-user user1@default password irreversible-cipher some_password_hash_1
         undo local-user user2@default password irreversible-cipher some_password_hash_2
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user2@default password irreversible-cipher
        #
        """
    ).strip()
    diff_config_processed = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher P@ssw0rd
        #
        """
    ).strip()
    parser = CTreeParser(Vendor.HUAWEI)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw

    diff_processed = CTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed


def test_huawei_aaa_user_case_3() -> None:
    # случай 3: меняем пароль для user1, не меняем для user2, на устройстве лишний пользователь
    target_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
        #
        """
    ).strip()
    current_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher some_password_hash_1
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher some_password_hash_2
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
         local-user user3@default password irreversible-cipher some_password_hash_3
         local-user user3@default service-type terminal ssh
         local-user user3@default level 3
        #
        """
    ).strip()
    diff_config_raw = dedent(
        """
        aaa
         undo local-user user1@default password irreversible-cipher some_password_hash_1
         undo local-user user2@default password irreversible-cipher some_password_hash_2
         undo local-user user3@default password irreversible-cipher some_password_hash_3
         undo local-user user3@default service-type terminal ssh
         undo local-user user3@default level 3
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user2@default password irreversible-cipher
        #
        """
    ).strip()
    diff_config_processed = dedent(
        """
        aaa
         undo local-user user3@default
         local-user user1@default password irreversible-cipher P@ssw0rd
        #
        """
    ).strip()

    parser = CTreeParser(Vendor.HUAWEI)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw

    diff_processed = CTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed


def test_huawei_aaa_user_case_4() -> None:
    # случай 4: меняем пароль для user1, не меняем для user2, на устройстве не хватает пользователя и один лишний
    target_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
         local-user user4@default password irreversible-cipher P@ssw0rd
         local-user user4@default service-type terminal ssh
         local-user user4@default level 3
        #
        """
    ).strip()
    current_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher some_password_hash_1
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher some_password_hash_2
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
         local-user user3@default password irreversible-cipher some_password_hash_3
         local-user user3@default service-type terminal ssh
         local-user user3@default level 3
        #
        """
    ).strip()
    diff_config_raw = dedent(
        """
        aaa
         undo local-user user1@default password irreversible-cipher some_password_hash_1
         undo local-user user2@default password irreversible-cipher some_password_hash_2
         undo local-user user3@default password irreversible-cipher some_password_hash_3
         undo local-user user3@default service-type terminal ssh
         undo local-user user3@default level 3
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user2@default password irreversible-cipher
         local-user user4@default password irreversible-cipher P@ssw0rd
         local-user user4@default service-type terminal ssh
         local-user user4@default level 3
        #
        """
    ).strip()
    diff_config_processed = dedent(
        """
        aaa
         undo local-user user3@default
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user4@default password irreversible-cipher P@ssw0rd
         local-user user4@default service-type terminal ssh
         local-user user4@default level 3
        #
        """
    ).strip()

    parser = CTreeParser(Vendor.HUAWEI)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw

    diff_processed = CTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed


def test_huawei_aaa_user_case_5() -> None:
    # случай 5: меняем пароль для user1, не меняем для user2, меняем level для user2
    target_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher
         local-user user2@default service-type terminal ssh
         local-user user2@default level 1
        #
        """
    ).strip()
    current_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher some_password_hash_1
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher some_password_hash_2
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
        #
        """
    ).strip()
    diff_config_raw = dedent(
        """
        aaa
         undo local-user user1@default password irreversible-cipher some_password_hash_1
         undo local-user user2@default password irreversible-cipher some_password_hash_2
         undo local-user user2@default level 3
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user2@default password irreversible-cipher
         local-user user2@default level 1
        #
        """
    ).strip()
    diff_config_processed = dedent(
        """
        aaa
         undo local-user user2@default level
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user2@default level 1
        #
        """
    ).strip()

    parser = CTreeParser(Vendor.HUAWEI)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw

    diff_processed = CTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed


def test_huawei_aaa_user_case_6() -> None:
    # случай 6:
    # - user1 нет в системе, а в целевом конфиге нет пароля
    # - user2 есть в системе и в целевом конфиге есть пароль
    # - user3 есть в системе, а в целевом конфиге нет пароля
    target_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher P@ssw0rd
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
         local-user user3@default password irreversible-cipher
         local-user user3@default service-type terminal ssh
         local-user user3@default level 1
        #
        """
    ).strip()
    current_config = dedent(
        """
        aaa
         local-user user2@default password irreversible-cipher some_password_hash_2
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
         local-user user3@default password irreversible-cipher some_password_hash_3
         local-user user3@default service-type terminal ssh
         local-user user3@default level 3
        #
        """
    ).strip()
    diff_config_raw = dedent(
        """
        aaa
         undo local-user user2@default password irreversible-cipher some_password_hash_2
         undo local-user user3@default password irreversible-cipher some_password_hash_3
         undo local-user user3@default level 3
         local-user user1@default password irreversible-cipher
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher P@ssw0rd
         local-user user3@default password irreversible-cipher
         local-user user3@default level 1
        #
        """
    ).strip()
    diff_config_processed = dedent(
        """
        aaa
         undo local-user user3@default level
         local-user user2@default password irreversible-cipher P@ssw0rd
         local-user user3@default level 1
        #
        """
    ).strip()

    parser = CTreeParser(Vendor.HUAWEI)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw

    diff_processed = CTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed
