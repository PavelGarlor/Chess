from game.models.pieces.piece import *



class BoardState:
    SIZE = 8

    def __init__(self, fen: str):
        self.current_turn = "white"
        self.fen = fen
        self.positions: dict[tuple[int, int], Piece] = {}
        self._parse_fen()

    def get_piece(self, pos: tuple[int, int]) -> Piece | None:
        return self.positions.get(pos)

    def place_piece(self, piece: Piece, pos: tuple[int, int]) -> None:
        piece.position = pos
        self.positions[pos] = piece

    def move_piece(
        self,
        from_pos: tuple[int, int],
        to_pos: tuple[int, int],
    ) -> Piece | None:
        piece = self.positions.pop(from_pos, None)
        if piece is None:
            return None

        captured = self.positions.pop(to_pos, None)
        piece.position = to_pos
        self.positions[to_pos] = piece

        return captured

    def get_allowed_moves(self, position, board_state):
        x, y = position
        moves = []
        direction = 1 if self.color == "white" else -1
        target = (x, y + direction)
        if 0 <= target[1] < board_state.SIZE and not board_state.get_piece(target):
            moves.append(target)

        #after obtaining all the moves that the piece can do we filter the legals

        return moves

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
