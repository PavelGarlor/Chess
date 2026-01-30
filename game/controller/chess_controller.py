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

    # ----------------------------
    # MAIN INPUT HANDLER
    # ----------------------------
    def handle_mouse_click(self, mouse_pos: Tuple[int, int]):
        grid_pos = self.view.pixel_to_grid(mouse_pos)
        if not grid_pos:
            return

        piece = self.state.get_piece(grid_pos)

        if piece and piece.color == self.state.current_turn:
            # Select piece
            self.selected_pos = grid_pos
            self.view.highlight_selected = grid_pos
            # Ask the piece for its allowed moves
            self.view.highlight_moves = piece.get_allowed_moves(grid_pos, self.state)

        elif self.selected_pos:
            if grid_pos in self.view.highlight_moves:
                # Valid move

                self.attempt_move(self.selected_pos, grid_pos)
            # Clear selection
            self.selected_pos = None
            self.view.highlight_selected = None
            self.view.highlight_moves = []

    # ----------------------------
    # MOVE LOGIC
    # ----------------------------
    def attempt_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        piece: Optional[Piece] = self.state.get_piece(from_pos)
        if piece is None:
            return

        # Perform the move; get captured piece and all moves done
        captured_piece, moves_done = self.state.move_piece(from_pos, to_pos)

        # Animate each move in the moves_done list
        for move in moves_done:
            move_piece = move["piece"]
            move_from = move["from"]
            move_to = move["to"]
            move_captured = move["captured"]
            self.animate_move(move_piece, move_from, move_to, move_captured)

        # Switch turn
        self.state.current_turn= "black" if self.state.current_turn == "white" else "white"

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

    def pixel_to_grid(self, position: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Converts mouse pixel coordinates to grid coordinates (0-7, 0-7).
        Returns None if clicked outside the board.
        """
        mouse_x, mouse_y = position
        bx, by = self.view.board_x, self.view.board_y
        sq = self.view.square_size
        size = self.view.SIZE

        # Check if inside board bounds
        if not (bx <= mouse_x <= bx + sq * size and by <= mouse_y <= by + sq * size):
            return None

        # Convert to 0-7 grid
        grid_x = int((mouse_x - bx) // sq)
        grid_y = int((mouse_y - by) // sq)

        # Flip vertically because pixel y=0 is top of screen
        grid_y = size - 1 - grid_y

        return grid_x, grid_y
