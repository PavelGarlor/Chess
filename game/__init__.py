import pygame
import time

from game.config import *
from game.models.board import Board
from game.models.pieces.piece import Pawn, Knight, Queen, Rook
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
chessboard_size = min(window_width, window_height) * 0.8
chessboard_x = (window_width - chessboard_size) / 2
chessboard_y = (window_height - chessboard_size) / 2
square_size = chessboard_size / 8

board = Board( chessboard_x, chessboard_y, square_size)
# Example: placing some pieces on the board
board.place_piece(Pawn("black"), (0, 0))   # a1
board.place_piece(Pawn("white"), (0, 1))   # a2
board.place_piece(Pawn("black"), (3, 3))   # d4
board.place_piece(Pawn("white"), (6, 6))   # g7

# Assuming you have classes Knight, Queen, Rook implemented
board.place_piece(Knight("white"), (1, 0))  # b1
board.place_piece(Knight("black"), (6, 7))  # g8
board.place_piece(Queen("white"), (3, 0))   # d1
board.place_piece(Queen("black"), (3, 7))   # d8
board.place_piece(Rook("white"), (0, 7))    # a8
board.place_piece(Rook("black"), (7, 0))    # h1


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
