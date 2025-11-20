from typing import TYPE_CHECKING

from ctreepo.differ import CTreeDiffer
from ctreepo.parser import CTreeParser

if TYPE_CHECKING:
    from tests.conftest import YamlTestCase


def test_huawei_interface_ip_secondary_order(
    yaml_data: "YamlTestCase",
    parser: CTreeParser,
) -> None:
    current = parser.parse(yaml_data.current)
    target = parser.parse(yaml_data.target)
    diff = CTreeDiffer.diff(current, target)

    assert diff.config == yaml_data.diff
    if yaml_data.patch:
        assert diff.patch == yaml_data.patch

    for node in diff.flatten:
        if node.line.startswith("undo interface ") and "." in node.line:
            assert "pre" in node.tags
        else:
            assert "pre" not in node.tags
