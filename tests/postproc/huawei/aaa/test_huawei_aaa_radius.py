from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Platform


def test_huawei_aaa_radius_case_1() -> None:
    # базовый сценарий замены пароля, undo убирается за счет маски
    current_config = dedent(
        """
        radius-server template my-radius-template
         radius-server shared-key cipher some-secret-hash-old
         radius-server accounting 1.2.3.4 1813 source Vlanif 123 weight 123
        #
        """,
    )
    target_config = dedent(
        """
        radius-server template my-radius-template
         radius-server shared-key cipher some-secret-hash-new
         radius-server accounting 1.2.3.4 1813 source Vlanif 123 weight 123
        #
        """,
    )
    diff_config = dedent(
        """
        radius-server template my-radius-template
         radius-server shared-key cipher some-secret-hash-new
        #
        """,
    ).strip()
    mask = dedent(
        """
        radius-server template \\S+
         radius-server shared-key cipher (?P<HASH>\\S+)
        #
        """,
    )
    parser = CTreeParser(Platform.HUAWEI_VRP)
    template = parser.parse(mask)
    current = parser.parse(current_config, template)
    target = parser.parse(target_config, template)
    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config


def test_huawei_aaa_radius_case_2() -> None:
    # сценарий замены пароля, но без маски. кроме всего у undo не должно быть хеша
    current_config = dedent(
        """
        radius-server template my-radius-template
         radius-server shared-key cipher some-secret-hash-old
         radius-server accounting 1.2.3.4 1813 source Vlanif 123 weight 123
        #
        """,
    )
    target_config = dedent(
        """
        radius-server template my-radius-template
         radius-server shared-key cipher some-secret-hash-new
         radius-server accounting 1.2.3.4 1813 source Vlanif 123 weight 123
        #
        """,
    )
    diff_config = dedent(
        """
        radius-server template my-radius-template
         undo radius-server shared-key
         radius-server shared-key cipher some-secret-hash-new
        #
        """,
    ).strip()

    parser = CTreeParser(Platform.HUAWEI_VRP)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config


def test_huawei_aaa_radius_case_3() -> None:
    # сценарий удаления пароля
    current_config = dedent(
        """
        radius-server template my-radius-template
         radius-server shared-key cipher some-secret-hash-old
         radius-server accounting 1.2.3.4 1813 source Vlanif 123 weight 123
        #
        """,
    )
    target_config = dedent(
        """
        radius-server template my-radius-template
         radius-server accounting 1.2.3.4 1813 source Vlanif 123 weight 123
        #
        """,
    )
    diff_config = dedent(
        """
        radius-server template my-radius-template
         undo radius-server shared-key
        #
        """,
    ).strip()

    parser = CTreeParser(Platform.HUAWEI_VRP)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config


def test_huawei_aaa_radius_case_4() -> None:
    # если пароль не меняем
    current_config = dedent(
        """
        radius-server template my-radius-template
         radius-server shared-key cipher some-secret-hash-old
         radius-server accounting 1.2.3.4 1813 source Vlanif 123 weight 123
        #
        """,
    )
    target_config = dedent(
        """
        radius-server template my-radius-template
         radius-server shared-key cipher
         radius-server accounting 1.2.3.4 1813 source Vlanif 123 weight 123
        #
        """,
    )
    diff_config = ""

    parser = CTreeParser(Platform.HUAWEI_VRP)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
