from .hex import (
    Color,
    Piece,
    Location,
    Direction,
    HException,
    Hex,
)
from .draw import Draw
from collections import defaultdict
from typing import Dict, Set, List
from threading import Thread


class Hive:
    def __init__(self):
        self.location_to_hex: Dict[Location, list[Hex]] = defaultdict(list)
        self.hex_to_location: Dict[Hex, Location] = {}
        self.drawer: Draw = Draw(self)
        self.draw_thread = Thread(target=self.drawer.draw_hive, daemon=True)
        self.draw_thread.start()

    def create_hex(self, piece: Piece, color: Color, location: Location = None) -> Hex:
        hex = Hex(self, piece, color)
        if location is not None:
            self.place_hex(hex, location)
        return hex

    def place_hex(self, hex: Hex, location: Location):
        if hex in self.hex_to_location:
            raise HException(f"Hex {hex} is already on the grid.")
        if self.location_to_hex[location] and hex.piece != Piece.BEETLE:
            raise HException(f"There is already a hex at location {location}.")
        self.location_to_hex[location].append(hex)
        self.hex_to_location[hex] = location

    def move_hex(self, hex: Hex, direction: Direction):
        if not hex.can_be_moved:
            raise HException(f"Moving {hex} would disconnect the hive.")
        if not hex.can_move_in_direction(direction):
            raise HException(f"Hex {hex} cannot move in direction {direction}.")
        old_location = hex.location
        self.remove_hex(hex)
        self.place_hex(hex, old_location + direction)

    def get_all_hexes_at_location(self, location: Location) -> List[Hex]:
        return self.location_to_hex[location]

    def get_top_hex_by_location(self, location: Location) -> Hex:
        try:
            return self.get_all_hexes_at_location(location)[-1]
        except IndexError:
            raise HException(f"No hex was found at location {location}.")

    def get_location_of_hex(self, hex: Hex) -> Location:
        try:
            return self.hex_to_location[hex]
        except KeyError:
            raise HException(f"Hex {hex} was not found in the grid.")

    def remove_hex(self, hex: Hex):
        location = self.get_location_of_hex(hex)
        del self.hex_to_location[hex]
        if hex == self.location_to_hex[location][-1]:
            self.location_to_hex[location].pop()
        else:
            raise HException(
                f"Hex {hex} is beneath hex {self.location_to_hex[location][-1]} and cannot be removed."
            )

    def location_is_occupied(self, location: Location):
        try:
            self.get_top_hex_by_location(location)
            return True
        except HException:
            return False

    @property
    def empty_neighboring_locations(self) -> Set[Location]:
        locations = set()
        for hex in self.hex_to_location.keys():
            locations |= hex.empty_neighboring_locations
        return locations

    @property
    def all_hexes(self) -> Set[Hex]:
        return set(self.hex_to_location.keys())

    @property
    def all_top_level_hexes(self) -> Set[Hex]:
        hexes = set()
        for hex in self.all_hexes:
            if hex.is_on_top:
                hexes.add(hex)
        return hexes

    @property
    def connected_hexes(self) -> set:
        """Breadth first search"""
        visited_hexes = set()
        start_hex = list(self.all_top_level_hexes)[0]
        connected_hexes = start_hex.neighbors
        while True:
            if connected_hexes == visited_hexes:
                break
            hexes_to_check = connected_hexes - visited_hexes
            for hex in hexes_to_check:
                connected_hexes |= hex.neighbors
                visited_hexes.add(hex)
        return connected_hexes

    @property
    def is_connected(self) -> bool:
        return self.all_top_level_hexes == self.connected_hexes

    # @property
    # def offset_grid_graph(self) -> Dict[Hex, Tuple[int, int]]:
    #     return {
    #         hex: hex.location.offset_coordinates for hex in self.hex_to_location.keys()
    #     }

    # def get_hex_at_offset_coordinates(
    #     self, offset_cooredinates: Tuple[int, int]
    # ) -> Hex:
    #     inverse_offset_grid = {v: k for k, v in self.offset_grid_graph.items()}
    #     try:
    #         return inverse_offset_grid[offset_cooredinates]
    #     except KeyError:
    #         raise HException(
    #             f"There is no hex at offset coordinates {offset_cooredinates}."
    #         )

    # @property
    # def offset_grid_bounds(self) -> Tuple[int, int, int, int]:
    #     """Find min and max row and column numbers in offset coordinates"""
    #     min_col, min_row, max_col, max_row = None, None, None, None
    #     for offset_coordinates in self.offset_grid_graph.values():
    #         col, row = offset_coordinates
    #         if min_col is None or min_row is None:
    #             min_col = max_col = col
    #             min_row = max_row = row
    #         if col < min_col:
    #             min_col = col
    #         elif col > max_col:
    #             max_col = col
    #         if row < min_row:
    #             min_row = row
    #         elif row > max_row:
    #             max_row = row
    #     return min_col, min_row, max_col, max_row

    # @property
    # def offset_grid(self) -> List[List[Optional[Hex]]]:
    #     min_col, min_row, max_col, max_row = self.offset_grid_bounds
    #     num_cols = max_col - min_col + 1
    #     num_rows = max_row - min_row + 1
    #     grid = [[None] * num_cols for _ in range(num_rows)]
    #     for grid_row in range(num_rows):
    #         for grid_col in range(num_cols):
    #             offset_col = min_col + grid_col
    #             offset_row = min_row + grid_row
    #             try:
    #                 hex = self.get_hex_at_offset_coordinates((offset_col, offset_row))
    #                 grid[grid_row][grid_col] = hex
    #             except HException:
    #                 pass
    #     return grid, min_row % 2

    # def __repr__(self):
    #     grid_str = ""
    #     offset_grid, first_row_parity = self.offset_grid
    #     for row_idx, row in enumerate(offset_grid):
    #         row_str = (
    #             " " * 4 * ((row_idx + first_row_parity) % 2)
    #         )  # Odd rows are offset by four spaces
    #         for hex in row:
    #             if hex is not None:
    #                 hex_name = hex.name
    #             else:
    #                 hex_name = "  "
    #             row_str += hex_name + "      "
    #         grid_str += row_str + "\n"
    #     return grid_str
