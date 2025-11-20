from ctreepo.differ import CTreeDiffer
from ctreepo.parser import CTreeParser

CURRENT_TEXT = """
interface BVI123
 description User-OLD
 vrf CE
 load-interval 30
!
prefix-set ps-some-networks
  1.2.3.0/24,
  5.6.7.0/24
end-set
!
""".strip()

TARGET_TEXT = """
interface BVI123
 description User-NEW
 vrf CE
!
prefix-set ps-some-networks
  1.2.3.0/24,
  10.10.10.0/24
end-set
!
""".strip()

EXPECTED_TEXT = """
interface BVI123
 no load-interval
 description User-NEW
!
prefix-set ps-some-networks
 1.2.3.0/24,
 10.10.10.0/24
!
""".strip()

TEMPLATE_TEXT = r"""
interface \S+
 (description) (?P<VAL>.*) UNDO>> no \1
 (load-interval) (?P<VAL>\d+) UNDO>> no \1
!
""".strip()


def test_differ_no_diff(parser: CTreeParser) -> None:
    template = parser.parse(TEMPLATE_TEXT)
    current = parser.parse(CURRENT_TEXT, template)
    target = parser.parse(TARGET_TEXT, template)
    diff = CTreeDiffer.diff(current, target)
    assert diff.config == EXPECTED_TEXT
