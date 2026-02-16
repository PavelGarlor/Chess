from game.models.piece import Piece
from game.models.pieces.pieceold import PieceOld


class BoardState:
    SIZE = 8
    def __init__(
        self,
        fen: str,
        is_whites_turn: bool = True,
        positions: dict[tuple[int, int], PieceOld] | None = None,
        castling_rights: dict | None = None,
        en_passant_target: tuple[int, int] | None = None,
        pieces_bitboard: list[int] | None = None,
        color_pieces: list[int] | None = None,
        all_pieces: int | None = None,
    ):
        self.fen = fen

        # TURN
        self.is_whites_turn = is_whites_turn

        # POSITIONS
        self.positions = positions if positions is not None else {}

        # CASTLING
        self.castling_rights = castling_rights if castling_rights is not None else {
            "white": {"K": True, "Q": True},
            "black": {"K": True, "Q": True},
        }

        # BITBOARDS
        self.pieces_bitboard = pieces_bitboard if pieces_bitboard is not None else [0] * 12
        self.color_pieces = color_pieces if color_pieces is not None else [0, 0]
        self.all_pieces = all_pieces if all_pieces is not None else 0

        # EN PASSANT
        self.en_passant_target = en_passant_target

        self.halfmove_clock = 0
        self.fullmove_number = 1

        # SLIDING PIECES (to be updated)
        self.friendly_orthogonal_sliders = 0
        self.friendly_diagonal_sliders = 0
        self.enemy_orthogonal_sliders = 0
        self.enemy_diagonal_sliders = 0

    def update_slider_bitboards(self):
        """
        Compute bitboards for friendly and enemy sliding pieces:
        - Orthogonal sliders: rook + queen
        - Diagonal sliders: bishop + queen
        """

        move_color = 0 if self.is_whites_turn else 1  # 0 = white, 1 = black
        opponent_color = 1 - move_color

        # Piece indices: 0-5 white, 6-11 black

        # FRIENDLY SLIDERS
        friendly_rook = Piece.make_piece(Piece.Rook, move_color)
        friendly_queen = Piece.make_piece(Piece.Queen, move_color)
        friendly_bishop = Piece.make_piece(Piece.Bishop, move_color)

        self.friendly_orthogonal_sliders = (
                self.pieces_bitboard[friendly_rook] | self.pieces_bitboard[friendly_queen]
        )
        self.friendly_diagonal_sliders = (
                self.pieces_bitboard[friendly_bishop] | self.pieces_bitboard[friendly_queen]
        )

        # ENEMY SLIDERS
        enemy_rook = Piece.make_piece(Piece.Rook, opponent_color)
        enemy_queen = Piece.make_piece(Piece.Queen, opponent_color)
        enemy_bishop = Piece.make_piece(Piece.Bishop, opponent_color)

        self.enemy_orthogonal_sliders = (
                self.pieces_bitboard[enemy_rook] | self.pieces_bitboard[enemy_queen]
        )
        self.enemy_diagonal_sliders = (
                self.pieces_bitboard[enemy_bishop] | self.pieces_bitboard[enemy_queen]
        )

    def rebuild_bitboards(self):
        """Rebuilds all bitboards based on self.positions."""

        # Reset all
        self.pieces_bitboard = [0] * 12
        self.color_pieces = [0, 0]  # [white, black]
        self.all_pieces = 0

        # Mapping piece type → index
        type_index_map = {
            "p": 0, "n": 1, "b": 2, "r": 3, "q": 4, "k": 5
        }

        for (x, y), piece in self.positions.items():

            bit = 1 << (y * 8 + x)

            # Add +6 if black
            idx = piece.get_piece_id()

            # Add to piece bitboard
            self.pieces_bitboard[idx] |= bit

            # Add to color bitboard
            if piece.color == "white":
                self.color_pieces[0] |= bit
            else:
                self.color_pieces[1] |= bit

            # Add to occupancy
            self.all_pieces |= bit
    def place_piece(self, piece: PieceOld, pos: tuple[int, int], debug=True) -> None:
        if piece is None : return
        piece.position = pos
        self.positions[pos] = piece

        j, i = pos
        pos_number = (i * self.SIZE) + j

        # --- Update color bitboards ---
        color_id = 0 if piece.color == "white" else 1
        self.color_pieces[color_id] |= (1 << pos_number)

        self.all_pieces |= (1 << pos_number)
        bitboard_id = piece.get_piece_id()
        # if debug:
        #     print("before setting")
            # self.visualize_bit_change(
            #     self.board_data.pieces_bitboard[bitboard_id],
            #     pos_number,
            #     total_bits=self.SIZE * self.SIZE
            # )
        self.pieces_bitboard[bitboard_id] |= (1 << pos_number)
        # if debug:
        #     print("after setting")
            # self.visualize_bit_change(
            #     self.board_data.pieces_bitboard[bitboard_id],
            #     pos_number,
            #     total_bits=self.SIZE * self.SIZE
            # )

    def remove_piece(self, pos: tuple[int, int], debug=False):
        piece = self.positions.pop(pos, None)
        if piece is None:
            return None

        bitboard_id = piece.get_piece_id()

        j, i = pos
        pos_number = i * self.SIZE + j

        # update color bitboards
        color_id = 0 if piece.color == "white" else 1
        self.color_pieces[color_id] &= ~(1 << pos_number)
        self.all_pieces &= ~(1 << pos_number)

        # update piece-type bitboard
        # piece_index = self.PIECE_TO_INDEX[bitboard_id]
        self.pieces_bitboard[bitboard_id] &= ~(1 << pos_number)

        # if debug:
            # self.visualize_bit_change(
            #     self.board_data.color_pieces[color_id],
            #     pos_number,
            #     total_bits=self.SIZE * self.SIZE
            # )

        return piece
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        # Compare turn
        if self.is_whites_turn != other.is_whites_turn:
            return False

        # Compare castling rights
        if self.castling_rights != other.castling_rights:
            return False

        # Compare en passant
        if self.en_passant_target != other.en_passant_target:
            return False

        # Compare positions
        if set(self.positions.keys()) != set(other.positions.keys()):
            return False

        for pos, piece in self.positions.items():
            other_piece = other.positions[pos]
            if piece.color != other_piece.color or piece.__class__ != other_piece.__class__:
                return False

        return True
