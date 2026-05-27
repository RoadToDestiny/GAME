from __future__ import annotations

import random

import pygame

from src.settings import FOOD_COLOR, FOOD_MARGIN, FOOD_SIZE, WINDOW_HEIGHT, WINDOW_WIDTH


class Food:
    def __init__(self) -> None:
        self.rect = pygame.Rect(0, 0, FOOD_SIZE, FOOD_SIZE)
        self.reposition()

    def reposition(self, blocked_rects: list[pygame.Rect] | None = None) -> None:
        blocked_rects = blocked_rects or []
        for _ in range(200):
            self.rect.x = random.randint(FOOD_MARGIN, WINDOW_WIDTH - FOOD_MARGIN - self.rect.width)
            self.rect.y = random.randint(FOOD_MARGIN, WINDOW_HEIGHT - FOOD_MARGIN - self.rect.height)
            if not any(self.rect.colliderect(rect) for rect in blocked_rects):
                return

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.ellipse(surface, FOOD_COLOR, self.rect)