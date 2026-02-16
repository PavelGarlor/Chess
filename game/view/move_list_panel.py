import pygame

class MoveListPanel:
    def __init__(self, screen, width=300):
        self.screen = screen
        self.width = width
        self.moves = []  # list of UCI moves
        self.is_open = True
        self.font = pygame.font.SysFont("Arial", 20)
        self.bg_color = (30, 30, 30)
        self.text_color = (255, 255, 255)
        self.scroll_offset = 0
        self.line_height = 24

    def add_move(self, move_uci: str):
        self.moves.append(move_uci)
        # Auto-scroll to bottom
        max_visible = self.screen.get_height() // self.line_height - 2
        if len(self.moves) > max_visible:
            self.scroll_offset = len(self.moves) - max_visible

    def toggle(self):
        self.is_open = not self.is_open

    def draw(self):
        if not self.is_open:
            return

        panel_rect = pygame.Rect(
            self.screen.get_width() - self.width,
            0,
            self.width,
            self.screen.get_height()
        )

        # Background
        pygame.draw.rect(self.screen, self.bg_color, panel_rect)

        # Title
        title_surf = self.font.render("Move List", True, self.text_color)
        self.screen.blit(title_surf, (panel_rect.left + 10, 10))

        # Draw moves
        start_y = 40
        for i, move in enumerate(self.moves[self.scroll_offset:]):
            y = start_y + i * self.line_height
            if y + self.line_height > self.screen.get_height():
                break  # don't draw off-screen
            move_surf = self.font.render(f"{i+self.scroll_offset+1}. {move}", True, self.text_color)
            self.screen.blit(move_surf, (panel_rect.left + 10, y))



