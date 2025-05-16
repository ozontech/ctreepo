from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Platform


def test_huawei_interface_lag_members_case_1() -> None:
    """Объединение в lag.

    сначала удалить подынтерфейсы, затем объединять в lag.
    """
    current_config = dedent(
        """
        interface GigabitEthernet0/0/1.100
         description sub-eth-interface-100
        interface GigabitEthernet0/0/1
         description eth-interface
        interface GigabitEthernet0/0/1.200
         description sub-eth-interface-200
        #
        """,
    ).strip()
    target_config = dedent(
        """
        interface Eth-Trunk1
         description lag-interface
        interface GigabitEthernet0/0/1
         description eth-interface
         eth-trunk 1
        #
        """,
    ).strip()
    diff_config = dedent(
        """
        interface Eth-Trunk1
         description lag-interface
        #
        undo interface GigabitEthernet0/0/1.100
        #
        undo interface GigabitEthernet0/0/1.200
        #
        interface GigabitEthernet0/0/1
         eth-trunk 1
        #
        """,
    ).strip()
    diff_config_raw = dedent(
        """
        interface Eth-Trunk1
         description lag-interface
        #
        interface GigabitEthernet0/0/1
         eth-trunk 1
        #
        undo interface GigabitEthernet0/0/1.100
        #
        undo interface GigabitEthernet0/0/1.200
        #
        """,
    ).strip()

    parser = CTreeParser(Platform.HUAWEI_VRP)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff.config == diff_config_raw

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config


def test_huawei_interface_lag_members_case_2() -> None:
    """Сначала снять undo команды, а затем переключать в portswitch режим."""
    current_config = dedent(
        """
        interface 10GE1/0/1
         description interface under test
         undo portswitch
         mtu 9198
        #
        """,
    )
    target_config = dedent(
        """
        interface 10GE1/0/1
         description interface under test
         eth-trunk 1
        #
        """,
    )
    diff_raw = dedent(
        """
        interface 10GE1/0/1
         portswitch
         undo mtu 9198
         eth-trunk 1
        #
        """,
    ).strip()
    diff_processed = dedent(
        """
        interface 10GE1/0/1
         undo mtu
         portswitch
         eth-trunk 1
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


def test_huawei_interface_lag_tags() -> None:
    """изменение тегов при разборе lag."""
    current_config = dedent(
        """
        interface GigabitEthernet0/0/1
         eth-trunk 1
         storm suppression multicast packets 1
        #
        """,
    ).strip()
    target_config = dedent(
        """
        interface GigabitEthernet0/0/1
         description test
        #
        """,
    ).strip()
    diff_config = dedent(
        """
        interface GigabitEthernet0/0/1
         undo eth-trunk 1
         undo storm suppression multicast packets 1
         description test
        #
        """,
    ).strip()

    parser = CTreeParser(Platform.HUAWEI_VRP)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config

    node = diff.children["interface GigabitEthernet0/0/1"]
    assert "pre" in node.children["undo eth-trunk 1"].tags
    assert "pre" in node.children["undo storm suppression multicast packets 1"].tags
