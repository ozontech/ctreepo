from dataclasses import dataclass
from enum import StrEnum, auto

__all__ = (
    "TaggingRule",
    "Vendor",
    "DiffAction",
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


class Vendor(StrEnum):
    ARISTA = auto()
    CISCO = auto()
    HUAWEI = auto()
    FORTINET = auto()


class DiffAction(StrEnum):
    ADD = "+"
    DEL = "-"
    EXISTS = " "
