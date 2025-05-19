from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Platform
from ctreepo.postproc.huawei_vrp import HuaweiVRPInterface


def test_pp_huawei_vrp_interface_ip() -> None:
    """Secondary ip после primary."""
    current_config = dedent(
        """
        interface GigabitEthernet0/0/1
         description test
         ip address 192.168.0.1 255.255.255.0
        #
        """,
    ).strip()
    target_config = dedent(
        """
        interface GigabitEthernet0/0/1
         description test
         ip address 192.168.2.1 255.255.255.0 sub
         ip address 192.168.1.1 255.255.255.0
        #
        """,
    ).strip()
    diff_config = dedent(
        """
        interface GigabitEthernet0/0/1
         undo ip address 192.168.0.1 255.255.255.0
         ip address 192.168.1.1 255.255.255.0
         ip address 192.168.2.1 255.255.255.0 sub
        #
        """,
    ).strip()

    parser = CTreeParser(Platform.HUAWEI_VRP)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target, post_proc_rules=[HuaweiVRPInterface])
    assert diff.config == diff_config
