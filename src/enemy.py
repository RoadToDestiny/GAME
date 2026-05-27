from __future__ import annotations

import random

import pygame

from src.settings import (
    ENEMY_AGGRO_BASE_RANGE,
    ENEMY_ATTACK_RANGE,
    ENEMY_BASE_HP,
    ENEMY_COLOR,
    ENEMY_CONTACT_DAMAGE,
    ENEMY_PATROL_RADIUS,
    ENEMY_SIZE,
    ENEMY_SPEED_MAX,
    ENEMY_SPEED_MIN,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


class Enemy:
    def __init__(self, spawn_pos: tuple[int, int] | None = None) -> None:
        self.rect = pygame.Rect(0, 0, ENEMY_SIZE, ENEMY_SIZE)
        self.base_pos = spawn_pos
        self.reposition()
        self.max_hp = ENEMY_BASE_HP
        self.current_hp = ENEMY_BASE_HP
        self.stunned_until_ms = 0
        self.state = "patrol"
        self.speed = random.randint(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)
        self.aggro_range = ENEMY_AGGRO_BASE_RANGE + random.randint(0, 30)
        self.patrol_target = self._random_patrol_target()
        self.contact_damage = ENEMY_CONTACT_DAMAGE

    def reposition(self) -> None:
        if self.base_pos is None:
            self.rect.x = random.randint(0, WINDOW_WIDTH - self.rect.width)
            self.rect.y = random.randint(0, WINDOW_HEIGHT - self.rect.height)
            self.base_pos = self.rect.center
            return
        self.rect.center = self.base_pos

    def update(self, now_ms: int, player_center: tuple[int, int], obstacles: list[pygame.Rect]) -> None:
        if now_ms < self.stunned_until_ms:
            return

        px, py = player_center
        ex, ey = self.rect.center
        dx = px - ex
        dy = py - ey
        dist_sq = dx * dx + dy * dy
        if dist_sq <= ENEMY_ATTACK_RANGE * ENEMY_ATTACK_RANGE:
            self.state = "attack"
        elif dist_sq <= self.aggro_range * self.aggro_range:
            self.state = "chase"
        elif self.state in ("chase", "attack"):
            self.state = "return"

        if self.state == "patrol":
            self._move_to(self.patrol_target, obstacles)
            ex, ey = self.rect.center
            tx, ty = self.patrol_target
            if (ex - tx) * (ex - tx) + (ey - ty) * (ey - ty) <= 64:
                self.patrol_target = self._random_patrol_target()
        elif self.state in ("chase", "attack"):
            self._move_to((px, py), obstacles)
        elif self.state == "return":
            self._move_to(self.base_pos, obstacles)
            ex, ey = self.rect.center
            bx, by = self.base_pos
            if (ex - bx) * (ex - bx) + (ey - by) * (ey - by) <= 100:
                self.state = "patrol"
                self.patrol_target = self._random_patrol_target()

    def take_damage(self, amount: int, now_ms: int, stun_ms: int) -> bool:
        self.current_hp = max(0, self.current_hp - amount)
        self.stunned_until_ms = max(self.stunned_until_ms, now_ms + stun_ms)
        if self.current_hp > 0:
            self.state = "chase"
        return self.current_hp <= 0

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, ENEMY_COLOR, self.rect, border_radius=6)

    def _random_patrol_target(self) -> tuple[int, int]:
        bx, by = self.base_pos
        tx = random.randint(bx - ENEMY_PATROL_RADIUS, bx + ENEMY_PATROL_RADIUS)
        ty = random.randint(by - ENEMY_PATROL_RADIUS, by + ENEMY_PATROL_RADIUS)
        tx = max(self.rect.width // 2, min(WINDOW_WIDTH - self.rect.width // 2, tx))
        ty = max(self.rect.height // 2, min(WINDOW_HEIGHT - self.rect.height // 2, ty))
        return tx, ty

    def _move_to(self, target: tuple[int, int], obstacles: list[pygame.Rect]) -> None:
        ex, ey = self.rect.center
        tx, ty = target
        dx = tx - ex
        dy = ty - ey
        distance = (dx * dx + dy * dy) ** 0.5
        if distance < 1e-6:
            return
        step = min(self.speed, distance)
        step_x = (dx / distance) * step
        step_y = (dy / distance) * step

        old_center = self.rect.center
        self.rect.centerx = int(ex + step_x)
        if any(self.rect.colliderect(obstacle) for obstacle in obstacles):
            self.rect.centerx = old_center[0]

        self.rect.centery = int(self.rect.centery + step_y)
        if any(self.rect.colliderect(obstacle) for obstacle in obstacles):
            self.rect.centery = old_center[1]