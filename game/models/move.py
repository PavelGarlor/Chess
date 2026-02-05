

class Move:
    def __init__(self, piece , target_pos : tuple[int,int] , promotion  = None):
        self.piece = piece
        self.target_pos = target_pos
        self.promotion = promotion

    def __str__(self):
        return f"{self.piece.__class__.__name__}({self.piece.color}) {self.piece.position} -> {self.target_pos}"

    __repr__ = __str__  # optional, so lists of moves print nicely