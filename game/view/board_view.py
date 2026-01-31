import random
import time
from typing import Dict, Tuple, Optional

import pygame

from game.config import *
from game.models.board_state import BoardState
from game.models.move import Move
from game.models.pieces.piece import Piece
from game.models.square import Square
from game.view.piece_view import PieceView


class BoardView:
    SIZE = 8
    BORDER_PADDING = 20

    STATE_ANIMATING = "animating"
    STATE_STABLE = "stable"
    FONT_SIZE = 20


    def __init__(
        self,
        board_state: BoardState,
        board_x: float,
        board_y: float,
        square_size: float,
        *,
        animate_board: bool = ANIMATE_BOARD,
        animate_pieces: bool = ANIMATE_PIECES,
        orientation: str = "white",  # new: "white" or "black" at bottom
    ):
        self.state = board_state
        self.board_x = board_x
        self.board_y = board_y
        self.square_size = square_size
        self.animate_board = animate_board
        self.animate_pieces = animate_pieces
        self.orientation = orientation  # store orientation
        self.view_state = self.STATE_ANIMATING if animate_board else self.STATE_STABLE
        self.elapsed_time = 0.0

        self.squares: list[Square] = []
        self.piece_views: Dict[Piece, PieceView] = {}
        self.visible_square_count = 0 if animate_board else self.SIZE * self.SIZE
        self.last_spawn_time = time.time()
        self.fall_start_time: float | None = None

        self.highlight_selected: Optional[Tuple[int, int]] = None
        self.highlight_moves: list[Move] = []

        # Font must be created after pygame.init()
        self.font = pygame.font.SysFont("Arial", self.FONT_SIZE)

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
            start_time = time.time()
            for view in self.piece_views.values():
                if self.animate_pieces:
                    view.start_spawn(start_time)
                else:
                    view.finish()

    # ------------------------------------------------------------------
    # DRAW
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        # Draw FEN at the top
        if DISPLAY_FEN : self._draw_fen(surface)

        # Draw squares
        for square in self.squares[: self.visible_square_count]:
            square.draw(surface)

        # Draw highlights
        self._draw_highlights(surface)

        # Draw pieces
        self._draw_pieces(surface)

        # Draw coordinates
        self._draw_coordinates(surface)

    def _draw_coordinates(self, surface: pygame.Surface):
        sq = self.square_size
        bx, by = self.board_x, self.board_y
        files = "abcdefgh"
        ranks = "12345678"

        for i in range(self.SIZE):
            # Letters (bottom of board)
            letter = files[i]
            # Determine which square this is: bottom row = rank 1
            square_color = LIGHT_SQ if (self.SIZE - 1 + i) % 2 == 0 else DARK_SQ
            font_color = LIGHT_SQ if square_color == DARK_SQ else DARK_SQ
            text_surf = self.font.render(letter, True, font_color)
            rect = text_surf.get_rect()
            rect.topleft = (bx + i * sq + 2, by + self.SIZE * sq - self.FONT_SIZE - 2)
            surface.blit(text_surf, rect)

            # Numbers (left of board)
            number = ranks[self.SIZE - 1 - i]
            square_color = LIGHT_SQ if (i + 0) % 2 == 0 else DARK_SQ  # leftmost column
            font_color = LIGHT_SQ if square_color == DARK_SQ else DARK_SQ
            text_surf = self.font.render(number, True, font_color)
            rect = text_surf.get_rect()
            rect.topleft = (bx + 2, by + i * sq + 2)
            surface.blit(text_surf, rect)

    def _draw_highlights(self, surface: pygame.Surface):
        if self.highlight_selected:
            x, y = self.highlight_selected
            rect = pygame.Rect(
                self.board_x + x * self.square_size,
                self.board_y + (self.SIZE - 1 - y) * self.square_size,
                self.square_size,
                self.square_size,
            )
            self._draw_transparent_rect(
                surface,
                (128, 255, 120),  # teal / green
                rect,
                186  # transparency (0–255)
            )
        if self.state.en_passant_target:
            x, y = self.state.en_passant_target
            rect = pygame.Rect(
                self.board_x + x * self.square_size,
                self.board_y + (self.SIZE - 1 - y) * self.square_size,
                self.square_size,
                self.square_size,
            )
            self._draw_transparent_rect(
                surface,
                (255, 0, 0),  # teal / green
                rect,
                186  # transparency (0–255)
            )


        for move in self.highlight_moves:
            x,y = move.target_pos
            rect = pygame.Rect(
                self.board_x + x * self.square_size,
                self.board_y + (self.SIZE - 1 - y) * self.square_size,
                self.square_size,
                self.square_size,
            )
            #pygame.draw.rect(surface, (0.2, 140, 141, 186), rect)  # green overlay
            self._draw_transparent_rect(
                surface,
                (140, 141, 186),  # teal / green
                rect,
                186  # transparency (0–255)
            )


    def _draw_transparent_rect(self,surface, color, rect, alpha):
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((*color, alpha))
        surface.blit(overlay, rect.topleft)

    def _draw_pieces(self, surface: pygame.Surface) -> None:
        for view in sorted(
                self.piece_views.values(),
                key=lambda v: v.piece.position[1],
                reverse=True,
        ):
            view.draw(surface)

    def _draw_fen(self, surface: pygame.Surface):
        fen = self.state.to_fen()

        text_surf = self.font.render(fen, True, FONT_COLOR)
        text_rect = text_surf.get_rect()

        # CENTER horizontally above the board
        text_rect.centerx = self.board_x + (self.SIZE * self.square_size) / 2

        # Put it ABOVE the board
        text_rect.bottom = self.board_y - 50  # 10px margin

        surface.blit(text_surf, text_rect)

    # ------------------------------------------------------------------
    # EVENTS
    # ------------------------------------------------------------------
    def on_piece_moved(self, piece: Piece, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> None:
        view = self.piece_views[piece]
        view.animate_to(self.grid_to_pixel(*to_pos))

    def on_piece_captured(self, piece: Piece) -> None:
        view = self.piece_views.pop(piece, None)
        if view:
            view.start_capture()

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    def pixel_to_grid(self, position: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        mouse_x, mouse_y = position
        bx, by = self.board_x, self.board_y
        sq = self.square_size
        if not (bx <= mouse_x <= bx + sq * self.SIZE and by <= mouse_y <= by + sq * self.SIZE):
            return None
        grid_x = int((mouse_x - bx) // sq)
        grid_y = self.SIZE - 1 - int((mouse_y - by) // sq)
        return grid_x, grid_y

    def grid_to_pixel(self, grid_x: int, grid_y: int) -> Tuple[float, float]:
        """Convert grid coordinates to pixel coordinates based on board orientation"""
        if self.orientation == "white":
            px = self.board_x + grid_x * self.square_size
            py = self.board_y + (self.SIZE - 1 - grid_y) * self.square_size + self.square_size
        else:  # black at bottom
            px = self.board_x + (self.SIZE - 1 - grid_x) * self.square_size
            py = self.board_y + grid_y * self.square_size + self.square_size
        return px, py

    # ------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------
    def _create_squares(self) -> None:
        self.squares.clear()
        for row in range(self.SIZE):
            for col in range(self.SIZE):
                color = LIGHT_SQ if (row + col) % 2 == 0 else DARK_SQ
                x = self.board_x + col * self.square_size
                y = self.board_y + row * self.square_size
                self.squares.append(Square(color, x, y, self.square_size))

    def _create_piece_views(self) -> None:
        """Spawn pieces outside screen randomly"""
        window_width, window_height = pygame.display.get_window_size()
        padding = self.square_size * 2

        for pos, piece in self.state.positions.items():
            target_pixel = self.grid_to_pixel(*pos)

            # Random spawn outside screen
            side = random.choice(["top", "bottom", "left", "right"])
            if side == "top":
                spawn_pos = (random.uniform(-padding, window_width + padding), -padding)
            elif side == "bottom":
                spawn_pos = (random.uniform(-padding, window_width + padding), window_height + padding)
            elif side == "left":
                spawn_pos = (-padding, random.uniform(-padding, window_height + padding))
            else:  # right
                spawn_pos = (window_width + padding, random.uniform(-padding, window_height + padding))

            view = PieceView(
                piece=piece,
                target_position=target_pixel,
                square_size=self.square_size,
                animate=self.animate_pieces,
            )
            view.spawn_position = spawn_pos
            self.piece_views[piece] = view
