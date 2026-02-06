class Piece:
    # ---------------------------
    # Piece Types
    # ---------------------------
    NoneType = 0
    Pawn = 1
    Knight = 2
    Bishop = 3
    Rook = 4
    Queen = 5
    King = 6

    # ---------------------------
    # Piece Colours
    # ---------------------------
    White = 0
    Black = 8

    # ---------------------------
    # Combined Pieces
    # ---------------------------
    WhitePawn = Pawn | White
    WhiteKnight = Knight | White
    WhiteBishop = Bishop | White
    WhiteRook = Rook | White
    WhiteQueen = Queen | White
    WhiteKing = King | White

    BlackPawn = Pawn | Black
    BlackKnight = Knight | Black
    BlackBishop = Bishop | Black
    BlackRook = Rook | Black
    BlackQueen = Queen | Black
    BlackKing = King | Black

    MaxPieceIndex = BlackKing

    PieceIndices = [
        WhitePawn, WhiteKnight, WhiteBishop, WhiteRook, WhiteQueen, WhiteKing,
        BlackPawn, BlackKnight, BlackBishop, BlackRook, BlackQueen, BlackKing
    ]

    # ---------------------------
    # Bit Masks
    # ---------------------------
    _typeMask = 0b0111
    _colourMask = 0b1000

    # ---------------------------
    # Static methods
    # ---------------------------
    @staticmethod
    def make_piece(piece_type: int, piece_colour: int) -> int:
        return piece_type | piece_colour

    @staticmethod
    def make_piece_bool(piece_type: int, piece_is_white: bool) -> int:
        return Piece.make_piece(piece_type, Piece.White if piece_is_white else Piece.Black)

    @staticmethod
    def is_colour(piece: int, colour: int) -> bool:
        return (piece & Piece._colourMask) == colour and piece != 0

    @staticmethod
    def is_white(piece: int) -> bool:
        return Piece.is_colour(piece, Piece.White)

    @staticmethod
    def piece_colour(piece: int) -> int:
        return piece & Piece._colourMask

    @staticmethod
    def piece_type(piece: int) -> int:
        return piece & Piece._typeMask

    @staticmethod
    def is_orthogonal_slider(piece: int) -> bool:
        return Piece.piece_type(piece) in (Piece.Rook, Piece.Queen)

    @staticmethod
    def is_diagonal_slider(piece: int) -> bool:
        return Piece.piece_type(piece) in (Piece.Bishop, Piece.Queen)

    @staticmethod
    def is_sliding_piece(piece: int) -> bool:
        return Piece.piece_type(piece) in (Piece.Bishop, Piece.Rook, Piece.Queen)

    @staticmethod
    def get_symbol(piece: int) -> str:
        mapping = {
            Piece.Rook: 'R',
            Piece.Knight: 'N',
            Piece.Bishop: 'B',
            Piece.Queen: 'Q',
            Piece.King: 'K',
            Piece.Pawn: 'P'
        }
        piece_type = Piece.piece_type(piece)
        symbol = mapping.get(piece_type, ' ')
        return symbol.upper() if Piece.is_white(piece) else symbol.lower()

    @staticmethod
    def get_piece_type_from_symbol(symbol: str) -> int:
        mapping = {
            'R': Piece.Rook,
            'N': Piece.Knight,
            'B': Piece.Bishop,
            'Q': Piece.Queen,
            'K': Piece.King,
            'P': Piece.Pawn
        }
        return mapping.get(symbol.upper(), Piece.NoneType)
