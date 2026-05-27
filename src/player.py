from __future__ import annotations

import pygame

from src.settings import (
    PLAYER_COLOR,
    PLAYER_GROWTH_STAGES,
    PLAYER_HIT_INVULNERABILITY_MS,
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

        self.speed = 0.0
        self.max_hp = 0
        self.current_hp = 0
        self.bite_damage = 0
        self.bite_range = 0
        self.bite_cooldown_ms = 0
        self.bite_stun_ms = 0
        self.sprint_multiplier = 1.0
        self._apply_stage(self.stage_index, keep_hp_ratio=False)

    def update(self, keys: pygame.key.ScancodeWrapper, dt: float) -> None:
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
        can_sprint = sprint_pressed and is_moving and self.stamina > 0.0
        speed = self.speed * (self.sprint_multiplier if can_sprint else 1.0)

        if is_moving:
            vector_length = (move_x * move_x + move_y * move_y) ** 0.5
            move_x /= vector_length
            move_y /= vector_length
            self.pos_x += move_x * speed * 60.0 * dt
            self.pos_y += move_y * speed * 60.0 * dt

        if can_sprint:
            self.stamina = max(0.0, self.stamina - PLAYER_SPRINT_DRAIN_PER_SECOND * dt)
        else:
            self.stamina = min(
                PLAYER_SPRINT_STAMINA_MAX,
                self.stamina + PLAYER_SPRINT_REGEN_PER_SECOND * dt,
            )

        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)
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

    def reset_position(self) -> None:
        """Return the player to the start position without changing its size."""
        self.rect.centerx = WINDOW_WIDTH // 2
        self.rect.centery = WINDOW_HEIGHT // 2 + 70
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)
        self._clamp_to_window()

    def reset(self) -> None:
        """Reset player to initial size and position."""
        self.food_collected = 0
        self.stage_index = 0
        self.stamina = PLAYER_SPRINT_STAMINA_MAX
        self.last_hit_ms = -PLAYER_HIT_INVULNERABILITY_MS
        self.last_bite_ms = -10_000
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

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, PLAYER_COLOR, self.rect, border_radius=8)