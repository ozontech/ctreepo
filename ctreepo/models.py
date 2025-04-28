from dataclasses import dataclass
from enum import StrEnum

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
    ARISTA = "arista"
    CISCO = "cisco"
    HUAWEI = "huawei"


class DiffAction(StrEnum):
    ADD = "+"
    DEL = "-"
    EXISTS = " "
