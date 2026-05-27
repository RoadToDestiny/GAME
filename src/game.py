from __future__ import annotations

import pygame

from src.food import Food
from src.player import Player
from src.enemy import Enemy
from src.settings import (
    BACKGROUND_COLOR,
    FPS,
    GAME_TITLE,
    HELP_TEXT,
    TEXT_COLOR,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    INITIAL_LIVES,
    ENEMY_INITIAL_COUNT,
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
        self.lives = INITIAL_LIVES

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def _update(self) -> None:
        keys = pygame.key.get_pressed()
        self.player.update(keys)

        if self.player.rect.colliderect(self.food.rect):
            self.score += 1
            self.player.grow()
            self.food.reposition()

        for enemy in self.enemies:
            enemy.update()
            if self.player.rect.colliderect(enemy.rect):
                self.lives -= 1
                enemy.reposition()
                # reset player to start position without changing its size
                self.player.reset_position()
                if self.lives <= 0:
                    self.running = False

    def _draw(self) -> None:
        self.screen.fill(BACKGROUND_COLOR)

        title_surface = self.font.render(GAME_TITLE, True, TEXT_COLOR)
        help_surface = self.small_font.render(HELP_TEXT, True, TEXT_COLOR)
        score_surface = self.small_font.render(f"Food: {self.score}", True, TEXT_COLOR)
        size_surface = self.small_font.render(f"Size: {self.player.rect.width}", True, TEXT_COLOR)
        lives_surface = self.small_font.render(f"Lives: {self.lives}", True, TEXT_COLOR)

        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20))
        help_rect = help_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
        score_rect = score_surface.get_rect(topleft=(16, 16))
        size_rect = size_surface.get_rect(topleft=(16, 42))
        lives_rect = lives_surface.get_rect(topright=(WINDOW_WIDTH - 16, 16))

        self.screen.blit(title_surface, title_rect)
        self.screen.blit(help_surface, help_rect)
        self.screen.blit(score_surface, score_rect)
        self.screen.blit(size_surface, size_rect)
        self.screen.blit(lives_surface, lives_rect)
        self.food.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        self.player.draw(self.screen)
        pygame.display.flip()

    def run(self, max_frames: int | None = None) -> None:
        frame_count = 0

        while self.running:
            self._handle_events()
            self._update()
            self._draw()
            self.clock.tick(FPS)

            frame_count += 1
            if max_frames is not None and frame_count >= max_frames:
                self.running = False

        pygame.quit()