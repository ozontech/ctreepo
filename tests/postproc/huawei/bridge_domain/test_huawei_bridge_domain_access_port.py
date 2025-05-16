from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Platform


def test_huawei_bridge_domain_access_port() -> None:
    current_config = dedent(
        """
        bridge-domain 100
         statistics enable
         vlan 100 access-port interface Eth-Trunk1 to Eth-Trunk10
         vlan 100 access-port interface 10GE1/0/1 to 10GE1/0/6
         vlan 100 access-port interface 10GE1/0/7 to 10GE1/0/42
         vlan 100 access-port interface 10GE1/0/44
         vlan 100 access-port interface 10GE1/0/46 to 10GE1/0/48
        #
        """,
    )
    target_config = dedent(
        """
        bridge-domain 100
         statistics enable
         vlan 100 access-port interface Eth-Trunk1 to Eth-Trunk4
         vlan 100 access-port interface Eth-Trunk6 to Eth-Trunk10
         vlan 100 access-port interface 10GE1/0/2 to 10GE1/0/6
         vlan 100 access-port interface 10GE1/0/7 to 10GE1/0/48
        bridge-domain test
         statistics enable
        #
        """,
    )
    diff_config = dedent(
        """
        bridge-domain 100
         undo vlan 100 access-port interface 10GE1/0/1
         undo vlan 100 access-port interface Eth-Trunk5
         vlan 100 access-port interface 10GE1/0/43
         vlan 100 access-port interface 10GE1/0/45
        #
        bridge-domain test
         statistics enable
        #
        """,
    ).strip()
    parser = CTreeParser(Platform.HUAWEI_VRP)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
