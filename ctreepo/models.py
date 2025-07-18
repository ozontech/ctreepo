from dataclasses import dataclass
from enum import StrEnum, auto

__all__ = (
    "TaggingRule",
    "DiffAction",
    "Platform",
)


@dataclass(frozen=True, slots=True)
class TaggingRule:
    # - regex: ^ip vpn-instance (\\S+)$
    #   tags:
    #     - vpn
    #     - vrf
    # - regex: ^interface (\\S+)$
    #   tags:
    #     - interface
    regex: str
    tags: list[str]


class Platform(StrEnum):
    ARISTA_EOS = auto()
    CISCO_IOSXE = auto()
    HUAWEI_VRP = auto()


class DiffAction(StrEnum):
    ADD = "+"
    DEL = "-"
    EXISTS = " "
