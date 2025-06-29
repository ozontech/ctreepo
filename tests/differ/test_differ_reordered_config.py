from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Platform


def test_reordered_config() -> None:
    config1 = dedent(
        """
        bgp 64512
         ipv4-family unicast
          import-route direct route-policy RP_CONNECTED
         ipv4-family vpn-instance LAN
          peer PEER_GROUP_1 route-policy RP_NAME_IN_1 import
          peer PEER_GROUP_1 route-policy RP_NAME_OUT export
          peer PEER_GROUP_2 route-policy RP_NAME_IN_2 import
          peer PEER_GROUP_2 route-policy RP_NAME_OUT export
          peer PEER_GROUP_3 route-policy RP_NAME_IN_3 import
          peer PEER_GROUP_3 route-policy RP_NAME_OUT export
        """,
    ).strip()

    config2 = dedent(
        """
        bgp 64512
         ipv4-family vpn-instance LAN
          peer PEER_GROUP_1 route-policy RP_NAME_IN_1 import
          peer PEER_GROUP_2 route-policy RP_NAME_IN_2 import
          peer PEER_GROUP_3 route-policy RP_NAME_IN_3 import
          peer PEER_GROUP_1 route-policy RP_NAME_OUT export
          peer PEER_GROUP_2 route-policy RP_NAME_OUT export
          peer PEER_GROUP_3 route-policy RP_NAME_OUT export
         ipv4-family unicast
          import-route direct route-policy RP_CONNECTED
        """,
    ).strip()

    parser = CTreeParser(platform=Platform.HUAWEI_VRP)
    root1 = parser.parse(config1)
    root2 = parser.parse(config2)

    assert len(CTreeDiffer.diff(root1, root2).config) == 0
