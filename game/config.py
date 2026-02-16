# Colors
from game.models.piece import Piece

LIGHT_SQ = (192, 209, 196)
DARK_SQ = (13, 74, 27)

# ---------------------------
# Game animation settings
# ---------------------------
# Animation settings
animation_duration = 0.2
spawn_interval = 0.05
ANIMATE_BOARD = False       # Should the board squares animate in?
ANIMATE_PIECES = False# Should the pieces animate from above?

# Colors
BACKGROUND_COLOR = (9, 18, 33)
FONT_COLOR = (181, 179, 51)
# Settings
DISPLAY_FEN = False
PRINT_FEN  = False
SHOW_ATTACKED_SQUARES = True
SHOW_COLOR_BITMAP = False
SHOW_JOINED_BITMAP = False
SHOW_PIECE_BITMAPS = False
BITBOARDS_TO_SHOW = [
    Piece.WhitePawn,
    Piece.WhiteKnight,
    Piece.WhiteBishop,
    Piece.WhiteRook,
    Piece.WhiteQueen,
    Piece.WhiteKing,
    Piece.BlackPawn,
    Piece.BlackKnight,
    Piece.BlackBishop,
    Piece.BlackRook,
    Piece.BlackQueen,
    Piece.BlackKing
]

cooldown_time = 0.5           # hover before falling
dark_factor = 0.2             # darkness while hovering
x_offset = 15
y_offset = 30
size_multiplier = 1.2

ROWS, COLS = 8, 8

