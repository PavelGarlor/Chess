import pygame
import time
from typing import Optional, Tuple, List

from game import PRINT_FEN
from game.models.move import Move
from game.models.pieces.piece import Piece, King, Rook
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
            pseudo_legal_moves = piece.get_allowed_moves(grid_pos, self.state)
            #filter moves
            self.view.highlight_moves = self.get_legal_moves(pseudo_legal_moves,self.state)
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
        captured_piece, moves_done = self.state.make_move(move)


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

    def get_legal_moves(self, pseudo_legal_moves: List[Move], state):
        legal_moves: List[Move] = []
        enemy = "black" if state.current_turn == "white" else "white"

        for move in pseudo_legal_moves:
            piece = move.piece
            from_pos = piece.position
            to_pos = move.target_pos

            # ------------------------------------------------------------
            # HANDLE CASTLING LEGALITY
            # ------------------------------------------------------------
            if isinstance(piece, King) and abs(to_pos[0] - from_pos[0]) == 2:
                color = piece.color
                row = 0 if color == "white" else 7

                # 1. King must NOT be in check
                if state.is_square_attacked(from_pos, enemy):
                    continue

                # 2. Which side?
                if to_pos[0] == 6:  # kingside
                    rook_from = (7, row)
                    path = [(5, row), (6, row)]
                    between = [(5, row)]
                    rights_flag = "K"
                else:  # queenside
                    rook_from = (0, row)
                    path = [(3, row), (2, row)]
                    between = [(3, row), (2, row), (1, row)]
                    rights_flag = "Q"

                # 3. Rook must exist and be unmoved
                rook_piece = state.positions.get(rook_from)
                if not isinstance(rook_piece, Rook) or rook_piece.color != color:
                    continue

                # 4. Castling rights must allow it
                if not state.castling_rights[color][rights_flag]:
                    continue

                # 5. Squares between king and rook must be empty
                if any(s in state.positions for s in between):
                    continue

                # 6. King must not pass through check
                illegal = False
                for sq in path:
                    if state.is_square_attacked(sq, enemy):
                        illegal = True
                        break
                if illegal:
                    continue

                # → Castling is legal!
                legal_moves.append(move)
                continue

            # ------------------------------------------------------------
            # NORMAL MOVE + En Passant + Captures (simulate)
            # ------------------------------------------------------------
            temp_state = state.copy()
            temp_state.make_move(move)

            # After simulation — king may not be in check
            king_pos = temp_state.find_king(piece.color)
            if king_pos is None:
                continue

            if temp_state.is_square_attacked(king_pos, enemy):
                continue  # illegal — king ends in check

            # If we get here → legal
            legal_moves.append(move)

        return legal_moves


