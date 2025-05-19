from textwrap import dedent

import pytest

from ctreepo import CTreeDiffer, CTreeParser, Platform
from ctreepo.postproc.huawei_vrp import HuaweiVRPLocalUser


@pytest.mark.parametrize(
    "current_config, target_config, raw_diff_config, pp_diff_config",
    [
        (
            dedent(
                """
                aaa
                 local-user user1@default password irreversible-cipher old_hash_1
                 local-user user1@default service-type terminal ssh
                 local-user user1@default level 3
                 local-user user2@default password irreversible-cipher old_hash_2
                 local-user user2@default service-type terminal ssh
                 local-user user2@default level 3
                """,
            ),
            dedent(
                """
                aaa
                 local-user user1@default password irreversible-cipher old_hash_1
                 local-user user1@default service-type terminal ssh
                 local-user user1@default level 3
                """,
            ),
            dedent(
                """
                aaa
                 undo local-user user2@default password irreversible-cipher old_hash_2
                 undo local-user user2@default service-type terminal ssh
                 undo local-user user2@default level 3
                #
                """,
            ).strip(),
            dedent(
                """
                aaa
                 undo local-user user2@default password irreversible-cipher old_hash_2
                #
                """,
            ).strip(),
        ),
    ],
)
def test_pp_huawei_vrp_aaa_localuser(
    current_config: str,
    target_config: str,
    raw_diff_config: str,
    pp_diff_config: str,
) -> None:
    parser = CTreeParser(platform=Platform.HUAWEI_VRP)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    raw_diff = CTreeDiffer.diff(current, target, post_proc_rules=[])
    assert raw_diff.config == raw_diff_config, "raw"

    pp_diff = CTreeDiffer.diff(current, target, post_proc_rules=[HuaweiVRPLocalUser])
    assert pp_diff.config == pp_diff_config, "post-processed"
