import pygame


pygame.init()
screen = pygame.display.set_mode((0,0))
pygame.display.update()
clock = pygame.time.Clock()
running = True

BACKGROUND_COLOR = (9, 18, 33)
DARK_SQ = (13, 74, 27)
LIGHT_SQ = (192, 209, 196)


while running:
    window_width = screen.get_width()
    window_height =  screen.get_height()
    chessboard_size = min(window_width,window_height) * 0.9
    chessboard_x = (window_width - chessboard_size)/2
    chessboard_y = (window_height - chessboard_size)/2
    square_size = chessboard_size/8

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BACKGROUND_COLOR)

    # RENDER YOUR GAME HERE
    currentColor = LIGHT_SQ
    for i in range(0, 8):
        for j in range(0,8):
            currentColor = LIGHT_SQ if (i + j) % 2 == 0 else DARK_SQ
            x = (j * square_size) + chessboard_x
            y = (i * square_size) + chessboard_y
            pygame.draw.rect(screen,currentColor,pygame.Rect(x,y,square_size,square_size))



    # flip() the display to put your work on screen
    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()