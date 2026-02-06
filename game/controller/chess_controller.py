from typing import Optional

from ai_engine.versions.ai_player import PlayerAI
from game.models.pieces.piece import *
from game.view.piece_view import PieceView
from game.view.board_view import BoardView
from game.models.board_state import BoardState
import threading

class ChessController:
    def __init__(self, board_state: BoardState, board_view: BoardView, game_view=None):
        self.state = board_state
        self.view = board_view
        self.game_view = game_view
        self.selected_pos: Optional[Tuple[int, int]] = None
        self.ai_thread = None
        self.ai_result = None
        self.ai_thinking = False


    # ----------------------------
    # MAIN INPUT HANDLER
    # ----------------------------
    def handle_mouse_click(self, mouse_pos: Tuple[int, int]) -> Move | None:
        grid_pos = self.view.pixel_to_grid(mouse_pos)
        if not grid_pos:
            return None

        # If promotion UI is open → handle & exit
        # if self.game_view.promotion_active:
        #     self._handle_promotion_click(mouse_pos)
        #     return None

        piece = self.state.get_piece(grid_pos)


        if piece and ((piece.color == "white" and self.state.is_whites_turn) or (piece.color == "black" and not self.state.is_whites_turn)):
            self.selected_pos = grid_pos
            self.view.highlight_selected = grid_pos

            pseudo_moves = piece.get_allowed_moves(grid_pos, self.state)
            self.view.highlight_moves = self.state.get_legal_moves(pseudo_moves, self.state)
            return None

        # Trying to make a move
        if self.selected_pos:
            moves = [m for m in self.view.highlight_moves if m.target_pos == grid_pos]
            if moves:
                move = moves[0]

                # Clear UI selection
                self.selected_pos = None
                self.view.highlight_selected = None
                self.view.highlight_moves = []

                # RETURN the move to main loop
                return move

            # Not a valid move → reset selection
            self.selected_pos = None
            self.view.highlight_selected = None
            self.view.highlight_moves = []

        return None

    # ----------------------------
    # MOVE LOGIC
    # ----------------------------
    def attempt_move(self, move :Move):

        captured_piece, moves_done, status = self.state.make_move(move ,True)

        # Animate each move in the moves_done list
        for move_done in moves_done:
            move_piece = move_done["piece"]
            move_from = move_done["from"]
            move_to = move_done["to"]
            move_captured = move_done["captured"]
            promotion = move_done["promotes"]
            self.animate_move(move_piece, move_from, move_to, move_captured)
            if promotion: self.view.replace_piece(move_from, promotion)


        # After switching, check if the next player is AI
        next_player = (
            self.game_view.white_player if self.state.is_whites_turn
            else self.game_view.black_player
        )

        if isinstance(next_player, PlayerAI):
            self.start_ai_move(next_player)
        # Check game state
        enemy = "white" if self.state.is_whites_turn else "black" # The side that must move now

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
        self.state.place_piece(new_piece, pos)

        # update view
        self.view.replace_piece(pos, new_piece)

        # resume turn
        self.state.is_whites_turn = color != "white"



    def start_ai_move(self, ai_player):
        if self.ai_thinking:
            return  # AI is already thinking

        self.ai_thinking = True
        self.ai_result = None

        def worker():
            result = ai_player.request_move(self.state)
            self.ai_result = result
            self.ai_thinking = False

        self.ai_thread = threading.Thread(target=worker, daemon=True)
        self.ai_thread.start()

    def get_ai_move(self):
        if not self.ai_thinking and self.ai_result:
            move = self.ai_result
            self.ai_result = None
            return move
        return None
