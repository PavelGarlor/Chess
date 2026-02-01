


class Player:
    def __init__(self, color: str, username: str = "Player"):
        self.color = color          # "white" or "black"
        self.username = username

    def request_move(self, board_state):
        """
        Return: Move object (or None)
        Human players will return None.
        AI players will override this and return a move.
        """
        return None
