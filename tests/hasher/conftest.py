from collections.abc import Iterator
from typing import Self

import pytest

from ctreepo.ctree import CTree
from ctreepo.parser import CTreeParser


class HashedNode:
    def __init__(self, node_line: str, node_hash: str) -> None:
        self.line = node_line
        self.hash = node_hash
        self.children: list[Self] = []

    def __iter__(self) -> Iterator[Self]:
        """Итерируемся по детям."""
        return iter(self.children)


CONFIG_TEXT = r"""
service tcp-keepalives-in
!
interface Loopback0
 description test-0
 ip address 192.168.1.1 255.255.255.255
!
router bgp 64512
 neighbor 192.168.255.1 password 7 some-secret
 address-family ipv4
  network 192.168.100.0 mask 255.255.255.0
  neighbor 192.168.255.1 activate
 exit-address-family
 address-family vpnv6
 exit-address-family
!
""".strip()


@pytest.fixture(scope="module")
def config_tree() -> CTree:
    parser = CTreeParser("cisco_iosxe")
    root = parser.parse(CONFIG_TEXT)
    return root


# root - 52dc916d5bddaef44250ec1c6039966daa759623eeb2ee6876b7ab35922c8495
#  interface Loopback0 - c142bff0f7aca11db9afb63662aa41dfe01633441338ed1ed5bb548cef22d53a
#   description test-0 - 6f6df222d7c6bbaf447b8a7ba2c819cc929850158c1e34bf2d7658b453cdf105
#   ip address 192.168.1.1 255.255.255.255 - a9d6d939c7d3fdc0984bae09b9ace8c5aa21c7b9c38a4dd3c61590b09d852099
#  router bgp 64512 - cbb37de08483eda38aa7bd2229dc930d6493515a83ca835940a4835f77c6e8bf
#   address-family ipv4 - cfedcb8ec9d7338e1219c1f1df2e572f56e51af8389a5bb094bcbeafa03a51b4
#    neighbor 192.168.255.1 activate - dfd046fc3f6de67609a5f37a6b1b4edf065d56b9fae30af804f0f834e8ebfb6d
#    network 192.168.100.0 mask 255.255.255.0 - c1d45bd59e74f87940c7ea2837aa50ea80213e2de8317db367cec54c597ffa2d
#   address-family vpnv6 - cff39e4d317d2582e6f6b0f2856bff87098bbeaad05dacc2df6ef6450d0756be
#   neighbor 192.168.255.1 password 7 some-secret - 2149e0335e350155c2d0ab9020c3553590017e30ef87ecf12758a124c52164c8
#  service tcp-keepalives-in - d4e0f0aa67c001dfd56d54bea70a1c426a4c50d06954c460b0d5926b76e1d763


@pytest.fixture(scope="package")
def config_hash() -> dict[str, str]:
    return {
        "root": "52dc916d5bddaef44250ec1c6039966daa759623eeb2ee6876b7ab35922c8495",
        "interface Loopback0": "c142bff0f7aca11db9afb63662aa41dfe01633441338ed1ed5bb548cef22d53a",
        "description test-0": "6f6df222d7c6bbaf447b8a7ba2c819cc929850158c1e34bf2d7658b453cdf105",
        "ip address 192.168.1.1 255.255.255.255": "a9d6d939c7d3fdc0984bae09b9ace8c5aa21c7b9c38a4dd3c61590b09d852099",
        "router bgp 64512": "cbb37de08483eda38aa7bd2229dc930d6493515a83ca835940a4835f77c6e8bf",
        "address-family ipv4": "cfedcb8ec9d7338e1219c1f1df2e572f56e51af8389a5bb094bcbeafa03a51b4",
        "neighbor 192.168.255.1 activate": "dfd046fc3f6de67609a5f37a6b1b4edf065d56b9fae30af804f0f834e8ebfb6d",
        "network 192.168.100.0 mask 255.255.255.0": "c1d45bd59e74f87940c7ea2837aa50ea80213e2de8317db367cec54c597ffa2d",
        "address-family vpnv6": "cff39e4d317d2582e6f6b0f2856bff87098bbeaad05dacc2df6ef6450d0756be",
        "neighbor 192.168.255.1 password 7 some-secret": "2149e0335e350155c2d0ab9020c3553590017e30ef87ecf12758a124c52164c8",  # noqa: E501
        "service tcp-keepalives-in": "d4e0f0aa67c001dfd56d54bea70a1c426a4c50d06954c460b0d5926b76e1d763",
    }
