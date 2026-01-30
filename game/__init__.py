import sys
import time
import pygame

from game.config import *
from game.models.board_state import BoardState
from game.view.board_view import BoardView
from game.controller.chess_controller import ChessController  # new

# --------------------------------------------------
# INIT
# --------------------------------------------------
pygame.init()
pygame.font.init()
FONT_SIZE = 20
FONT_COLOR = (255, 255, 255)

FONT = pygame.font.SysFont("Arial", FONT_SIZE)  # system font
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Chess")

clock = pygame.time.Clock()
running = True

# --------------------------------------------------
# BOARD SETUP
# --------------------------------------------------
window_width = screen.get_width()
window_height = screen.get_height()

chessboard_size = min(window_width, window_height) * 0.8
square_size = chessboard_size / 8

chessboard_x = (window_width - chessboard_size) / 2
chessboard_y = (window_height - chessboard_size) / 2

# Create game state (truth)
board_state = BoardState(
    # fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    # fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    # fen="rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2 "
    fen=" 8/8/8/4p1K1/2k1P3/8/8/8 b - - 0 1"
)

# Create visual board (mirror)
board_view = BoardView(
    board_state=board_state,
    board_x=chessboard_x,
    board_y=chessboard_y,
    square_size=square_size,
)

# Create controller
controller = ChessController(board_state, board_view)

# --------------------------------------------------
# START SPAWN ANIMATIONS
# --------------------------------------------------
now = time.time()
for piece_view in board_view.piece_views.values():
    piece_view.start_spawn(now)

# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------
while running:
    now = time.time()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # left click
                controller.handle_mouse_click(event.pos)

    # UPDATE
    board_view.update(now)

    # DRAW
    screen.fill(BACKGROUND_COLOR)
    board_view.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
