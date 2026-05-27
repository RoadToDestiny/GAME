from __future__ import annotations

import pygame

from src.settings import PROJECTILE_COLOR, PROJECTILE_DAMAGE, PROJECTILE_SIZE, PROJECTILE_SPEED


class Projectile:
    def __init__(self, position: tuple[int, int], direction: tuple[float, float], stun_ms: int = 0, owner_center: tuple[int, int] | None = None) -> None:
        self.rect = pygame.Rect(0, 0, PROJECTILE_SIZE, PROJECTILE_SIZE)
        self.rect.center = position
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)
        self.dx, self.dy = direction
        self.damage = PROJECTILE_DAMAGE
        self.stun_ms = stun_ms
        # store where the projectile originated so we can determine bush ownership
        self.owner_center = owner_center

    def update(self, dt: float) -> None:
        self.pos_x += self.dx * PROJECTILE_SPEED * 60.0 * dt
        self.pos_y += self.dy * PROJECTILE_SPEED * 60.0 * dt
        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.ellipse(surface, PROJECTILE_COLOR, self.rect)
