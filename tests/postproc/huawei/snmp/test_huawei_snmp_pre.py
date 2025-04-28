from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Vendor
from ctreepo.parser import TaggingRulesDict


def test_huawei_snmp_pre() -> None:
    # undo с тегом pre до добавления community
    current_config = dedent(
        """
        snmp-agent community read cipher public12345 mib-view iso-view alias __CommunityRO
        snmp-agent sys-info location my-location
        snmp-agent sys-info version v2c v3
        """
    )
    target_config = dedent(
        """
        snmp-agent community read cipher private54321 mib-view iso-view alias __CommunityRO
        snmp-agent sys-info location my-location
        snmp-agent sys-info version v2c v3
        """
    )
    diff_config = dedent(
        """
        undo snmp-agent community read cipher public12345 mib-view iso-view alias __CommunityRO
        #
        snmp-agent community read cipher private54321 mib-view iso-view alias __CommunityRO
        #
        """
    ).strip()

    tagging_rules = TaggingRulesDict(
        {Vendor.HUAWEI: [{"regex": r"^(?:undo )?snmp-agent", "tags": ["snmp"]}]},
    )

    parser = CTreeParser(Vendor.HUAWEI, tagging_rules=tagging_rules)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target)
    diff.reorder(["pre", "post"])
    assert list(diff.children.values())[0].tags == ["snmp", "pre"]
    assert list(diff.children.values())[1].tags == ["snmp"]
    assert diff.config == diff_config
