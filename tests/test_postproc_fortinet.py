from textwrap import dedent

import pytest

from ctreepo import CTreeDiffer, CTreeParser, Vendor
from ctreepo.postproc_fortinet import FortinetFortiOSUnset


@pytest.mark.parametrize(
    ("current_config", "target_config", "raw_diff_patch", "pp_diff_patch"),
    [
        (
            dedent(
                """
                config system global
                    set admin-concurrent enable
                    set admin-console-timeout 0
                end
                """,
            ),
            dedent(
                """
                config system global
                    set admin-concurrent enable
                    set admin-console-timeout 15
                end
                """,
            ),
            dedent(
                """
                config system global
                unset set admin-console-timeout 0
                set admin-console-timeout 15
                end
                """,
            ).strip(),
            dedent(
                """
                config system global
                unset admin-console-timeout 0
                set admin-console-timeout 15
                end
                """,
            ).strip(),
        ),
    ],
)
def test_pp_cisco_iosxe_no_value(
    current_config: str,
    target_config: str,
    raw_diff_patch: str,
    pp_diff_patch: str,
) -> None:
    parser = CTreeParser(vendor=Vendor.FORTINET)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    raw_diff = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert raw_diff.patch == raw_diff_patch

    pp_diff = CTreeDiffer.diff(current, target, post_proc_rules=[FortinetFortiOSUnset])
    assert pp_diff.patch == pp_diff_patch
