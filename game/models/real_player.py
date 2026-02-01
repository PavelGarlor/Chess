from game.models.player import Player


class RealPlayer(Player):
    def __init__(self, color: str , username):
        super().__init__(color,username)

