from ctreepo.ctree import CTree
from ctreepo.parser import CTreeParser
from ctreepo.tagging import TaggingRulesFromDict


def test_ctree_parser_with_tags(manual_tree: CTree, config_text: str, config_tags: dict[str, list[str]]) -> None:
    tagging_rules = TaggingRulesFromDict("cisco_iosxe", config_tags)
    parser = CTreeParser("cisco_iosxe", tagging_rules=tagging_rules)
    root = parser.parse(config_text)

    assert root == manual_tree


def test_ctree_parser_without_tags(manual_tree: CTree, config_text: str) -> None:
    parser = CTreeParser("cisco_iosxe")
    root = parser.parse(config_text)

    assert root.config == manual_tree.config
