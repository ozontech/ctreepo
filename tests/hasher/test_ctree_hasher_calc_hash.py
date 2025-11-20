from ctreepo.ctree import CTree


def test_ctree_hasher_calc_hash(config_tree: CTree, config_hash: dict[str, str]) -> None:
    assert config_tree.hash == config_hash["root"]
    for node in config_tree.flatten:
        result = node.hash
        expected = config_hash[node.line]
        assert result == expected
