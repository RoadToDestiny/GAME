from __future__ import annotations

import pygame

from src.settings import (
    PLAYER_COLOR,
    PLAYER_GROWTH_STAGES,
    PLAYER_HIT_INVULNERABILITY_MS,
    PLAYER_SPRITE_PATH,
    PLAYER_START_X,
    PLAYER_START_Y,
    PLAYER_SIZE,
    PLAYER_SPRINT_DRAIN_PER_SECOND,
    PLAYER_SPRINT_REGEN_PER_SECOND,
    PLAYER_SPRINT_STAMINA_MAX,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


class Player:
    def __init__(self) -> None:
        self.rect = pygame.Rect(PLAYER_START_X, PLAYER_START_Y, PLAYER_SIZE, PLAYER_SIZE)
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)
        self.food_collected = 0
        self.stage_index = 0
        self.stamina = PLAYER_SPRINT_STAMINA_MAX
        self.last_hit_ms = -PLAYER_HIT_INVULNERABILITY_MS
        self.last_bite_ms = -10_000
        self.stunned_until_ms = 0

        self.speed = 0.0
        self.max_hp = 0
        self.current_hp = 0
        self.bite_damage = 0
        self.bite_range = 0
        self.bite_cooldown_ms = 0
        self.bite_stun_ms = 0
        self.sprint_multiplier = 1.0
        self._apply_stage(self.stage_index, keep_hp_ratio=False)
        self._sprite_source = self._load_sprite()
        self._sprite_size = 0
        self._sprite_scaled: pygame.Surface | None = None
        self._sprite_flipped: pygame.Surface | None = None
        self.facing_left = False

    def update(
        self,
        keys: pygame.key.ScancodeWrapper,
        dt: float,
        obstacles: list[pygame.Rect],
        now_ms: int,
    ) -> None:
        if now_ms < self.stunned_until_ms:
            self.stamina = min(
                PLAYER_SPRINT_STAMINA_MAX,
                self.stamina + PLAYER_SPRINT_REGEN_PER_SECOND * dt,
            )
            return
        move_x = 0.0
        move_y = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x += 1.0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_y -= 1.0
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_y += 1.0

        sprint_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        is_moving = move_x != 0.0 or move_y != 0.0
        # Update facing direction when a horizontal input is present
        if is_moving and move_x != 0.0:
            self.facing_left = move_x < 0.0
        can_sprint = sprint_pressed and is_moving and self.stamina > 0.0
        speed = self.speed * (self.sprint_multiplier if can_sprint else 1.0)

        if is_moving:
            vector_length = (move_x * move_x + move_y * move_y) ** 0.5
            move_x /= vector_length
            move_y /= vector_length
            self._move_axis(move_x * speed * 60.0 * dt, 0.0, obstacles)
            self._move_axis(0.0, move_y * speed * 60.0 * dt, obstacles)

        if can_sprint:
            self.stamina = max(0.0, self.stamina - PLAYER_SPRINT_DRAIN_PER_SECOND * dt)
        else:
            self.stamina = min(
                PLAYER_SPRINT_STAMINA_MAX,
                self.stamina + PLAYER_SPRINT_REGEN_PER_SECOND * dt,
            )

        self._clamp_to_window()

    def collect_food(self) -> None:
        self.food_collected += 1
        while self.stage_index + 1 < len(PLAYER_GROWTH_STAGES):
            required_food = PLAYER_GROWTH_STAGES[self.stage_index + 1][0]
            if self.food_collected < required_food:
                break
            self._apply_stage(self.stage_index + 1, keep_hp_ratio=True)

    def try_bite(self, now_ms: int) -> tuple[int, int, int] | None:
        if now_ms - self.last_bite_ms < self.bite_cooldown_ms:
            return None
        self.last_bite_ms = now_ms
        return self.bite_range, self.bite_damage, self.bite_stun_ms

    def take_hit(self, now_ms: int, damage: int = 1) -> bool:
        if now_ms - self.last_hit_ms < PLAYER_HIT_INVULNERABILITY_MS:
            return False
        self.last_hit_ms = now_ms
        self.current_hp = max(0, self.current_hp - damage)
        return True

    def apply_stun(self, now_ms: int, stun_ms: int) -> None:
        self.stunned_until_ms = max(self.stunned_until_ms, now_ms + stun_ms)

    def reset_position(self) -> None:
        self.rect.centerx = WINDOW_WIDTH // 2
        self.rect.centery = WINDOW_HEIGHT // 2 + 70
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)
        self._clamp_to_window()

    def reset(self) -> None:
        self.food_collected = 0
        self.stage_index = 0
        self.stamina = PLAYER_SPRINT_STAMINA_MAX
        self.last_hit_ms = -PLAYER_HIT_INVULNERABILITY_MS
        self.last_bite_ms = -10_000
        self.stunned_until_ms = 0
        self._apply_stage(0, keep_hp_ratio=False)
        self.reset_position()

    def _apply_stage(self, stage_index: int, keep_hp_ratio: bool) -> None:
        previous_max_hp = self.max_hp if self.max_hp > 0 else 1
        current_ratio = self.current_hp / previous_max_hp

        self.stage_index = stage_index
        stage = PLAYER_GROWTH_STAGES[stage_index]
        _, speed, max_hp, size, bite_damage, bite_range, bite_cooldown_ms, bite_stun_ms, sprint_multiplier = stage
        self.speed = speed
        self.max_hp = max_hp
        self.bite_damage = bite_damage
        self.bite_range = bite_range
        self.bite_cooldown_ms = bite_cooldown_ms
        self.bite_stun_ms = bite_stun_ms
        self.sprint_multiplier = sprint_multiplier

        center = self.rect.center
        self.rect.size = (size, size)
        self.rect.center = center
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)
        self._clamp_to_window()

        if keep_hp_ratio:
            self.current_hp = max(1, int(round(self.max_hp * current_ratio)))
        else:
            self.current_hp = self.max_hp

    def _clamp_to_window(self) -> None:
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, WINDOW_WIDTH)
        self.rect.top = max(self.rect.top, 0)
        self.rect.bottom = min(self.rect.bottom, WINDOW_HEIGHT)
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)

    def _move_axis(self, dx: float, dy: float, obstacles: list[pygame.Rect]) -> None:
        self.pos_x += dx
        self.pos_y += dy
        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

        for obstacle in obstacles:
            if not self.rect.colliderect(obstacle):
                continue
            if dx > 0:
                self.rect.right = obstacle.left
            elif dx < 0:
                self.rect.left = obstacle.right
            if dy > 0:
                self.rect.bottom = obstacle.top
            elif dy < 0:
                self.rect.top = obstacle.bottom
            self.pos_x = float(self.rect.x)
            self.pos_y = float(self.rect.y)

    def draw(self, surface: pygame.Surface) -> None:
        if self._sprite_source is None:
            pygame.draw.rect(surface, PLAYER_COLOR, self.rect, border_radius=8)
            return
        if self._sprite_scaled is None or self._sprite_size != self.rect.width:
            self._sprite_size = self.rect.width
            self._sprite_scaled = pygame.transform.smoothscale(self._sprite_source, self.rect.size)
            self._sprite_flipped = pygame.transform.flip(self._sprite_scaled, True, False) if self._sprite_scaled is not None else None
        sprite = self._sprite_flipped if self.facing_left and self._sprite_flipped is not None else self._sprite_scaled
        surface.blit(sprite, self.rect)

    @staticmethod
    def _load_sprite() -> pygame.Surface | None:
        import os
        import glob

        def try_load(path: str) -> pygame.Surface | None:
            try:
                return pygame.image.load(path).convert_alpha()
            except Exception:
                return None

        # Try configured path first
        sprite = try_load(PLAYER_SPRITE_PATH)
        if sprite is not None:
            return sprite

        # Fallback: search assets folder and choose best match by filename tokens
        import re
        assets_dir = os.path.dirname(PLAYER_SPRITE_PATH) or "assets"
        desired_tokens = {"player", "idle", "stay", "rex", "hero"}

        candidates = [f for f in glob.glob(os.path.join(assets_dir, "*.*"))]
        best_candidate = None
        best_score = 0
        for candidate in candidates:
            base = os.path.basename(candidate)
            name = os.path.splitext(base)[0].lower()
            tokens = set(re.findall(r"[A-Za-z0-9]+", name))
            score = len(tokens & desired_tokens)
            if score > best_score:
                # try loading before committing
                sprite = try_load(candidate)
                if sprite is not None:
                    best_score = score
                    best_candidate = (candidate, sprite)
        # If we found a scored candidate, return it
        if best_candidate is not None:
            print(f"[INFO] Player sprite loaded from {best_candidate[0]}")
            return best_candidate[1]

        # As a last resort, try any image file (excluding obvious map files)
        for candidate in candidates:
            if "map" in candidate.lower():
                continue
            sprite = try_load(candidate)
            if sprite is not None:
                print(f"[INFO] Player sprite loaded from {candidate}")
                return sprite
        return None