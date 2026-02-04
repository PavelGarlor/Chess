from abc import ABC, abstractmethod
from typing import List, Tuple

from game.models.move import Move

Position = Tuple[int, int]


class Piece(ABC):
    SYMBOL = "?"
    def __init__(self, color: str, position = None):
        self.color = color
        self.position: Position | None = position

    @abstractmethod
    def get_allowed_moves(
        self,
        position: Position,
        board_state,
        for_attack=False

    ) -> List[Move]:
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

    def get_allowed_moves(self, position, board_state, for_attack=False):
        """
        Generate all allowed moves for this pawn.

        :param position: current pawn position (x, y)
        :param board_state: BoardState object
        :param for_attack: if True, include diagonal squares even if empty (for is_square_attacked)
        :return: list of Move objects
        """
        moves: List[Move] = []
        x, y = position

        direction = 1 if self.color == "white" else -1
        start_row = 1 if self.color == "white" else 6
        promotion_rank = 7 if self.color == "white" else 0

        # -----------------------
        # Forward move (1 square)
        # -----------------------
        one_step = (x, y + direction)
        if board_state.is_empty(one_step) and not for_attack:

            # Promotion
            if one_step[1] == promotion_rank:
                moves.extend([
                    Move(self, one_step, Queen(self.color, position)),
                    Move(self, one_step, Knight(self.color, position)),
                    Move(self, one_step, Bishop(self.color, position)),
                    Move(self, one_step, Rook(self.color, position)),
                ])
            else:
                moves.append(Move(self, one_step))

            # -----------------------
            # Forward move (2 squares)
            # -----------------------
            two_step = (x, y + 2 * direction)
            if y == start_row and board_state.is_empty(two_step):
                moves.append(Move(self, two_step))

        # -----------------------
        # Captures (diagonal)
        # -----------------------
        for dx in (-1, 1):
            target = (x + dx, y + direction)
            if for_attack:
                # For attack checking, include diagonal squares even if empty
                moves.append(Move(self, target))
            else:
                if board_state.is_enemy(target, self.color):
                    # Promotion capture
                    if target[1] == promotion_rank:
                        moves.extend([
                            Move(self, target, Queen(self.color, position)),
                            Move(self, target, Knight(self.color, position)),
                            Move(self, target, Bishop(self.color, position)),
                            Move(self, target, Rook(self.color, position)),
                        ])
                    else:
                        moves.append(Move(self, target))
                # En passant
                elif board_state.en_passant_target == target:
                    moves.append(Move(self, target))

        return moves


# -------------------------------------------------
# ROOK
# -------------------------------------------------
class Rook(Piece):
    SYMBOL = "r"
    def get_allowed_moves(self, position, board_state,for_attack=False):
        moves: List[Move] = []
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
                    moves.append(Move(self,pos))
                else:
                    if board_state.is_enemy(pos, self.color):
                        moves.append(Move(self,pos))
                    break  # stop scanning in this direction

                nx += dx
                ny += dy

        return moves

# -------------------------------------------------
# BISHOP
# -------------------------------------------------
class Bishop(Piece):
    SYMBOL = "b"
    def get_allowed_moves(self, position, board_state,for_attack=False):
        moves: List[Move] = []
        x, y = position
        directions = [
            (1, 1),
            (-1, 1),
            (1, -1),
            (-1, -1),
        ]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy

            while 0 <= nx < 8 and 0 <= ny < 8:
                pos = (nx, ny)

                if board_state.is_empty(pos):
                    moves.append(Move(self,pos))
                else:
                    if board_state.is_enemy(pos, self.color):
                        moves.append(Move(self,pos))
                    break  # stop scanning in this direction

                nx += dx
                ny += dy

        return moves


# -------------------------------------------------
# KNIGHT
# -------------------------------------------------
class Knight(Piece):
    SYMBOL = "n"
    def get_allowed_moves(self, position, board_state,for_attack=False):
        moves: List[Move] = []
        x, y = position

        jumps = [
            (-2, -1), (-2,  1),
            (-1, -2), (-1,  2),
            ( 1, -2), ( 1,  2),
            ( 2, -1), ( 2,  1),
        ]

        for dx, dy in jumps:
            nx, ny = x + dx, y + dy
            new_pos = (nx, ny)

            if not board_state.in_bounds(new_pos):
                continue

            if board_state.is_empty(new_pos):
                moves.append(Move(self,new_pos))
            elif board_state.is_enemy(new_pos, self.color):
                moves.append(Move(self,new_pos))

        return moves


# -------------------------------------------------
# QUEEN
# -------------------------------------------------
class Queen(Piece):
    SYMBOL = "q"
    def get_allowed_moves(self, position, board_state,for_attack=False):
        moves: List[Move] = []
        x, y = position
        directions = [
            (1, 0),  # right
            (-1, 0),  # left
            (0, 1),  # up
            (0, -1),  # down
            (1, 1),
            (-1, 1),
            (1, -1),
            (-1, -1),
        ]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy

            while 0 <= nx < 8 and 0 <= ny < 8:
                pos = (nx, ny)

                if board_state.is_empty(pos):
                    moves.append(Move(self,pos))
                else:
                    if board_state.is_enemy(pos, self.color):
                        moves.append(Move(self,pos))
                    break  # stop scanning in this direction

                nx += dx
                ny += dy

        return moves


# -------------------------------------------------
# KING
# -------------------------------------------------
class King(Piece):
    SYMBOL = "k"

    def get_allowed_moves(self, position, board_state,for_attack=False):
        moves: List[Move] = []
        x, y = position
        color = self.color

        # All 8 possible directions
        directions = [
            (-1, -1), (0, -1), (1, -1),
            (-1, 0), (1, 0),
            (-1, 1), (0, 1), (1, 1),
        ]
        if board_state.castling_rights[color]["K"]:
            # Squares between king and rook must be empty
            if board_state.is_empty((x + 1, y)) and board_state.is_empty((x + 2, y)):
                # King cannot castle through check (you need an is_square_attacked function)
                # if not board_state.is_square_attacked((x, y), color) and \
                #         not board_state.is_square_attacked((x + 1, y), color) and \
                #         not board_state.is_square_attacked((x + 2, y), color):
                moves.append(Move(self,(x + 2, y)))

        if board_state.castling_rights[color]["Q"]:
            if board_state.is_empty((x - 1, y)) and board_state.is_empty((x - 2, y)) and board_state.is_empty(
                    (x - 3, y)):
                # if not board_state.is_square_attacked((x, y), color) and \
                #         not board_state.is_square_attacked((x - 1, y), color) and \
                #         not board_state.is_square_attacked((x - 2, y), color):
                moves.append(Move(self,(x - 2, y)))

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            new_pos = (nx, ny)

            if not board_state.in_bounds(new_pos):
                continue

            if board_state.is_empty(new_pos):
                moves.append(Move(self,new_pos))
            elif board_state.is_enemy(new_pos, self.color):
                moves.append(Move(self,new_pos))

        return moves
