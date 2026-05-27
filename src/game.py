from __future__ import annotations

import pygame

from src.food import Food
from src.player import Player
from src.enemy import Enemy
from src.level import Level
from src.settings import (
    BACKGROUND_COLOR,
    FPS,
    GAME_TITLE,
    HELP_TEXT,
    TEXT_COLOR,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    ENEMY_INITIAL_COUNT,
    LEVEL_ENEMY_INCREMENT,
    LEVEL_MAX_NUMBER,
)


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.Font(None, 40)
        self.small_font = pygame.font.Font(None, 28)

        self.player = Player()
        self.food = Food()
        self.score = 0
        self.enemies = [Enemy() for _ in range(ENEMY_INITIAL_COUNT)]

        self.level = Level()
        self.level_food = 0
        self.state = "playing"  # playing | level_complete | game_over

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif self.state == "playing" and event.key == pygame.K_SPACE:
                    self._player_bite()
                elif self.state == "level_complete":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._advance_level()
                elif self.state == "game_over":
                    if event.key == pygame.K_r:
                        self._restart()
                    elif event.key == pygame.K_q:
                        self.running = False

    def _update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        self.player.update(keys, dt)
        now_ms = pygame.time.get_ticks()

        if self.player.rect.colliderect(self.food.rect):
            self.score += 1
            self.level_food += 1
            self.player.collect_food()
            self.food.reposition()
            if self.level_food >= self.level.target:
                self.state = "level_complete"

        for enemy in self.enemies:
            enemy.update(now_ms)
            if self.player.rect.colliderect(enemy.rect):
                if self.player.take_hit(now_ms):
                    enemy.reposition()
                    # reset player to start position without changing its stage
                    self.player.reset_position()
                    if self.player.current_hp <= 0:
                        self.state = "game_over"

    def _draw(self) -> None:
        self.screen.fill(BACKGROUND_COLOR)

        title_surface = self.font.render(GAME_TITLE, True, TEXT_COLOR)
        help_surface = self.small_font.render(HELP_TEXT, True, TEXT_COLOR)
        score_surface = self.small_font.render(f"Food: {self.score}", True, TEXT_COLOR)
        size_surface = self.small_font.render(f"Size: {self.player.rect.width}", True, TEXT_COLOR)
        health_surface = self.small_font.render(
            f"HP: {self.player.current_hp}/{self.player.max_hp}",
            True,
            TEXT_COLOR,
        )
        stamina_surface = self.small_font.render(
            f"Stamina: {int(self.player.stamina)}",
            True,
            TEXT_COLOR,
        )
        bite_surface = self.small_font.render(
            f"Bite dmg/range: {self.player.bite_damage}/{self.player.bite_range}",
            True,
            TEXT_COLOR,
        )
        level_surface = self.small_font.render(
            f"Level {self.level.number}: {self.level_food}/{self.level.target}", True, TEXT_COLOR
        )

        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20))
        help_rect = help_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
        score_rect = score_surface.get_rect(topleft=(16, 16))
        size_rect = size_surface.get_rect(topleft=(16, 42))
        health_rect = health_surface.get_rect(topright=(WINDOW_WIDTH - 16, 16))
        stamina_rect = stamina_surface.get_rect(topright=(WINDOW_WIDTH - 16, 42))
        bite_rect = bite_surface.get_rect(topleft=(16, 68))
        level_rect = level_surface.get_rect(center=(WINDOW_WIDTH // 2, 24))

        self.screen.blit(title_surface, title_rect)
        self.screen.blit(help_surface, help_rect)
        self.screen.blit(score_surface, score_rect)
        self.screen.blit(size_surface, size_rect)
        self.screen.blit(health_surface, health_rect)
        self.screen.blit(stamina_surface, stamina_rect)
        self.screen.blit(bite_surface, bite_rect)
        self.screen.blit(level_surface, level_rect)
        self.food.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        self.player.draw(self.screen)

        # Overlay screens
        if self.state == "level_complete":
            overlay = self.font.render(
                f"Level {self.level.number} complete! Press Enter to continue",
                True,
                TEXT_COLOR,
            )
            rect = overlay.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.screen.blit(overlay, rect)

        if self.state == "game_over":
            overlay = self.font.render("Game Over - Press R to restart or Q to quit", True, TEXT_COLOR)
            rect = overlay.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.screen.blit(overlay, rect)

        pygame.display.flip()

    def run(self, max_frames: int | None = None) -> None:
        frame_count = 0

        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            if self.state == "playing":
                self._update(dt)
            self._draw()

            frame_count += 1
            if max_frames is not None and frame_count >= max_frames:
                self.running = False

        pygame.quit()

    def _advance_level(self) -> None:
        # Move to the next level, increase difficulty and reset per-level counters
        if self.level.number >= LEVEL_MAX_NUMBER:
            # final level reached - for now treat as game over/win
            self.state = "game_over"
            return

        self.level.advance()
        # add a bit more challenge
        for _ in range(LEVEL_ENEMY_INCREMENT):
            self.enemies.append(Enemy())

        self.level_food = 0
        self.player.reset_position()
        self.food.reposition()
        self.state = "playing"

    def _restart(self) -> None:
        # Reset game to initial state
        self.level = Level()
        self.level_food = 0
        self.score = 0
        self.player.reset()
        self.enemies = [Enemy() for _ in range(ENEMY_INITIAL_COUNT)]
        self.food.reposition()
        self.state = "playing"

    def _player_bite(self) -> None:
        now_ms = pygame.time.get_ticks()
        bite_info = self.player.try_bite(now_ms)
        if bite_info is None:
            return

        bite_range, bite_damage, bite_stun_ms = bite_info
        px, py = self.player.rect.center
        alive_enemies: list[Enemy] = []

        for enemy in self.enemies:
            ex, ey = enemy.rect.center
            dx = ex - px
            dy = ey - py
            total_range = bite_range + enemy.rect.width // 2
            if dx * dx + dy * dy <= total_range * total_range:
                enemy_died = enemy.take_damage(bite_damage, now_ms, bite_stun_ms)
                if enemy_died:
                    self.score += 2
                    continue
            alive_enemies.append(enemy)

        self.enemies = alive_enemies