import pygame

from ai_engine.versions.v0_random_AI import *
from game.models.pieces.piece import *
from game.models.player import Player
from game.models.real_player import RealPlayer
from game.view.piece_view import PieceView


class GameView:
    def __init__(self, screen, board_view):
        self.screen = screen
        self.board_view = board_view
        self.font = pygame.font.SysFont("Arial", 32)
        self.message_font = pygame.font.SysFont("Arial", 64, bold=True)

        # Example UI fields
        self.white_player : Player = RealPlayer("white" ,"Pavel")
        self.black_player: Player = RealPlayer("black" ,"BOT2")
        self.message = None  # e.g. "Checkmate! White wins"

        self.promotion_active = False
        self.promotion_color = None
        self.promotion_position = None

    def set_message(self, msg: str):
        self.message = msg

    def draw(self):
        # Draw background UI (timers, names, etc)
        self._draw_player_names()

        # Draw board inside UI
        self.board_view.draw(self.screen)

        # winner message
        self._draw_message()

        # if self.promotion_active:
        #     self._draw_promotion_menu()

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

    def start_promotion(self, color, pos):
        self.promotion_active = True
        self.promotion_color = color
        self.promotion_position = pos

    def _draw_promotion_menu(self):
        if not self.promotion_active:
            return

        # ---- DARK OVERLAY ----
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        pieces = ["Queen", "Rook", "Bishop", "Knight"]
        w, h = 150, 150
        spacing = 30

        start_x = (self.screen.get_width() - (4 * w + 3 * spacing)) // 2
        y = self.screen.get_height() // 2 - h // 2

        self.promotion_buttons = []

        color = self.promotion_color  # "white" or "black"

        for i, name in enumerate(pieces):
            rect = pygame.Rect(start_x + i * (w + spacing), y, w, h)
            self.promotion_buttons.append((rect, name))

            # Button background
            pygame.draw.rect(self.screen, (230, 230, 230), rect, border_radius=12)

            # ---- USE PieceView TO DRAW THE IMAGE ----
            piece_cls = {"Queen": Queen, "Rook": Rook, "Bishop": Bishop, "Knight": Knight}[name]

            preview_piece = piece_cls(color)
            preview_piece.position = (-1, -1)  # temp position, never used on board

            # Create a temporary PieceView (correct image & scaling)
            pv = PieceView(
                piece=preview_piece,
                target_position=rect.center,
                square_size=self.board_view.square_size,
                animate=False
            )

            # Draw centered inside rect
            pv.draw_at(self.screen, rect.center)

            # Button border
            pygame.draw.rect(self.screen, (60, 60, 60), rect, width=3, border_radius=12)


