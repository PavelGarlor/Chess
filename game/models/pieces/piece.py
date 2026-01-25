from abc import ABC, abstractmethod
from typing import List, Tuple


Position = Tuple[int, int]


class Piece(ABC):
    def __init__(self, color: str):
        self.color = color
        self.position: Position | None = None

    @abstractmethod
    def get_pseudo_legal_moves(
        self,
        position: Position,
        board_state,
    ) -> List[Position]:
        """
        Returns all moves ignoring check/checkmate.
        To be implemented later.
        """
        pass

    def enemy_color(self) -> str:
        return "black" if self.color == "white" else "white"


# -------------------------------------------------
# PAWN
# -------------------------------------------------
class Pawn(Piece):
    def get_pseudo_legal_moves(self, position, board_state):
        pass


# -------------------------------------------------
# ROOK
# -------------------------------------------------
class Rook(Piece):
    def get_pseudo_legal_moves(self, position, board_state):
        pass


# -------------------------------------------------
# BISHOP
# -------------------------------------------------
class Bishop(Piece):
    def get_pseudo_legal_moves(self, position, board_state):
        pass


# -------------------------------------------------
# KNIGHT
# -------------------------------------------------
class Knight(Piece):
    def get_pseudo_legal_moves(self, position, board_state):
        pass


# -------------------------------------------------
# QUEEN
# -------------------------------------------------
class Queen(Piece):
    def get_pseudo_legal_moves(self, position, board_state):
        pass


# -------------------------------------------------
# KING
# -------------------------------------------------
class King(Piece):
    def get_pseudo_legal_moves(self, position, board_state):
        pass
