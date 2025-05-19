from textwrap import dedent

import pytest

from ctreepo import CTreeDiffer, CTreeParser, CTreeSearcher, Platform
from ctreepo.postproc.huawei_vrp import HuaweiVRPBridgeDomain


@pytest.mark.parametrize(
    "current_config, target_config, pre_diff_config, main_diff_config, post_diff_config",
    [
        # undo access-port помечаем PRE тегом
        (
            dedent(
                """
                bridge-domain 100
                 statistics enable
                 vlan 100 access-port interface Eth-Trunk1
                #
                """,
            ),
            dedent(
                """
                bridge-domain 100
                 statistics enable
                #
                """,
            ),
            dedent(
                """
                bridge-domain 100
                 undo vlan 100 access-port interface Eth-Trunk1
                #
                """,
            ).strip(),
            dedent(
                """
                """,
            ).strip(),
            dedent(
                """
                """,
            ).strip(),
        ),
        # undo access-port помечаем PRE тегом, остальное в main
        (
            dedent(
                """
                bridge-domain 100
                 statistics enable
                 vlan 100 access-port interface Eth-Trunk1
                #
                """,
            ),
            dedent(
                """
                bridge-domain 100
                 statistics enable
                 vlan 100 access-port interface Eth-Trunk2
                #
                """,
            ),
            dedent(
                """
                bridge-domain 100
                 undo vlan 100 access-port interface Eth-Trunk1
                #
                """,
            ).strip(),
            dedent(
                """
                bridge-domain 100
                 vlan 100 access-port interface Eth-Trunk2
                #
                """,
            ).strip(),
            dedent(
                """
                """,
            ).strip(),
        ),
        # undo access-port помечаем PRE тегом, остальное в main, глобальный POST
        (
            dedent(
                """
                bridge-domain 100
                 statistics enable
                 vlan 100 access-port interface Eth-Trunk1
                #
                bridge-domain 101
                 statistics enable
                #
                """,
            ),
            dedent(
                """
                bridge-domain 100
                 statistics enable
                 vlan 100 access-port interface Eth-Trunk2
                #
                """,
            ),
            dedent(
                """
                bridge-domain 100
                 undo vlan 100 access-port interface Eth-Trunk1
                #
                """,
            ).strip(),
            dedent(
                """
                bridge-domain 100
                 vlan 100 access-port interface Eth-Trunk2
                #
                """,
            ).strip(),
            dedent(
                """
                undo bridge-domain 101
                #
                """,
            ).strip(),
        ),
    ],
)
def test_pp_huawei_vrp_bridge_domain_pre_tag(
    current_config: str,
    target_config: str,
    pre_diff_config: str,
    main_diff_config: str,
    post_diff_config: str,
) -> None:
    parser = CTreeParser(Platform.HUAWEI_VRP)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target, post_proc_rules=[HuaweiVRPBridgeDomain])

    pre_diff = CTreeSearcher.search(diff, include_tags=["pre"])
    assert pre_diff.config == pre_diff_config

    main_diff = CTreeSearcher.search(diff, exclude_tags=["pre", "post"])
    assert main_diff.config == main_diff_config

    post_diff = CTreeSearcher.search(diff, include_tags=["post"])
    assert post_diff.config == post_diff_config
