from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from math import sqrt
from typing import List, Optional, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .hive import Hive


HEX_ID = 0


class HException(Exception):
    pass


class Piece(Enum):
    QUEEN = auto()
    ANT = auto()
    SPIDER = auto()
    BEETLE = auto()
    GRASSHOPPER = auto()
    # MOSQUITO = auto()
    # LADYBUG = auto()


class Color(Enum):
    WHITE = auto()
    BLACK = auto()


class Direction(Enum):
    RIGHT = auto()
    UP_RIGHT = auto()
    DOWN_RIGHT = auto()
    LEFT = auto()
    UP_LEFT = auto()
    DOWN_LEFT = auto()

    def __neg__(self) -> Direction:
        return {
            Direction.RIGHT: Direction.LEFT,
            Direction.UP_RIGHT: Direction.DOWN_LEFT,
            Direction.DOWN_RIGHT: Direction.UP_LEFT,
            Direction.LEFT: Direction.RIGHT,
            Direction.UP_LEFT: Direction.DOWN_RIGHT,
            Direction.DOWN_LEFT: Direction.UP_RIGHT,
        }[self]


@dataclass
class Location:
    x: int
    y: int
    z: int

    def __post_init__(self):
        if self.x + self.y + self.z != 0:
            raise HException(f"Invalid location {self}. Coordinates must sum to zero.")

    def __repr__(self):
        return f"Location({self.x}, {self.y}, {self.z})"

    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"

    def __hash__(self):
        return (self.x, self.y, self.z).__hash__()

    def __add__(self, direction: Direction) -> Location:
        """Return a new location shifted one hex in the target direction"""
        return {
            Direction.RIGHT: Location(self.x + 1, self.y - 1, self.z),
            Direction.UP_RIGHT: Location(self.x + 1, self.y, self.z - 1),
            Direction.DOWN_RIGHT: Location(self.x, self.y - 1, self.z + 1),
            Direction.LEFT: Location(self.x - 1, self.y + 1, self.z),
            Direction.UP_LEFT: Location(self.x, self.y + 1, self.z - 1),
            Direction.DOWN_LEFT: Location(self.x - 1, self.y, self.z + 1),
        }[direction]

    def __sub__(self, other: Location) -> int:
        """Return the distance between two locations"""
        return (
            abs(self.x - other.x) + abs(self.y - other.y) + abs(self.z - other.z)
        ) / 2

    @property
    def to_offset_coordinates(self) -> Tuple[int, int]:
        """Return odd-r offset coordinates for this location"""
        col = int(self.x + (self.z - (self.z % 2)) / 2)
        row = self.z
        return col, row

    @property
    def to_pixel(self) -> Tuple[int, int]:
        x, z = self.x, self.z
        return (
            sqrt(3) * x + sqrt(3) / 2 * z,
            3 / 2 * z,
        )

    @classmethod
    def round(cls, x, y, z):
        rx = round(x)
        ry = round(y)
        rz = round(z)

        x_diff = abs(rx - x)
        y_diff = abs(ry - y)
        z_diff = abs(rz - z)

        if x_diff > y_diff and x_diff > z_diff:
            rx = -(ry + rz)
        elif y_diff > z_diff:
            ry = -(rx + rz)
        else:
            rz = -(rx + ry)

        return cls(rx, ry, rz)


@dataclass
class Hex:
    hive: Hive
    piece: Piece
    color: Color

    def __post_init__(self):
        global HEX_ID
        self.id = HEX_ID
        HEX_ID += 1

    def __hash__(self):
        return self.id

    @property
    def location(self) -> Location:
        return self.hive.get_location_of_hex(self)

    @property
    def name(self) -> str:
        return self.color.name[0] + self.piece.name[0]

    def get_neighbor(self, direction: Direction) -> Optional[Hex]:
        try:
            return self.hive.get_hex_by_location(self.location + direction)
        except HException:
            pass

    @property
    def neighbors(self) -> Set[Hex]:
        neighbors = set()
        for direction in Direction:
            neighbor = self.get_neighbor(direction)
            if neighbor is not None:
                neighbors.add(neighbor)
        return neighbors

    @property
    def num_neighbors(self) -> int:
        return len(self.neighbors)

    @property
    def can_be_moved(self) -> bool:
        location = self.location
        self.hive.remove_hex(self)
        try:
            is_connected = self.hive.is_connected
            return is_connected
        finally:
            self.hive.place_hex(self, location)

    def can_move_in_direction(self, direction: Direction) -> bool:
        if not self.can_be_moved:
            return False
        old_location = self.location
        new_location = self.location + direction
        old_neighbors = self.neighbors
        # If there's already a hex at the target location, the answer is no
        try:
            self.hive.get_hex_by_location(new_location)
            return False
        except HException:
            pass
        self.hive.remove_hex(self)
        try:
            self.hive.place_hex(self, new_location)
            new_neighbors = self.neighbors
            # If the hive is disconnected now, the answer is no
            if not self.hive.is_connected:
                return False
            # Check whether the new and old hex have two neighbors in common
            # This indicates the hex cannot be slid into place
            if len(new_neighbors & old_neighbors) >= 2:
                return False
            return True
        finally:
            try:
                self.hive.remove_hex(self)
            except HException:
                pass
            self.hive.place_hex(self, old_location)

    def move_in_direction(self, direction: Direction):
        self.hive.move_hex(self, direction)

    @property
    def empty_neighboring_locations(self) -> Set[Location]:
        locations = set()
        for direction in Direction:
            location = self.location + direction
            if not self.hive.location_is_occupied(location):
                locations.add(location)
        return locations

    @property
    def queen_moveable_locations(self) -> Set[Location]:
        locations = set()
        for direction in Direction:
            location = self.location + direction
            if self.can_move_in_direction(
                direction
            ) and not self.hive.location_is_occupied(location):
                locations.add(location)
        return locations

    @property
    def beetle_moveable_locations(self) -> Set[Location]:
        locations = set()
        for direction in Direction:
            location = self.location + direction
            if self.can_move_in_direction(direction):
                locations.add(location)
        for neighbor_hex in self.neighbors:
            locations.add(neighbor_hex.location)
        return locations

    @property
    def spider_moveable_locations(self) -> Set[Location]:
        locations = set()
        for direction_1 in Direction:
            if not self.can_move_in_direction(direction_1):
                continue
            self.move_in_direction(direction_1)
            for direction_2 in Direction:
                if direction_2 == -direction_1 or not self.can_move_in_direction(
                    direction_2
                ):
                    continue
                self.move_in_direction(direction_2)
                for direction_3 in Direction:
                    if direction_3 == -direction_2 or not self.can_move_in_direction(
                        direction_3
                    ):
                        continue
                    locations.add(self.location + direction_3)
                self.move_in_direction(-direction_2)
            self.move_in_direction(-direction_1)
        return locations

    @property
    def moveable_locations(self) -> Set[Location]:
        return {
            Piece.QUEEN: self.queen_moveable_locations,
            Piece.BEETLE: self.beetle_moveable_locations,
            Piece.SPIDER: self.spider_moveable_locations,
        }[self.piece]

    def __repr__(self) -> str:
        return (
            f"Hex({self.piece}, {self.color})<id={self.id}, location={self.location}>"
        )

    def __str__(self) -> str:
        return f"{self.color.name} {self.piece.name}"
