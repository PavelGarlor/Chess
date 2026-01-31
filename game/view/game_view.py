import pygame

from game.models.player import Player


class GameView:
    def __init__(self, screen, board_view):
        self.screen = screen
        self.board_view = board_view
        self.font = pygame.font.SysFont("Arial", 32)
        self.message_font = pygame.font.SysFont("Arial", 64, bold=True)

        # Example UI fields
        self.white_player : Player = Player("Pavel")
        self.black_player: Player = Player("BOT1")
        self.message = None  # e.g. "Checkmate! White wins"

    def set_message(self, msg: str):
        self.message = msg

    def draw(self):
        # Draw background UI (timers, names, etc)
        self._draw_player_names()

        # Draw board inside UI
        self.board_view.draw(self.screen)

        # winner message
        self._draw_message()

    def _draw_player_names(self):
        white_name = self.white_player.username
        black_name = self.black_player.username
        # White at bottom
        white_surf = self.font.render(white_name, True, (255,255,255))
        black_surf = self.font.render(black_name, True, (255,255,255))

        self.screen.blit(white_surf, (50, self.screen.get_height() - 50))
        self.screen.blit(black_surf, (50, 20))

    def _draw_message(self):
        if not self.message:
            return

        # --- DARK OVERLAY ---
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  # (R,G,B,Alpha) → 150 = transparency
        self.screen.blit(overlay, (0, 0))

        # --- MESSAGE TEXT ---
        surf = self.message_font.render(self.message, True, (227, 182, 18))
        rect = surf.get_rect(center=(
            self.screen.get_width() // 2,
            self.screen.get_height() // 2
        ))
        self.screen.blit(surf, rect)



