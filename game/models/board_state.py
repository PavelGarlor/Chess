from game.models.pieces.piece import *



class BoardState:
    SIZE = 8

    def __init__(self, fen: str):
        self.current_turn = "white"
        self.fen = fen
        self.positions: dict[tuple[int, int], Piece] = {}
        self._parse_fen()
        self.en_passant_target = None

    def get_piece(self, pos: tuple[int, int]) -> Piece | None:
        return self.positions.get(pos)

    def place_piece(self, piece: Piece, pos: tuple[int, int]) -> None:
        piece.position = pos
        self.positions[pos] = piece

    def move_piece(self, from_pos: tuple[int, int], to_pos: tuple[int, int]) -> Piece | None:
        piece = self.positions.get(from_pos)
        if piece is None:
            return None

        # -----------------------------------
        # EN PASSANT CAPTURE HANDLING
        # -----------------------------------
        if isinstance(piece, Pawn) and self.en_passant_target == to_pos:
            # The captured pawn is behind the en passant square
            direction = 1 if piece.color == "white" else -1
            captured_square = (to_pos[0], to_pos[1] - direction)
            captured_piece = self.positions.pop(captured_square, None)
        else:
            captured_piece = self.positions.pop(to_pos, None)

        # -----------------------------------
        # MOVE THE PIECE
        # -----------------------------------
        self.positions.pop(from_pos, None)
        piece.position = to_pos
        self.positions[to_pos] = piece

        # -----------------------------------
        # SET NEW EN PASSANT TARGET
        # -----------------------------------
        if isinstance(piece, Pawn) and abs(to_pos[1] - from_pos[1]) == 2:
            mid_rank = (to_pos[1] + from_pos[1]) // 2
            self.en_passant_target = (from_pos[0], mid_rank)
        else:
            self.en_passant_target = None

        return captured_piece

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
