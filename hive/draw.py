from __future__ import annotations

from .hex import Color, Direction, HException, Hex, Location, Piece
from math import sqrt, sin, cos, pi
from pygame import gfxdraw
from pygame import freetype
from typing import List, Optional, TYPE_CHECKING, Tuple

import pygame

if TYPE_CHECKING:
    from .hive import Hive


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

SCROLL_SPEED = 4
ZOOM_SPEED = 2

IMAGES = {
    Piece.QUEEN: "hive/static/pieces/queen.png",
    Piece.ANT: "hive/static/pieces/ant.png",
    Piece.BEETLE: "hive/static/pieces/beetle.png",
    Piece.GRASSHOPPER: "hive/static/pieces/grasshopper.png",
    Piece.SPIDER: "hive/static/pieces/spider.png",
}


class Draw:
    def __init__(self, hive: Hive):
        self.hive = hive
        self.radius = 100
        self.selected_hex: Optional[Hex] = None
        self.possible_moves: List[Hex] = []

    def draw_hex(self, hex: Hex):
        center_x, center_y = self.center
        x, y = hex.location.to_pixel
        x = self.radius * x + center_x
        y = self.radius * y + center_y
        img = pygame.image.load(IMAGES[hex.piece])
        img_rect = img.get_rect()
        max_dim = max(img_rect.width, img_rect.height)
        img_width = 1.3 * self.radius * img_rect.width / max_dim
        img_height = 1.3 * self.radius * img_rect.height / max_dim
        img_rect = pygame.Rect(
            x - img_width / 2, y - img_height / 2, x + img_width / 2, y + img_height / 2
        )
        img = pygame.transform.scale(img, (int(img_width), int(img_height)))
        args = [
            self.screen,
            [
                (
                    x + (0.96 * self.radius) * cos(pi * (i / 3 - 1 / 6)),
                    y + (0.96 * self.radius) * sin(pi * (i / 3 - 1 / 6)),
                )
                for i in range(6)
            ],
            BLACK,
        ]
        if hex.color == Color.BLACK:
            gfxdraw.filled_polygon(*args)
            gfxdraw.aapolygon(*args)
        else:
            gfxdraw.aapolygon(*args)
        self.screen.blit(img, img_rect)

    def draw_preview_hex(self, hex: Hex, idx: int):
        preview_radius = (0.3 / 1.3) * self.radius
        center_x, center_y = self.center
        x, y = hex.location.to_pixel
        x = self.radius * x + center_x + 0.7 * self.radius
        y = (
            self.radius * y
            + center_y
            - 0.45 * self.radius
            + 2 * idx * (preview_radius + 1)
        )
        img = pygame.image.load(IMAGES[hex.piece])
        img_rect = img.get_rect()
        max_dim = max(img_rect.width, img_rect.height)
        img_width = 0.3 * self.radius * img_rect.width / max_dim
        img_height = 0.3 * self.radius * img_rect.height / max_dim
        img_rect = pygame.Rect(
            x - img_width / 2, y - img_height / 2, x + img_width / 2, y + img_height / 2
        )
        img = pygame.transform.scale(img, (int(img_width), int(img_height)))
        args = [
            self.screen,
            [
                (
                    x + preview_radius * cos(pi * (i / 3 - 1 / 6)),
                    y + preview_radius * sin(pi * (i / 3 - 1 / 6)),
                )
                for i in range(6)
            ],
        ]
        if hex.color == Color.BLACK:
            gfxdraw.filled_polygon(*args, BLACK)
            gfxdraw.aapolygon(*args, WHITE)
        else:
            gfxdraw.filled_polygon(*args, WHITE)
            gfxdraw.aapolygon(*args, BLACK)
        self.screen.blit(img, img_rect)

    def highlight_hex_at_location(
        self, location: Location, color: Tuple[int, int, int]
    ):
        center_x, center_y = self.center
        transparent_color = color + (50,)
        x, y = location.to_pixel
        x = self.radius * x + center_x
        y = self.radius * y + center_y
        args = [
            self.screen,
            [
                (
                    x + (0.96 * self.radius) * cos(pi * (i / 3 - 1 / 6)),
                    y + (0.96 * self.radius) * sin(pi * (i / 3 - 1 / 6)),
                )
                for i in range(6)
            ],
        ]
        gfxdraw.filled_polygon(*args, transparent_color)
        gfxdraw.aapolygon(*args, color)

    def highlight_selected_hex(self):
        self.highlight_hex_at_location(self.selected_hex.location, RED)

    def highlight_possible_moves(self):
        for location in self.possible_moves:
            self.highlight_hex_at_location(location, BLUE)

    def draw_number_on_hex(self, number: int, hex: Hex):
        if hex.color == Color.WHITE:
            text_color = BLACK
        else:
            text_color = WHITE
        center_x, center_y = self.center
        x, y = hex.location.to_pixel
        x = self.radius * x + center_x + 0.7 * self.radius
        y = self.radius * y + center_y - 0.45 * self.radius
        self.font.render_to(self.screen, (x, y), str(number), text_color)

    def mouse_position_to_location(self, mouse_position):
        mouse_x, mouse_y = mouse_position
        center_x, center_y = self.center
        mouse_x -= center_x
        mouse_y -= center_y
        x = (sqrt(3) / 3 * mouse_x - 1 / 3 * mouse_y) / self.radius
        z = (2 / 3 * mouse_y) / self.radius
        y = -(x + z)
        location = Location.round(x, y, z)
        return location

    def mouse_position_to_hex(self, mouse_position):
        location = self.mouse_position_to_location(mouse_position)
        return self.hive.get_top_hex_by_location(location)

    def draw_hive(self):
        pygame.init()
        pygame.display.set_caption("Hive")

        self.font = freetype.Font("hive/static/fonts/arial.ttf", 10)

        infoObject = pygame.display.Info()
        self.screen = pygame.display.set_mode(
            (infoObject.current_w - 100, infoObject.current_h - 100), pygame.RESIZABLE
        )
        self.center = self.screen.get_width() / 2, self.screen.get_height() / 2

        while True:
            for event in pygame.event.get():
                mouse_position = pygame.mouse.get_pos()
                # Exit
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                # Click
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    left_click = pygame.mouse.get_pressed()[0]
                    if left_click:
                        if self.selected_hex is None:
                            try:
                                self.selected_hex = self.mouse_position_to_hex(
                                    mouse_position
                                )
                                self.possible_moves = (
                                    self.selected_hex.moveable_locations
                                )
                                print(
                                    f"{self.selected_hex} @ {self.selected_hex.location}"
                                )
                            except HException:
                                pass
                        else:
                            selected_location = self.mouse_position_to_location(
                                mouse_position
                            )
                            if self.selected_hex.location == selected_location:
                                self.selected_hex = None
                                self.possible_moves.clear()
                            else:
                                if (
                                    selected_location
                                    in self.selected_hex.moveable_locations
                                ):
                                    self.hive.remove_hex(self.selected_hex)
                                    self.hive.place_hex(
                                        self.selected_hex, selected_location
                                    )
                                    self.selected_hex = None

            pressed = pygame.key.get_pressed()

            # Scrolling
            if pressed[pygame.K_UP]:
                center_x, center_y = self.center
                self.center = (center_x, center_y + SCROLL_SPEED)
            elif pressed[pygame.K_DOWN]:
                center_x, center_y = self.center
                self.center = (center_x, center_y - SCROLL_SPEED)
            elif pressed[pygame.K_LEFT]:
                center_x, center_y = self.center
                self.center = (center_x + SCROLL_SPEED, center_y)
            elif pressed[pygame.K_RIGHT]:
                center_x, center_y = self.center
                self.center = (center_x - SCROLL_SPEED, center_y)

            # Zooming
            if pressed[pygame.K_MINUS]:
                self.radius -= 1
            elif pressed[pygame.K_EQUALS]:
                self.radius += 1

            # Set font size proportional to radius
            self.font.size = 0.15 * self.radius

            self.screen.fill(WHITE)

            for hex in self.hive.all_hexes:
                if hex.is_on_top:
                    self.draw_hex(hex)
                if hex.is_on_top and hex.has_pieces_beneath:
                    self.draw_number_on_hex(hex.num_pieces_beneath, hex)

            if self.selected_hex is not None:
                self.highlight_selected_hex()
                self.highlight_possible_moves()

            # Hover over beetle
            try:
                hex: Hex = self.mouse_position_to_hex(mouse_position)
                if hex.piece == Piece.BEETLE:
                    for idx, hex_beneath in enumerate(hex.hexes_beneath[::-1]):
                        self.draw_preview_hex(hex_beneath, idx)
            except HException:
                pass

            pygame.display.flip()
