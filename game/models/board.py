# --------------------
# BOARD CLASS
# --------------------
import time

import pygame

from game.config import *
from game.models.square import Square


class Board:
    def __init__(self, rows, cols, board_x, board_y, square_size):
        self.rows = rows
        self.cols = cols
        self.square_size = square_size
        self.board_x = board_x
        self.board_y = board_y
        self.squares = []
        self.square_index = 0
        self.last_spawn_time = time.time()
        self.fall_start_time = None
        # Pre-create all squares
        for i in range(rows):
            for j in range(cols):
                color = LIGHT_SQ if (i+j)%2==0 else DARK_SQ
                target_x = board_x + j * square_size
                target_y = board_y + i * square_size
                self.squares.append(Square(color, target_x, target_y, square_size))

    def update(self, current_time):
        # Spawn squares gradually
        if self.square_index < len(self.squares) and current_time - self.last_spawn_time >= spawn_interval:
            self.square_index += 1
            self.last_spawn_time = current_time
            if self.square_index == len(self.squares):
                self.fall_start_time = current_time

        # Update all visible squares
        for idx, sq in enumerate(self.squares[:self.square_index]):
            sq.update(current_time, self.fall_start_time, idx, animation_duration)

    def draw(self, surface):
        # Draw board border
        total_size = self.square_size * self.rows
        pygame.draw.rect(surface, (92,70,48),
                         pygame.Rect(self.board_x-20, self.board_y-20,
                                     total_size+40, total_size+40))
        # Draw squares
        for sq in self.squares[:self.square_index]:
            sq.draw(surface)