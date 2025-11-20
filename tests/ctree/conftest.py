import pytest

from ctreepo.ctree import CTree
from ctreepo.parser import CTreeParser

CONFIG_TEXT = """
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
!
route-map rm_DENY deny 10
!
interface Loopback0
 description test-0
 ip address 192.168.1.1 255.255.255.255
!
interface Loopback100
 description test-100
 ip address 192.168.1.1 255.255.255.255
!
interface Loopback200
 description test-200
 ip address 192.168.200.1 255.255.255.255
!
interface FastEthernet0
 switchport access vlan 100
 no ip address
!
route-map rm_PERMIT permit 10
!
router bgp 64512
 neighbor 192.168.255.1 remote-as 64512
 neighbor 192.168.255.1 update-source Loopback0
 neighbor 192.168.255.1 password 7 some-secret
 address-family ipv4
  network 192.168.100.0 mask 255.255.255.0
  neighbor 192.168.255.1 activate
 exit-address-family
 address-family vpnv4
  network 192.168.1.0 mask 255.255.255.0
 exit-address-family
 address-family ipv6
 exit-address-family
 address-family vpnv6
 exit-address-family
!
""".strip()

CONFIG_PATCH = """
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
route-map rm_DENY deny 10
exit
interface Loopback0
description test-0
ip address 192.168.1.1 255.255.255.255
exit
interface Loopback100
description test-100
ip address 192.168.1.1 255.255.255.255
exit
interface Loopback200
description test-200
ip address 192.168.200.1 255.255.255.255
exit
interface FastEthernet0
switchport access vlan 100
no ip address
exit
route-map rm_PERMIT permit 10
exit
router bgp 64512
neighbor 192.168.255.1 remote-as 64512
neighbor 192.168.255.1 update-source Loopback0
neighbor 192.168.255.1 password 7 some-secret
address-family ipv4
network 192.168.100.0 mask 255.255.255.0
neighbor 192.168.255.1 activate
exit
address-family vpnv4
network 192.168.1.0 mask 255.255.255.0
exit
address-family ipv6
exit
address-family vpnv6
exit
exit
""".strip()


@pytest.fixture(scope="package")
def config_text() -> str:
    return CONFIG_TEXT


@pytest.fixture(scope="package")
def config_patch() -> str:
    return CONFIG_PATCH


@pytest.fixture(scope="package")
def config_tree() -> CTree:
    parser = CTreeParser("cisco_iosxe")
    root = parser.parse(CONFIG_TEXT)
    return root
