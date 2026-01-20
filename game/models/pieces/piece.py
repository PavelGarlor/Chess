import pygame
from abc import ABC, abstractmethod
from typing import Tuple, List
import os

ASSETS_PATH = "assets/pieces/3Dpieces"  # folder with piece images


class Piece(ABC):
    _images_cache = {}  # shared cache so we don't load the same image multiple times

    def __init__(self, piece_type: str, color: str):
        self.type = piece_type
        self.color = color  # "white" or "black"
        self.image = self.load_image()

    @abstractmethod
    def moves(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Return all possible moves from the given position."""
        pass

    def load_image(self) -> pygame.Surface:
        """Load the piece image based on its type and color."""
        filename = f"{self.color[0]}{self.type[0]}.png"  # e.g., wp.png
        path = os.path.join(ASSETS_PATH, filename)

        # Use cache if already loaded
        if path in Piece._images_cache:
            return Piece._images_cache[path]

        if not os.path.exists(path):
            raise FileNotFoundError(f"Piece image not found: {path}")

        image = pygame.image.load(path).convert_alpha()
        Piece._images_cache[path] = image
        return image

    def draw(self, surface: pygame.Surface, position: Tuple[float, float]):
        """Draw the piece centered at the given pixel position."""
        rect = self.image.get_rect(center=position)
        surface.blit(self.image, rect)


class Pawn(Piece):
    def __init__(self, color: str):
        super().__init__("pawn", color)

    def moves(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        x, y = position
        direction = 1 if self.color == "white" else -1
        return [(x, y + direction)]
