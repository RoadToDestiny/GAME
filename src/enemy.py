from __future__ import annotations

import random

import pygame

from src.settings import (
    ENEMY_AGGRO_BASE_RANGE,
    ENEMY_ATTACK_RANGE,
    ENEMY_BASE_HP,
    ENEMY_COLOR,
    ENEMY_CONTACT_DAMAGE,
    ENEMY_MELEE_SPRITE_PATH,
    ENEMY_PATROL_RADIUS,
    ENEMY_RANGED_COOLDOWN_MS,
    ENEMY_RANGED_RANGE,
    ENEMY_SHOOTER_COLOR,
    ENEMY_SHOOTER_SPRITE_PATH,
    ENEMY_SIZE,
    ENEMY_SPEED_MAX,
    ENEMY_SPEED_MIN,
    ENEMY_STUN_COOLDOWN_MS,
    ENEMY_STUN_DURATION_MS,
    ENEMY_STUNNER_COLOR,
    ENEMY_STUNNER_SPRITE_PATH,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


class Enemy:
    _sprite_sources: dict[str, pygame.Surface | None] | None = None

    def __init__(self, spawn_pos: tuple[int, int] | None = None, enemy_type: str = "melee") -> None:
        self.rect = pygame.Rect(0, 0, ENEMY_SIZE, ENEMY_SIZE)
        self.base_pos = spawn_pos
        self.enemy_type = enemy_type
        self.reposition()
        self.max_hp = ENEMY_BASE_HP + (1 if enemy_type == "stunner" else 0)
        self.current_hp = self.max_hp
        self.stunned_until_ms = 0
        self.state = "patrol"
        self.speed = random.randint(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)
        if enemy_type == "stunner":
            self.speed = max(1, self.speed - 1)
        self.aggro_range = ENEMY_AGGRO_BASE_RANGE + random.randint(0, 30)
        self.patrol_target = self._random_patrol_target()
        self.last_known_player_pos: tuple[int, int] | None = None
        self.contact_damage = ENEMY_CONTACT_DAMAGE
        self.last_attack_ms = -10_000
        self._sprite = self._prepare_sprite()

    def reposition(self) -> None:
        if self.base_pos is None:
            self.rect.x = random.randint(0, WINDOW_WIDTH - self.rect.width)
            self.rect.y = random.randint(0, WINDOW_HEIGHT - self.rect.height)
            self.base_pos = self.rect.center
            return
        self.rect.center = self.base_pos

    def update(
        self,
        now_ms: int,
        player_center: tuple[int, int],
        obstacles: list[pygame.Rect],
        bushes: list[pygame.Rect],
    ) -> tuple[tuple[int, int], tuple[float, float], int] | None:
        if now_ms < self.stunned_until_ms:
            return None

        px, py = player_center
        ex, ey = self.rect.center
        dx = px - ex
        dy = py - ey
        dist_sq = dx * dx + dy * dy
        attack_range = ENEMY_RANGED_RANGE if self.enemy_type in ("shooter", "stunner") else ENEMY_ATTACK_RANGE

        # Determine which bush (if any) the player is in
        player_bush: pygame.Rect | None = None
        for bush in bushes:
            if bush.collidepoint(px, py):
                player_bush = bush
                break

        visible = self._can_see_player(player_center, obstacles, bushes)

        if visible:
            # remember last known player position while visible
            self.last_known_player_pos = player_center
            if dist_sq <= attack_range * attack_range:
                self.state = "attack"
            elif dist_sq <= self.aggro_range * self.aggro_range and self.enemy_type != "stunner":
                self.state = "chase"
        else:
            if self.state in ("chase", "attack"):
                # lost sight: go search to last known position
                self.state = "search"

        if self.state == "patrol":
            if self.enemy_type != "stunner":
                self._move_to(self.patrol_target, obstacles, player_bush)
            ex, ey = self.rect.center
            tx, ty = self.patrol_target
            if (ex - tx) * (ex - tx) + (ey - ty) * (ey - ty) <= 64:
                self.patrol_target = self._random_patrol_target()
        elif self.state in ("chase", "attack"):
            if self.enemy_type == "melee":
                self._move_to((px, py), obstacles, player_bush)
            elif self.enemy_type == "shooter":
                preferred_dist = ENEMY_RANGED_RANGE * 0.65
                if dist_sq < preferred_dist * preferred_dist:
                    self._move_to((2 * ex - px, 2 * ey - py), obstacles, player_bush)
                elif dist_sq > ENEMY_RANGED_RANGE * ENEMY_RANGED_RANGE:
                    self._move_to((px, py), obstacles, player_bush)
            else:
                self._move_to(self.base_pos, obstacles, player_bush)
        elif self.state == "search":
            if self.last_known_player_pos is not None:
                self._move_to(self.last_known_player_pos, obstacles, player_bush)
                ex, ey = self.rect.center
                lx, ly = self.last_known_player_pos
                if (ex - lx) * (ex - lx) + (ey - ly) * (ey - ly) <= 100:
                    self.state = "return"
        elif self.state == "return":
            self._move_to(self.base_pos, obstacles, player_bush)
            ex, ey = self.rect.center
            bx, by = self.base_pos
            if (ex - bx) * (ex - bx) + (ey - by) * (ey - by) <= 100:
                self.state = "patrol"
                self.patrol_target = self._random_patrol_target()
        return self._try_attack(now_ms, player_center)

    def take_damage(self, amount: int, now_ms: int, stun_ms: int) -> bool:
        self.current_hp = max(0, self.current_hp - amount)
        self.stunned_until_ms = max(self.stunned_until_ms, now_ms + stun_ms)
        if self.current_hp > 0:
            self.state = "chase"
        return self.current_hp <= 0

    def draw(self, surface: pygame.Surface) -> None:
        if self._sprite is not None:
            surface.blit(self._sprite, self.rect)
            return
        if self.enemy_type == "shooter":
            color = ENEMY_SHOOTER_COLOR
        elif self.enemy_type == "stunner":
            color = ENEMY_STUNNER_COLOR
        else:
            color = ENEMY_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=6)

    def _random_patrol_target(self) -> tuple[int, int]:
        bx, by = self.base_pos
        tx = random.randint(bx - ENEMY_PATROL_RADIUS, bx + ENEMY_PATROL_RADIUS)
        ty = random.randint(by - ENEMY_PATROL_RADIUS, by + ENEMY_PATROL_RADIUS)
        tx = max(self.rect.width // 2, min(WINDOW_WIDTH - self.rect.width // 2, tx))
        ty = max(self.rect.height // 2, min(WINDOW_HEIGHT - self.rect.height // 2, ty))
        return tx, ty

    def _move_to(self, target: tuple[int, int], obstacles: list[pygame.Rect], player_bush: pygame.Rect | None = None) -> None:
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

        # If player is hidden in a bush and enemy wasn't in that bush, don't enter it
        if player_bush is not None:
            was_in_bush = player_bush.collidepoint(old_center)
            now_in_bush = player_bush.collidepoint(self.rect.center)
            if not was_in_bush and now_in_bush:
                # revert to avoid entering player's bush
                self.rect.center = old_center

    def _can_see_player(self, player_center: tuple[int, int], obstacles: list[pygame.Rect], bushes: list[pygame.Rect]) -> bool:
        px, py = player_center
        ex, ey = self.rect.center

        # If player is inside a bush and enemy isn't in the same bush, player is hidden
        player_bush: pygame.Rect | None = None
        for bush in bushes:
            if bush.collidepoint(px, py):
                player_bush = bush
                break
        if player_bush is not None and not player_bush.collidepoint(ex, ey):
            return False

        # Check if any obstacle blocks line of sight
        for obstacle in obstacles:
            try:
                if obstacle.clipline((ex, ey), (px, py)):
                    return False
            except Exception:
                # If clipline isn't available or fails, conservatively assume not blocked
                pass
        return True

    def _try_attack(
        self,
        now_ms: int,
        player_center: tuple[int, int],
    ) -> tuple[tuple[int, int], tuple[float, float], int] | None:
        if self.state != "attack":
            return None
        cooldown_ms = ENEMY_RANGED_COOLDOWN_MS if self.enemy_type == "shooter" else ENEMY_STUN_COOLDOWN_MS
        if self.enemy_type == "melee":
            return None
        if now_ms - self.last_attack_ms < cooldown_ms:
            return None
        ex, ey = self.rect.center
        px, py = player_center
        dx = px - ex
        dy = py - ey
        length = (dx * dx + dy * dy) ** 0.5
        if length < 1e-6:
            return None
        self.last_attack_ms = now_ms
        stun_ms = ENEMY_STUN_DURATION_MS if self.enemy_type == "stunner" else 0
        return (ex, ey), (dx / length, dy / length), stun_ms

    def _prepare_sprite(self) -> pygame.Surface | None:
        if Enemy._sprite_sources is None:
            Enemy._sprite_sources = {
                "melee": self._load_sprite(ENEMY_MELEE_SPRITE_PATH),
                "shooter": self._load_sprite(ENEMY_SHOOTER_SPRITE_PATH),
                "stunner": self._load_sprite(ENEMY_STUNNER_SPRITE_PATH),
            }
        source = Enemy._sprite_sources.get(self.enemy_type)
        if source is None:
            return None
        return pygame.transform.smoothscale(source, self.rect.size)

    @staticmethod
    def _load_sprite(path: str) -> pygame.Surface | None:
        try:
            return pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError):
            return None