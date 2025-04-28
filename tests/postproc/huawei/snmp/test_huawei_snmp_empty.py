from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Vendor


def test_huawei_snmp_empty() -> None:
    # удалить узлы с нулевым community
    current_config = dedent(
        """
        snmp-agent community read cipher public12345 mib-view iso-view alias __CommunityRO
        snmp-agent community read cipher public12345
        snmp-agent sys-info location my-location
        snmp-agent sys-info version v2c v3
        """
    )
    target_config = dedent(
        """
        snmp-agent community read cipher public12345 mib-view iso-view alias __CommunityRO_1
        snmp-agent community read cipher  mib-view iso-view alias __CommunityRO
        snmp-agent community read cipher
        snmp-agent sys-info location my-location
        snmp-agent sys-info version v2c v3
        """
    )
    diff_config = dedent(
        """
        snmp-agent community read cipher public12345 mib-view iso-view alias __CommunityRO_1
        #
        """
    ).strip()

    parser = CTreeParser(Vendor.HUAWEI)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
