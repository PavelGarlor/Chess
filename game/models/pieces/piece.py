from abc import ABC, abstractmethod
from typing import List, Tuple



Position = Tuple[int, int]


class Piece(ABC):
    SYMBOL = "?"
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
    SYMBOL = "p"
    def get_allowed_moves(self, position, board_state):
        moves = []
        x, y = position

        direction = 1 if self.color == "white" else -1
        start_row = 1 if self.color == "white" else 6

        # -----------------------
        # Forward move (1 square)
        # -----------------------
        one_step = (x, y + direction)
        if board_state.is_empty(one_step):
            moves.append(one_step)

            # -----------------------
            # Forward move (2 squares)
            # -----------------------
            two_step = (x, y + 2 * direction)
            if y == start_row and board_state.is_empty(two_step):
                moves.append(two_step)

        # -----------------------
        # Captures (diagonal)
        # -----------------------
        for dx in (-1, 1):
            capture_pos = (x + dx, y + direction)
            if board_state.is_enemy(capture_pos, self.color):
                moves.append(capture_pos)

        return moves


# -------------------------------------------------
# ROOK
# -------------------------------------------------
class Rook(Piece):
    SYMBOL = "r"
    def get_allowed_moves(self, position, board_state):
        moves = []
        x, y = position
        directions = [
            (1, 0),   # right
            (-1, 0),  # left
            (0, 1),   # up
            (0, -1),  # down
        ]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy

            while 0 <= nx < 8 and 0 <= ny < 8:
                pos = (nx, ny)

                if board_state.is_empty(pos):
                    moves.append(pos)
                else:
                    if board_state.is_enemy(pos, self.color):
                        moves.append(pos)
                    break  # stop scanning in this direction

                nx += dx
                ny += dy

        return moves


# -------------------------------------------------
# BISHOP
# -------------------------------------------------
class Bishop(Piece):
    SYMBOL = "b"
    def get_allowed_moves(self, position, board_state):
        return []


# -------------------------------------------------
# KNIGHT
# -------------------------------------------------
class Knight(Piece):
    SYMBOL = "n"
    def get_allowed_moves(self, position, board_state):
        return []


# -------------------------------------------------
# QUEEN
# -------------------------------------------------
class Queen(Piece):
    SYMBOL = "q"
    def get_allowed_moves(self, position, board_state):
        return []


# -------------------------------------------------
# KING
# -------------------------------------------------
class King(Piece):
    SYMBOL = "k"
    def get_allowed_moves(self, position, board_state):
        return []
