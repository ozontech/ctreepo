from textwrap import dedent

import pytest

from ctreepo import CTreeDiffer, CTreeParser, Platform


@pytest.mark.parametrize(
    "current_config, target_config, diff_config",
    [
        # trunk -> hybrid
        (
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description my-interface
                 port link-type trunk
                 port trunk pvid vlan 200
                 undo port trunk allow-pass vlan 1
                 port trunk allow-pass vlan 2 to 99 101 to 199 201 to 299
                 stp edged-port enable
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description my-interface
                 port link-type hybrid
                 port hybrid pvid vlan 200
                 port hybrid tagged vlan 2 to 99 101 to 199 201 to 299
                 port hybrid untagged vlan 200
                 stp edged-port enable
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 undo port link-type
                 port link-type hybrid
                 port hybrid pvid vlan 200
                 port hybrid tagged vlan 2 to 99 101 to 199 201 to 299
                 port hybrid untagged vlan 200
                #
                """,
            ).strip(),
        ),
        # trunk -> access
        (
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description my-interface
                 port link-type trunk
                 port trunk pvid vlan 200
                 undo port trunk allow-pass vlan 1
                 port trunk allow-pass vlan 2 to 99 101 to 199 201 to 299
                 stp edged-port enable
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description my-interface
                 port link-type access
                 port default vlan 200
                 stp edged-port enable
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 undo port link-type
                 port link-type access
                 port default vlan 200
                #
                """,
            ).strip(),
        ),
        # access -> hybrid
        (
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description my-interface
                 port link-type access
                 port default vlan 200
                 stp edged-port enable
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description my-interface
                 port link-type hybrid
                 port hybrid pvid vlan 200
                 port hybrid tagged vlan 2 to 99 101 to 199 201 to 299
                 port hybrid untagged vlan 200
                 stp edged-port enable
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 undo port link-type
                 port link-type hybrid
                 port hybrid pvid vlan 200
                 port hybrid tagged vlan 2 to 99 101 to 199 201 to 299
                 port hybrid untagged vlan 200
                #
                """,
            ).strip(),
        ),
        # access -> trunk
        (
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description my-interface
                 port link-type access
                 port default vlan 200
                 stp edged-port enable
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description my-interface
                 port link-type trunk
                 port trunk pvid vlan 200
                 undo port trunk allow-pass vlan 1
                 port trunk allow-pass vlan 2 to 99 101 to 199 201 to 299
                 stp edged-port enable
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 undo port link-type
                 port link-type trunk
                 port trunk pvid vlan 200
                 undo port trunk allow-pass vlan 1
                 port trunk allow-pass vlan 2 to 99 101 to 199 201 to 299
                #
                """,
            ).strip(),
        ),
        # hybrid -> trunk
        (
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description my-interface
                 port link-type hybrid
                 port hybrid pvid vlan 200
                 port hybrid tagged vlan 2 to 99 101 to 199 201 to 299
                 port hybrid untagged vlan 200
                 stp edged-port enable
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description my-interface
                 port link-type trunk
                 port trunk pvid vlan 200
                 undo port trunk allow-pass vlan 1
                 port trunk allow-pass vlan 2 to 99 101 to 199 201 to 299
                 stp edged-port enable
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 undo port link-type
                 port link-type trunk
                 port trunk pvid vlan 200
                 undo port trunk allow-pass vlan 1
                 port trunk allow-pass vlan 2 to 99 101 to 199 201 to 299
                #
                """,
            ).strip(),
        ),
        # hybrid -> access
        (
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description my-interface
                 port link-type hybrid
                 port hybrid pvid vlan 200
                 port hybrid tagged vlan 2 to 99 101 to 199 201 to 299
                 port hybrid untagged vlan 200
                 stp edged-port enable
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description my-interface
                 port link-type access
                 port default vlan 200
                 stp edged-port enable
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 undo port link-type
                 port link-type access
                 port default vlan 200
                #
                """,
            ).strip(),
        ),
        # shuffled commands (trunk -> hybrid)
        (
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description my-interface
                 port link-type trunk
                 port trunk pvid vlan 200
                 undo port trunk allow-pass vlan 1
                 port trunk allow-pass vlan 2 to 99 101 to 199 201 to 299
                 stp edged-port enable
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 port hybrid tagged vlan 2 to 99 101 to 199 201 to 299
                 description my-interface
                 port hybrid pvid vlan 200
                 port link-type hybrid
                 port hybrid untagged vlan 200
                 stp edged-port enable
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 undo port link-type
                 port link-type hybrid
                 port hybrid pvid vlan 200
                 port hybrid tagged vlan 2 to 99 101 to 199 201 to 299
                 port hybrid untagged vlan 200
                #
                """,
            ).strip(),
        ),
        (
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description my-interface
                 port link-type trunk
                 port trunk pvid vlan 200
                 port trunk allow-pass vlan 2 to 4094
                 stp edged-port enable
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 description my-interface
                 port link-type trunk
                 port trunk pvid vlan 200
                 undo port trunk allow-pass vlan 1
                 port trunk allow-pass vlan 100 to 199 201 to 299 500
                 stp edged-port enable
                #
                """,
            ),
            dedent(
                """
                interface GigabitEthernet1/0/1
                 undo port trunk allow-pass vlan 2 to 99 200 300 to 499 501 to 4094
                 undo port trunk allow-pass vlan 1
                 port trunk allow-pass vlan 100 to 199 201 to 299 500
                #
                """,
            ).strip(),
        ),
    ],
)
def test_pp_huawei_vrp_interface_link_type(current_config: str, target_config: str, diff_config: str) -> None:
    parser = CTreeParser(platform=Platform.HUAWEI_VRP)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
