from __future__ import annotations

import pygame

from src.food import Food
from src.player import Player
from src.enemy import Enemy
from src.level import Level
from src.projectile import Projectile
from src.settings import (
    BACKGROUND_COLOR,
    EXIT_COLOR,
    FPS,
    GAME_TITLE,
    HELP_TEXT,
    OBSTACLE_COLOR,
    TEXT_COLOR,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    LEVEL_MAX_NUMBER,
    LEVEL_TRANSITION_DELAY_MS,
    BUSH_COLOR,
    BUSH_ALPHA,
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

        self.level = Level()
        self.player.reset_position()
        self.player.rect.center = self.level.start_pos
        self.player.pos_x = float(self.player.rect.x)
        self.player.pos_y = float(self.player.rect.y)
        self.enemies = [Enemy((x, y), enemy_type) for x, y, enemy_type in self.level.enemy_spawns]
        self.projectiles: list[Projectile] = []
        self.level_food = 0
        self.state = "playing"
        self.level_complete_started_ms: int | None = None
        self.food.reposition(self.level.obstacles + [self.level.exit_rect])

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif self.state == "playing" and event.key == pygame.K_SPACE:
                    self._player_bite()
                elif self.state == "game_over":
                    if event.key == pygame.K_r:
                        self._restart()
                    elif event.key == pygame.K_q:
                        self.running = False

    def _update(self, dt: float) -> None:
        now_ms = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        self.player.update(keys, dt, self.level.obstacles, now_ms)

        if self.player.rect.colliderect(self.food.rect):
            self.score += 1
            self.level_food += 1
            self.player.collect_food()
            self.food.reposition(self.level.obstacles + [self.level.exit_rect])

        if self.player.rect.colliderect(self.level.exit_rect):
            self.state = "level_complete"
            self.level_complete_started_ms = now_ms

        for enemy in self.enemies:
            attack_payload = enemy.update(now_ms, self.player.rect.center, self.level.obstacles, self.level.bushes)
            if attack_payload is not None:
                projectile_pos, projectile_dir, stun_ms = attack_payload
                # store owner center so we can check bush ownership for collisions
                self.projectiles.append(Projectile(projectile_pos, projectile_dir, stun_ms, owner_center=enemy.rect.center))
            if enemy.enemy_type == "melee" and self.player.rect.colliderect(enemy.rect) and enemy.state == "attack":
                # If player is in a bush and enemy isn't in the same bush, ignore damage
                player_bush = self.level.bush_for_point(self.player.rect.center)
                if player_bush is not None and not player_bush.collidepoint(enemy.rect.center):
                    continue
                if self.player.take_hit(now_ms, enemy.contact_damage):
                    if self.player.current_hp <= 0:
                        self.state = "game_over"
                    else:
                        self.player.reset_position()
                        self.player.rect.center = self.level.start_pos
                        self.player.pos_x = float(self.player.rect.x)
                        self.player.pos_y = float(self.player.rect.y)

        alive_projectiles: list[Projectile] = []
        for projectile in self.projectiles:
            projectile.update(dt)
            if self._projectile_hits_wall(projectile):
                continue
            if not self._inside_world(projectile.rect):
                continue
            if projectile.rect.colliderect(self.player.rect):
                # If player is inside a bush and projectile owner isn't in same bush, ignore
                player_bush = self.level.bush_for_point(self.player.rect.center)
                owner_bush = None
                if getattr(projectile, "owner_center", None) is not None:
                    owner_bush = self.level.bush_for_point(projectile.owner_center)
                if player_bush is not None and owner_bush is not player_bush:
                    continue
                if self.player.take_hit(now_ms, projectile.damage):
                    if projectile.stun_ms > 0:
                        self.player.apply_stun(now_ms, projectile.stun_ms)
                    if self.player.current_hp <= 0:
                        self.state = "game_over"
                continue
            alive_projectiles.append(projectile)
        self.projectiles = alive_projectiles

    def _update_level_complete(self) -> None:
        if self.level_complete_started_ms is None:
            self.level_complete_started_ms = pygame.time.get_ticks()
            return
        now_ms = pygame.time.get_ticks()
        if now_ms - self.level_complete_started_ms >= LEVEL_TRANSITION_DELAY_MS:
            self._advance_level()

    def _draw(self) -> None:
        self.screen.fill(BACKGROUND_COLOR)

        pygame.draw.rect(self.screen, EXIT_COLOR, self.level.exit_rect, border_radius=6)
        for obstacle in self.level.obstacles:
            pygame.draw.rect(self.screen, OBSTACLE_COLOR, obstacle, border_radius=6)

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
        objective_surface = self.small_font.render(
            "Objective: reach blue exit to finish level",
            True,
            TEXT_COLOR,
        )

        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20))
        help_rect = help_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
        score_rect = score_surface.get_rect(topleft=(16, 16))
        size_rect = size_surface.get_rect(topleft=(16, 42))
        health_rect = health_surface.get_rect(topright=(WINDOW_WIDTH - 16, 16))
        stamina_rect = stamina_surface.get_rect(topright=(WINDOW_WIDTH - 16, 42))
        bite_rect = bite_surface.get_rect(topleft=(16, 68))
        level_rect = level_surface.get_rect(center=(WINDOW_WIDTH // 2, 24))
        objective_rect = objective_surface.get_rect(center=(WINDOW_WIDTH // 2, 50))

        self.screen.blit(title_surface, title_rect)
        self.screen.blit(help_surface, help_rect)
        self.screen.blit(score_surface, score_rect)
        self.screen.blit(size_surface, size_rect)
        self.screen.blit(health_surface, health_rect)
        self.screen.blit(stamina_surface, stamina_rect)
        self.screen.blit(bite_surface, bite_rect)
        self.screen.blit(level_surface, level_rect)
        self.screen.blit(objective_surface, objective_rect)
        self.food.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        for projectile in self.projectiles:
            projectile.draw(self.screen)
        self.player.draw(self.screen)

        # Draw bushes as semi-transparent overlays (on top of player/enemies)
        for bush in self.level.bushes:
            try:
                bush_surf = pygame.Surface(bush.size, pygame.SRCALPHA)
                bush_surf.fill((*BUSH_COLOR, BUSH_ALPHA))
                self.screen.blit(bush_surf, bush.topleft)
            except Exception:
                # Fallback: draw opaque rect if alpha surface creation fails
                pygame.draw.rect(self.screen, BUSH_COLOR, bush, border_radius=6)

        if self.state == "level_complete":
            overlay = self.font.render(
                f"Level {self.level.number} complete! Next level loading...",
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
            elif self.state == "level_complete":
                self._update_level_complete()
            self._draw()

            frame_count += 1
            if max_frames is not None and frame_count >= max_frames:
                self.running = False

        pygame.quit()

    def _advance_level(self) -> None:
        if self.level.number >= LEVEL_MAX_NUMBER:
            self.state = "game_over"
            return

        self.level.advance()
        self.level_food = 0
        self.player.reset_position()
        self.player.rect.center = self.level.start_pos
        self.player.pos_x = float(self.player.rect.x)
        self.player.pos_y = float(self.player.rect.y)
        self.enemies = [Enemy((x, y), enemy_type) for x, y, enemy_type in self.level.enemy_spawns]
        self.projectiles = []
        self.food.reposition(self.level.obstacles + [self.level.exit_rect])
        self.state = "playing"
        self.level_complete_started_ms = None

    def _restart(self) -> None:
        self.level = Level()
        self.level_food = 0
        self.score = 0
        self.player.reset()
        self.player.rect.center = self.level.start_pos
        self.player.pos_x = float(self.player.rect.x)
        self.player.pos_y = float(self.player.rect.y)
        self.enemies = [Enemy((x, y), enemy_type) for x, y, enemy_type in self.level.enemy_spawns]
        self.projectiles = []
        self.food.reposition(self.level.obstacles + [self.level.exit_rect])
        self.state = "playing"
        self.level_complete_started_ms = None

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

    @staticmethod
    def _inside_world(rect: pygame.Rect) -> bool:
        return rect.right >= 0 and rect.left <= WINDOW_WIDTH and rect.bottom >= 0 and rect.top <= WINDOW_HEIGHT

    def _projectile_hits_wall(self, projectile: Projectile) -> bool:
        return any(projectile.rect.colliderect(obstacle) for obstacle in self.level.obstacles)