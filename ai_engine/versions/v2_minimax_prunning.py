import copy
import time
from ai_engine.versions.ai_player import PlayerAI
from game.models.board_state import BoardState
from game.models.pieces.piece import Pawn, Knight, Bishop, Rook, Queen, King

PIECE_VALUES = {
    Pawn: 1,
    Knight: 3,
    Bishop: 3,
    Rook: 5,
    Queen: 9,
    King: 1000
}


class SimpleMinimaxPruning(PlayerAI):
    def __init__(self, color, username, depth=2):
        super().__init__(color, username)
        self.depth = depth
        self.positions_evaluated = 0

    def request_move(self, board_state: BoardState):
        self.positions_evaluated = 0  # reset counter at start
        legal_moves = board_state.all_legal_moves(self.color)
        if not legal_moves:
            return None

        best_score = -float("inf")
        best_move = None

        for move in legal_moves:
            captured, moves_done, status = board_state.make_move(move)
            score = self.minimax(board_state, self.depth - 1, False, -float("inf"), float("inf"))
            board_state.undo_move(moves_done, captured)

            if score > best_score:
                best_score = score
                best_move = move

        # print(f"[{self.username}] positions evaluated: {self.positions_evaluated}")
        return best_move

    def minimax(self, board_state: BoardState, depth, is_maximizing, alpha, beta):
        if depth == 0:
            return self.evaluate_board(board_state)

        current_color = self.color if is_maximizing else ("black" if self.color == "white" else "white")
        legal_moves = board_state.all_legal_moves(current_color)

        if not legal_moves:
            if board_state.is_checkmate(current_color):
                return -1000 if is_maximizing else 1000
            return 0

        if is_maximizing:
            max_eval = -float("inf")

            for move in legal_moves:
                captured, moves_done, status = board_state.make_move(move)
                eval = self.minimax(board_state, depth - 1, False, alpha, beta)
                board_state.undo_move(moves_done, captured)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float("inf")
            legal_moves.sort(key=lambda m: 0 if board_state.get_piece(m.target_pos) is None else PIECE_VALUES[type(board_state.get_piece(m.target_pos))])

            for move in legal_moves:
                captured, moves_done, status = board_state.make_move(move)
                eval = self.minimax(board_state, depth - 1, True, alpha, beta)
                board_state.undo_move(moves_done, captured)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def evaluate_board(self, board_state: BoardState):
        self.positions_evaluated += 1
        enemy_color = "black" if self.color == "white" else "white"

        if board_state.is_checkmate(self.color):
            return -1000
        if board_state.is_checkmate(enemy_color):
            return 1000
        if board_state.is_stalemate(self.color) or board_state.is_stalemate(enemy_color):
            return 0

        score = 0
        if board_state.is_in_check(self.color):
            score -= 0.5
        if board_state.is_in_check(enemy_color):
            score += 0.5

        for pos, piece in board_state.positions.items():
            value = PIECE_VALUES.get(type(piece), 0)
            if piece.color == self.color:
                score += value
            else:
                score -= value

        return score
