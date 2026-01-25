import random
import time
from typing import Dict, Tuple

import pygame

from game.config import *
from game.models.board_state import BoardState
from game.models.pieces.piece import Piece
from game.models.square import Square
from game.view.piece_view import PieceView


class BoardView:
    SIZE = 8
    BORDER_PADDING = 20

    STATE_ANIMATING = "animating"
    STATE_STABLE = "stable"

    def __init__(
        self,
        board_state: BoardState,
        board_x: float,
        board_y: float,
        square_size: float,
        *,
        animate_board: bool = ANIMATE_BOARD,
        animate_pieces: bool = ANIMATE_PIECES,
    ):
        self.state = board_state

        self.board_x = board_x
        self.board_y = board_y
        self.square_size = square_size

        self.animate_board = animate_board
        self.animate_pieces = animate_pieces

        self.view_state = (
            self.STATE_ANIMATING if animate_board else self.STATE_STABLE
        )

        self.elapsed_time = 0.0

        self.squares: list[Square] = []
        self.piece_views: Dict[Piece, PieceView] = {}

        self.visible_square_count = 0 if animate_board else self.SIZE * self.SIZE
        self.last_spawn_time = time.time()
        self.fall_start_time: float | None = None

        self._create_squares()
        self._create_piece_views()

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    def update(self, current_time: float) -> None:
        if self.view_state == self.STATE_ANIMATING:
            self._update_board_animation(current_time)
        else:
            for view in self.piece_views.values():
                view.update(current_time)

    def _update_board_animation(self, current_time: float) -> None:
        if (
            self.visible_square_count < len(self.squares)
            and current_time - self.last_spawn_time >= spawn_interval
        ):
            self.visible_square_count += 1
            self.last_spawn_time = current_time

            if self.visible_square_count == len(self.squares):
                self.fall_start_time = current_time

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
            self.view_state = self.STATE_STABLE

            if self.animate_pieces:
                start_time = time.time()
                for view in self.piece_views.values():
                    view.start_spawn(start_time)
            else:
                for view in self.piece_views.values():
                    view.finish()

    # ------------------------------------------------------------------
    # DRAW
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        # if self.view_state == self.STATE_STABLE:
        #     self._draw_border(surface)

        for square in self.squares[: self.visible_square_count]:
            square.draw(surface)

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
        """Draw pieces according to turn orientation while keeping animations"""

        for view in sorted(
                self.piece_views.values(),
                key=lambda v: v.piece.position[1] if self.state.current_turn == "white"
                else 7 - v.piece.position[1],
                reverse=True,
        ):
            # Compute rotated offset without breaking animation
            x, y = view.current_position  # this is animated position
            grid_x, grid_y = view.piece.position

            if self.state.current_turn == "black":
                # mirror x and y around the board center
                x = self.board_x + (self.SIZE - 1 - grid_x) * self.square_size + (x % 1)
                y = self.board_y + grid_y * self.square_size + (y % 1)

            view.draw(surface)

    # ------------------------------------------------------------------
    # EVENTS FROM CONTROLLER
    # ------------------------------------------------------------------
    def on_piece_moved(
        self,
        piece: Piece,
        from_pos: Tuple[int, int],
        to_pos: Tuple[int, int],
    ) -> None:
        view = self.piece_views[piece]
        view.animate_to(self.grid_to_pixel(*to_pos))

    def on_piece_captured(self, piece: Piece) -> None:
        view = self.piece_views.pop(piece, None)
        if view:
            view.start_capture()

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    def grid_to_pixel(self, grid_x: int, grid_y: int) -> tuple[float, float]:
        """
        Returns the bottom-left pixel coordinates of a square (used for PieceView),
        taking board rotation into account.
        """
        if self.state.current_turn == "white":
            # normal orientation: white at bottom
            px = self.board_x + grid_x * self.square_size
            py = self.board_y + (self.SIZE - 1 - grid_y) * self.square_size + self.square_size
        else:
            # black's turn: rotate board 180 degrees
            px = self.board_x + (self.SIZE - 1 - grid_x) * self.square_size
            py = self.board_y + grid_y * self.square_size + self.square_size
        return px, py

    def _create_squares(self) -> None:
        """Create square positions; rotation will be handled in draw/pixel conversion"""
        self.squares.clear()
        for row in range(self.SIZE):
            for col in range(self.SIZE):
                color = LIGHT_SQ if (row + col) % 2 == 0 else DARK_SQ
                x = self.board_x + col * self.square_size
                y = self.board_y + row * self.square_size
                self.squares.append(Square(color, x, y, self.square_size))

    def _create_piece_views(self) -> None:
        window_width, window_height = pygame.display.get_window_size()
        padding = self.square_size * 2  # how far outside the screen

        for pos, piece in self.state.positions.items():
            # Target pixel on the board
            target_pixel = self.grid_to_pixel(*pos)

            # Random spawn completely outside the screen
            side = random.choice(["top", "bottom", "left", "right"])
            if side == "top":
                spawn_pos = (random.uniform(-padding, window_width + padding), -padding)
            elif side == "bottom":
                spawn_pos = (random.uniform(-padding, window_width + padding), window_height + padding)
            elif side == "left":
                spawn_pos = (-padding, random.uniform(-padding, window_height + padding))
            else:  # right
                spawn_pos = (window_width + padding, random.uniform(-padding, window_height + padding))

            # Create PieceView
            view = PieceView(
                piece=piece,
                target_position=target_pixel,
                square_size=self.square_size,
                animate=self.animate_pieces,
            )

            # Assign random spawn
            view.spawn_position = spawn_pos
            self.piece_views[piece] = view
    # def _create_piece_views(self) -> None:
    #     for pos, piece in self.state.positions.items():
    #         self.piece_views[piece] = PieceView(
    #             piece=piece,
    #             target_position=self.grid_to_pixel(*pos),
    #             square_size=self.square_size,
    #             animate=self.animate_pieces,
    #         )
