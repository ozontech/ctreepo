import pytest

from ctreepo.ctree import CTree
from ctreepo.filter import CTreeFilter


def test_filter_with_empty_input(config_tree: CTree) -> None:
    # если ничего не передали
    result = CTreeFilter.filter(
        config_tree,
    )
    assert result == config_tree


def test_filter_wrong_include_mode(config_tree: CTree) -> None:
    with pytest.raises(expected_exception=ValueError):
        _ = CTreeFilter.filter(
            config_tree,
            include_tags=("bgp",),
            include_mode="wrong",  # type: ignore[arg-type]
        )
