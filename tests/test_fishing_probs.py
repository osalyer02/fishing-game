from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from game.content import load_content
from game.rng import GameRng
from game.state import GameState
from systems.fishing import cast_line


class FishingProbabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.content = load_content()

    def _simulate_average_value(self, rod_id: str, casts: int, seed: int) -> float:
        state = GameState.new_game()
        state.equipped_rod_id = rod_id
        state.casts_remaining = casts
        rng = GameRng(seed)

        total_value = 0
        for _ in range(casts):
            result = cast_line(state, self.content, rng)
            total_value += result.sell_value

        return total_value / casts

    def test_each_rod_category_row_totals_100(self) -> None:
        for rod in self.content.rods.values():
            total = sum(rod.category_weights.values())
            self.assertAlmostEqual(total, 100.0, places=5)

    def test_higher_tier_rod_has_better_average_value(self) -> None:
        twig_avg = self._simulate_average_value("twig_rod", casts=1200, seed=3)
        carbon_avg = self._simulate_average_value("carbon_rod", casts=1200, seed=3)
        self.assertGreater(carbon_avg, twig_avg)


if __name__ == "__main__":
    unittest.main()
