from typing import List
from .magic_helper import MagicHelper
from .precomputed_magic import PrecomputedMagics


class Magic:
    RookMask: List[int] = [0] * 64
    BishopMask: List[int] = [0] * 64
    RookAttacks: List[List[int]] = [[] for _ in range(64)]
    BishopAttacks: List[List[int]] = [[] for _ in range(64)]

    @staticmethod
    def get_slider_attacks(square: int, blockers: int, ortho: bool) -> int:
        return Magic.get_rook_attacks(square, blockers) if ortho else Magic.get_bishop_attacks(square, blockers)

    @staticmethod
    def get_rook_attacks(square: int, blockers: int) -> int:
        mask = Magic.RookMask[square]
        magic = PrecomputedMagics.RookMagics[square]
        shift = PrecomputedMagics.RookShifts[square]
        relevant_bits = bin(mask).count("1")
        table_size = 1 << relevant_bits
        index = ((blockers & mask) * magic) >> (64 - relevant_bits)
        index &= table_size - 1  # ensure index fits
        return Magic.RookAttacks[square][index]

    @staticmethod
    def get_bishop_attacks(square: int, blockers: int) -> int:
        mask = Magic.BishopMask[square]
        magic = PrecomputedMagics.BishopMagics[square]
        shift = PrecomputedMagics.BishopShifts[square]
        relevant_bits = bin(mask).count("1")
        table_size = 1 << relevant_bits
        index = ((blockers & mask) * magic) >> (64 - relevant_bits)
        index &= table_size - 1
        return Magic.BishopAttacks[square][index]

    # Initialize tables
    for sq in range(64):
        RookMask[sq] = MagicHelper.create_movement_mask(sq, True)
        BishopMask[sq] = MagicHelper.create_movement_mask(sq, False)

    for sq in range(64):
        def create_table(square: int, rook: bool, magic: int) -> List[int]:
            movement_mask = MagicHelper.create_movement_mask(square, rook)
            blocker_patterns = MagicHelper.create_all_blocker_bitboards(movement_mask)
            relevant_bits = bin(movement_mask).count("1")
            table_size = 1 << relevant_bits
            table = [0] * table_size
            for pattern in blocker_patterns:
                index = ((pattern & movement_mask) * magic) >> (64 - relevant_bits)
                index &= table_size - 1
                table[index] = MagicHelper.legal_move_bitboard_from_blockers(square, pattern, rook)
            return table

        RookAttacks[sq] = create_table(sq, True, PrecomputedMagics.RookMagics[sq])
        BishopAttacks[sq] = create_table(sq, False, PrecomputedMagics.BishopMagics[sq])
