from __future__ import annotations

from src.settings import LEVEL_BASE_TARGET, LEVEL_TARGET_INCREMENT


class Level:
    def __init__(self, number: int = 1) -> None:
        self.number = number
        self.target = LEVEL_BASE_TARGET + (self.number - 1) * LEVEL_TARGET_INCREMENT

    def advance(self) -> None:
        self.number += 1
        self.target = LEVEL_BASE_TARGET + (self.number - 1) * LEVEL_TARGET_INCREMENT
