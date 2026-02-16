from copy import deepcopy

from game.config import PRINT_FEN
from game.models.board_state import BoardState
from game.models.pieces.pieceold import *
from game.move_generation.bitboard_utilities import BitBoardUtility
from game.move_generation.move_generator import MoveGenerator


class Board:
    SIZE = 8
    PIECE_TO_INDEX = {p: i for i, p in enumerate(Piece.PieceIndices)}

    def __init__(self, fen: str):
        self.board_data: BoardState = BoardState(fen)
        self.board_data : BoardState = self.parse_fen(fen)

    def get_piece(self, pos: tuple[int, int]) -> PieceOld | None:
        return self.board_data.positions.get(pos)

    def visualize_bit_change(self,old_value: int, bit: int, total_bits: int = 64) -> None:
        RED = "\033[91m"
        GREEN = "\033[92m"
        RESET = "\033[0m"

        def format_bits(value, highlight=False):
            bits = ""
            for i in range(total_bits - 1, -1, -1):
                bit_val = (value >> i) & 1
                if i == bit:
                    # highlight this bit
                    if highlight:
                        bits += f"{GREEN}{bit_val}{RESET}"
                    else:
                        bits += f"{RED}{bit_val}{RESET}"
                else:
                    bits += str(bit_val)
            return bits

        new_value = old_value | (1 << bit)

        print("Before: ", format_bits(old_value, highlight=False))
        print("After : ", format_bits(new_value, highlight=True))
        print(f"\nChanged bit: {bit}")

    def make_move(self, move: Move, debug=False):
        """
        Make a move and store everything needed for a perfect undo.
        """

        from_pos = move.start_pos
        to_pos = move.target_pos
        moving_piece = self.get_piece(from_pos)

        if moving_piece is None:
            return None, [], None

        moves_done = []

        # Save info for undo
        castling_before = {c: r.copy() for c, r in self.board_data.castling_rights.items()}
        en_passant_before = self.board_data.en_passant_target
        turn_before = self.board_data.is_whites_turn
        halfmove_before = self.board_data.halfmove_clock
        fullmove_before = self.board_data.fullmove_number

        captured_piece = None
        move_type = "move"

        # -----------------------------
        # Handle en passant
        # -----------------------------
        if isinstance(moving_piece, Pawn) and to_pos == self.board_data.en_passant_target:
            direction = 1 if moving_piece.color == "white" else -1
            captured_square = (to_pos[0], to_pos[1] - direction)
            captured_piece = self.board_data.remove_piece(captured_square)
            move_type = "enpassant"
        else:
            captured_piece = self.board_data.remove_piece(to_pos)

        # -----------------------------
        # Handle castling
        # -----------------------------
        is_castling = False
        rook_from = None
        rook_to = None
        rook_piece = None

        if isinstance(moving_piece, King):
            dx = to_pos[0] - from_pos[0]
            if dx == 2:  # kingside
                is_castling = True
                rook_from = (7, from_pos[1])
                rook_to = (5, from_pos[1])
            elif dx == -2:  # queenside
                is_castling = True
                rook_from = (0, from_pos[1])
                rook_to = (3, from_pos[1])

        if is_castling:
            rook_piece = self.board_data.remove_piece(rook_from)
            self.board_data.place_piece(rook_piece, rook_to)

        # -----------------------------
        # Move main piece
        # -----------------------------
        self.board_data.remove_piece(from_pos)

        if move.promotion:
            promoted_piece = move.promotion(moving_piece.color, to_pos)
            self.board_data.place_piece(promoted_piece, to_pos)
            move_type = "promotion"
        else:
            self.board_data.place_piece(moving_piece, to_pos)

        # -----------------------------
        # Record move in a single consistent entry
        # -----------------------------
        moves_done.append({
            "type": move_type if not is_castling else "castle",
            "piece": moving_piece,
            "from": from_pos,
            "to": to_pos,
            "captured": captured_piece,
            "promotion": promoted_piece if move.promotion else None,
            "is_castling": is_castling,
            "rook": rook_piece,
            "rook_from": rook_from,
            "rook_to": rook_to,
            "castling_before": castling_before,
            "en_passant_before": en_passant_before,
            "turn_before": turn_before,
            "halfmove_before": halfmove_before,
            "fullmove_before": fullmove_before,
        })

        # -----------------------------
        # Update castling rights
        # -----------------------------
        if isinstance(moving_piece, King):
            self.board_data.castling_rights[moving_piece.color]["K"] = False
            self.board_data.castling_rights[moving_piece.color]["Q"] = False
        if isinstance(moving_piece, Rook):
            if moving_piece.color == "white":
                if from_pos == (0, 0): self.board_data.castling_rights["white"]["Q"] = False
                if from_pos == (7, 0): self.board_data.castling_rights["white"]["K"] = False
            else:
                if from_pos == (0, 7): self.board_data.castling_rights["black"]["Q"] = False
                if from_pos == (7, 7): self.board_data.castling_rights["black"]["K"] = False

        # -----------------------------
        # Update en passant
        # -----------------------------
        if move.en_passant:
            mid_rank = (to_pos[1] + from_pos[1]) // 2
            self.board_data.en_passant_target = (from_pos[0], mid_rank)
        else:
            self.board_data.en_passant_target = None

        # -----------------------------
        # Halfmove / Fullmove
        # -----------------------------
        if isinstance(moving_piece, Pawn) or captured_piece:
            self.board_data.halfmove_clock = 0
        else:
            self.board_data.halfmove_clock += 1

        if not self.board_data.is_whites_turn:
            self.board_data.fullmove_number += 1

        self.board_data.update_slider_bitboards()

        # -----------------------------
        # Toggle turn
        # -----------------------------
        self.board_data.is_whites_turn = not self.board_data.is_whites_turn
        self.board_data.fen = self.to_fen()

        status = "promotion" if move.promotion else None
        if PRINT_FEN:
            print(self.board_data.fen)

        return captured_piece, moves_done, status

    def undo_move(self, moves_done):
        """
        Undo the LAST performed move.
        Works for:
        - normal moves
        - captures
        - en passant
        - promotions
        - castling
        - restores en passant, castling rights, turn, halfmove and fullmove numbers
        """

        if not moves_done:
            return

        move_info = moves_done[-1]

        # Restore general info
        self.board_data.is_whites_turn = move_info["turn_before"]
        self.board_data.castling_rights = {c: r.copy() for c, r in move_info["castling_before"].items()}
        self.board_data.en_passant_target = move_info["en_passant_before"]
        self.board_data.halfmove_clock = move_info["halfmove_before"]
        self.board_data.fullmove_number = move_info["fullmove_before"]

        move_type = move_info["type"]
        piece = move_info["piece"]
        from_pos = move_info["from"]
        to_pos = move_info["to"]
        captured_piece = move_info["captured"]

        # -----------------------------
        # Undo promotion
        # -----------------------------
        if move_type == "promotion":
            self.board_data.remove_piece(to_pos)
            self.board_data.place_piece(piece, from_pos)
            if captured_piece:
                self.board_data.place_piece(captured_piece, to_pos)
            self.board_data.fen = self.to_fen()
            return

        # -----------------------------
        # Undo castling
        # -----------------------------
        if move_info.get("is_castling"):
            # Move rook back
            rook = move_info["rook"]
            rook_from = move_info["rook_from"]
            rook_to = move_info["rook_to"]
            if rook:
                self.board_data.remove_piece(rook_to)
                self.board_data.place_piece(rook, rook_from)

            # Move king back
            self.board_data.remove_piece(to_pos)
            self.board_data.place_piece(piece, from_pos)
            self.board_data.fen = self.to_fen()
            return

        # -----------------------------
        # Undo en passant
        # -----------------------------
        if move_type == "enpassant":
            direction = 1 if piece.color == "white" else -1
            self.board_data.remove_piece(to_pos)
            self.board_data.place_piece(piece, from_pos)
            cap_square = (to_pos[0], to_pos[1] - direction)
            if captured_piece:
                self.board_data.place_piece(captured_piece, cap_square)
            self.board_data.fen = self.to_fen()
            return

        # -----------------------------
        # Undo normal move / capture
        # -----------------------------
        self.board_data.remove_piece(to_pos)
        self.board_data.place_piece(piece, from_pos)
        if captured_piece:
            self.board_data.place_piece(captured_piece, to_pos)
        self.board_data.fen = self.to_fen()

    def is_empty(self, pos: tuple[int, int]) -> bool:

        return pos not in self.board_data.positions

    def is_enemy(self, pos: tuple[int, int], color: str) -> bool:
        piece = self.get_piece(pos)
        return piece is not None and piece.color != color

    def king_square(self, is_white: bool) -> int:
        """
        Returns the square index (0..63) of the king of the given color.
        """
        king_type = Piece.King + (0 if is_white else 6) -1  # white=0..5, black=6..11
        king_bb = self.board_data.pieces_bitboard[king_type]
        if king_bb == 0:
            return -1
        # Get index of LSB (only king exists, so LSB == MSB)
        index, _ = BitBoardUtility.pop_lsb(king_bb)
        return index
    @staticmethod
    def in_bounds(pos):
        x, y = pos
        return 0 <= x < 8 and 0 <= y < 8

    def copy(self) -> "Board":
        new_state = Board(self.board_data.fen)  # or create an empty BoardState
        return new_state

    def parse_fen(self, fen: str) -> BoardState:
        """
        Parses a FEN string and returns a fully initialized BoardState object.
        Board no longer stores piece info directly; only BoardState does.
        """

        parts = fen.split()
        if len(parts) < 6:
            raise ValueError("FEN must have 6 parts: pieces, turn, castling, en passant, halfmove, fullmove")

        board_fen, turn_fen, castling_fen, en_passant_fen, halfmove_fen, fullmove_fen = parts

        state = BoardState(fen)
        state.positions.clear()

        # -----------------------------
        # 1) PIECE PLACEMENT
        # -----------------------------
        row = self.SIZE - 1
        col = 0

        piece_map = {
            "p": Pawn,
            "r": Rook,
            "n": Knight,
            "b": Bishop,
            "q": Queen,
            "k": King,
        }

        for char in board_fen:
            if char == "/":
                row -= 1
                col = 0
                continue
            if char.isdigit():
                col += int(char)
                continue
            color = "white" if char.isupper() else "black"
            piece_class = piece_map[char.lower()]
            piece = piece_class(color, (col, row))
            state.place_piece(piece, (col, row), debug=False)
            col += 1

        # -----------------------------
        # 2) TURN
        # -----------------------------
        state.is_whites_turn = (turn_fen.lower() == "w")

        # -----------------------------
        # 3) CASTLING RIGHTS
        # -----------------------------
        state.castling_rights = {
            "white": {"K": False, "Q": False},
            "black": {"K": False, "Q": False},
        }
        if "K" in castling_fen: state.castling_rights["white"]["K"] = True
        if "Q" in castling_fen: state.castling_rights["white"]["Q"] = True
        if "k" in castling_fen: state.castling_rights["black"]["K"] = True
        if "q" in castling_fen: state.castling_rights["black"]["Q"] = True

        # -----------------------------
        # 4) EN PASSANT TARGET
        # -----------------------------
        if en_passant_fen == "-":
            state.en_passant_target = None
        else:
            file_char, rank_char = en_passant_fen
            x = ord(file_char) - ord("a")
            y = int(rank_char) - 1
            state.en_passant_target = (x, y)

        # -----------------------------
        # 5) Halfmove and Fullmove
        # -----------------------------
        state.halfmove_clock = int(halfmove_fen)
        state.fullmove_number = int(fullmove_fen)

        # -----------------------------
        # 6) Rebuild bitboards
        # -----------------------------
        state.rebuild_bitboards()

        return state

    def to_fen(self) -> str:
        """Converts current board state back into full FEN (6 fields)."""

        # 1) Piece placement
        rows = []
        for rank in range(self.SIZE - 1, -1, -1):
            row_fen = ""
            empty = 0
            for file in range(self.SIZE):
                pos = (file, rank)
                if pos in self.board_data.positions:
                    if empty > 0:
                        row_fen += str(empty)
                        empty = 0
                    piece = self.board_data.positions[pos]
                    row_fen += piece.SYMBOL.upper() if piece.color == "white" else piece.SYMBOL.lower()
                else:
                    empty += 1
            if empty > 0:
                row_fen += str(empty)
            rows.append(row_fen)
        board_fen = "/".join(rows)

        # 2) Turn
        turn_fen = "w" if self.board_data.is_whites_turn else "b"

        # 3) Castling rights
        cr = ""
        if self.board_data.castling_rights["white"]["K"]: cr += "K"
        if self.board_data.castling_rights["white"]["Q"]: cr += "Q"
        if self.board_data.castling_rights["black"]["K"]: cr += "k"
        if self.board_data.castling_rights["black"]["Q"]: cr += "q"
        castling_fen = cr if cr else "-"

        # 4) En passant
        if self.board_data.en_passant_target is None:
            ep_fen = "-"
        else:
            x, y = self.board_data.en_passant_target
            ep_fen = f"{chr(ord('a') + x)}{y + 1}"

        # 5) Halfmove clock
        halfmove_fen = str(self.board_data.halfmove_clock)

        # 6) Fullmove number
        fullmove_fen = str(self.board_data.fullmove_number)

        # Return full 6-field FEN
        return f"{board_fen} {turn_fen} {castling_fen} {ep_fen} {halfmove_fen} {fullmove_fen}"

    def is_square_attacked(self, target_sq: tuple[int, int], attacker_color: str) -> bool:
        """
        Returns True if `attacker_color` attacks the square `target_sq`.
        More efficient than checking every piece manually.
        """

        # Use a MoveGenerator for the attacker color
        mg = MoveGenerator(self)

        enemy_attack_map = mg.generate_enemy_attack_map(color=attacker_color)

        # Convert (x, y) to bitboard index (0-63)
        sq_index = target_sq[1] * 8 + target_sq[0]

        # Check if target square is attacked
        return (enemy_attack_map >> sq_index) & 1 != 0

    def find_king(self, color: str) -> tuple[int, int] | None:
        """Return (x,y) of the king of given color, or None if not found."""
        for pos, piece in self.board_data.positions.items():
            if isinstance(piece, King) and piece.color == color:
                return pos
        return None

    def is_in_check(self, color: str) -> bool:
        king_pos = self.find_king(color)
        if king_pos is None:
            return False  # should not happen normally
        enemy_color = "black" if color == "white" else "white"
        return self.is_square_attacked(king_pos, enemy_color)

    def get_legal_moves(self, pseudo_legal_moves: list[Move]):
        """
        Filters pseudo-legal moves into truly legal moves.
        Uses make_move and undo_move to test king safety.
        Works for both white and black.
        """
        legal_moves =pseudo_legal_moves
        # legal_moves = []
        # for move in pseudo_legal_moves:
        #     side_just_moved = self.board_data.is_whites_turn
        #     # 1. Make the move on the actual board state
        #     captured_piece, moves_done, status = self.make_move(move)
        #
        #     # 3. Get the king square for the side that just moved
        #     king_sq = self.king_square(side_just_moved)
        #
        #     # 4. Generate enemy attack map for the opponent of the side that just moved
        #     mg = MoveGenerator(self)
        #     turn  = "white" if  self.board_data.is_whites_turn else "black"
        #     enemy_attack_map = mg.generate_enemy_attack_map(color=turn)
        #
        #     # 5. Only keep moves where our king is not in check
        #     if king_sq != -1 and not ((enemy_attack_map >> king_sq) & 1):
        #         legal_moves.append(move)
        #
        #     # 6. Undo the move immediately
        #     self.undo_move(moves_done)

        return legal_moves

    def generate_all_legal_moves(self) -> list[Move]:
        """
        Generate all legal moves for a color using bitboard-based MoveGenerator.
        """
        mg = MoveGenerator(self)
        all_moves = mg.generate_all_moves()


        # Finally filter for king safety
        legal_moves: list[Move] = self.get_legal_moves(all_moves)

        return legal_moves

    def is_checkmate(self, color: str) -> bool:
        if not self.is_in_check(color):
            return False
        return len(self.generate_all_legal_moves()) == 0

    def is_stalemate(self, color: str) -> bool:
        if self.is_in_check(color):
            return False
        return len(self.generate_all_legal_moves()) == 0

    def sq_index(self, pos):
        return pos[1] * 8 + pos[0]

    def bb_set(self, bb, sq):
        return bb | (1 << sq)

    def bb_clear(self, bb, sq):
        return bb & ~(1 << sq)

    def bb_move(self, bb, from_sq, to_sq):
        bb = self.bb_clear(bb, from_sq)
        return self.bb_set(bb, to_sq)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        return self.board_data == other.board_data

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        """
        Display board rotated:
        - Rows labeled a–h
        - Columns labeled 1–8 at bottom
        - Pieces oriented as in the example
        - Extra info: turn, castling, en-passant, FEN
        """

        size = self.SIZE
        board_lines = []

        # Row labels a–h (top to bottom)
        row_labels = ["a", "b", "c", "d", "e", "f", "g", "h"]

        # Empty grid
        grid = [["." for _ in range(size)] for _ in range(size)]

        # Fill grid
        for (r, c), piece in self.board_data.positions.items():
            symbol = piece.SYMBOL  # uppercase = white, lowercase = black
            grid[r][c] = symbol

        # ROTATE THE BOARD: rows = a–h, columns = 1–8
        for i, row_label in enumerate(row_labels):
            line = row_label + "  " + " ".join(grid[i])
            board_lines.append(line)

        # Column numbers at bottom
        board_lines.append("   " + " ".join(str(i) for i in range(1, size + 1)))

        # Extra info
        turn = "White" if self.board_data.is_whites_turn else "Black"

        castling = []
        if self.board_data.castling_rights["white"]["K"]: castling.append("K")
        if self.board_data.castling_rights["white"]["Q"]: castling.append("Q")
        if self.board_data.castling_rights["black"]["K"]: castling.append("k")
        if self.board_data.castling_rights["black"]["Q"]: castling.append("q")
        castling_str = "".join(castling) if castling else "-"

        ep = self.board_data.en_passant_target if self.board_data.en_passant_target else "-"

        board_lines.append(f"Turn: {turn}")
        board_lines.append(f"Castling: {castling_str}")
        board_lines.append(f"En Passant: {ep}")
        board_lines.append(f"FEN: {self.board_data.fen}")

        return "\n".join(board_lines)






