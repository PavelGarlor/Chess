import pygame
import time

pygame.init()
screen = pygame.display.set_mode((0, 0))
pygame.display.update()
clock = pygame.time.Clock()
running = True

# Colors
BACKGROUND_COLOR = (9, 18, 33)
DARK_SQ = (13, 74, 27)
LIGHT_SQ = (192, 209, 196)

# ======= SETTINGS =======
board_reveal_time = 3.0    # total time to reveal all squares
fall_total_time = 12.0      # total time for all squares to finish falling
dark_factor = 0.2           # darkness while hovering
x_offset = 15
y_offset = 30
size_multiplier = 1.2
# ========================

ROWS, COLS = 8, 8
squares = []
square_index = 0
last_spawn_time = time.time()
fall_start_time = None  # when the full board starts falling

# Compute interval between square reveals
spawn_interval = board_reveal_time / (ROWS * COLS)

# Screen layout
window_width = screen.get_width()
window_height = screen.get_height()
chessboard_size = min(window_width, window_height) * 0.9
chessboard_x = (window_width - chessboard_size) / 2
chessboard_y = (window_height - chessboard_size) / 2
square_size = chessboard_size / 8

def interpolate_color(from_color, to_color, t):
    r = int(from_color[0] + (to_color[0] - from_color[0]) * t)
    g = int(from_color[1] + (to_color[1] - from_color[1]) * t)
    b = int(from_color[2] + (to_color[2] - from_color[2]) * t)
    return (r, g, b)

# Calculate per-square fall duration so that all squares reach at the same time
fall_duration = fall_total_time / (ROWS * COLS)

start_time = time.time()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_time = time.time()
    screen.fill(BACKGROUND_COLOR)
    pygame.draw.rect(screen, (92, 70, 48),
                     pygame.Rect(chessboard_x - 20, chessboard_y - 20,
                                 chessboard_size + 40, chessboard_size + 40))

    # ======= REVEAL PHASE =======
    if square_index < 64 and current_time - last_spawn_time >= spawn_interval:
        i = square_index // 8
        j = square_index % 8
        color = LIGHT_SQ if (i + j) % 2 == 0 else DARK_SQ
        target_x = chessboard_x + j * square_size
        target_y = chessboard_y + i * square_size
        squares.append({
            "start_x": target_x + x_offset,
            "start_y": target_y - y_offset,
            "size": square_size * size_multiplier,
            "target_x": target_x,
            "target_y": target_y,
            "target_size": square_size,
            "color": color,
            "spawn_time": current_time,  # when it appeared
            "fall_started": False        # flag for individual fall
        })
        square_index += 1
        last_spawn_time = current_time

        # When last square spawned, mark the fall start
        if square_index == 64:
            fall_start_time = current_time

    # ======= ANIMATE PHASE =======
    for idx, sq in enumerate(squares):
        if fall_start_time is None:
            # Board still revealing or hovering
            current_color = interpolate_color((0, 0, 0), sq["color"], dark_factor)
            sq_x = sq["start_x"]
            sq_y = sq["start_y"]
            sq_size = sq["size"]
        else:
            # Each square starts falling with a small delay relative to its index
            individual_delay = idx * (fall_total_time / (ROWS * COLS))
            t_anim = max(0, min((current_time - fall_start_time - individual_delay) / fall_duration, 1))
            # Keep hovering until its delay passed
            if t_anim <= 0:
                current_color = interpolate_color((0, 0, 0), sq["color"], dark_factor)
                sq_x = sq["start_x"]
                sq_y = sq["start_y"]
                sq_size = sq["size"]
            else:
                # Falling + brightening
                sq_x = sq["start_x"] + (sq["target_x"] - sq["start_x"]) * t_anim
                sq_y = sq["start_y"] + (sq["target_y"] - sq["start_y"]) * t_anim
                sq_size = sq["size"] + (sq["target_size"] - sq["size"]) * t_anim
                current_color = interpolate_color(interpolate_color((0,0,0), sq["color"], dark_factor), sq["color"], t_anim)

        pygame.draw.rect(screen, current_color, pygame.Rect(sq_x, sq_y, sq_size, sq_size))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
