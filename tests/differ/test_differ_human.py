from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Platform

current_config = dedent(
    """
    interface Tunnel1
     ip address 10.0.0.2 255.255.255.0
     ip address 10.2.0.2 255.255.255.0 secondary
     no ip redirects
    !
    interface Tunnel2
     ip address 10.1.0.2 255.255.255.0
     no ip redirects
    !
    interface Tunnel4
    !
    interface Tunnel5
     ip address 10.1.0.2 255.255.255.0
     no ip redirects
    !
    enable password 7 secret
    !
    router bgp 12345
     bgp router-id 1.2.3.4
     address-family ipv4 unicast
      redistribute static
      network 1.2.3.0 255.255.255.0
      some subsection
       line 3
       line 1
       line 5
       line 6
    !
    router ospf 1
     router-id 1.2.3.4
    !
    """,
).strip()

target_config = dedent(
    """
    interface Tunnel1
     ip address 10.0.0.2 255.255.255.0
     no ip redirects
    !
    interface Tunnel2
     ip address 10.1.0.3 255.255.255.0
     ip address 10.2.0.2 255.255.255.0 secondary
     no ip redirects
    !
    interface Tunnel3
     no ip redirects
    !
    interface Tunnel4
     no ip redirects
    !
    enable password
    !
    router bgp 12345
     bgp router-id 1.2.3.4
     address-family ipv4 unicast
      redistribute connected
      some subsection
       line 1
       line 2
       line 3
    !
    router ospf 1
     router-id 4.3.2.1
    !
    """,
).strip()


def test_differ_human_full() -> None:
    expected_diff = dedent(
        """
         interface Tunnel1
          ip address 10.0.0.2 255.255.255.0
        - ip address 10.2.0.2 255.255.255.0 secondary
          no ip redirects
         !
         interface Tunnel2
        - ip address 10.1.0.2 255.255.255.0
        + ip address 10.1.0.3 255.255.255.0
        + ip address 10.2.0.2 255.255.255.0 secondary
          no ip redirects
         !
        +interface Tunnel3
        + no ip redirects
         !
         interface Tunnel4
        + no ip redirects
         !
        -interface Tunnel5
        - ip address 10.1.0.2 255.255.255.0
        - no ip redirects
         !
        -enable password 7 secret
         !
        +enable password
         !
         router bgp 12345
          bgp router-id 1.2.3.4
          address-family ipv4 unicast
        -  redistribute static
        -  network 1.2.3.0 255.255.255.0
        +  redistribute connected
           some subsection
        +   line 2
            line 3
            line 1
        -   line 5
        -   line 6
         !
         router ospf 1
        - router-id 1.2.3.4
        + router-id 4.3.2.1
         !
        """,
    ).strip("\n")
    parser = CTreeParser(Platform.CISCO_IOSXE)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.human_diff(current=current, target=target, mode="full")
    assert diff == expected_diff


def test_differ_human_diff_only() -> None:
    expected_diff = dedent(
        """
         interface Tunnel1
        - ip address 10.2.0.2 255.255.255.0 secondary
         !
         interface Tunnel2
        - ip address 10.1.0.2 255.255.255.0
        + ip address 10.1.0.3 255.255.255.0
        + ip address 10.2.0.2 255.255.255.0 secondary
         !
        +interface Tunnel3
        + no ip redirects
         !
         interface Tunnel4
        + no ip redirects
         !
        -interface Tunnel5
        - ip address 10.1.0.2 255.255.255.0
        - no ip redirects
         !
        -enable password 7 secret
         !
        +enable password
         !
         router bgp 12345
          address-family ipv4 unicast
        -  redistribute static
        -  network 1.2.3.0 255.255.255.0
        +  redistribute connected
           some subsection
        +   line 2
        -   line 5
        -   line 6
         !
         router ospf 1
        - router-id 1.2.3.4
        + router-id 4.3.2.1
         !
        """,
    ).strip("\n")
    parser = CTreeParser(Platform.CISCO_IOSXE)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.human_diff(current=current, target=target, mode="diff-only")
    assert diff == expected_diff


def test_differ_human_add_all() -> None:
    """Сравнение пустой конфигурации с целевой."""
    expected_diff = dedent(
        """
        +interface Tunnel1
        + ip address 10.0.0.2 255.255.255.0
        + no ip redirects
         !
        +interface Tunnel2
        + ip address 10.1.0.3 255.255.255.0
        + ip address 10.2.0.2 255.255.255.0 secondary
        + no ip redirects
         !
        +interface Tunnel3
        + no ip redirects
         !
        +interface Tunnel4
        + no ip redirects
         !
        +enable password
         !
        +router bgp 12345
        + bgp router-id 1.2.3.4
        + address-family ipv4 unicast
        +  redistribute connected
        +  some subsection
        +   line 1
        +   line 2
        +   line 3
         !
        +router ospf 1
        + router-id 4.3.2.1
         !
        """,
    ).strip("\n")
    parser = CTreeParser(Platform.CISCO_IOSXE)
    current = parser.parse("")
    target = parser.parse(target_config)
    diff = CTreeDiffer.human_diff(current=current, target=target, mode="full")
    assert diff == expected_diff


def test_differ_human_delete_all() -> None:
    """Сравнение целевой с пустой конфигурацией."""
    expected_diff = dedent(
        """
        -interface Tunnel1
        - ip address 10.0.0.2 255.255.255.0
        - ip address 10.2.0.2 255.255.255.0 secondary
        - no ip redirects
         !
        -interface Tunnel2
        - ip address 10.1.0.2 255.255.255.0
        - no ip redirects
         !
        -interface Tunnel4
         !
        -interface Tunnel5
        - ip address 10.1.0.2 255.255.255.0
        - no ip redirects
         !
        -enable password 7 secret
         !
        -router bgp 12345
        - bgp router-id 1.2.3.4
        - address-family ipv4 unicast
        -  redistribute static
        -  network 1.2.3.0 255.255.255.0
        -  some subsection
        -   line 3
        -   line 1
        -   line 5
        -   line 6
         !
        -router ospf 1
        - router-id 1.2.3.4
         !
        """,
    ).strip("\n")
    parser = CTreeParser(Platform.CISCO_IOSXE)
    current = parser.parse(current_config)
    target = parser.parse("")
    diff = CTreeDiffer.human_diff(current=current, target=target, mode="full")
    assert diff == expected_diff


def test_differ_human_no_diff() -> None:
    """Сравнение одинаковых конфигураций."""
    expected_diff = ""

    parser = CTreeParser(Platform.CISCO_IOSXE)
    current = parser.parse(current_config)
    target = parser.parse(current_config)
    diff = CTreeDiffer.human_diff(current=current, target=target, mode="diff-only")
    assert diff == expected_diff
