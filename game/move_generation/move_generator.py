from torch.onnx.symbolic_opset9 import is_pinned

from game.models.move import Move
from game.models.piece import Piece
from game.models.pieces.pieceold import Pawn, Knight, Bishop, Rook, Queen, King
from game.move_generation.bitboard_utilities import BitBoardUtility
from game.move_generation.magic.magic import Magic


class MoveGenerator:
    def __init__(self, board, generate_quiet=True):


        self.pinned_move_masks = {}
        self.opponent_sliding_attack_map = 0
        self.board = board
        self.board_state = board.board_data
        self.generate_quiet_moves = generate_quiet
        self.empty_squares = ~self.board_state.all_pieces & 0xFFFFFFFFFFFFFFFF
        self.enemy_color = 0 if not self.board_state.is_whites_turn else 6
        self.friendly_color = 0 if self.board_state.is_whites_turn else 6
        self.enemy_pieces = self.board_state.color_pieces[1 if self.board_state.is_whites_turn else 0]
        self.friendly_pieces = self.board_state.color_pieces[0 if self.board_state.is_whites_turn else 1]
        self.enemy_rooks_or_queens = self.board_state.pieces_bitboard[Piece.Rook + self.enemy_color -1] | self.board_state.pieces_bitboard[Piece.Queen + self.enemy_color -1]
        self.empty_or_enemy_squares = self.empty_squares | self.enemy_pieces
        self.move_type_mask = (2 ** 64 - 1) if generate_quiet else self.enemy_pieces

        self.check_ray_bitmask = 0xFFFFFFFFFFFFFFFF
        self.in_check = False
        self.in_double_check = False
        self.pin_rays = 0
        self.pin_mask = {}  # maps pinned square → allowed movement bitboard
        self.not_pin_rays = ~self.pin_rays
        self.enemy_attack_map = 0
        self.king_square = self.board.king_square(self.board_state.is_whites_turn)
        self.calculate_attack_data()

    # ----------------- Pawn moves -----------------
    def generate_pawn_moves(self):
        moves = []
        push_dir = 1 if self.board_state.is_whites_turn else -1
        push_offset = push_dir * 8
        pawns = self.board_state.pieces_bitboard[Piece.Pawn + self.friendly_color - 1]

        promotion_rank_mask = BitBoardUtility.RANK8 if self.board_state.is_whites_turn else BitBoardUtility.RANK1

        # -----------------------------
        # PUSHES
        # -----------------------------
        single_push = BitBoardUtility.shift(pawns, push_offset) & self.empty_squares
        push_promotions = single_push & promotion_rank_mask & self.check_ray_bitmask
        single_push_no_promotions = single_push & ~promotion_rank_mask & self.check_ray_bitmask

        # -----------------------------
        # CAPTURES
        # -----------------------------
        capture_edge_file_mask = BitBoardUtility.NOT_A_FILE if self.board_state.is_whites_turn else BitBoardUtility.NOT_H_FILE
        capture_edge_file_mask2 = BitBoardUtility.NOT_H_FILE if self.board_state.is_whites_turn else BitBoardUtility.NOT_A_FILE

        # normal captures
        capture_a = BitBoardUtility.shift(pawns & capture_edge_file_mask, push_dir * 7) & self.enemy_pieces
        capture_b = BitBoardUtility.shift(pawns & capture_edge_file_mask2, push_dir * 9) & self.enemy_pieces

        # promotions for captures
        capture_promotions_a = capture_a & promotion_rank_mask & self.check_ray_bitmask
        capture_promotions_b = capture_b & promotion_rank_mask & self.check_ray_bitmask

        capture_a &= self.check_ray_bitmask & ~promotion_rank_mask
        capture_b &= self.check_ray_bitmask & ~promotion_rank_mask

        # ============================================================
        # 🔥 PIN HANDLER (core logic)
        # ============================================================
        def allowed(start_sq, target_sq):
            """Return True if move is legal given pin constraints."""
            if start_sq not in self.pin_mask:
                return True  # not pinned → always allowed
            return (1 << target_sq) & self.pin_mask[start_sq]

        # ============================================================
        # PUSH MOVES
        # ============================================================
        while single_push_no_promotions:
            target_sq, single_push_no_promotions = BitBoardUtility.pop_lsb(single_push_no_promotions)
            start_sq = target_sq - push_offset

            if allowed(start_sq, target_sq):
                moves.append(Move(self.index_to_xy(start_sq),
                                  self.index_to_xy(target_sq)))

        # Double push
        double_push_rank = BitBoardUtility.RANK4 if self.board_state.is_whites_turn else BitBoardUtility.RANK5
        double_push = BitBoardUtility.shift(single_push, push_offset) & self.empty_squares & double_push_rank

        while double_push:
            target_sq, double_push = BitBoardUtility.pop_lsb(double_push)
            start_sq = target_sq - push_offset * 2

            if allowed(start_sq, target_sq):
                moves.append(Move(self.index_to_xy(start_sq),
                                  self.index_to_xy(target_sq),
                                  en_passant=True))

        # ============================================================
        # NORMAL CAPTURES
        # ============================================================
        for capture_bb, offset in [(capture_a, 7), (capture_b, 9)]:
            while capture_bb:
                target_sq, capture_bb = BitBoardUtility.pop_lsb(capture_bb)
                start_sq = target_sq - push_dir * offset

                if allowed(start_sq, target_sq):
                    moves.append(Move(self.index_to_xy(start_sq),
                                      self.index_to_xy(target_sq)))

        # ============================================================
        # PROMOTION CAPTURES + PROMOTION SINGLE PUSHES
        # ============================================================
        for promo_bb, offset in [(push_promotions, 8), (capture_promotions_a, 7), (capture_promotions_b, 9)]:
            while promo_bb:
                target_sq, promo_bb = BitBoardUtility.pop_lsb(promo_bb)
                start_sq = target_sq - push_dir * offset

                if allowed(start_sq, target_sq):
                    for promo_piece in [Queen, Rook, Bishop, Knight]:
                        moves.append(
                            Move(self.index_to_xy(start_sq),
                                 self.index_to_xy(target_sq),
                                 promotion=promo_piece)
                        )

        # ============================================================
        # EN PASSANT — MUST ALSO RESPECT PIN
        # ============================================================
        capture_a = BitBoardUtility.shift(pawns & capture_edge_file_mask, push_dir * 7)
        capture_b = BitBoardUtility.shift(pawns & capture_edge_file_mask2, push_dir * 9)

        if self.board_state.en_passant_target is not None:
            ep_x, ep_y = self.board_state.en_passant_target
            ep_index = self.xy_to_index(ep_x, ep_y)
            ep_bit = 1 << ep_index

            for capture_mask, offset in [(capture_a, 7), (capture_b, 9)]:
                if capture_mask & ep_bit:
                    start_sq = ep_index - push_dir * offset

                    if allowed(start_sq, ep_index):
                        moves.append(
                            Move(
                                self.index_to_xy(start_sq),
                                self.index_to_xy(ep_index),
                                en_passant=True
                            )
                        )

        return moves

    # ----------------- Knight moves -----------------
    def generate_knights_moves(self):
        moves = []
        knight_type = Piece.Knight + self.friendly_color - 1
        knights = self.board_state.pieces_bitboard[knight_type]
        move_mask = self.empty_or_enemy_squares & self.move_type_mask
        color = "white" if not self.friendly_color else "black"
        while knights:
            knight_sq, knights = BitBoardUtility.pop_lsb(knights)
            targets = BitBoardUtility.KNIGHT_ATTACKS[knight_sq] & move_mask
            for target_sq in BitBoardUtility.squares_from_bitboard(targets):
                if self.is_not_pinned(knight_sq, target_sq):
                    moves.append(Move(self.index_to_xy(knight_sq),
                                      self.index_to_xy(target_sq)))
        return moves

    # ----------------- Sliding moves -----------------
    def generate_sliding_moves(self, piece_cls, is_white,ignore_pins: bool = False) -> list[Move]:
        """
        Generate sliding moves (bishop, rook, queen) with optional pin check.

        Args:
            piece_cls: Piece type (Piece.Bishop / Piece.Rook / Piece.Queen)
            ignore_pins: If True, ignores pin restrictions (used for enemy attack maps)
        Returns:
            List of Move objects
        """
        moves: list[Move] = []
        piece_type_index = piece_cls + (0 if is_white else 6) - 1
        pieces_bb = self.board_state.pieces_bitboard[piece_type_index]

        occ = self.board_state.all_pieces
        pin_rays = self.pin_rays if not ignore_pins else 0

        while pieces_bb:
            sq, pieces_bb = BitBoardUtility.pop_lsb(pieces_bb)
            start_xy = self.index_to_xy(sq)

            # --- 1. Compute raw sliding attacks ---
            if piece_cls == Piece.Bishop:
                attack_bb = BitBoardUtility.get_bishop_attacks(sq, occ)
            elif piece_cls == Piece.Rook:
                attack_bb = BitBoardUtility.get_rook_attacks(sq, occ)
            else:
                attack_bb = (
                        BitBoardUtility.get_bishop_attacks(sq, occ)
                        | BitBoardUtility.get_rook_attacks(sq, occ)
                )

            # Only keep empty or enemy squares
            attack_bb &= self.empty_or_enemy_squares

            # --- 2. Apply pin logic if needed ---
            if pin_rays:
                pinned_mask = pin_rays & (1 << sq)
                if pinned_mask:
                    # Allow only moves along the pin ray
                    attack_bb &= pin_rays

            # --- 3. Convert bitboard to Move objects ---
            while attack_bb:
                target_sq, attack_bb = BitBoardUtility.pop_lsb(attack_bb)
                moves.append(Move(start_xy, self.index_to_xy(target_sq)))

        return moves

    # ----------------- King moves & Castling -----------------
    def generate_king_moves(self):
        moves = []

        king_type = Piece.King + self.friendly_color - 1
        king_bb = self.board_state.pieces_bitboard[king_type]
        king_sq = BitBoardUtility.bit_scan_forward(king_bb)
        if king_sq == -1:
            return []

        self.king_square = king_sq
        # print("-----------------------------START-------------------------------")
        # Squares attacked by enemy + occupied by friendly pieces are illegal
        # self.print_bitboard(  self.enemy_attack_map, title = "Enemy Attack Bitboard")
        illegal_squares = self.enemy_attack_map | self.friendly_pieces
        # self.print_bitboard(illegal_squares, title="Illegal Squares Bitboard")
        # King can move to adjacent squares that are not illegal
        king_attacks = BitBoardUtility.KING_ATTACKS[king_sq]
        # self.print_bitboard(king_attacks, title="King_attacks Bitboard")
        legal_squares = king_attacks & ~illegal_squares & self.move_type_mask
        # self.print_bitboard(legal_squares, title="Legal squares Bitboard")

        for target_sq in BitBoardUtility.squares_from_bitboard(legal_squares):
            moves.append(Move(self.index_to_xy(king_sq), self.index_to_xy(target_sq)))

        # Castling (king cannot castle through or into check)
        moves.extend(self.generate_castling_moves(king_sq))

        return moves

    def generate_castling_moves(self, king_sq):
        moves = []
        color = "white" if self.board_state.is_whites_turn else "black"
        rank = 0 if color == "white" else 7

        rights = self.board_state.castling_rights[color]

        # Kingside castling
        if rights["K"]:
            f_sq = rank * 8 + 5
            g_sq = rank * 8 + 6
            # all squares between king and rook must be empty
            if ((self.empty_squares >> f_sq) & 1) and ((self.empty_squares >> g_sq) & 1):
                # king cannot be in check or pass through attacked squares
                if not self.is_square_attacked(rank * 8 + 4) and \
                        not self.is_square_attacked(f_sq) and \
                        not self.is_square_attacked(g_sq):
                    moves.append(Move(
                        self.index_to_xy(king_sq),
                        self.index_to_xy(g_sq)
                    ))

        # Queenside castling
        if rights["Q"]:
            d_sq = rank * 8 + 3
            c_sq = rank * 8 + 2
            b_sq = rank * 8 + 1
            if ((self.empty_squares >> d_sq) & 1) and ((self.empty_squares >> c_sq) & 1) and (
                    (self.empty_squares >> b_sq) & 1):
                if not self.is_square_attacked(rank * 8 + 4) and \
                        not self.is_square_attacked(d_sq) and \
                        not self.is_square_attacked(c_sq):
                    moves.append(Move(
                        self.index_to_xy(king_sq),
                        self.index_to_xy(c_sq)
                    ))

        return moves

    # ----------------- Helpers -----------------
    def index_to_xy(self, sq: int):
        return (sq % 8, sq // 8)

    def calculate_attack_data(self):
        """
        Compute enemy attacks, pin rays, check rays
        """
        self.in_check = False
        self.in_double_check = False
        color = "white" if not self.board_state.is_whites_turn else "black"
        self.enemy_attack_map = self.generate_enemy_attack_map(color)
        self.gen_sliding_attack_map()
        self.check_ray_bitmask = 0xFFFFFFFFFFFFFFFF
        self.pin_rays = 0
        self.not_pin_rays = ~self.pin_rays

    def is_square_attacked(self, sq: int) -> bool:
        """
        Returns True if the given square `sq` is attacked by any enemy piece.
        Uses the precomputed enemy attack map.
        """
        return (self.enemy_attack_map >> sq) & 1 != 0

    # def is_pinned(self, square: int) -> bool:
    #     """Return True if the piece on `square` is pinned to its king."""
    #     return ((self.pin_rays >> square) & 1) != 0

    def is_pinned(self, sq):
        return sq in self.pin_mask

    def gen_sliding_attack_map(self):
        """Generate the bitboard of all squares attacked by enemy rooks, bishops, and queens."""
        self.opponent_sliding_attack_map = 0

        # Orthogonal sliders: rooks + queens
        self._update_slide_attack(self.board_state.enemy_orthogonal_sliders, ortho=True)
        # Diagonal sliders: bishops + queens
        self._update_slide_attack(self.board_state.enemy_diagonal_sliders, ortho=False)

    def _update_slide_attack(self, piece_board: int, ortho: bool):
        """Update attack map for all pieces in `piece_board` (bitboard) in given directions."""
        # Remove friendly king to avoid sliding attacks passing through it
        blockers = self.board_state.all_pieces & ~(1 << self.king_square)

        while piece_board:
            start_square, piece_board = BitBoardUtility.pop_lsb(piece_board)
            move_board = Magic.get_slider_attacks(start_square, blockers, ortho)
            self.opponent_sliding_attack_map |= move_board
    def is_not_pinned(self, from_sq: int, to_sq: int) -> bool:
        """
        Returns True if moving the piece from `from_sq` to `to_sq` does NOT expose
        the king to check (i.e., the piece is not pinned or the move is along the pin ray).
        """
        return not self.is_pinned(from_sq)

    def generate_enemy_attack_map(self, color: str) -> int:
        attack_map = 0
        all_pieces = self.board_state.all_pieces

        # Map color to piece indices
        enemy_base = 0 if color == "white" else 6

        # Pawns
        pawns_bb = self.board_state.pieces_bitboard[Piece.Pawn + enemy_base -1]
        # self.print_bitboard(pawns_bb , "Pawn bitboard")
        # push_dir = +1 for white, -1 for black
        push_dir = 1 if color == "white" else -1
        # File masks
        mask_A = BitBoardUtility.NOT_A_FILE
        mask_H = BitBoardUtility.NOT_H_FILE

        # Capture diagonals
        capture_a = BitBoardUtility.shift(pawns_bb & mask_H, push_dir * 9)  # NE / SE
        capture_b = BitBoardUtility.shift(pawns_bb & mask_A, push_dir * 7)  # NW / SW

        attack_map |= capture_a
        attack_map |= capture_b
        # self.print_bitboard(attack_map, "attack_map after Pawn bitboard")
        # Knights
        knights_bb = self.board_state.pieces_bitboard[Piece.Knight + enemy_base -1]
        while knights_bb:
            sq, knights_bb = BitBoardUtility.pop_lsb(knights_bb)
            attack_map |= BitBoardUtility.KNIGHT_ATTACKS[sq]
        # self.print_bitboard(attack_map, "attack_map after Knights bitboard")

        # King (for king adjacency check)
        king_bb = self.board_state.pieces_bitboard[Piece.King + enemy_base - 1]
        while king_bb:
            sq, king_bb = BitBoardUtility.pop_lsb(king_bb)
            attack_map |= BitBoardUtility.KING_ATTACKS[sq]

        # Bishops + queens
        for piece_type in [Piece.Bishop, Piece.Queen]:
            bb = self.board_state.pieces_bitboard[piece_type + enemy_base - 1]
            while bb:
                sq, bb = BitBoardUtility.pop_lsb(bb)
                attack_map |= BitBoardUtility.get_bishop_attacks(sq, all_pieces)

        # Rooks + queens
        for piece_type in [Piece.Rook, Piece.Queen]:
            bb = self.board_state.pieces_bitboard[piece_type + enemy_base -1]
            while bb:
                sq, bb = BitBoardUtility.pop_lsb(bb)
                attack_map |= BitBoardUtility.get_rook_attacks(sq, all_pieces)

        return attack_map & 0xFFFFFFFFFFFFFFFF  # ensure 64-bit

    def compute_pin_rays(self):
        """
        Computes:
          • self.pin_rays  → bitboard of all pin rays
          • self.pin_mask[sq] → squares the pinned piece is allowed to move to
        """

        self.pin_rays = 0
        self.pin_mask = {}

        # 1. King square
        king_type = Piece.King + self.friendly_color - 1
        king_sq = BitBoardUtility.bit_scan_forward(
            self.board_state.pieces_bitboard[king_type]
        )
        occupancy = self.board_state.all_pieces

        # 2. Enemy slider lists
        rook_type = Piece.Rook + self.enemy_color - 1
        bishop_type = Piece.Bishop + self.enemy_color - 1
        queen_type = Piece.Queen + self.enemy_color - 1

        enemy_rooks = self.board_state.pieces_bitboard[rook_type] | self.board_state.pieces_bitboard[queen_type]
        enemy_bishops = self.board_state.pieces_bitboard[bishop_type] | self.board_state.pieces_bitboard[queen_type]

        # ---------------------------------------------------
        # Helper: process a potential pin
        # ---------------------------------------------------
        def check_slider(slider_sq, direction):

            # Must be aligned in the correct direction
            if not BitBoardUtility.is_aligned(king_sq, slider_sq, direction):
                return

            # Get between mask
            between = BitBoardUtility.BETWEEN_MASKS[king_sq][slider_sq]

            # Count friendly blockers
            blockers = between & self.friendly_pieces
            if BitBoardUtility.count_bits(blockers) != 1:
                return

            # Extract pinned square
            pinned_sq = BitBoardUtility.bit_scan_forward(blockers)

            # Movement mask is:
            #   all squares between king and slider + the slider square
            allowed_mask = between | (1 << slider_sq)

            # Store restricted move mask for this pinned piece
            self.pin_mask[pinned_sq] = allowed_mask

            # Add whole ray to global pin_rays
            self.pin_rays |= allowed_mask | (1 << pinned_sq) | (1 << king_sq)

        # ---------------------------------------------------
        # 3. Rook/Queen pins (straight lines)
        # ---------------------------------------------------
        sliders = enemy_rooks
        while sliders:
            sq, sliders = BitBoardUtility.pop_lsb(sliders)
            check_slider(sq, "rook")

        # ---------------------------------------------------
        # 4. Bishop/Queen pins (diagonals)
        # ---------------------------------------------------
        sliders = enemy_bishops
        while sliders:
            sq, sliders = BitBoardUtility.pop_lsb(sliders)
            check_slider(sq, "bishop")

    def piece_on(self, sq: int) -> int | None:
        for piece_type, bb in enumerate(self.board_state.pieces_bitboard):
            if (bb >> sq) & 1:
                return piece_type
        return None

    def register_pin(self, slider_sq: int, between_mask: int, king_sq: int):
        """
        Adds pin rays along the line king -> pinned piece -> slider.
        """
        # The only blocker is the pinned piece
        pinned_sq = BitBoardUtility.bit_scan_forward(between_mask & self.friendly_pieces)

        piece_type = self.piece_on(pinned_sq)
        if piece_type is None:
            return  # should not happen

        # Determine pin direction based on slider type
        if (1 << slider_sq) & self.enemy_rooks_or_queens:
            direction = "rook"
        else:
            direction = "bishop"

        # Compute the full ray between king and slider
        ray = BitBoardUtility.BETWEEN_MASKS[king_sq][slider_sq] | (1 << king_sq) | (1 << slider_sq)

        self.pin_rays |= ray

        # Store move mask for the specific pinned piece
        self.pinned_move_masks[pinned_sq] = ray

    def exposes_king_ep(self, from_sq: int, ep_sq: int) -> bool:
        """
        Returns True if performing en-passant capture from `from_sq` to `ep_sq`
        exposes the king to check. This requires temporarily removing the captured pawn
        from the board and checking if the king is attacked.
        """
        # Identify captured pawn square
        push_dir = 1 if self.board_state.is_whites_turn else -1
        captured_sq = ep_sq - push_dir * 8

        # Temporarily remove the pawn from the board
        captured_bit = 1 << captured_sq
        temp_enemy_pieces = self.enemy_pieces & ~captured_bit
        temp_all_pieces = (self.board_state.all_pieces & ~captured_bit)

        # Generate enemy attacks ignoring captured pawn
        turn  = "white" if self.board_state.is_whites_turn else "black"
        temp_enemy_attack_map = self.generate_enemy_attack_map(turn)
        # Check if king is attacked after en-passant
        return (temp_enemy_attack_map >> self.king_square) & 1 != 0


    def generate_all_moves(self):
        self.compute_pin_rays()
        moves = []
        moves.extend(self.generate_pawn_moves())
        moves.extend(self.generate_knights_moves())
        moves.extend(self.generate_sliding_moves(Piece.Bishop,self.board_state.is_whites_turn))
        moves.extend(self.generate_sliding_moves(Piece.Rook,self.board_state.is_whites_turn))
        moves.extend(self.generate_sliding_moves(Piece.Queen,self.board_state.is_whites_turn))
        moves.extend(self.generate_king_moves())
        # for i, move in enumerate(moves, start=1):
        #     print(f"{i:>3}.\t{move}")
        return moves

    def xy_to_index(self, x: int, y: int) -> int:
        """Convert (file=x, rank=y) to a 0–63 square index."""
        return y * 8 + x

    def print_bitboard(self,bb: int, title="Bitboard"):
        print(f"\n{title}:")
        print("  +---+---+---+---+---+---+---+---+")
        for rank in range(7, -1, -1):
            row = []
            for file in range(8):
                index = rank * 8 + file
                bit = (bb >> index) & 1
                row.append("1" if bit else ".")
            print(f"{rank + 1} | " + " ".join(row) + " |")
        print("  +---+---+---+---+---+---+---+---+")
        print("    a   b   c   d   e   f   g   h\n")



