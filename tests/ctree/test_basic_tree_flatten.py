from ctreepo.ctree import CTree


def test_basic_tree_flatten(
    config_tree: CTree,
    config_patch: str,
) -> None:
    expected = config_patch.replace(config_tree.spec.section_exit, "")
    expected = expected.replace("\n\n", "\n").strip()
    result = "\n".join(node.line for node in config_tree.flatten)
    assert result == expected
