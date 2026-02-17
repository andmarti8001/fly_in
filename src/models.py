# andmarti

from __future__ import annotations

from enum import Enum
from typing import ClassVar


class Metadata(str, Enum):
    """Supported metadata keys from the parsing spec."""
    ZONE = "zone"
    COLOR = "color"
    MAX_DRONES = "max_drones"
    MAX_LINK_CAPACITY = "max_link_capacity"


class ZoneType(str, Enum):
    """Allowed zone types from the parsing spec."""
    # costs 1 turn
    NORMAL = "normal"
    # blocked, may not traverse these hubs will be pruned
    BLOCKED = "blocked"
    # costs 2 turns: one turn in transit
    # and one turn on node
    RESTRICTED = "restricted"
    # costs 1 turn, but preferred over normal zone
    PRIORITY = "priority"
    # unlimited capacity all drones start here
    START = "start_hub"
    # unlimited capacity all drones must arrive here
    END = "end_hub"


class Color(str, Enum):
    """Known map colors mapped to ANSI terminal color codes."""

    DEFAULT = "\033[37m"
    BLACK = "\033[30m"
    BLUE = "\033[34m"
    BROWN = "\033[38;5;94m"
    CRIMSON = "\033[38;5;197m"
    CYAN = "\033[36m"
    DARKRED = "\033[38;5;88m"
    GOLD = "\033[38;5;220m"
    GREEN = "\033[32m"
    LIME = "\033[38;5;118m"
    MAGENTA = "\033[35m"
    MAROON = "\033[38;5;1m"
    ORANGE = "\033[38;5;208m"
    PURPLE = "\033[38;5;93m"
    RED = "\033[31m"
    VIOLET = "\033[38;5;177m"
    YELLOW = "\033[33m"
    RESET = "\033[0m"

    @classmethod
    def code_for_name(cls, color_name: str) -> str:
        """Resolve color name to ANSI code, using DEFAULT when unsupported."""
        enum_member = cls.__members__.get(color_name.strip().upper())
        if enum_member is None:
            return cls.DEFAULT.value
        return enum_member.value


class Hub:
    _next_id: ClassVar[int] = 0

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone: ZoneType = ZoneType.NORMAL,
        color: str | None = None,
        max_drones: int = 1
    ) -> None:
        self.id = Hub._next_id
        Hub._next_id += 1
        self.name = name
        self.x = x
        self.y = y
        self.zone = zone
        self.color = color
        self.max_drones = max_drones

    def print(self) -> None:
        print(f"id: {self.id}")
        print(f"name: {self.name}")
        print(f"x: {self.x}")
        print(f"y: {self.y}")
        print(f"zone: {self.zone.value}")
        color_name: str = self.color if self.color is not None else "none"
        color_lookup: str = self.color if self.color is not None else "default"
        color_code: str = Color.code_for_name(color_lookup)
        color_swatch: str = f"{color_code}##{Color.RESET.value}"
        print(f"color: {color_name} ({color_swatch})")
        print(f"max_drones: {self.max_drones}")


class Connection:
    def __init__(
        self,
        hub1: str,
        hub2: str,
        max_link_capacity: int = 1
    ) -> None:
        self.hub1 = hub1
        self.hub2 = hub2
        self.max_link_capacity = max_link_capacity

    def print(self) -> None:
        print(f"hub1: {self.hub1}")
        print(f"hub2: {self.hub2}")
        print(f"max_link_capacity: {self.max_link_capacity}")


# class FlyInManager:
#     """ this class manages the map for fly_in 42 project """
#     def __init__(
#         self,
#         nb_drones: int,
#         hubs: list[Hub],
#         connections: list[Connection],
#         adjacency_list: dict[str, list[str]]
#     ) -> None:
