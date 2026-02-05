from copy import deepcopy

from game.models.pieces import piece
from game.models.pieces.piece import *



class BoardState:
    SIZE = 8

    def __init__(self, fen: str):
        self.current_turn = "white"
        self.fen = fen
        self.positions: dict[tuple[int, int], Piece] = {}
        self.castling_rights = {
            "white": {"K": True, "Q": True},
            "black": {"K": True, "Q": True},
        }
        self._parse_fen()
        self.en_passant_target = None


    def get_piece(self, pos: tuple[int, int]) -> Piece | None:
        return self.positions.get(pos)

    def set_piece(self, piece: Piece, pos: tuple[int, int]) -> None:
        piece.position = pos
        self.positions[pos] = piece

    def make_move(self, move: Move) -> tuple[Piece | None, list[dict], str | None]:
        """
        Move a piece from `from_pos` to `to_pos`, handling:
        - Normal moves

        - Captures
        - En passant
        - Castling
        - Castling rights

        Returns:
            captured_piece: The main captured piece (or None)
            moves_done: List of dicts for all moves performed:
                {"piece": Piece, "from": (x, y), "to": (x, y), "captured": Optional[Piece]}
        """
        moves_done = []
        from_pos = move.piece.position
        to_pos = move.target_pos
        moving_piece = self.positions.get(from_pos)
        is_promotion = move.promotion is not None
        if moving_piece is None:
            return None, moves_done, None

        captured_piece = None

        # -----------------------------------
        # TRACK CASTLING RIGHTS
        # -----------------------------------
        if isinstance(moving_piece, King):
            self.castling_rights[moving_piece.color]["K"] = False
            self.castling_rights[moving_piece.color]["Q"] = False

        if isinstance(moving_piece, Rook):
            if moving_piece.color == "white":
                if from_pos == (0, 0):
                    self.castling_rights["white"]["Q"] = False
                elif from_pos == (7, 0):
                    self.castling_rights["white"]["K"] = False
            else:
                if from_pos == (0, 7):
                    self.castling_rights["black"]["Q"] = False
                elif from_pos == (7, 7):
                    self.castling_rights["black"]["K"] = False

        # -----------------------------------
        # DETECT CASTLING BEFORE MOVING KING
        # -----------------------------------
        is_castling = False
        rook_from = None
        rook_to = None
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

        # -----------------------------------
        # HANDLE CAPTURES
        # -----------------------------------
        if isinstance(moving_piece, Pawn) and to_pos == self.en_passant_target:
            # En passant capture
            direction = 1 if moving_piece.color == "white" else -1
            captured_square = (to_pos[0], to_pos[1] - direction)
            captured_piece = self.positions.pop(captured_square, None)
            if captured_piece:
                moves_done.append(
                    {"piece": captured_piece, "from": captured_square, "to": captured_square, "captured": None, "promotes": None})
        else:
            captured_piece = self.positions.pop(to_pos, None)

        # -----------------------------------
        # CASTLING: MOVE ROOK
        # -----------------------------------
        if is_castling:
            rook_piece = self.positions.pop(rook_from, None)
            if rook_piece:
                rook_piece.position = rook_to
                self.positions[rook_to] = rook_piece
                moves_done.append({"piece": rook_piece, "from": rook_from, "to": rook_to, "captured": None, "promotes": None})

        # -----------------------------------
        # MOVE THE PIECE
        # -----------------------------------
        self.positions.pop(from_pos, None)
        moving_piece.position = to_pos
        if move.promotion:
            move.promotion.position = to_pos
        self.positions[to_pos] = move.promotion if move.promotion else moving_piece
        moves_done.append({"piece": moving_piece, "from": from_pos, "to": to_pos, "captured": captured_piece , "promotes": move.promotion})

        # -----------------------------------
        # SET EN PASSANT TARGET
        # -----------------------------------
        if isinstance(moving_piece, Pawn) and abs(to_pos[1] - from_pos[1]) == 2:
            mid_rank = (to_pos[1] + from_pos[1]) // 2
            self.en_passant_target = (from_pos[0], mid_rank)
        else:
            self.en_passant_target = None

        # --- PAWN PROMOTION DETECTION ---
        if isinstance(moving_piece, Pawn):
            last_rank = 7 if moving_piece.color == "white" else 0
            if to_pos[1] == last_rank:
                return captured_piece, moves_done, "promotion"

        return captured_piece, moves_done, None

    def is_empty(self, pos: tuple[int, int]) -> bool:
        return pos not in self.positions

    def is_enemy(self, pos: tuple[int, int], color: str) -> bool:
        piece = self.get_piece(pos)
        return piece is not None and piece.color != color

    @staticmethod
    def in_bounds(pos):
        x, y = pos
        return 0 <= x < 8 and 0 <= y < 8

    def copy(self) -> "BoardState":
        new_state = BoardState(self.fen)  # or create an empty BoardState
        # Deep copy pieces
        new_state.positions = {}
        for pos, piece in self.positions.items():
            # Create a new piece of the same type and color
            piece_class = type(piece)
            new_piece = piece_class(piece.color)
            new_piece.position = piece.position
            new_state.positions[pos] = new_piece

        # Copy other attributes
        new_state.current_turn = self.current_turn
        new_state.castling_rights = deepcopy(self.castling_rights)
        new_state.en_passant_target = self.en_passant_target

        return new_state

    def _parse_fen(self) -> None:
        """
        Parses FEN string into:
        - board pieces (self.positions)
        - current turn (self.current_turn)
        - castling rights (self.castling_rights)
        - en passant target (self.en_passant_target)
        """
        parts = self.fen.split()
        if len(parts) < 4:
            raise ValueError("FEN must have at least 4 parts")

        board_fen, turn_fen, castling_fen, en_passant_fen = parts[:4]

        # --- 1) Pieces ---
        self.positions.clear()
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
            self.set_piece(piece_class(color), (col, row))
            col += 1

        # --- 2) Current turn ---
        self.current_turn = "white" if turn_fen.lower() == "w" else "black"

        # --- 3) Castling rights ---
        self.castling_rights = {
            "white": {"K": False, "Q": False},
            "black": {"K": False, "Q": False},
        }
        if "K" in castling_fen:
            self.castling_rights["white"]["K"] = True
        if "Q" in castling_fen:
            self.castling_rights["white"]["Q"] = True
        if "k" in castling_fen:
            self.castling_rights["black"]["K"] = True
        if "q" in castling_fen:
            self.castling_rights["black"]["Q"] = True

        # --- 4) En passant target ---
        if en_passant_fen == "-":
            self.en_passant_target = None
        else:
            # Convert algebraic (e3) to grid coordinates (x, y)
            file_char = en_passant_fen[0]
            rank_char = en_passant_fen[1]
            x = ord(file_char.lower()) - ord("a")
            y = int(rank_char) - 1
            self.en_passant_target = (x, y)

    def to_fen(self) -> str:
        """
        Converts current board state back into full FEN:
        pieces / turn / castling rights / en passant.
        """
        # -------------------------------------------------
        # 1) PIECE PLACEMENT
        # -------------------------------------------------
        rows = []

        for rank in range(self.SIZE - 1, -1, -1):  # 7 → 0
            row_fen = ""
            empty = 0

            for file in range(self.SIZE):
                pos = (file, rank)

                if pos in self.positions:
                    # flush accumulated empties
                    if empty > 0:
                        row_fen += str(empty)
                        empty = 0

                    piece = self.positions[pos]
                    symbol = piece.SYMBOL

                    # apply capitalization
                    row_fen += symbol.upper() if piece.color == "white" else symbol.lower()
                else:
                    empty += 1

            # flush trailing empties
            if empty > 0:
                row_fen += str(empty)

            rows.append(row_fen)

        board_fen = "/".join(rows)

        # -------------------------------------------------
        # 2) TURN
        # -------------------------------------------------
        turn_fen = "w" if self.current_turn == "white" else "b"

        # -------------------------------------------------
        # 3) CASTLING RIGHTS
        # -------------------------------------------------
        cr = ""

        if self.castling_rights["white"]["K"]:
            cr += "K"
        if self.castling_rights["white"]["Q"]:
            cr += "Q"
        if self.castling_rights["black"]["K"]:
            cr += "k"
        if self.castling_rights["black"]["Q"]:
            cr += "q"

        castling_fen = cr if cr else "-"

        # -------------------------------------------------
        # 4) EN PASSANT TARGET
        # -------------------------------------------------
        if self.en_passant_target is None:
            ep_fen = "-"
        else:
            x, y = self.en_passant_target
            ep_fen = f"{chr(ord('a') + x)}{y + 1}"

        # -------------------------------------------------
        # RETURN FULL FEN
        # -------------------------------------------------
        return f"{board_fen} {turn_fen} {castling_fen} {ep_fen}"

    def is_square_attacked(self, target_sq: tuple[int, int], attacker_color: str) -> bool:
        """
        Returns True if `attacker_color` attacks the square `target_sq`.
        Used for king safety and castling legality.
        """

        for pos, piece in self.positions.items():
            if piece.color != attacker_color:
                continue

            moves = piece.get_allowed_moves(pos, self,True)  # pseudo-legal moves

            for mv in moves:
                if mv.target_pos == target_sq:
                    return True

        return False

    def find_king(self, color: str) -> tuple[int, int] | None:
        """Return (x,y) of the king of given color, or None if not found."""
        for pos, piece in self.positions.items():
            if isinstance(piece, King) and piece.color == color:
                return pos
        return None

    def is_in_check(self, color: str) -> bool:
        king_pos = self.find_king(color)
        if king_pos is None:
            return False  # should not happen normally
        enemy_color = "black" if color == "white" else "white"
        return self.is_square_attacked(king_pos, enemy_color)

    def get_legal_moves(self, pseudo_legal_moves: List[Move], state):
        legal_moves: List[Move] = []
        enemy = "black" if state.current_turn == "white" else "white"

        for move in pseudo_legal_moves:
            piece = move.piece
            from_pos = piece.position
            to_pos = move.target_pos

            # ------------------------------------------------------------
            # HANDLE CASTLING LEGALITY
            # ------------------------------------------------------------
            if isinstance(piece, King) and abs(to_pos[0] - from_pos[0]) == 2:
                color = piece.color
                row = 0 if color == "white" else 7

                # 1. King must NOT be in check
                if state.is_square_attacked(from_pos, enemy):
                    continue

                # 2. Which side?
                if to_pos[0] == 6:  # kingside
                    rook_from = (7, row)
                    path = [(5, row), (6, row)]
                    between = [(5, row)]
                    rights_flag = "K"
                else:  # queenside
                    rook_from = (0, row)
                    path = [(3, row), (2, row)]
                    between = [(3, row), (2, row), (1, row)]
                    rights_flag = "Q"

                # 3. Rook must exist and be unmoved
                rook_piece = state.positions.get(rook_from)
                if not isinstance(rook_piece, Rook) or rook_piece.color != color:
                    continue

                # 4. Castling rights must allow it
                if not state.castling_rights[color][rights_flag]:
                    continue

                # 5. Squares between king and rook must be empty
                if any(s in state.positions for s in between):
                    continue

                # 6. King must not pass through check
                illegal = False
                for sq in path:
                    if state.is_square_attacked(sq, enemy):
                        illegal = True
                        break
                if illegal:
                    continue

                # → Castling is legal!
                legal_moves.append(move)
                continue

            # ------------------------------------------------------------
            # NORMAL MOVE + En Passant + Captures (simulate)
            # ------------------------------------------------------------
            temp_state = state.copy()
            temp_state.make_move(move)

            # After simulation — king may not be in check
            king_pos = temp_state.find_king(piece.color)
            if king_pos is None:
                continue

            if temp_state.is_square_attacked(king_pos, enemy):
                continue  # illegal — king ends in check

            # If we get here → legal
            legal_moves.append(move)

        return legal_moves



    def all_legal_moves(self, color: str) -> list[Move]:
        moves = []
        for pos, piece in self.positions.items():
            if piece.color != color:
                continue
            pseudo_moves = piece.get_allowed_moves(pos, self)
            legal_moves = self.get_legal_moves(pseudo_moves, self)
            moves.extend(legal_moves)
        return moves

    def is_checkmate(self, color: str) -> bool:
        if not self.is_in_check(color):
            return False
        return len(self.all_legal_moves(color)) == 0

    def is_stalemate(self, color: str) -> bool:
        if self.is_in_check(color):
            return False
        return len(self.all_legal_moves(color)) == 0

    def undo_move(self, moves_done: list[dict], captured_piece):
        """
        Undo a list of moves performed by make_move.
        moves_done: list of dicts with keys "piece", "from", "to", "captured"
        captured_piece: the piece that was captured in the main move (if any)
        """
        # Reverse the moves in reverse order
        for move in reversed(moves_done):
            piece = move["piece"]
            from_pos = move["from"]
            to_pos = move["to"]
            captured = move["captured"]

            # Move the piece back
            self.positions[from_pos] = piece
            piece.position = from_pos

            # Remove from destination
            if to_pos in self.positions:
                del self.positions[to_pos]

            # Restore captured piece
            if captured:
                self.positions[to_pos] = captured
                captured.position = to_pos

        # If your board state tracks other things like en passant or castling rights,
        # you should also restore them here if make_move changed them.

