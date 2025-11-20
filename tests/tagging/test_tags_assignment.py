import re

from ctreepo.ctree import CTree


def test_tags_assignment(config_tree: CTree, config_tags_dict: dict[str, list[str]]) -> None:
    def _check_node_tags(node: CTree) -> None:
        for rule, tags in config_tags_dict.items():
            if m := re.fullmatch(rule, node.line_formal):
                assert node.tags == {
                    *(tag.format_map(m.groupdict()) for tag in tags),
                    *m.groups(),
                }
                return
        assert isinstance(node.parent, CTree)
        assert node.tags == node.parent.tags

    for node in config_tree.flatten:
        _check_node_tags(node)
