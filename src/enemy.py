from __future__ import annotations

import random

import pygame

from src.settings import (
    ENEMY_BASE_HP,
    ENEMY_COLOR,
    ENEMY_SIZE,
    ENEMY_SPEED_MAX,
    ENEMY_SPEED_MIN,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


class Enemy:
    def __init__(self) -> None:
        self.rect = pygame.Rect(0, 0, ENEMY_SIZE, ENEMY_SIZE)
        self.reposition()
        self.vx = random.choice([-1, 1]) * random.randint(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)
        self.vy = random.choice([-1, 1]) * random.randint(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)
        self.max_hp = ENEMY_BASE_HP
        self.current_hp = ENEMY_BASE_HP
        self.stunned_until_ms = 0

    def reposition(self) -> None:
        self.rect.x = random.randint(0, WINDOW_WIDTH - self.rect.width)
        self.rect.y = random.randint(0, WINDOW_HEIGHT - self.rect.height)

    def update(self, now_ms: int) -> None:
        if now_ms < self.stunned_until_ms:
            return

        self.rect.x += self.vx
        self.rect.y += self.vy

        if self.rect.left <= 0 or self.rect.right >= WINDOW_WIDTH:
            self.vx = -self.vx
        if self.rect.top <= 0 or self.rect.bottom >= WINDOW_HEIGHT:
            self.vy = -self.vy

    def take_damage(self, amount: int, now_ms: int, stun_ms: int) -> bool:
        self.current_hp = max(0, self.current_hp - amount)
        self.stunned_until_ms = max(self.stunned_until_ms, now_ms + stun_ms)
        return self.current_hp <= 0

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, ENEMY_COLOR, self.rect, border_radius=6)