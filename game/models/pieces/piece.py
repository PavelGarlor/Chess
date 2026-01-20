import pygame
from abc import ABC, abstractmethod
from typing import Tuple, List
import os

ASSETS_PATH = "assets/pieces/3Dpieces"  # folder with piece images


class Piece(ABC):
    _images_cache = {}

    def __init__(self, piece_type: str, color: str):
        self.type = piece_type
        self.color = color
        self.original_image = self.load_image()
        self.image = self.original_image

    def load_image(self) -> pygame.Surface:
        filename = f"{self.color[0]}{self.type[0]}.png"
        path = os.path.join("assets/pieces/3Dpieces", filename)

        if path in Piece._images_cache:
            return Piece._images_cache[path]

        img = pygame.image.load(path).convert_alpha()
        Piece._images_cache[path] = img
        return img

    def rescale_to_square(self, square_size: float):
        w, h = self.original_image.get_size()
        scale = square_size / w
        new_w = int(w * scale)
        new_h = int(h * scale)
        self.image = pygame.transform.smoothscale(
            self.original_image, (new_w, new_h)
        )

    def draw(self, surface, position: tuple[float, float]):
        x, y = position
        rect = self.image.get_rect()
        rect.midbottom = (int(x), int(y))
        surface.blit(self.image, rect)



class Pawn(Piece):
    def __init__(self, color: str):
        super().__init__("p", color)

    def moves(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        x, y = position
        direction = 1 if self.color == "white" else -1
        return [(x, y + direction)]

class Rook(Piece):
    def __init__(self, color: str):
        super().__init__("r", color)

    def moves(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        pass

class Bishop(Piece):
    def __init__(self, color: str):
        super().__init__("b", color)
    def moves(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        pass

class Knight(Piece):
    def __init__(self, color: str):
        super().__init__("n", color)
    def moves(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        pass

class King(Piece):
    def __init__(self, color: str):
        super().__init__("k", color)
    def moves(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        pass

class Queen(Piece):
    def __init__(self, color: str):
        super().__init__("q", color)
    def moves(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        pass