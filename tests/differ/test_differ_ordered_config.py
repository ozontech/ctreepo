from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Vendor


def test_differ_ordered_section() -> None:
    current_config = dedent(
        """
        aaa accounting commands all default start-stop logging
        #
        section 1
         sub-line 1.2
         sub-line 1.1
         sub-line 1.3
         sub-section 2
          sub-line 2.2
          sub-line 2.1
        #
        aaa group server tacacs+ group_name
         server 10.1.0.2 vrf MGMT
         server 10.1.0.6 vrf MGMT
         server 10.1.0.4 vrf MGMT
         server 10.1.0.5 vrf MGMT
         server 10.1.0.3 vrf MGMT
        #
        """
    ).strip()
    target_config = dedent(
        """
        aaa accounting commands all default start-stop logging
        #
        aaa group server tacacs+ group_name
         server 10.1.0.6 vrf MGMT
         server 10.1.0.5 vrf MGMT
         server 10.1.0.4 vrf MGMT
         server 10.1.0.3 vrf MGMT
         server 10.1.0.7 vrf MGMT
        #
        section 1
         sub-line 1.1
         sub-section 2
          sub-line 2.1
          sub-line 2.2
          sub-line 2.3
         sub-line 1.2
         sub-line 1.3
        #
        some config
        """
    ).strip()
    diff_default = dedent(
        """
        aaa group server tacacs+ group_name
         undo server 10.1.0.2 vrf MGMT
         server 10.1.0.7 vrf MGMT
        #
        section 1
         sub-section 2
          sub-line 2.3
        #
        some config
        #
        """
    ).strip()
    diff_ordered_tacacs = dedent(
        """
        aaa group server tacacs+ group_name
         undo server 10.1.0.2 vrf MGMT
         undo server 10.1.0.4 vrf MGMT
         undo server 10.1.0.3 vrf MGMT
         server 10.1.0.4 vrf MGMT
         server 10.1.0.3 vrf MGMT
         server 10.1.0.7 vrf MGMT
        #
        section 1
         sub-section 2
          sub-line 2.3
        #
        some config
        #
        """
    ).strip()
    diff_ordered_tacacs_and_section = dedent(
        """
        section 1
         undo sub-line 1.2
         undo sub-line 1.3
         sub-section 2
          sub-line 2.3
         sub-line 1.2
         sub-line 1.3
        #
        aaa group server tacacs+ group_name
         undo server 10.1.0.2 vrf MGMT
         undo server 10.1.0.4 vrf MGMT
         undo server 10.1.0.3 vrf MGMT
         server 10.1.0.4 vrf MGMT
         server 10.1.0.3 vrf MGMT
         server 10.1.0.7 vrf MGMT
        #
        some config
        #
        """
    ).strip()
    diff_ordered_subsection = dedent(
        """
        section 1
         sub-section 2
          undo sub-line 2.2
          sub-line 2.2
          sub-line 2.3
        #
        aaa group server tacacs+ group_name
         undo server 10.1.0.2 vrf MGMT
         server 10.1.0.7 vrf MGMT
        #
        some config
        #
        """
    ).strip()
    diff_ordered_root = dedent(
        """
        aaa group server tacacs+ group_name
         undo server 10.1.0.2 vrf MGMT
         undo server 10.1.0.4 vrf MGMT
         undo server 10.1.0.3 vrf MGMT
         server 10.1.0.4 vrf MGMT
         server 10.1.0.3 vrf MGMT
         server 10.1.0.7 vrf MGMT
        #
        section 1
         sub-line 1.1
         sub-section 2
          sub-line 2.1
          sub-line 2.2
          sub-line 2.3
         sub-line 1.2
         sub-line 1.3
        #
        some config
        #
        undo section 1
        #
        """
    ).strip()
    diff_ordered_root_wo_reorder = dedent(
        """
        undo section 1
        #
        aaa group server tacacs+ group_name
         undo server 10.1.0.2 vrf MGMT
         undo server 10.1.0.4 vrf MGMT
         undo server 10.1.0.3 vrf MGMT
         server 10.1.0.4 vrf MGMT
         server 10.1.0.3 vrf MGMT
         server 10.1.0.7 vrf MGMT
        #
        section 1
         sub-line 1.1
         sub-section 2
          sub-line 2.1
          sub-line 2.2
          sub-line 2.3
         sub-line 1.2
         sub-line 1.3
        #
        some config
        #
        """
    ).strip()

    parser = CTreeParser(Vendor.HUAWEI)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_default

    diff = CTreeDiffer.diff(
        current,
        target,
        ordered_sections=[r"^aaa group server tacacs\+"],
    )
    assert diff.config == diff_ordered_tacacs

    diff = CTreeDiffer.diff(
        current,
        target,
        ordered_sections=[r"^aaa group server tacacs\+", r"^section \d+$"],
    )
    assert diff.config == diff_ordered_tacacs_and_section

    diff = CTreeDiffer.diff(
        current,
        target,
        ordered_sections=[r"^section \d+ / sub-section \d+$"],
    )
    assert diff.config == diff_ordered_subsection

    diff = CTreeDiffer.diff(
        current,
        target,
        ordered_sections=[r".*"],
    )
    assert diff.config == diff_ordered_root

    diff = CTreeDiffer.diff(
        current,
        target,
        ordered_sections=[r".*"],
        reorder_root=False,
    )
    assert diff.config == diff_ordered_root_wo_reorder


def test_differ_ordered_root() -> None:
    current_config = dedent(
        """
        dns resolve
        dns server 1.1.1.1
        dns server 1.1.1.3
        dns server 1.1.1.4
        dns server 1.1.1.2
        dns domain company.ru
        """
    ).strip()
    target_config = dedent(
        """
        dns resolve
        dns server 1.1.1.1
        dns server 1.1.1.2
        dns server 1.1.1.3
        dns server 1.1.1.4
        dns domain company.ru
        """
    ).strip()
    not_ordered_diff_config = ""
    ordered_diff_config = dedent(
        """
        undo dns server 1.1.1.3
        #
        undo dns server 1.1.1.4
        #
        undo dns domain company.ru
        #
        dns server 1.1.1.3
        #
        dns server 1.1.1.4
        #
        dns domain company.ru
        #
        """
    ).strip()

    parser = CTreeParser(Vendor.HUAWEI)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    not_ordered_diff = CTreeDiffer.diff(current, target)
    assert not_ordered_diff.config == not_ordered_diff_config

    ordered_diff = CTreeDiffer.diff(current, target, ordered_sections=[""], reorder_root=False)
    assert ordered_diff.config == ordered_diff_config
