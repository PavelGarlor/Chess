# --------------------
# BOARD CLASS
# --------------------
import time
from typing import Optional, Tuple

import pygame

from game.config import *
from game.models.pieces.piece import Piece
from game.models.square import Square


class Board:
    ANIMATING = 0
    STABLE = 1

    def __init__(
        self,
        board_x: float,
        board_y: float,
        square_size: float,
        current_FEN_position: Optional[str] = None,
    ):
        self.initial_FEN_position = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.current_FEN_position = (
            self.initial_FEN_position
            if current_FEN_position is None
            else current_FEN_position
        )

        # Grid positions -> pieces
        self.positions: dict[Tuple[int, int], Piece] = {}
        # All pieces list
        self.pieces: list[Piece] = []

        self.size = 8
        self.square_size = square_size
        self.board_x = board_x
        self.board_y = board_y

        self.squares = []
        self.square_index = 0
        self.last_spawn_time = time.time()
        self.fall_start_time = None

        self.state = Board.ANIMATING

        # Pre-create all squares
        for i in range(self.size):
            for j in range(self.size):
                color = LIGHT_SQ if (i + j) % 2 == 0 else DARK_SQ
                target_x = board_x + j * square_size
                target_y = board_y + i * square_size
                self.squares.append(Square(color, target_x, target_y, square_size))

    # -------------------- UPDATES --------------------
    def update(self, current_time):
        if self.state == Board.ANIMATING:
            self._update_animation(current_time)
        elif self.state == Board.STABLE:
            self._update_stable(current_time)

    def _update_animation(self, current_time):
        # Spawn squares gradually
        if (
            self.square_index < len(self.squares)
            and current_time - self.last_spawn_time >= spawn_interval
        ):
            self.square_index += 1
            self.last_spawn_time = current_time

            if self.square_index == len(self.squares):
                self.fall_start_time = current_time

        all_finished = True

        # Update all visible squares
        for idx, sq in enumerate(self.squares[: self.square_index]):
            finished = sq.update(current_time, self.fall_start_time, idx, animation_duration)
            if not finished:
                all_finished = False

        if self.square_index == len(self.squares) and all_finished:
            self.state = Board.STABLE

    def _update_stable(self, current_time):
        # Board is fully built. You can handle piece movement here.
        pass

    # -------------------- DRAWING --------------------
    def draw(self, surface):
        # # Draw board border
        # total_size = self.square_size * self.size
        # pygame.draw.rect(
        #     surface,
        #     (92, 70, 48),
        #     pygame.Rect(
        #         self.board_x - 20,
        #         self.board_y - 20,
        #         total_size + 40,
        #         total_size + 40,
        #     ),
        # )

        # Draw squares
        for sq in self.squares[: self.square_index]:
            sq.draw(surface)

        # Draw pieces only when the board is fully built
        if self.state == Board.STABLE:
            self.draw_pieces(surface)

    def draw_pieces(self, surface):
        # Loop over all pieces in positions dict
        for (grid_x, grid_y), piece in self.positions.items():
            if piece:
                position = self.get_position_from_grid(grid_x, grid_y)
                piece.draw(surface, position)

    # -------------------- GRID TO PIXEL --------------------
    def get_position_from_grid(self, grid_x: int, grid_y: int) -> Tuple[float, float]:
        """
        Convert board grid coordinates (0-7, 0-7) to pixel coordinates.
        grid_x = column (0 = left)
        grid_y = row    (0 = bottom)
        """
        pixel_x = self.board_x + grid_x * self.square_size + self.square_size / 2
        pixel_y = self.board_y + (7 - grid_y) * self.square_size + self.square_size / 2
        return pixel_x, pixel_y

    # -------------------- BOARD MANAGEMENT --------------------
    def place_piece(self, piece: Piece, grid_pos: Tuple[int, int]):
        """Place a piece on the board"""
        self.positions[grid_pos] = piece
        if piece not in self.pieces:
            self.pieces.append(piece)

    def move_piece(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        """Move a piece from one square to another"""
        piece = self.positions.pop(from_pos, None)
        if not piece:
            return
        captured = self.positions.get(to_pos)
        if captured:
            self.pieces.remove(captured)
        self.positions[to_pos] = piece
