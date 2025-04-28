from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Vendor


def test_differ_no_diff_section_case_1() -> None:
    """XPL для huawei."""
    current_config = dedent(
        """
        interface Vbdif1234
         mtu 9000
         ip binding vpn-instance INTERNET
         ip address 1.2.3.4 255.255.255.0
        #
        route-policy RP_LEGACY_POLICY permit node 10
         if-match ip-prefix PL_PREFIX_LIST_NAME_OLD
        #
        xpl route-filter RP_XPL_POLICY
         if community matches-any CL_COMMUNITY_LIST_1 and community matches-any CL_COMMUNITY_LIST_2 then
          apply local-preference 150
          approve
         elseif community matches-any CL_COMMUNITY_LIST_OLD then
          approve
         endif
         end-filter
        #
        xpl route-filter RP_XPL_BLOCK
         refuse
         end-filter
        #
        """
    ).strip()
    target_config = dedent(
        """
        interface Vbdif1234
         mtu 9000
         description some svi
         ip binding vpn-instance INTERNET
         ip address 4.3.2.1 255.255.255.0
        #
        route-policy RP_LEGACY_POLICY permit node 10
         if-match ip-prefix PL_PREFIX_LIST_NAME_NEW
        #
        xpl route-filter RP_XPL_POLICY
         if community matches-any CL_COMMUNITY_LIST_1 and community matches-any CL_COMMUNITY_LIST_2 then
          apply local-preference 150
          approve
         elseif community matches-any CL_COMMUNITY_LIST_NEW then
          approve
         endif
         end-filter
        #
        route-policy RP_LEGACY_BLOCK deny node 10
        #
        xpl route-filter RP_XPL_BLOCK
         refuse
         end-filter
        #
        """
    ).strip()
    diff_raw_config = dedent(
        """
        interface Vbdif1234
         undo ip address 1.2.3.4 255.255.255.0
         description some svi
         ip address 4.3.2.1 255.255.255.0
        #
        route-policy RP_LEGACY_POLICY permit node 10
         undo if-match ip-prefix PL_PREFIX_LIST_NAME_OLD
         if-match ip-prefix PL_PREFIX_LIST_NAME_NEW
        #
        xpl route-filter RP_XPL_POLICY
         undo elseif community matches-any CL_COMMUNITY_LIST_OLD then
         elseif community matches-any CL_COMMUNITY_LIST_NEW then
          approve
        #
        route-policy RP_LEGACY_BLOCK deny node 10
        #
        """
    ).strip()
    diff_raw_patch = dedent(
        """
        interface Vbdif1234
        undo ip address 1.2.3.4 255.255.255.0
        description some svi
        ip address 4.3.2.1 255.255.255.0
        quit
        route-policy RP_LEGACY_POLICY permit node 10
        undo if-match ip-prefix PL_PREFIX_LIST_NAME_OLD
        if-match ip-prefix PL_PREFIX_LIST_NAME_NEW
        quit
        xpl route-filter RP_XPL_POLICY
        undo elseif community matches-any CL_COMMUNITY_LIST_OLD then
        elseif community matches-any CL_COMMUNITY_LIST_NEW then
        approve
        route-policy RP_LEGACY_BLOCK deny node 10
        quit
        """
    ).strip()
    diff_raw_empty_section_patch = dedent(
        """
        interface Vbdif1234
        undo ip address 1.2.3.4 255.255.255.0
        description some svi
        ip address 4.3.2.1 255.255.255.0
        quit
        route-policy RP_LEGACY_POLICY permit node 10
        undo if-match ip-prefix PL_PREFIX_LIST_NAME_OLD
        if-match ip-prefix PL_PREFIX_LIST_NAME_NEW
        quit
        xpl route-filter RP_XPL_POLICY
        undo elseif community matches-any CL_COMMUNITY_LIST_OLD then
        elseif community matches-any CL_COMMUNITY_LIST_NEW then
        approve
        route-policy RP_LEGACY_BLOCK deny node 10
        quit
        """
    ).strip()
    diff_no_diff_config = dedent(
        """
        interface Vbdif1234
         undo ip address 1.2.3.4 255.255.255.0
         description some svi
         ip address 4.3.2.1 255.255.255.0
        #
        route-policy RP_LEGACY_POLICY permit node 10
         undo if-match ip-prefix PL_PREFIX_LIST_NAME_OLD
         if-match ip-prefix PL_PREFIX_LIST_NAME_NEW
        #
        xpl route-filter RP_XPL_POLICY
         if community matches-any CL_COMMUNITY_LIST_1 and community matches-any CL_COMMUNITY_LIST_2 then
          apply local-preference 150
          approve
         elseif community matches-any CL_COMMUNITY_LIST_NEW then
          approve
         endif
         end-filter
        #
        route-policy RP_LEGACY_BLOCK deny node 10
        #
        """
    ).strip()
    diff_no_diff_patch = dedent(
        """
        interface Vbdif1234
        undo ip address 1.2.3.4 255.255.255.0
        description some svi
        ip address 4.3.2.1 255.255.255.0
        quit
        route-policy RP_LEGACY_POLICY permit node 10
        undo if-match ip-prefix PL_PREFIX_LIST_NAME_OLD
        if-match ip-prefix PL_PREFIX_LIST_NAME_NEW
        quit
        xpl route-filter RP_XPL_POLICY
        if community matches-any CL_COMMUNITY_LIST_1 and community matches-any CL_COMMUNITY_LIST_2 then
        apply local-preference 150
        approve
        elseif community matches-any CL_COMMUNITY_LIST_NEW then
        approve
        endif
        end-filter
        route-policy RP_LEGACY_BLOCK deny node 10
        quit
        """
    ).strip()

    parser = CTreeParser(Vendor.HUAWEI)
    target = parser.parse(target_config)
    current = parser.parse(current_config)

    diff_raw = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_raw_config
    assert diff_raw.patch == diff_raw_patch

    diff_raw_empty_section = CTreeDiffer.diff(current, target)
    assert diff_raw_empty_section.patch == diff_raw_empty_section_patch

    diff_no_diff = CTreeDiffer.diff(
        a=current,
        b=target,
        no_diff_sections=[r"^xpl \S+ \S+$"],
    )
    assert diff_no_diff.config == diff_no_diff_config
    assert diff_no_diff.patch == diff_no_diff_patch


def test_differ_no_diff_section_case_2() -> None:
    """route-policy (абстрактный пример)."""
    current_config = dedent(
        """
        some root line 1
        #
        route-policy NO_DIFF_POLICY
         line 1
         line 3
        #
        some root line 2
        some root line 3
        #
        """
    )
    target_config = dedent(
        """
        some root line 1
        #
        route-policy NO_DIFF_POLICY
         line 1
         line 2
         line 3
        #
        some root line 3
        #
        """
    )
    diff_config = dedent(
        """
        route-policy NO_DIFF_POLICY
         line 1
         line 2
         line 3
        #
        undo some root line 2
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        route-policy NO_DIFF_POLICY
        line 1
        line 2
        line 3
        quit
        undo some root line 2
        """
    ).strip()
    parser = CTreeParser(Vendor.HUAWEI)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target, no_diff_sections=[r"route-policy \S+"])
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_differ_no_diff_section_case_3() -> None:
    """Абстрактный route-policy вложенный в секцию."""
    current_config = dedent(
        """
        some root line 1
        #
        section 1
         sub-line 1
         #
         route-policy NO_DIFF_POLICY
          line 1
          line 3
         #
        #
        some root line 2
        some root line 3
        #
        """
    )
    target_config = dedent(
        """
        some root line 1
        #
        section 1
         sub-line 1
         #
         route-policy NO_DIFF_POLICY
          line 1
          line 2
          line 3
         #
        #
        some root line 3
        #
        """
    )
    diff_config = dedent(
        """
        section 1
         route-policy NO_DIFF_POLICY
          line 1
          line 2
          line 3
        #
        undo some root line 2
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        section 1
        route-policy NO_DIFF_POLICY
        line 1
        line 2
        line 3
        quit
        quit
        undo some root line 2
        """
    ).strip()
    parser = CTreeParser(Vendor.HUAWEI)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target, no_diff_sections=[r"section \d+ / route-policy \S+"])
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_differ_no_diff_section_case_4() -> None:
    """no-diff + удаление."""
    current_config = dedent(
        """
        route-policy NO_DIFF_POLICY_1
         line 1
         line 2
        #
        route-policy NO_DIFF_POLICY_2
         line 1
         line 2
        #
        route-policy NO_DIFF_POLICY_3
         line 1
         line 2
        #
        """
    )
    target_config = dedent(
        """
        route-policy NO_DIFF_POLICY_1
         line 1
         line 2
        #
        route-policy NO_DIFF_POLICY_2
         line 1
         line 2
         line 3
        #
        """
    )
    diff_config = dedent(
        """
        route-policy NO_DIFF_POLICY_2
         line 1
         line 2
         line 3
        #
        undo route-policy NO_DIFF_POLICY_3
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        route-policy NO_DIFF_POLICY_2
        line 1
        line 2
        line 3
        quit
        undo route-policy NO_DIFF_POLICY_3
        """
    ).strip()
    parser = CTreeParser(Vendor.HUAWEI)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target, no_diff_sections=[r"route-policy \S+"])
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_differ_no_diff_section_case_5() -> None:
    """Несколько вложенных route-policy."""
    current_config = dedent(
        """
        section 1
         route-policy NO_DIFF_POLICY_1
          line 1
          line 2
         #
         route-policy NO_DIFF_POLICY_2
          line 1
          line 2
         #
         route-policy NO_DIFF_POLICY_3
          line 1
          line 2
         #
        #
        """
    )
    target_config = dedent(
        """
        section 1
         route-policy NO_DIFF_POLICY_1
          line 1
          line 2
         #
         route-policy NO_DIFF_POLICY_2
          line 1
          line 2
          line 3
         #
        #
        """
    )
    diff_config = dedent(
        """
        section 1
         undo route-policy NO_DIFF_POLICY_3
         route-policy NO_DIFF_POLICY_2
          line 1
          line 2
          line 3
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        section 1
        undo route-policy NO_DIFF_POLICY_3
        route-policy NO_DIFF_POLICY_2
        line 1
        line 2
        line 3
        quit
        quit
        """
    ).strip()
    parser = CTreeParser(Vendor.HUAWEI)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target, no_diff_sections=[r"route-policy \S+"])
    assert diff.config == diff_config
    assert diff.patch == diff_patch
