import pytest

from ctreepo.differ import CTreeDiffer
from ctreepo.parser import CTreeParser
from ctreepo.platforms.huawei_vrp.handlers_diff import undo_route_policy

current_text = """
telnet server disable
telnet ipv6 server disable
#
route-policy RP_NAME_1 permit node 30
 if-match ip-prefix PL_NAME_1
 apply community community-list CL_NAME_1 additive
#
route-policy RP_NAME_1 permit node 40
 if-match ip-prefix PL_NAME_1
 if-match ip next-hop ip-prefix PL_NHOP_NAME_1_2
 apply community community-list CL_NAME_1 additive
#
route-policy RP_NAME_1 deny node 50
 if-match ip-prefix PL_NAME_2
#
"""
target_text = """
telnet server disable
telnet ipv6 server disable
undo telnet server-source all-interface
undo telnet ipv6 server-source all-interface
#
route-policy RP_NAME_1 permit node 30
 if-match ip-prefix PL_NAME_1
 apply community community-list CL_NAME_1 additive
#
"""
expected_before = """
undo telnet server-source all-interface
undo telnet ipv6 server-source all-interface
undo route-policy RP_NAME_1 permit node 40
undo route-policy RP_NAME_1 deny node 50
#
""".strip()
expected_after = """
undo telnet server-source all-interface
undo telnet ipv6 server-source all-interface
undo route-policy RP_NAME_1 node 40
undo route-policy RP_NAME_1 node 50
#
""".strip()


def test_undo_route_policy(parser: CTreeParser) -> None:
    current = parser.parse(current_text)
    target = parser.parse(target_text)
    diff = CTreeDiffer.diff(current, target, diff_handlers=[])
    assert diff.config == expected_before
    diff = CTreeDiffer.diff(current, target, diff_handlers=[undo_route_policy])
    assert diff.config == expected_after


def test_undo_route_exception(parser: CTreeParser) -> None:
    wrong_current_text = current_text.replace(" deny node 50", " wrong node 50")
    current = parser.parse(wrong_current_text)
    target = parser.parse(target_text)
    with pytest.raises(ValueError, match=r"неизвестная настройка .*"):
        _ = CTreeDiffer.diff(current, target, diff_handlers=[undo_route_policy])


def test_undo_route_no_action(parser: CTreeParser) -> None:
    current = parser.parse(current_text)
    target = parser.parse(current_text)
    diff = CTreeDiffer.diff(current, target, diff_handlers=[undo_route_policy])
    assert diff.config == ""
