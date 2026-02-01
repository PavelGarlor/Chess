from game.models.player import Player


class PlayerAI(Player):
    def __init__(self, color: str , username : str):
        super().__init__(color, username)
