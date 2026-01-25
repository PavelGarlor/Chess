import pygame
import time
from typing import Optional, Tuple

from game.models.pieces.piece import Piece
from game.view.piece_view import PieceView
from game.view.board_view import BoardView
from game.models.board_state import BoardState


class ChessController:
    def __init__(self, board_state: BoardState, board_view: BoardView):
        self.state = board_state
        self.view = board_view
        self.selected_pos: Optional[Tuple[int, int]] = None
        self.current_turn: str = "white"  # white moves first

    # ----------------------------
    # MAIN INPUT HANDLER
    # ----------------------------
    def handle_mouse_click(self, mouse_pos: Tuple[int, int]):
        grid_pos = self.pixel_to_grid(mouse_pos)
        if grid_pos is None:
            return

        piece = self.state.get_piece(grid_pos)

        if piece and piece.color == self.current_turn:
            # Select piece
            self.selected_pos = grid_pos
        elif self.selected_pos:
            # Attempt to move selected piece
            self.attempt_move(self.selected_pos, grid_pos)
            self.selected_pos = None

    # ----------------------------
    # MOVE LOGIC
    # ----------------------------
    def attempt_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        piece: Optional[Piece] = self.state.get_piece(from_pos)
        if piece is None:
            return

        # You can add real chess move validation here later
        captured = self.state.move_piece(from_pos, to_pos)
        self.animate_move(piece, from_pos, to_pos, captured)

        # Switch turn
        self.current_turn = "black" if self.current_turn == "white" else "white"

    # ----------------------------
    # ANIMATION TRIGGER
    # ----------------------------
    def animate_move(
        self,
        piece: Piece,
        from_pos: Tuple[int, int],
        to_pos: Tuple[int, int],
        captured: Optional[Piece],
    ):
        # Get PieceView
        piece_view: PieceView = self.view.piece_views[piece]

        # Compute pixel position
        target_pixel = self.view.grid_to_pixel(*to_pos)
        piece_view.animate_to(target_pixel)

        # Animate captured piece
        if captured:
            captured_view: PieceView = self.view.piece_views[captured]
            captured_view.start_capture()

    # ----------------------------
    # HELPERS
    # ----------------------------
