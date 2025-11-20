import pytest

from ctreepo.ctree import CTree
from ctreepo.sorter import CTreeSorter


def test_ctree_sorter_wrong_mode(config_tree: CTree) -> None:
    tags = ("ip", "rm", "interface", "bgp")
    mode = "wrong"
    with pytest.raises(
        expected_exception=ValueError,
        match=f"неизвестный режим {mode!r}",
    ):
        _ = "\n".join(
            CTreeSorter.config_by_tags(
                *tags,
                node=config_tree,
                skip_no_tag=True,
                mode=mode,  # type: ignore[arg-type]
            ),
        )


def test_ctree_sorter_wrong_tags(config_tree: CTree) -> None:
    tags = ((True, "interface"), "rm", "interface", "bgp")
    with pytest.raises(
        expected_exception=ValueError,
        match="неправильный формат передачи тегов",
    ):
        _ = "\n".join(
            CTreeSorter.config_by_tags(
                *tags,  # type: ignore[arg-type]
                node=config_tree,
                skip_no_tag=True,
                mode="config",
            ),
        )
