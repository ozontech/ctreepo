from typing import Any

from ctreepo.ctree import CTree
from ctreepo.serializer import CTreeSerializer


def test_serializer_to_dict(config_tree: CTree, config_dict: dict[str, dict[str, Any]]) -> None:
    result = CTreeSerializer.to_dict(config_tree)
    assert result == config_dict


def test_serializer_from_dict(config_tree: CTree, config_dict: dict[str, dict[str, Any]]) -> None:
    root = CTreeSerializer.from_dict("cisco_iosxe", config_dict)
    result_list = list(root.flatten)
    expected_list = list(config_tree.flatten)
    assert root == config_tree
    assert len(result_list) == len(expected_list)
    for indx, expected_node in enumerate(expected_list):
        result_node = result_list[indx]
        assert result_node == expected_node
        assert result_node.line == expected_node.line
        assert result_node.template == expected_node.template
        assert result_node.undo == expected_node.undo
        assert result_node.tags == expected_node.tags
