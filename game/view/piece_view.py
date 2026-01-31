import time
from typing import Tuple, Optional
import pygame
import os

from game.helpers import animation as anim
from game.models.pieces.piece import Piece


class PieceView:
    FALL_DURATION = 0.9
    CAPTURE_FADE_TIME = 0.3
    ASSETS_PATH = "assets/pieces/3Dpieces"
    # ASSETS_PATH = "assets/pieces/Futuristic"

    def __init__(
        self,
        *,
        piece: Piece,
        target_position: Tuple[float, float],
        square_size: float,
        animate: bool = True,
    ):
        self.piece = piece
        self.square_size = square_size
        self.animate = animate

        # Target and spawn positions
        self.target_position = target_position
        self.spawn_position = (target_position[0], -square_size * 2)

        # Animation state
        self.spawn_time: Optional[float] = None
        self.move_start_time: Optional[float] = None
        self.capture_time: Optional[float] = None

        # Initialize current_position at spawn if animating
        if self.animate:
            self.current_position = self.spawn_position
            self.has_spawned = False
        else:
            self.current_position = self.target_position
            self.has_spawned = True

        self.is_moving = False
        self.is_captured = False
        self.delay = 0.0
        self.alpha = 255

        # Load and scale piece sprite
        self.image = self._load_and_scale_image(piece)

    # ----------------------------
    # IMAGE LOADING
    # ----------------------------
    def _load_and_scale_image(self, piece: Piece) -> pygame.Surface:
        filename = f"{piece.color[0]}{piece.SYMBOL}.png"
        path = os.path.join(self.ASSETS_PATH, filename)

        img = pygame.image.load(path).convert_alpha()

        # Scale width to square size (height can vary)
        w, h = img.get_size()
        scale = self.square_size / w
        new_w = int(w * scale)
        new_h = int(h * scale)
        return pygame.transform.smoothscale(img, (new_w, new_h))

    # ------------------------------------------------------------------
    # LIFECYCLE
    # ------------------------------------------------------------------
    def start_spawn(self, start_time: float) -> None:
        """Begin falling animation from spawn_position to target_position"""
        if not self.animate:
            self.current_position = self.target_position
            self.has_spawned = True
            return

        self.spawn_time = start_time
        self.current_position = self.spawn_position
        self.has_spawned = False

    def animate_to(self, new_target: Tuple[float, float]) -> None:
        """Animate piece moving to a new target position"""
        if not self.animate:
            self.current_position = new_target
            self.target_position = new_target
            return

        self.move_start_time = time.time()
        self.start_position = self.current_position
        self.target_position = new_target
        self.is_moving = True

    def start_capture(self) -> None:
        """Start capture fade animation"""
        self.is_captured = True
        self.capture_time = time.time()

    def finish(self) -> None:
        """Immediately finish all animations"""
        self.current_position = self.target_position
        self.has_spawned = True
        self.is_moving = False

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    def update(self, now: float) -> None:
        """Update piece animation state"""
        if self.is_captured:
            elapsed = now - self.capture_time
            self.alpha = max(0, 255 * (1 - elapsed / self.CAPTURE_FADE_TIME))
            return

        if not self.has_spawned and self.spawn_time is not None:
            local_time = max(0.0, now - self.spawn_time - self.delay)
            pos = anim.animate_to_pos(
                self.spawn_position,
                self.target_position,
                local_time,
                self.FALL_DURATION,
            )
            self.current_position = pos

            if pos == self.target_position:
                self.has_spawned = True

        elif self.is_moving and self.move_start_time is not None:
            local_time = now - self.move_start_time
            pos = anim.animate_to_pos(
                self.start_position,
                self.target_position,
                local_time,
                self.FALL_DURATION * 0.6,
            )
            self.current_position = pos

            if pos == self.target_position:
                self.is_moving = False

    # ------------------------------------------------------------------
    # DRAW
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the piece aligned to bottom-left of square"""
        if self.is_captured and self.alpha <= 0:
            return

        image = self.image.copy()
        image.set_alpha(int(self.alpha))

        rect = image.get_rect()
        rect.bottomleft = (int(self.current_position[0]), int(self.current_position[1]))
        surface.blit(image, rect)
