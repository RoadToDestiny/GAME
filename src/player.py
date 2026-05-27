from __future__ import annotations

import pygame

from src.settings import (
    PLAYER_COLOR,
    PLAYER_GROWTH_STEP,
    PLAYER_MAX_SIZE,
    PLAYER_START_X,
    PLAYER_START_Y,
    PLAYER_SIZE,
    PLAYER_SPEED,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


class Player:
    def __init__(self) -> None:
        self.rect = pygame.Rect(PLAYER_START_X, PLAYER_START_Y, PLAYER_SIZE, PLAYER_SIZE)

    def update(self, keys: pygame.key.ScancodeWrapper) -> None:
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += PLAYER_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= PLAYER_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += PLAYER_SPEED

        self._clamp_to_window()

    def grow(self) -> None:
        if self.rect.width >= PLAYER_MAX_SIZE:
            return

        center = self.rect.center
        new_size = min(self.rect.width + PLAYER_GROWTH_STEP, PLAYER_MAX_SIZE)
        self.rect.size = (new_size, new_size)
        self.rect.center = center
        self._clamp_to_window()

    def reset_position(self) -> None:
        """Return the player to the start position without changing its size."""
        self.rect.centerx = WINDOW_WIDTH // 2
        self.rect.centery = WINDOW_HEIGHT // 2 + 70
        self._clamp_to_window()

    def reset(self) -> None:
        """Reset player to initial size and position."""
        self.rect.size = (PLAYER_SIZE, PLAYER_SIZE)
        self.rect.centerx = WINDOW_WIDTH // 2
        self.rect.centery = WINDOW_HEIGHT // 2 + 70
        self._clamp_to_window()

    def _clamp_to_window(self) -> None:
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, WINDOW_WIDTH)
        self.rect.top = max(self.rect.top, 0)
        self.rect.bottom = min(self.rect.bottom, WINDOW_HEIGHT)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, PLAYER_COLOR, self.rect, border_radius=8)