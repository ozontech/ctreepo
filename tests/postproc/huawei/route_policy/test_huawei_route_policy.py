from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Vendor


def test_huawei_route_policy_delete() -> None:
    current_config = dedent(
        """
        route-policy RP_NAME_1 permit node 10
         if-match ip-prefix PL_NAME_1
         if-match ip next-hop ip-prefix PL_NHOP_NAME_1
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 20
         if-match ip-prefix PL_NAME_2
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 30
         if-match ip-prefix PL_NAME_1
         if-match ip next-hop ip-prefix PL_NHOP_NAME_1_1
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 40
         if-match ip-prefix PL_NAME_1
         if-match ip next-hop ip-prefix PL_NHOP_NAME_1_2
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 50
         if-match ip-prefix PL_NAME_3
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 70
         if-match ip-prefix PL_NAME_4
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 80
         if-match ip-prefix PL_NAME_5
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 90
         if-match ip-prefix PL_NAME_6
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 100
         if-match ip-prefix PL_NAME_7
         if-match ip next-hop ip-prefix PL_NHOP_NAME_3
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_2 permit node 10
         if-match ip-prefix PL_NAME_8
        #
        route-policy RP_NAME_2 permit node 20
         if-match ip-prefix PL_NAME_9
        #
        route-policy RP_NAME_3 permit node 5
         apply community community-list CL_NAME_2 additive
        #
        """
    ).strip()
    target_config = dedent(
        """
        route-policy RP_NAME_1 permit node 10
         if-match ip-prefix PL_NAME_1
         if-match ip next-hop ip-prefix PL_NHOP_NAME_1
         apply community community-list CL_NAME_1 additive
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
        route-policy RP_NAME_1 permit node 50
         if-match ip-prefix PL_NAME_3
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 70
         if-match ip-prefix PL_NAME_4
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 80
         if-match ip-prefix PL_NAME_5
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 90
         if-match ip-prefix PL_NAME_6
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 100
         if-match ip-prefix PL_NAME_7
         if-match ip next-hop ip-prefix PL_NHOP_NAME_3
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_BLOCK deny node 10
        #
        route-policy RP_NAME_3 permit node 5
         apply community community-list CL_NAME_2 additive
        #
        """
    ).strip()
    diff_config = dedent(
        """
        route-policy RP_NAME_1 permit node 30
         undo if-match ip next-hop ip-prefix PL_NHOP_NAME_1_1
        #
        route-policy RP_BLOCK deny node 10
        #
        undo route-policy RP_NAME_1 node 20
        #
        undo route-policy RP_NAME_2 node 10
        #
        undo route-policy RP_NAME_2 node 20
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        route-policy RP_NAME_1 permit node 30
        undo if-match ip next-hop ip-prefix PL_NHOP_NAME_1_1
        quit
        route-policy RP_BLOCK deny node 10
        quit
        undo route-policy RP_NAME_1 node 20
        undo route-policy RP_NAME_2 node 10
        undo route-policy RP_NAME_2 node 20
        """
    ).strip()
    parser = CTreeParser(vendor=Vendor.HUAWEI)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
    assert diff.patch == diff_patch
