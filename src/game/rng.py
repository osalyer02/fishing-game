"""Seedable RNG wrapper for deterministic tests."""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class GameRng:
    seed: int | None = None

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def random(self) -> float:
        return self._rng.random()

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)

    def choice(self, seq):
        return self._rng.choice(seq)

    def weighted_choice(self, items: list[tuple[object, float]]):
        total = sum(weight for _, weight in items)
        if total <= 0:
            raise ValueError("Weighted choice requires positive total weight")
        roll = self.random() * total
        running = 0.0
        for item, weight in items:
            running += weight
            if roll <= running:
                return item
        return items[-1][0]
