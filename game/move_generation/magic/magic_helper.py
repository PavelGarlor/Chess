from typing import List

class MagicHelper:
    rook_directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # E, W, N, S
    bishop_directions = [(1, 1), (-1, 1), (1, -1), (-1, -1)]  # NE, NW, SE, SW
    @staticmethod
    def create_all_blocker_bitboards(movement_mask: int) -> List[int]:
        """
        Generate all possible blocker bitboards within a movement mask.
        Each bit in the movement_mask can be either occupied (1) or empty (0),
        so this generates 2^n possible combinations.
        """
        # Get all indices where movement_mask has a 1
        move_square_indices = [i for i in range(64) if (movement_mask >> i) & 1]

        num_patterns = 1 << len(move_square_indices)  # 2^n
        blocker_bitboards = [0] * num_patterns

        for pattern_index in range(num_patterns):
            bitboard = 0
            for bit_index, sq in enumerate(move_square_indices):
                if (pattern_index >> bit_index) & 1:
                    bitboard |= 1 << sq
            blocker_bitboards[pattern_index] = bitboard

        return blocker_bitboards

    @staticmethod
    def create_movement_mask(square_index: int, ortho: bool) -> int:
        """
        Create movement mask for a rook (ortho=True) or bishop (ortho=False)
        on an empty board, excluding edges.
        """
        mask = 0
        start_x, start_y = square_index % 8, square_index // 8

        directions = MagicHelper.rook_directions if ortho else MagicHelper.bishop_directions

        for dx, dy in directions:
            for dist in range(1, 8):
                x, y = start_x + dx * dist, start_y + dy * dist
                next_x, next_y = start_x + dx * (dist + 1), start_y + dy * (dist + 1)

                if 0 <= x < 8 and 0 <= y < 8:
                    mask |= 1 << (y * 8 + x)
                    if not (0 <= next_x < 8 and 0 <= next_y < 8):
                        break
                else:
                    break

        return mask

    @staticmethod
    def legal_move_bitboard_from_blockers(start_square: int, blocker_bitboard: int, ortho: bool) -> int:
        """
        Calculate all legal moves for a sliding piece from start_square
        given a blocker bitboard.
        """
        bitboard = 0
        start_x, start_y = start_square % 8, start_square // 8
        directions = MagicHelper.rook_directions if ortho else MagicHelper.bishop_directions

        for dx, dy in directions:
            for dist in range(1, 8):
                x, y = start_x + dx * dist, start_y + dy * dist
                if 0 <= x < 8 and 0 <= y < 8:
                    sq_index = y * 8 + x
                    bitboard |= 1 << sq_index
                    if (blocker_bitboard >> sq_index) & 1:
                        break
                else:
                    break

        return bitboard
