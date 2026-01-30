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

    def move_piece(self, from_pos: tuple[int, int], to_pos: tuple[int, int]) -> tuple[Piece | None, list[dict]]:
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

    def _parse_fen(self) -> None:
        board_fen = self.fen.split()[0]

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
