from __future__ import annotations

import random

import pygame

from src.settings import ENEMY_COLOR, ENEMY_SIZE, ENEMY_SPEED_MIN, ENEMY_SPEED_MAX, WINDOW_HEIGHT, WINDOW_WIDTH


class Enemy:
    def __init__(self) -> None:
        self.rect = pygame.Rect(0, 0, ENEMY_SIZE, ENEMY_SIZE)
        self.reposition()
        self.vx = random.choice([-1, 1]) * random.randint(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)
        self.vy = random.choice([-1, 1]) * random.randint(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)

    def reposition(self) -> None:
        self.rect.x = random.randint(0, WINDOW_WIDTH - self.rect.width)
        self.rect.y = random.randint(0, WINDOW_HEIGHT - self.rect.height)

    def update(self) -> None:
        self.rect.x += self.vx
        self.rect.y += self.vy

        if self.rect.left <= 0 or self.rect.right >= WINDOW_WIDTH:
            self.vx = -self.vx
        if self.rect.top <= 0 or self.rect.bottom >= WINDOW_HEIGHT:
            self.vy = -self.vy

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, ENEMY_COLOR, self.rect, border_radius=6)