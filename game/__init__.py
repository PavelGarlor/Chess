import time

import pygame


pygame.init()
screen = pygame.display.set_mode((0,0))
pygame.display.update()
clock = pygame.time.Clock()
running = True

BACKGROUND_COLOR = (9, 18, 33)
DARK_SQ = (13, 74, 27)
LIGHT_SQ = (192, 209, 196)


# Animation variables
square_index = 0          # counts how many squares are drawn
animation_speed = 0.1     # seconds per square
last_time = time.time()   # last square draw time

while running:
    # Screen size and chessboard layout
    window_width = screen.get_width()
    window_height = screen.get_height()
    chessboard_size = min(window_width, window_height) * 0.9
    chessboard_x = (window_width - chessboard_size) / 2
    chessboard_y = (window_height - chessboard_size) / 2
    square_size = chessboard_size / 8

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BACKGROUND_COLOR)

    # Calculate how many squares to draw based on timer
    current_time = time.time()
    if current_time - last_time >= animation_speed and square_index < 64:
        square_index += 1
        last_time = current_time

    # Draw squares up to square_index
    for idx in range(square_index):
        i = idx // 8  # row
        j = idx % 8   # column
        currentColor = LIGHT_SQ if (i + j) % 2 == 0 else DARK_SQ
        x = (j * square_size) + chessboard_x
        y = (i * square_size) + chessboard_y
        pygame.draw.rect(screen, currentColor, pygame.Rect(x, y, square_size, square_size))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()