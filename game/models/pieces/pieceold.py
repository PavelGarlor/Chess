from abc import ABC, abstractmethod

from typing import List, Tuple

from game.models.move import Move
from game.models.piece import Piece

Position = Tuple[int, int]


class PieceOld(ABC):
    SYMBOL = "?"
    PIECE_TYPE = Piece.NoneType
    PIECE_TO_INDEX = {
        ("white", "pawn"): 0,
        ("white", "knight"): 1,
        ("white", "bishop"): 2,
        ("white", "rook"): 3,
        ("white", "queen"): 4,
        ("white", "king"): 5,

        ("black", "pawn"): 6,
        ("black", "knight"): 7,
        ("black", "bishop"): 8,
        ("black", "rook"): 9,
        ("black", "queen"): 10,
        ("black", "king"): 11,
    }

    def __init__(self, color: str, position: tuple[int, int]):
        self.color = color
        self.position = position

        # 0 = white, 1 = black
        self.color_index = 0 if color == "white" else 1

        # name must be implemented in child classes
        name = self.__class__.__name__.lower()  # "pawn", "rook", etc.

        # Assign bitboard index
        self.piece_index = self.PIECE_TO_INDEX[(color, name)]


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

    def get_piece_id(self) -> int:
        piece_type = self.PIECE_TYPE - 1 # e.g., Piece.Pawn = 1, Piece.Rook = 4

        if self.color == "white":
            return piece_type  # already WhitePawn..WhiteKing (1..6)

        else:
            return piece_type + 6


# -------------------------------------------------
# PAWN
# -------------------------------------------------
class Pawn(PieceOld):
    SYMBOL = "p"
    PIECE_TYPE = Piece.Pawn
    PIECE_ID = 0
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
                    Move(self.position, one_step, Queen(self.color, position)),
                    Move(self.position, one_step, Knight(self.color, position)),
                    Move(self.position, one_step, Bishop(self.color, position)),
                    Move(self.position, one_step, Rook(self.color, position)),
                ])
            else:
                moves.append(Move(self.position, one_step))

            # -----------------------
            # Forward move (2 squares)
            # -----------------------
            two_step = (x, y + 2 * direction)
            if y == start_row and board_state.is_empty(two_step):
                moves.append(Move(self.position, two_step))

        # -----------------------
        # Captures (diagonal)
        # -----------------------
        for dx in (-1, 1):
            target = (x + dx, y + direction)
            if for_attack:
                # For attack checking, include diagonal squares even if empty
                moves.append(Move(self.position, target))
            else:
                if board_state.is_enemy(target, self.color):
                    # Promotion capture
                    if target[1] == promotion_rank:
                        moves.extend([
                            Move(self.position, target, Queen(self.color, position)),
                            Move(self.position, target, Knight(self.color, position)),
                            Move(self.position, target, Bishop(self.color, position)),
                            Move(self.position, target, Rook(self.color, position)),
                        ])
                    else:
                        moves.append(Move(self.position, target))
                # En passant
                elif board_state.en_passant_target == target:
                    moves.append(Move(self.position, target))

        return moves


# -------------------------------------------------
# ROOK
# -------------------------------------------------
class Rook(PieceOld):
    SYMBOL = "r"
    PIECE_TYPE = Piece.Rook
    PIECE_ID = 3
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
                    moves.append(Move(self.position,pos))
                else:
                    if board_state.is_enemy(pos, self.color):
                        moves.append(Move(self.position,pos))
                    break  # stop scanning in this direction

                nx += dx
                ny += dy

        return moves

# -------------------------------------------------
# BISHOP
# -------------------------------------------------
class Bishop(PieceOld):
    SYMBOL = "b"
    PIECE_TYPE = Piece.Bishop
    PIECE_ID = 2
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
                    moves.append(Move(self.position,pos))
                else:
                    if board_state.is_enemy(pos, self.color):
                        moves.append(Move(self.position,pos))
                    break  # stop scanning in this direction

                nx += dx
                ny += dy

        return moves


# -------------------------------------------------
# KNIGHT
# -------------------------------------------------
class Knight(PieceOld):
    SYMBOL = "n"
    PIECE_TYPE = Piece.Knight
    PIECE_ID = 1
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
                moves.append(Move(self.position,new_pos))
            elif board_state.is_enemy(new_pos, self.color):
                moves.append(Move(self.position,new_pos))

        return moves


# -------------------------------------------------
# QUEEN
# -------------------------------------------------
class Queen(PieceOld):
    SYMBOL = "q"
    PIECE_TYPE = Piece.Queen
    PIECE_ID = 4
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
                    moves.append(Move(self.position,pos))
                else:
                    if board_state.is_enemy(pos, self.color):
                        moves.append(Move(self.position,pos))
                    break  # stop scanning in this direction

                nx += dx
                ny += dy

        return moves


# -------------------------------------------------
# KING
# -------------------------------------------------
class King(PieceOld):
    SYMBOL = "k"
    PIECE_TYPE = Piece.King
    PIECE_ID = 5
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
        if board_state.board_data.castling_rights[color]["K"]:
            # Squares between king and rook must be empty
            if board_state.is_empty((x + 1, y)) and board_state.is_empty((x + 2, y)):
                # King cannot castle through check (you need an is_square_attacked function)
                # if not board_state.is_square_attacked((x, y), color) and \
                #         not board_state.is_square_attacked((x + 1, y), color) and \
                #         not board_state.is_square_attacked((x + 2, y), color):
                moves.append(Move(self.position,(x + 2, y)))

        if board_state.board_data.castling_rights[color]["Q"]:
            if board_state.is_empty((x - 1, y)) and board_state.is_empty((x - 2, y)) and board_state.is_empty(
                    (x - 3, y)):
                # if not board_state.is_square_attacked((x, y), color) and \
                #         not board_state.is_square_attacked((x - 1, y), color) and \
                #         not board_state.is_square_attacked((x - 2, y), color):
                moves.append(Move(self.position,(x - 2, y)))

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            new_pos = (nx, ny)

            if not board_state.in_bounds(new_pos):
                continue

            if board_state.is_empty(new_pos):
                moves.append(Move(self.position,new_pos))
            elif board_state.is_enemy(new_pos, self.color):
                moves.append(Move(self.position,new_pos))

        return moves
