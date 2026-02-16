import random
import time

from ai_engine.versions.ai_player import PlayerAI
from game.models.board import Board



class RandomAI(PlayerAI):
    def __init__(self, color,username):
        super().__init__(color,username)

    def request_move(self, board_state : Board):
        """Return a random legal move."""
        time.sleep(1)  # ← AI "thinks" for 2 seconds
        legal_moves = board_state.generate_all_legal_moves(self.color)

        if not legal_moves:
            return None  # Checkmate or stalemate

        return random.choice(legal_moves)