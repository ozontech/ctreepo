import builtins
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest import MonkeyPatch
from pytest_mock import MockerFixture

from ctreepo.ctree import CTree
from ctreepo.parser import CTreeParser
from ctreepo.spec import PlatformRegistry

CONFIG_TEXT = r"""
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
!
interface Loopback0
 description test-0
 ip address 192.168.1.1 255.255.255.255
!
""".strip()


# тут в SpecFactory уже есть платформа CISCO_IOSXE (от других запусков тестов), поэтому новую платформу
# не подгрузить поверх, поэтому делаем monkeypatch и обнуляем внутренний словарь. Может есть другой вариант,
# например делать в другой платформе, но пока так.
@pytest.fixture(scope="function")
def config_tree_rewritten_spec(monkeypatch: MonkeyPatch) -> CTree:
    monkeypatch.setattr(PlatformRegistry, "_PLATFORMS", {})
    parser = CTreeParser(
        "cisco_iosxe",
        custom_platform_yaml=Path(Path(__file__).parent, "./_spec_cisco_iosxe_v2.yaml"),
    )
    root = parser.parse(CONFIG_TEXT)
    return root


@pytest.fixture(scope="function")
def open_spy(
    monkeypatch: MonkeyPatch,
    mocker: MockerFixture,
) -> MagicMock:
    monkeypatch.setattr(PlatformRegistry, "_PLATFORMS", {})
    open_spy = mocker.spy(builtins, "open")
    return open_spy
