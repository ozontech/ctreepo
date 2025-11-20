from textwrap import dedent

import pytest

from ctreepo.differ import CTreeDiffer
from ctreepo.parser import CTreeParser


@pytest.mark.parametrize(
    ("current_text", "target_text", "expected"),
    [
        # ничего не нужно менять
        (
            dedent(
                """
                ip access-list standard acl_TEST
                 permit 1.1.1.1
                 permit 8.8.8.8
                 deny   any
                !
                """,
            ).strip(),
            dedent(
                """
                ip access-list standard acl_TEST
                 permit 1.1.1.1
                 permit 8.8.8.8
                 deny   any
                !
                """,
            ).strip(),
            "",
        ),
        # меняем две средние строки местами
        (
            dedent(
                """
                ip access-list standard acl_TEST
                 permit 0.0.0.0
                 permit 1.1.1.1
                 permit 2.2.2.2
                 deny   any
                !
                """,
            ).strip(),
            dedent(
                """
                ip access-list standard acl_TEST
                 permit 0.0.0.0
                 permit 2.2.2.2
                 permit 1.1.1.1
                 deny   any
                !
                """,
            ).strip(),
            dedent(
                """
                ip access-list standard acl_TEST
                 no permit 1.1.1.1
                 no deny   any
                 permit 1.1.1.1
                 deny   any
                !
                """,
            ).strip(),
        ),
    ],
)
def test_differ_ordered(current_text: str, target_text: str, expected: str, parser: CTreeParser) -> None:
    current = parser.parse(current_text)
    target = parser.parse(target_text)
    diff = CTreeDiffer.diff(current, target)
    assert diff.config == expected
