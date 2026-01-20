import pygame
import time

from game.config import *
from game.models.board import Board
from game.models.pieces.piece import Pawn
from game.models.square import Square

pygame.init()
screen = pygame.display.set_mode((0, 0))
pygame.display.update()
clock = pygame.time.Clock()
running = True


square_size = 0  # will be computed later



# --------------------
# INITIALIZE BOARD
# --------------------
window_width = screen.get_width()
window_height = screen.get_height()
chessboard_size = min(window_width, window_height) * 0.9
chessboard_x = (window_width - chessboard_size) / 2
chessboard_y = (window_height - chessboard_size) / 2
square_size = chessboard_size / 8

board = Board( chessboard_x, chessboard_y, square_size)
board.place_piece(Pawn("white"),(0,0))
board.place_piece(Pawn("white"),(0,1))

# --------------------
# MAIN LOOP
# --------------------
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_time = time.time()
    screen.fill(BACKGROUND_COLOR)
    board.update(current_time)
    board.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
