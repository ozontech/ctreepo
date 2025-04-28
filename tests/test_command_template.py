from textwrap import dedent

from ctreepo import CTreeEnv
from ctreepo.parser import CTreeParser
from ctreepo.vendors import CiscoCT, Vendor


def test_parsing_with_template() -> None:
    config_str = dedent(
        """
        hostname router.my.lab
        !
        interface loopback0
         ip address 1.2.3.4 255.255.255.0
         description test
         ip nat inside
        !
        interface loopback1
         ip address 5.4.3.2 255.255.255.0
         description test
         ip nat inside
        !
        router bgp 12345
         bgp router-id 1.2.3.4
         address-family ipv4 unicast
          neighbor 1.1.1.1 remote-as 11111
          neighbor 1.1.1.1 description test peer1
          neighbor 2.2.2.2 remote-as 11112
          neighbor 2.2.2.2 description test peer2
        !
        """
    )
    template_str = dedent(
        """
        hostname (?P<HOSTNAME>\\S+)
        !
        interface \\S+
         ip address (?P<IP>\\S+) (?P<MASK>\\S+)
         description (?P<DESCRIPTION>.*)
        !
        router bgp \\d+
         bgp router-id (?P<BGP_RID>\\S+)
         address-family .*
          neighbor \\S+ description (?P<DESCRIPTION>.*)
        !
        """
    )
    root_config = dedent(
        """
        hostname router.my.lab
        !
        interface loopback0
         ip address 1.2.3.4 255.255.255.0
         description test
         ip nat inside
        !
        interface loopback1
         ip address 5.4.3.2 255.255.255.0
         description test
         ip nat inside
        !
        router bgp 12345
         bgp router-id 1.2.3.4
         address-family ipv4 unicast
          neighbor 1.1.1.1 remote-as 11111
          neighbor 1.1.1.1 description test peer1
          neighbor 2.2.2.2 remote-as 11112
          neighbor 2.2.2.2 description test peer2
        !
        """
    ).strip()

    parser = CTreeParser(vendor=Vendor.CISCO)
    template = parser.parse(template_str)
    root = parser.parse(config_str, template)
    assert root.config == root_config

    assert root.children["interface loopback0"].template == ""
    assert root.children["hostname router.my.lab"].template == "hostname (?P<HOSTNAME>\\S+)"
    af = root.children["router bgp 12345"].children["address-family ipv4 unicast"]
    assert (
        af.children["neighbor 1.1.1.1 description test peer1"].template
        == "neighbor 1.1.1.1 description (?P<DESCRIPTION>.*)"
    )
    assert (
        af.children["neighbor 2.2.2.2 description test peer2"].template
        == "neighbor 2.2.2.2 description (?P<DESCRIPTION>.*)"
    )


def test_diff_with_template() -> None:
    current_config = dedent(
        """
        hostname router.my.lab
        !
        interface loopback0
         ip address 1.2.3.4 255.255.255.0
         description test
         ip nat inside
        !
        interface loopback1
         ip address 5.4.3.2 255.255.255.0
         description test
         ip nat inside
        !
        router bgp 12345
         bgp router-id 1.2.3.4
         address-family ipv4 unicast
          neighbor 1.1.1.1 remote-as 11111
          neighbor 1.1.1.1 description test peer1
          neighbor 2.2.2.2 remote-as 11112
          neighbor 2.2.2.2 description test peer2
        !
        """
    )
    target_config = dedent(
        """
        hostname router.my.lab
        !
        interface loopback0
         ip address 1.2.3.4 255.255.255.0
         description test
         ip nat inside
        !
        interface loopback1
         ip address 5.4.3.2 255.255.255.0
         description test-new
         ip nat inside
        !
        router bgp 12345
         bgp router-id 1.2.3.4
         address-family ipv4 unicast
          neighbor 1.1.1.1 remote-as 11111
          neighbor 1.1.1.1 description test peer1 new
          neighbor 2.2.2.2 remote-as 11112
          neighbor 2.2.2.2 description test peer2 new
        !
        """
    )
    template = dedent(
        """
        hostname (?P<HOSTNAME>\\S+)
        !
        interface \\S+
         ip address (?P<IP>\\S+) (?P<MASK>\\S+)
         description (?P<DESCRIPTION>.*)
        !
        router bgp \\d+
         bgp router-id (?P<BGP_RID>\\S+)
         address-family .*
          neighbor \\S+ description (?P<DESCRIPTION>.*)
        !
        """
    )
    diff_config = dedent(
        """
        interface loopback1
         description test-new
        !
        router bgp 12345
         address-family ipv4 unicast
          neighbor 1.1.1.1 description test peer1 new
          neighbor 2.2.2.2 description test peer2 new
        !
        """
    ).strip()

    env = CTreeEnv(vendor=Vendor.CISCO, template=template)
    current = env.parse(current_config)
    target = env.parse(target_config)
    diff = env.diff(current, target)
    assert diff.config == diff_config


def test_corner_cases_with_template() -> None:
    node = CiscoCT(
        line="hostname router.my.lab",
        parent=None,
        tags=["hostname"],
        template=r"hostname (?P<HOSTNAME>\S+)",
    )
    assert node.template == r"hostname (?P<HOSTNAME>\S+)"

    node = CiscoCT(
        line="hostname router.my.lab",
        parent=None,
        tags=["hostname"],
        template=r"hostname .*",
    )
    assert node.template == ""


def test_no_command_with_template() -> None:
    current_config = dedent(
        """
        interface gi0/0/0
         description some interface
         no some-no-command 40
        !
        """
    )
    target_config = dedent(
        """
        interface gi0/0/0
         description some interface-new
         no some-no-command 50
        !
        """
    )
    template = dedent(
        r"""
        interface .*
         description (?P<DESCRIPTION>.*)
         no some-no-command (?P<VALUE>\d+)
        !
        """
    )
    diff_raw = dedent(
        """
        interface gi0/0/0
         no description some interface
         some-no-command 40
         description some interface-new
         no some-no-command 50
        !
        """
    ).strip()
    diff_with_template = dedent(
        """
        interface gi0/0/0
         description some interface-new
         no some-no-command 50
        !
        """
    ).strip()
    env = CTreeEnv(vendor=Vendor.CISCO)
    current = env.parse(current_config)
    target = env.parse(target_config)
    diff = env.diff(current, target)
    assert diff.config == diff_raw

    template_tree = env.parse(template)
    env = CTreeEnv(vendor=Vendor.CISCO, template=template_tree)
    current = env.parse(current_config)
    target = env.parse(target_config)
    diff = env.diff(current, target)
    assert diff.config == diff_with_template
