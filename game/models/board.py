import random
import time
from typing import Dict, List, Optional, Tuple

import pygame

from game.config import LIGHT_SQ, DARK_SQ, spawn_interval, animation_duration
from game.helpers import animation as anim
from game.models.pieces.piece import (
    Piece,
    Pawn,
    Rook,
    Knight,
    Bishop,
    Queen,
    King,
)
from game.models.square import Square


class Board:
    SIZE = 8
    BORDER_PADDING = 20

    STATE_ANIMATING = "animating"
    STATE_STABLE = "stable"

    DEFAULT_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    def __init__(
        self,
        board_x: float,
        board_y: float,
        square_size: float,
        fen: Optional[str] = None,
    ):
        self.board_x = board_x
        self.board_y = board_y
        self.square_size = square_size

        self.current_fen = fen or self.DEFAULT_FEN

        self.state = self.STATE_ANIMATING
        self.elapsed_time = 0.0

        self.positions: Dict[Tuple[int, int], Piece] = {}
        self.pieces: List[Piece] = []

        self.squares: List[Square] = []
        self.visible_square_count = 0

        self.last_spawn_time = time.time()
        self.fall_start_time: Optional[float] = None

        self._create_squares()
        self._parse_fen()

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    def update(self, current_time: float) -> None:
        if self.state == self.STATE_ANIMATING:
            self._update_animation(current_time)
            self.elapsed_time = 0.0
        else:
            self.elapsed_time += current_time

    def _update_animation(self, current_time: float) -> None:
        self._spawn_squares(current_time)
        self._update_square_animations(current_time)

    def _spawn_squares(self, current_time: float) -> None:
        if (
            self.visible_square_count < len(self.squares)
            and current_time - self.last_spawn_time >= spawn_interval
        ):
            self.visible_square_count += 1
            self.last_spawn_time = current_time

            if self.visible_square_count == len(self.squares):
                self.fall_start_time = current_time

    def _update_square_animations(self, current_time: float) -> None:
        all_finished = True

        for index, square in enumerate(self.squares[: self.visible_square_count]):
            finished = square.update(
                current_time,
                self.fall_start_time,
                index,
                animation_duration,
            )
            if not finished:
                all_finished = False

        if self.visible_square_count == len(self.squares) and all_finished:
            self.state = self.STATE_STABLE

            start_time = time.time()
            for piece in self.pieces:
                piece.spawn_time = start_time

    # ------------------------------------------------------------------
    # DRAW
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        if self.state == self.STATE_STABLE:
            self._draw_border(surface)

        for square in self.squares[: self.visible_square_count]:
            square.draw(surface)

        if self.state == self.STATE_STABLE:
            self._draw_pieces(surface)

    def _draw_border(self, surface: pygame.Surface) -> None:
        total_size = self.square_size * self.SIZE
        pygame.draw.rect(
            surface,
            (92, 70, 48),
            pygame.Rect(
                self.board_x - self.BORDER_PADDING,
                self.board_y - self.BORDER_PADDING,
                total_size + self.BORDER_PADDING * 2,
                total_size + self.BORDER_PADDING * 2,
            ),
        )

    def _draw_pieces(self, surface: pygame.Surface) -> None:
        now = time.time()

        for (x, y), piece in sorted(
                self.positions.items(),
                key=lambda item: item[0][1],
                reverse=True,  # TOP → BOTTOM
        ):
            if piece.spawn_time is None or piece.has_arrived:
                piece.draw(surface, piece.target_position)
                continue

            local_time = max(0.0, now - piece.spawn_time - piece.delay)

            position = anim.animate_to_pos(
                piece.spawn_position,
                piece.target_position,
                local_time,
                0.9,
            )

            if position == piece.target_position:
                piece.has_arrived = True

            piece.draw(surface, position)

    # ------------------------------------------------------------------
    # GRID / POSITION
    # ------------------------------------------------------------------

    def grid_to_pixel(self, grid_x: int, grid_y: int) -> Tuple[float, float]:
        pixel_x = (
            self.board_x
            + grid_x * self.square_size
            + self.square_size / 2
        )
        pixel_y = (
            self.board_y
            + (self.SIZE - grid_y) * self.square_size
        )
        return pixel_x, pixel_y

    # ------------------------------------------------------------------
    # PIECES
    # ------------------------------------------------------------------

    def place_piece(self, piece: Piece, position: Tuple[int, int]) -> None:
        grid_x, grid_y = position

        piece.rescale_to_square(self.square_size)

        piece.spawn_position = self._get_top_spawn_position(grid_x)
        piece.target_position = self.grid_to_pixel(grid_x, grid_y)

        # Bottom rank first → top rank last
        piece.delay = (7 - grid_y) * 0.15

        piece.spawn_time = None
        piece.has_arrived = False

        self.positions[position] = piece
        self.pieces.append(piece)

    def move_piece(
        self,
        from_pos: Tuple[int, int],
        to_pos: Tuple[int, int],
    ) -> None:
        piece = self.positions.pop(from_pos, None)
        if piece is None:
            return

        captured = self.positions.pop(to_pos, None)
        if captured:
            self.pieces.remove(captured)

        self.positions[to_pos] = piece

    # ------------------------------------------------------------------
    # INITIALIZATION HELPERS
    # ------------------------------------------------------------------

    def _create_squares(self) -> None:
        for row in range(self.SIZE):
            for col in range(self.SIZE):
                color = LIGHT_SQ if (row + col) % 2 == 0 else DARK_SQ
                x = self.board_x + col * self.square_size
                y = self.board_y + row * self.square_size
                self.squares.append(Square(color, x, y, self.square_size))

    def _get_offscreen_spawn_position(self, grid_x: int) -> Tuple[float, float]:
        screen_width, screen_height = pygame.display.get_surface().get_size()

        pixel_x = (
                self.board_x
                + grid_x * self.square_size
                + self.square_size / 2
        )

        pixel_y = -self.square_size * 2  # well above the screen

        return pixel_x, pixel_y

    def _get_top_spawn_position(self, grid_x: int) -> Tuple[float, float]:
        pixel_x = (
                self.board_x
                + grid_x * self.square_size
                + self.square_size / 2
        )

        pixel_y = -self.square_size * 2  # above window

        return pixel_x, pixel_y

    def _parse_fen(self) -> None:
        board_fen = self.current_fen.split()[0]

        row = self.SIZE - 1
        col = 0

        piece_map = {
            "p": Pawn,
            "r": Rook,
            "n": Knight,
            "b": Bishop,
            "q": Queen,
            "k": King,
        }

        for char in board_fen:
            if char == "/":
                row -= 1
                col = 0
                continue

            if char.isdigit():
                col += int(char)
                continue

            color = "white" if char.isupper() else "black"
            piece_class = piece_map[char.lower()]
            self.place_piece(piece_class(color), (col, row))
            col += 1
