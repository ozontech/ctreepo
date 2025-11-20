from textwrap import dedent

from ctreepo.differ import CTreeDiffer
from ctreepo.parser import CTreeParser


def test_differ_naive(parser: CTreeParser, current_config: str, target_config: str) -> None:
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target)
    expected = dedent(
        """
        interface Loopback0
         no description test-0
         no ip address 192.168.1.1 255.255.255.255
         description test-0-changed
         ip address 192.168.1.2 255.255.255.255
        !
        interface FastEthernet0
         ip address
         no load-interval 30
         ip address 192.168.123.1 255.255.255.252
         load-interval 60
        !
        router bgp 64512
         no neighbor 192.168.255.1 password 7 some-secret-old-hash
         address-family ipv4
          no network 192.168.100.0 mask 255.255.255.0
          no neighbor 192.168.255.1 route-map rm_TEST_in_OLD in
          no neighbor 192.168.255.2 activate
          network 192.168.200.0 mask 255.255.255.0
          neighbor 192.168.255.1 route-map rm_TEST_in in
         !
         neighbor 192.168.255.1 password 7 some-secret-new-hash
         address-family vpnv4
          network 192.168.2.0 mask 255.255.255.0
         !
        !
        no service pad
        !
        interface Loopback300
         description test-300
         ip address 192.168.103.1 255.255.255.255
        !
        route-map rm_PERMIT permit 10
         match ip address 101
        !
        service dhcp
        no route-map rm_DENY deny 10
        !
        interface Loopback100
         no description test-100
        !
        no interface Loopback400
        !
        """,
    ).strip()
    assert diff.config == expected


def test_differ_masked(parser: CTreeParser, current_config: str, target_config: str) -> None:
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target, masked=True)
    expected = dedent(
        """
        interface Loopback0
         no description test-0
         no ip address 192.168.1.1 255.255.255.255
         description test-0-changed
         ip address 192.168.1.2 255.255.255.255
        !
        interface FastEthernet0
         ip address
         no load-interval 30
         ip address 192.168.123.1 255.255.255.252
         load-interval 60
        !
        router bgp 64512
         address-family ipv4
          no network 192.168.100.0 mask 255.255.255.0
          no neighbor 192.168.255.1 route-map rm_TEST_in_OLD in
          no neighbor 192.168.255.2 activate
          network 192.168.200.0 mask 255.255.255.0
          neighbor 192.168.255.1 route-map rm_TEST_in in
         !
         address-family vpnv4
          network 192.168.2.0 mask 255.255.255.0
         !
        !
        no service pad
        !
        interface Loopback300
         description test-300
         ip address 192.168.103.1 255.255.255.255
        !
        route-map rm_PERMIT permit 10
         match ip address 101
        !
        service dhcp
        no route-map rm_DENY deny 10
        !
        interface Loopback100
         no description test-100
        !
        no interface Loopback400
        !
        """,
    ).strip()
    assert diff.config == expected


def test_differ_with_template(parser: CTreeParser, current_config: str, target_config: str) -> None:
    template_text = dedent(
        r"""
        interface \S+
         (description) (?P<VAL>.*)               UNDO>> no \1
         no ip address                           UNDO>> <<--n/a-->>
         ip address (?P<IP>\S+) (?P<MASK>\S+)    UNDO>> no ip address \g<IP> \g<MASK>
         load-interval (?P<VAL>\d+)              UNDO>> no load-interval
        """,
    )
    template = parser.parse(template_text)
    current = parser.parse(current_config, template)
    target = parser.parse(target_config, template)
    diff = CTreeDiffer.diff(current, target)
    expected = dedent(
        """
        interface Loopback0
         description test-0-changed
         ip address 192.168.1.2 255.255.255.255
        !
        interface FastEthernet0
         ip address 192.168.123.1 255.255.255.252
         load-interval 60
        !
        router bgp 64512
         no neighbor 192.168.255.1 password 7 some-secret-old-hash
         address-family ipv4
          no network 192.168.100.0 mask 255.255.255.0
          no neighbor 192.168.255.1 route-map rm_TEST_in_OLD in
          no neighbor 192.168.255.2 activate
          network 192.168.200.0 mask 255.255.255.0
          neighbor 192.168.255.1 route-map rm_TEST_in in
         !
         neighbor 192.168.255.1 password 7 some-secret-new-hash
         address-family vpnv4
          network 192.168.2.0 mask 255.255.255.0
         !
        !
        no service pad
        !
        interface Loopback300
         description test-300
         ip address 192.168.103.1 255.255.255.255
        !
        route-map rm_PERMIT permit 10
         match ip address 101
        !
        service dhcp
        no route-map rm_DENY deny 10
        !
        interface Loopback100
         no description
        !
        no interface Loopback400
        !
        """,
    ).strip()
    assert diff.config == expected
