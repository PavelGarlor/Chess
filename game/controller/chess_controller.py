import pygame
import time
from typing import Optional, Tuple, List

from game import PRINT_FEN
from game.models.pieces.piece import *
from game.view.piece_view import PieceView
from game.view.board_view import BoardView
from game.models.board_state import BoardState


class ChessController:
    def __init__(self, board_state: BoardState, board_view: BoardView, game_view=None):
        self.state = board_state
        self.view = board_view
        self.game_view = game_view
        self.selected_pos: Optional[Tuple[int, int]] = None


    # ----------------------------
    # MAIN INPUT HANDLER
    # ----------------------------
    def handle_mouse_click(self, mouse_pos: Tuple[int, int]):
        grid_pos = self.view.pixel_to_grid(mouse_pos)
        if not grid_pos:
            return

        piece = self.state.get_piece(grid_pos)
        if self.game_view.promotion_active:
            self._handle_promotion_click(mouse_pos)
            return

        if piece and piece.color == self.state.current_turn:
            # Select piece
            self.selected_pos = grid_pos
            self.view.highlight_selected = grid_pos
            # Ask the piece for its allowed moves
            pseudo_legal_moves = piece.get_allowed_moves(grid_pos, self.state)
            #filter moves
            self.view.highlight_moves = self.state.get_legal_moves(pseudo_legal_moves,self.state)
        elif self.selected_pos:
            # Check if the clicked square is a valid target for the selected piece
            moves = [m for m in self.view.highlight_moves if m.target_pos == grid_pos]
            if moves:
                # Take the first matching move (or handle special cases like promotion later)
                move = moves[0]
                self.attempt_move(self.selected_pos, move.target_pos)
                self.state.fen = self.state.to_fen()
                if PRINT_FEN: print(self.state.fen)
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
        move = Move(piece,to_pos)
        captured_piece, moves_done, status = self.state.make_move(move)

        # Animate each move in the moves_done list
        for move in moves_done:
            move_piece = move["piece"]
            move_from = move["from"]
            move_to = move["to"]
            move_captured = move["captured"]
            self.animate_move(move_piece, move_from, move_to, move_captured)

        if status == "promotion":
            # freeze game
            self.state.current_turn = None
            # ask GameView to show promotion UI
            self.game_view.start_promotion(piece.color, to_pos)
            return

        # Switch turn
        self.state.current_turn= "black" if self.state.current_turn == "white" else "white"

        # Check game state
        enemy = self.state.current_turn  # The side that must move now

        if self.state.is_checkmate(enemy):
            winner = "white" if enemy == "black" else "black"

            print(f"CHECKMATE! {winner.upper()} WINS!")

            if self.game_view:
                self.game_view.set_message(f"Checkmate! {winner.capitalize()} wins!")

        elif self.state.is_in_check(enemy):
            print("CHECK on", enemy)

        elif self.state.is_stalemate(enemy):
            print("STALEMATE")
            if self.game_view:
                self.game_view.set_message("Stalemate! Draw.")

        return

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

    def _handle_promotion_click(self, mouse_pos):
        for rect, piece_name in self.game_view.promotion_buttons:
            if rect.collidepoint(mouse_pos):
                self._promote_pawn(piece_name)
                self.game_view.promotion_active = False
                return



    def _promote_pawn(self, piece_name):
        pos = self.game_view.promotion_position
        color = self.game_view.promotion_color


        cls = {"Queen": Queen, "Rook": Rook, "Bishop": Bishop, "Knight": Knight}[piece_name]

        # Replace pawn with new piece
        new_piece = cls(color)
        self.state.set_piece(new_piece,pos)

        # update view
        self.view.replace_piece(pos, new_piece)

        # resume turn
        self.state.current_turn = "black" if color == "white" else "white"