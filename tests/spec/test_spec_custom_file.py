from textwrap import dedent

from ctreepo.ctree import CTree


def test_spec_custom_file(config_tree_rewritten_spec: CTree) -> None:
    expected_config = dedent(
        """
        service tcp-keepalives-in
        service timestamps debug datetime msec localtime show-timezone
        #
        interface Loopback0
           description test-0
           ip address 192.168.1.1 255.255.255.255
        #
        """,
    ).strip()
    expected_patch = dedent(
        """
        service tcp-keepalives-in
        service timestamps debug datetime msec localtime show-timezone
        interface Loopback0
        description test-0
        ip address 192.168.1.1 255.255.255.255
        quit
        """,
    ).strip()
    spec = config_tree_rewritten_spec.spec
    assert spec.section_sep == "#"
    assert spec.spaces == "   "
    assert spec.section_exit == "quit"
    assert spec.junk_lines == ["\\s*!.*"]
    assert spec.mask_patterns == []
    assert spec.sections_required_exit == []
    assert spec.sections_without_exit == []
    assert config_tree_rewritten_spec.config == expected_config
    assert config_tree_rewritten_spec.patch == expected_patch
