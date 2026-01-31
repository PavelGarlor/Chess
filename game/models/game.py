import pygame

from game.controller.chess_controller import ChessController
from game.models.board_state import BoardState
from game.view.board_view import BoardView


class Game:
    def __init__(self):
        pygame.init()

        # Create model and view
        self.state = BoardState()
        self.view = BoardView()

        # Controller gets references to both
        self.controller = ChessController(self.state, self.view)

        self.clock = pygame.time.Clock()
        self.running = True

    def restart_game(self):
        self.state = BoardState()
        self.controller.state = self.state

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.controller.handle_mouse_click(event.pos)

            self.view.draw(self.state)
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
