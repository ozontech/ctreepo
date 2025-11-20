from ctreepo.ctree import CTree
from ctreepo.renderer import CTreeRenderer


def test_basic_tree_config(
    config_tree: CTree,
    config_text: str,
) -> None:
    expected_config = config_text.replace("exit-address-family", "!")
    assert config_tree.config == expected_config


def test_basic_tree_masked_config(
    config_tree: CTree,
    config_text: str,
) -> None:
    expected_config = config_text.replace("exit-address-family", "!")
    expected_config = expected_config.replace("some-secret", CTreeRenderer.secret_mask)
    assert config_tree.config_masked == expected_config
