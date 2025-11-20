from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

from ctreepo.parser import CTreeParser

CONFIG_TEXT = r"""
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
!
interface Loopback0
 description test-0
 ip address 192.168.1.1 255.255.255.255
!
""".strip()

CONFIG_CONFIG = r"""
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
!
interface Loopback0
 description test-0
 ip address 192.168.1.1 255.255.255.255
!
""".strip()


def test_spec_read_once_single_thread(open_spy: MagicMock) -> None:
    assert open_spy.call_count == 0

    for _ in range(3):
        parser = CTreeParser("cisco_iosxe")
        root = parser.parse(CONFIG_TEXT)
        assert root.config == CONFIG_CONFIG

    assert open_spy.call_count == 1


def test_spec_read_once_multi_thread(open_spy: MagicMock) -> None:
    def make_root() -> None:
        parser = CTreeParser("cisco_iosxe")
        root = parser.parse(CONFIG_TEXT)
        assert root.config == CONFIG_CONFIG

    assert open_spy.call_count == 0

    with ThreadPoolExecutor(max_workers=3) as pool:
        _ = [pool.submit(make_root) for _ in range(6)]

    assert open_spy.call_count == 1
