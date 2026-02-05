from sympy import false

from game.models.player import Player


class PlayerAI(Player):
    def __init__(self, color: str , username : str):
        super().__init__(color, username)
        self.searching =False
        self.positions_evaluated=0
