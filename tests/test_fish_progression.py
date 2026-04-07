from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from game.content import load_content
from game.rng import GameRng
from game.state import GameState
from systems.fishing import cast_line
from systems.loot_tables import choose_fish


class FishProgressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.content = load_content()

    def test_each_rod_tier_has_fish_unlock(self) -> None:
        by_tier = {tier: 0 for tier in range(1, 7)}
        for fish in self.content.fish.values():
            by_tier[fish.min_rod_tier] = by_tier.get(fish.min_rod_tier, 0) + 1

        for tier in range(1, 7):
            self.assertGreater(by_tier.get(tier, 0), 0, f"Expected at least one fish unlock for tier {tier}")

    def test_choose_fish_respects_rod_tier_unlock(self) -> None:
        rod = self.content.get_rod("twig_rod")
        rng = GameRng(seed=11)

        for _ in range(300):
            fish = choose_fish(self.content, rod, rng)
            self.assertLessEqual(fish.min_rod_tier, rod.tier)

    def test_fish_catches_are_recorded_in_diary_counts(self) -> None:
        state = GameState.new_game()
        state.casts_remaining = 200
        rng = GameRng(seed=7)

        for _ in range(200):
            cast_line(state, self.content, rng)

        for fish_id, inv_count in state.inventory.fish.items():
            self.assertEqual(inv_count, state.fish_caught_counts.get(fish_id, 0))


if __name__ == "__main__":
    unittest.main()
