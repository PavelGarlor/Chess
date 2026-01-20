# --------------------
# SQUARE CLASS
# --------------------
import pygame

from game import size_multiplier, y_offset, x_offset, dark_factor


class Square:
    def __init__(self, color, target_x, target_y, size):
        self.color = color
        self.target_x = target_x
        self.target_y = target_y
        self.start_x = target_x + x_offset
        self.start_y = target_y - y_offset
        self.start_size = size * size_multiplier
        self.target_size = size
        self.spawn_time = None

    def update(self, current_time, fall_start_time, idx, fall_duration):
        if self.spawn_time is None:
            self.spawn_time = current_time

        individual_delay = idx * fall_duration

        if fall_start_time is None or current_time < fall_start_time + individual_delay:
            # Hover/dark stage
            self.current_color = interpolate_color((0, 0, 0), self.color, dark_factor)
            self.current_pos = (self.start_x, self.start_y)
            self.current_size = self.start_size
            return False  # animation not finished yet
        else:
            t_anim = min((current_time - fall_start_time - individual_delay) / fall_duration, 1)
            self.current_pos = (
                self.start_x + (self.target_x - self.start_x) * t_anim,
                self.start_y + (self.target_y - self.start_y) * t_anim
            )
            self.current_size = self.start_size + (self.target_size - self.start_size) * t_anim
            self.current_color = interpolate_color(
                interpolate_color((0, 0, 0), self.color, dark_factor), self.color, t_anim
            )
            return t_anim >= 1  # animation finished when t_anim reaches 1

    def draw(self, surface):
        pygame.draw.rect(surface, self.current_color,
                         pygame.Rect(self.current_pos[0], self.current_pos[1],
                                     self.current_size, self.current_size))






# --------------------
# HELPER FUNCTION
# --------------------
def interpolate_color(from_color, to_color, t):
    r = int(from_color[0] + (to_color[0] - from_color[0]) * t)
    g = int(from_color[1] + (to_color[1] - from_color[1]) * t)
    b = int(from_color[2] + (to_color[2] - from_color[2]) * t)
    return (r, g, b)