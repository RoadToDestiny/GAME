from __future__ import annotations

from src.settings import LEVEL_BASE_TARGET, LEVEL_TARGET_INCREMENT


class Level:
    def __init__(self, number: int = 1) -> None:
        self.number = number
        self.target = self._compute_target(self.number)

    def advance(self) -> None:
        self.number += 1
        self.target = self._compute_target(self.number)

    @staticmethod
    def _compute_target(level_number: int) -> int:
        delta = level_number - 1
        # Non-linear progression keeps late levels noticeably harder.
        return LEVEL_BASE_TARGET + delta * LEVEL_TARGET_INCREMENT + (delta * delta) // 2
