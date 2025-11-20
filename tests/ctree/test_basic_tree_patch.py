from ctreepo.ctree import CTree
from ctreepo.renderer import CTreeRenderer


def test_basic_tree_patch(
    config_tree: CTree,
    config_patch: str,
) -> None:
    assert config_tree.patch == config_patch


def test_basic_tree_masked_patch(
    config_tree: CTree,
    config_patch: str,
) -> None:
    expected_patch = config_patch.replace("some-secret", CTreeRenderer.secret_mask)
    assert config_tree.patch_masked == expected_patch
