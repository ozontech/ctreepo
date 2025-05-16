from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, CTreeSearcher, Platform
from ctreepo.parser import TaggingRulesDict


def test_huawei_bridge_domain_pre_tag_case_1() -> None:
    # тест на наличие пустой секции после назначении pre тега
    current_config = dedent(
        """
        bridge-domain 100
         statistics enable
         vlan 100 access-port interface Eth-Trunk1
        #
        """,
    )
    target_config = dedent(
        """
        bridge-domain 100
         statistics enable
        #
        """,
    )
    pre_patch = dedent(
        """
        bridge-domain 100
        undo vlan 100 access-port interface Eth-Trunk1
        quit
        """,
    ).strip()
    bd_patch = ""

    tagging_rules_dict: dict[Platform, list[dict[str, str | list[str]]]] = {
        Platform.HUAWEI_VRP: [{"regex": r"^bridge-domain \d+$", "tags": ["bd"]}],
    }
    tagging_rules = TaggingRulesDict(tagging_rules_dict)
    parser = CTreeParser(Platform.HUAWEI_VRP, tagging_rules=tagging_rules)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target)

    pre = CTreeSearcher.search(diff, include_tags=["pre"])
    assert pre.patch == pre_patch

    bd = CTreeSearcher.search(diff, include_tags=["bd"], exclude_tags=["pre"])
    assert bd.patch == bd_patch


def test_huawei_bridge_domain_pre_tag_case_2() -> None:
    # тест на pre тэг для удаления интерфейсов из bd
    current_config = dedent(
        """
        bridge-domain 100
         statistics enable
         vlan 100 access-port interface Eth-Trunk1
        #
        """,
    )
    target_config = dedent(
        """
        bridge-domain 100
         statistics enable
         vlan 100 access-port interface Eth-Trunk2
        #
        """,
    )
    pre_patch = dedent(
        """
        bridge-domain 100
        undo vlan 100 access-port interface Eth-Trunk1
        quit
        """,
    ).strip()
    bd_patch = dedent(
        """
        bridge-domain 100
        vlan 100 access-port interface Eth-Trunk2
        quit
        """,
    ).strip()

    tagging_rules_dict: dict[Platform, list[dict[str, str | list[str]]]] = {
        Platform.HUAWEI_VRP: [{"regex": r"^bridge-domain \d+$", "tags": ["bd"]}],
    }
    tagging_rules = TaggingRulesDict(tagging_rules_dict)
    parser = CTreeParser(Platform.HUAWEI_VRP, tagging_rules=tagging_rules)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target)

    pre = CTreeSearcher.search(diff, include_tags=["pre"])
    assert pre.patch == pre_patch

    bd = CTreeSearcher.search(diff, include_tags=["bd"], exclude_tags=["pre"])
    assert bd.patch == bd_patch
