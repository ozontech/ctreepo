from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, CTreeSearcher, Platform


def test_huawei_interface_speed_mode_case_1() -> None:
    current_config = dedent(
        """
        interface 25GE1/0/1
         description interface under test
         mtu 9198
        #
        """,
    )
    target_config = dedent(
        """
        interface 25GE1/0/1
         description new
         port mode 10G
         mtu 9198
        #
        """,
    )
    diff_raw = dedent(
        """
        interface 25GE1/0/1
         undo description interface under test
         description new
         port mode 10G
        #
        """,
    ).strip()
    diff_processed = dedent(
        """
        interface 25GE1/0/1
         undo description interface under test
         description new
         shutdown
         port mode 10G
         undo shutdown
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


def test_huawei_interface_speed_mode_case_2() -> None:
    current_config = dedent(
        """
        interface 25GE1/0/1
         description interface under test
         mtu 9198
         port mode 10G
        #
        """,
    )
    target_config = dedent(
        """
        interface 25GE1/0/1
         description interface under test
         mtu 9198
        #
        """,
    )
    diff_raw = dedent(
        """
        interface 25GE1/0/1
         undo port mode 10G
        #
        """,
    ).strip()
    diff_processed = dedent(
        """
        interface 25GE1/0/1
         shutdown
         undo port mode 10G
         undo shutdown
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


def test_huawei_interface_speed_mode_case_3() -> None:
    current_config = dedent(
        """
        interface 25GE1/0/1
         description interface under test
         mtu 9198
         port mode 10G
        #
        """,
    )
    target_config = dedent(
        """
        interface 25GE1/0/1
         description interface under test
         mtu 9198
         port mode GE
        #
        """,
    )
    diff_raw = dedent(
        """
        interface 25GE1/0/1
         undo port mode 10G
         port mode GE
        #
        """,
    ).strip()
    diff_processed = dedent(
        """
        interface 25GE1/0/1
         shutdown
         undo port mode 10G
         port mode GE
         undo shutdown
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


def test_huawei_interface_speed_mode_case_4() -> None:
    current_config = dedent(
        """
        interface 25GE1/0/1
         description interface under test
         mtu 9198
         port mode 10G
        #
        interface 25GE1/0/2
         description interface under test
         mtu 9198
         port mode 10G
        #
        """,
    )
    target_config = dedent(
        """
        interface 25GE1/0/1
         description interface under test
         mtu 9198
        #
        interface 25GE1/0/2
         description changed description
         mtu 9198
        #
        """,
    )
    diff_raw = dedent(
        """
        interface 25GE1/0/1
         undo port mode 10G
        #
        interface 25GE1/0/2
         undo description interface under test
         undo port mode 10G
         description changed description
        #
        """,
    ).strip()
    patch_full = dedent(
        """
        interface 25GE1/0/1
        shutdown
        undo port mode 10G
        undo shutdown
        quit
        interface 25GE1/0/2
        undo description interface under test
        shutdown
        undo port mode 10G
        description changed description
        undo shutdown
        quit
        """,
    ).strip()
    pre_patch = dedent(
        """
        interface 25GE1/0/1
        shutdown
        quit
        interface 25GE1/0/2
        shutdown
        quit
        """,
    ).strip()
    main_patch = dedent(
        """
        interface 25GE1/0/1
        undo port mode 10G
        quit
        interface 25GE1/0/2
        undo description interface under test
        undo port mode 10G
        description changed description
        quit
        """,
    ).strip()
    main_wo_skip_patch = dedent(
        """
        interface 25GE1/0/2
        undo description interface under test
        description changed description
        quit
        """,
    ).strip()

    pre_wo_skip_patch = ""
    parser = CTreeParser(Platform.HUAWEI_VRP)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff.config == diff_raw

    diff = CTreeDiffer.diff(current, target)
    assert diff.patch == patch_full

    pre = CTreeSearcher.search(diff, include_tags=["pre"])
    assert pre.patch == pre_patch

    pre_wo_skip = CTreeSearcher.search(diff, include_tags=["pre"], exclude_tags=["skip-dry-run"])
    assert pre_wo_skip.patch == pre_wo_skip_patch

    main = CTreeSearcher.search(diff, exclude_tags=["pre", "post"])
    assert main.patch == main_patch

    main_wo_skip = CTreeSearcher.search(diff, exclude_tags=["pre", "post", "skip-dry-run"])
    assert main_wo_skip.patch == main_wo_skip_patch
