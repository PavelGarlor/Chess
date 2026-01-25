from abc import ABC, abstractmethod
from typing import List, Tuple


Position = Tuple[int, int]


class Piece(ABC):
    def __init__(self, color: str):
        self.color = color
        self.position: Position | None = None

    @abstractmethod
    def get_allowed_moves(
        self,
        position: Position,
        board_state,
    ) -> List[Position]:
        """
        Returns all moves ignoring check/checkmate.
        To be implemented later.
        """
        return []

    def enemy_color(self) -> str:
        return "black" if self.color == "white" else "white"


# -------------------------------------------------
# PAWN
# -------------------------------------------------
class Pawn(Piece):
    def get_allowed_moves(self, position, board_state):
        return []


# -------------------------------------------------
# ROOK
# -------------------------------------------------
class Rook(Piece):
    def get_allowed_moves(self, position, board_state):
        return []


# -------------------------------------------------
# BISHOP
# -------------------------------------------------
class Bishop(Piece):
    def get_allowed_moves(self, position, board_state):
        return []


# -------------------------------------------------
# KNIGHT
# -------------------------------------------------
class Knight(Piece):
    def get_allowed_moves(self, position, board_state):
        return []


# -------------------------------------------------
# QUEEN
# -------------------------------------------------
class Queen(Piece):
    def get_allowed_moves(self, position, board_state):
        return []


# -------------------------------------------------
# KING
# -------------------------------------------------
class King(Piece):
    def get_allowed_moves(self, position, board_state):
        return []
