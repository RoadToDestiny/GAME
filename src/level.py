from __future__ import annotations

import pygame

from src.settings import LEVEL_BASE_TARGET, LEVEL_TARGET_INCREMENT


class Level:
    def __init__(self, number: int = 1) -> None:
        self.number = number
        self.target = self._compute_target(self.number)
        self.start_pos = (80, 270)
        self.exit_rect = pygame.Rect(900, 200, 36, 140)
        self.obstacles = self._build_obstacles(self.number)
        self.enemy_spawns = self._build_enemy_spawns(self.number)

    def advance(self) -> None:
        self.number += 1
        self.target = self._compute_target(self.number)
        self.obstacles = self._build_obstacles(self.number)
        self.enemy_spawns = self._build_enemy_spawns(self.number)

    @staticmethod
    def _compute_target(level_number: int) -> int:
        delta = level_number - 1
        return LEVEL_BASE_TARGET + delta * LEVEL_TARGET_INCREMENT + (delta * delta) // 2

    @staticmethod
    def _build_obstacles(level_number: int) -> list[pygame.Rect]:
        base = [
            pygame.Rect(180, 80, 70, 260),
            pygame.Rect(330, 250, 80, 220),
            pygame.Rect(500, 60, 80, 260),
            pygame.Rect(660, 220, 90, 220),
        ]
        if level_number >= 3:
            base.append(pygame.Rect(780, 60, 65, 210))
        if level_number >= 5:
            base.append(pygame.Rect(420, 0, 60, 140))
        return base

    @staticmethod
    def _build_enemy_spawns(level_number: int) -> list[tuple[int, int, str]]:
        spawns: list[tuple[int, int, str]] = [(260, 420, "melee"), (560, 420, "melee")]
        if level_number >= 2:
            spawns.append((430, 120, "shooter"))
        if level_number >= 4:
            spawns.append((720, 120, "stunner"))
        if level_number >= 6:
            spawns.append((820, 430, "shooter"))
        return spawns
