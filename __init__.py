import sys
import time
import pygame

from ai_engine.versions.ai_player import PlayerAI
from game.config import *
from game.models.board_state import BoardState
from game.models.move import Move
from game.view.board_view import BoardView
from game.view.game_view import GameView
from game.controller.chess_controller import ChessController

# --------------------------------------------------
# INIT
# --------------------------------------------------
pygame.init()
pygame.font.init()

screen = pygame.display.set_mode((0, 0),  pygame.NOFRAME)
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

# Create game state
board_state = BoardState(
    # fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    # fen="2bqkbnr/r1pppppp/ppn5/7Q/2BPP3/8/PPP2PPP/RNB1K1NR w KQk -"
    # fen="2bqkbnr/rPpppppp/8/p3n2Q/2BPP3/8/1PP2PPP/RNB1K1NR b KQk -"
    # fen ="8/PPPPPPPP/8/K7/8/8/8/k7 w - - 0 1" all pawns to promote
    fen ="8/PPkPPPPP/8/8/8/8/2K5/8 b - -" #error pawns on last row capture

)

# Create board view
board_view = BoardView(
    board_state=board_state,
    board_x=chessboard_x,
    board_y=chessboard_y,
    square_size=square_size,
)

# Create GameView (HUD/UI)
game_view = GameView(screen, board_view)

# Create controller WITH game_view
controller = ChessController(board_state, board_view, game_view)
if isinstance(game_view.white_player, PlayerAI):
    controller.start_ai_move(game_view.white_player)
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
    human_move = None

    # Handle input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

        # Human move
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            human_move = controller.handle_mouse_click(event.pos)

    # --- H U M A N   M O V E ---
    if human_move is not None:
        controller.attempt_move(human_move)

    # --- A I   M O V E ---
    ai_move = controller.get_ai_move()
    if ai_move is not None:
        controller.attempt_move(ai_move)

    # Continue updating + drawing
    board_view.update(now)
    screen.fill(BACKGROUND_COLOR)
    game_view.draw()
    pygame.display.flip()
    clock.tick(60)



pygame.quit()
sys.exit()
