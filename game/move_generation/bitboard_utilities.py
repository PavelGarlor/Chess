# BitBoardUtility.py
from typing import List

from game.models.piece import Piece


class BitBoardUtility:
    # Files

    FILE_A = 0x0101010101010101
    FILE_H = FILE_A << 7
    NOT_A_FILE = ~FILE_A & 0xFFFFFFFFFFFFFFFF
    NOT_H_FILE = ~FILE_H & 0xFFFFFFFFFFFFFFFF

    # Ranks
    RANK1 = 0xFF
    RANK2 = RANK1 << 8
    RANK3 = RANK2 << 8
    RANK4 = RANK3 << 8
    RANK5 = RANK4 << 8
    RANK6 = RANK5 << 8
    RANK7 = RANK6 << 8
    RANK8 = RANK7 << 8

    # Precomputed attack tables
    # Knight offset vectors (C# knightJumps)
    knight_jumps = [
        (-2, -1), (-2, 1),
        (-1, -2), (-1, 2),
        (1, -2), (1, 2),
        (2, -1), (2, 1)
    ]
    KNIGHT_ATTACKS: List[int] = [0] * 64
    KING_ATTACKS: List[int] = [0] * 64
    WHITE_PAWN_ATTACKS: List[int] = [0] * 64
    BLACK_PAWN_ATTACKS: List[int] = [0] * 64
    BETWEEN_MASKS: List[List[int]] = [[0] * 64 for _ in range(64)]

    @staticmethod
    def init_attack_tables():
        BitBoardUtility.BETWEEN_MASKS = BitBoardUtility.generate_between_masks()
        for sq in range(64):
            BitBoardUtility.KNIGHT_ATTACKS[sq] = BitBoardUtility.compute_knight_attacks(sq)
            BitBoardUtility.KING_ATTACKS[sq] = BitBoardUtility.compute_king_attacks(sq)
            BitBoardUtility.WHITE_PAWN_ATTACKS[sq] = BitBoardUtility.compute_pawn_attacks(sq, white=True)
            BitBoardUtility.BLACK_PAWN_ATTACKS[sq] = BitBoardUtility.compute_pawn_attacks(sq, white=False)



    @staticmethod
    def valid_square_index(x: int, y: int):
        """Equivalent to C# ValidSquareIndex(out int targetSquare)"""
        if 0 <= x < 8 and 0 <= y < 8:
            return True, y * 8 + x  # convert (x,y) → 0–63
        return False, None
    @staticmethod
    def compute_knight_attacks(sq: int) -> int:
        """Exact Python equivalent of your C# code"""
        attacks = 0
        x, y = sq % 8, sq // 8
        for dx, dy in BitBoardUtility.knight_jumps:
            knight_x = x + dx
            knight_y = y + dy
            valid, target_square = BitBoardUtility.valid_square_index(knight_x, knight_y)
            if valid:
                attacks |= 1 << target_square
        return attacks
    @staticmethod
    def compute_king_attacks(sq: int) -> int:
        attacks = 0
        x, y = sq % 8, sq // 8
        moves = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        for dx, dy in moves:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                attacks |= 1 << (ny*8 + nx)
        return attacks

    @staticmethod
    def compute_pawn_attacks(sq: int, white=True) -> int:
        attacks = 0
        x, y = sq % 8, sq // 8
        dy = 1 if white else -1
        for dx in [-1, 1]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                attacks |= 1 << (ny*8 + nx)
        return attacks

    # Bitboard manipulation functions
    @staticmethod
    def pop_lsb(bitboard: int) -> tuple[int, int]:
        """Returns (lsb_index, new_bitboard_with_lsb_removed)."""
        lsb = bitboard & -bitboard
        index = (lsb.bit_length() - 1)
        new_bitboard = bitboard ^ lsb
        return index, new_bitboard

    @staticmethod
    def set_square(bb: int, sq: int) -> int:
        return bb | (1 << sq)

    @staticmethod
    def clear_square(bb: int, sq: int) -> int:
        return bb & ~(1 << sq)

    @staticmethod
    def toggle_square(bb: int, sq: int) -> int:
        return bb ^ (1 << sq)

    @staticmethod
    def toggle_squares(bb: int, sq1: int, sq2: int) -> int:
        return bb ^ ((1 << sq1) | (1 << sq2))

    @staticmethod
    def contains_square(bb: int, sq: int) -> bool:
        return ((bb >> sq) & 1) != 0

    @staticmethod
    def shift(bitboard: int, num_squares: int) -> int:
        if num_squares > 0:
            return (bitboard << num_squares) & 0xFFFFFFFFFFFFFFFF
        else:
            return (bitboard >> -num_squares) & 0xFFFFFFFFFFFFFFFF

    @classmethod
    def valid_move_index(cls, sq: int, target: int, d: int) -> bool:
        """
        Checks if a sliding move from sq to target in direction d stays on board
        and doesn't wrap around edges (files).
        """
        if target < 0 or target > 63:
            return False

        sq_file = sq % 8
        target_file = target % 8

        # Horizontal moves (E/W)
        if d == 1 or d == -1:
            if abs(sq_file - target_file) != 1:
                return False

        # Diagonal moves (NE, NW, SE, SW)
        if d in [9, -7]:  # NE or SW
            if target_file - sq_file != 1:
                return False
        if d in [7, -9]:  # NW or SE
            if sq_file - target_file != 1:
                return False

        return True

    @staticmethod
    def rank(square):
        """Return the rank (0-7) of a square 0..63"""
        return square // 8

    @staticmethod
    def file(square):
        """Return the file (0-7) of a square 0..63"""
        return square % 8

    @staticmethod
    def is_aligned(king_sq, sq, direction="rook"):
        """
        Returns True if king_sq and sq are aligned along
        - 'rook' → same rank or same file
        - 'bishop' → same diagonal (\\ or /)
        """
        kr, kf = BitBoardUtility.rank(king_sq), BitBoardUtility.file(king_sq)
        sr, sf = BitBoardUtility.rank(sq), BitBoardUtility.file(sq)

        if direction == "rook":
            return kr == sr or kf == sf

        elif direction == "bishop":
            # Same \ diagonal: rank - file is equal
            if (kr - kf) == (sr - sf):
                return True
            # Same / diagonal: rank + file is equal
            if (kr + kf) == (sr + sf):
                return True
            return False

        else:
            raise ValueError(f"Unknown direction: {direction}")
    @staticmethod
    def squares_from_bitboard(bitboard: int) -> list[int]:
        """
        Returns a list of square indices (0-63) corresponding to set bits in the bitboard.
        """
        squares = []
        while bitboard:
            index, bitboard = BitBoardUtility.pop_lsb(bitboard)
            squares.append(index)
        return squares

    @classmethod
    def bit_scan_forward(cls, bitboard: int) -> int:
        """
        Returns the index (0-63) of the least significant set bit (LSB) in the bitboard.
        Raises ValueError if bitboard is 0.
        """
        if bitboard == 0:
            return -1
        lsb = bitboard & -bitboard
        index = (lsb.bit_length() - 1)
        return index

    @staticmethod
    def get_bishop_attacks(sq: int, blockers: int) -> int:
        attacks = 0
        directions = [9, 7, -9, -7]  # NE, NW, SW, SE
        masks = [
            0xFEFEFEFEFEFEFEFE,  # mask for not wrapping around H file (NE/NW)
            0x7F7F7F7F7F7F7F7F,  # mask for not wrapping around A file (NW/SE)
            0x7F7F7F7F7F7F7F7F,  # same for SW
            0xFEFEFEFEFEFEFEFE  # same for SE
        ]

        for dir, mask in zip(directions, masks):
            attack = 0
            b = 1 << sq
            while True:
                if dir > 0:
                    b <<= dir
                else:
                    b >>= -dir
                if b & mask == 0:
                    break
                attack |= b
                if b & blockers:
                    break
            attacks |= attack
        return attacks

    @staticmethod
    @staticmethod
    def get_rook_attacks(sq: int, blockers: int) -> int:
        attacks = 0
        rank = sq // 8
        file = sq % 8

        # North
        for r in range(rank + 1, 8):
            idx = r * 8 + file
            attacks |= 1 << idx
            if blockers & (1 << idx):
                break

        # South
        for r in range(rank - 1, -1, -1):
            idx = r * 8 + file
            attacks |= 1 << idx
            if blockers & (1 << idx):
                break

        # East
        for f in range(file + 1, 8):
            idx = rank * 8 + f
            attacks |= 1 << idx
            if blockers & (1 << idx):
                break

        # West
        for f in range(file - 1, -1, -1):
            idx = rank * 8 + f
            attacks |= 1 << idx
            if blockers & (1 << idx):
                break

        return attacks

    @staticmethod
    def generate_between_masks():
        """
        Precompute all squares between any two squares along ranks, files, or diagonals.
        Returns a 64x64 array of 64-bit integers.
        """
        masks = [[0 for _ in range(64)] for _ in range(64)]

        def square_index(file, rank):
            return rank * 8 + file

        for from_rank in range(8):
            for from_file in range(8):
                from_sq = square_index(from_file, from_rank)

                for to_rank in range(8):
                    for to_file in range(8):
                        to_sq = square_index(to_file, to_rank)

                        # Skip same square
                        if from_sq == to_sq:
                            continue

                        mask = 0

                        df = to_file - from_file
                        dr = to_rank - from_rank

                        # Check rank alignment
                        if from_rank == to_rank:
                            step = 1 if df > 0 else -1
                            for f in range(from_file + step, to_file, step):
                                mask |= 1 << square_index(f, from_rank)

                        # Check file alignment
                        elif from_file == to_file:
                            step = 1 if dr > 0 else -1
                            for r in range(from_rank + step, to_rank, step):
                                mask |= 1 << square_index(from_file, r)

                        # Check diagonal alignment
                        elif abs(df) == abs(dr):
                            step_file = 1 if df > 0 else -1
                            step_rank = 1 if dr > 0 else -1
                            f, r = from_file + step_file, from_rank + step_rank
                            while f != to_file and r != to_rank:
                                mask |= 1 << square_index(f, r)
                                f += step_file
                                r += step_rank

                        masks[from_sq][to_sq] = mask

        return masks

    @staticmethod
    def count_bits(bb: int) -> int:
        """
        Count the number of set bits (1s) in the bitboard `bb`.
        """
        return bb.bit_count()


# Initialize attack tables at import
BitBoardUtility.init_attack_tables()
