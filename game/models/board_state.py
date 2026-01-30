from copy import deepcopy

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

    def place_piece(self, piece: Piece, pos: tuple[int, int]) -> None:
        piece.position = pos
        self.positions[pos] = piece

    def make_move(self, move : Move) -> tuple[Piece | None, list[dict]]:
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
        if moving_piece is None:
            return None, moves_done

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
                    {"piece": captured_piece, "from": captured_square, "to": captured_square, "captured": None})
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
                moves_done.append({"piece": rook_piece, "from": rook_from, "to": rook_to, "captured": None})

        # -----------------------------------
        # MOVE THE PIECE
        # -----------------------------------
        self.positions.pop(from_pos, None)
        moving_piece.position = to_pos
        self.positions[to_pos] = moving_piece
        moves_done.append({"piece": moving_piece, "from": from_pos, "to": to_pos, "captured": captured_piece})

        # -----------------------------------
        # SET EN PASSANT TARGET
        # -----------------------------------
        if isinstance(moving_piece, Pawn) and abs(to_pos[1] - from_pos[1]) == 2:
            mid_rank = (to_pos[1] + from_pos[1]) // 2
            self.en_passant_target = (from_pos[0], mid_rank)
        else:
            self.en_passant_target = None

        return captured_piece, moves_done

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
            self.place_piece(piece_class(color), (col, row))
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

