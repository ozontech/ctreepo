from typing import TYPE_CHECKING

from ctreepo.differ import CTreeDiffer
from ctreepo.parser import CTreeParser

if TYPE_CHECKING:
    from tests.conftest import YamlTestCase


def test_link_type(
    yaml_data: "YamlTestCase",
    parser: CTreeParser,
) -> None:
    template = parser.parse(yaml_data.template)
    current = parser.parse(yaml_data.current, template)
    target = parser.parse(yaml_data.target, template)
    diff = CTreeDiffer.diff(current, target)

    assert diff.config == yaml_data.diff
    if yaml_data.patch:
        assert diff.patch == yaml_data.patch
