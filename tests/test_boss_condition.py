from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from game.content import load_content
from game.rng import GameRng
from game.state import GameState
from systems.fishing import resolve_monster_encounter


class BossConditionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.content = load_content()

    def test_boss_only_spawns_once_with_final_rod(self) -> None:
        state = GameState.new_game()
        state.equipped_rod_id = "leviathan_rod"
        rng = GameRng(99)

        first = resolve_monster_encounter(state, self.content, rng)
        second = resolve_monster_encounter(state, self.content, rng)

        self.assertTrue(first.boss)
        self.assertEqual(first.id, "kraken_sovereign")
        self.assertTrue(state.boss_spawned)
        self.assertFalse(second.boss)


if __name__ == "__main__":
    unittest.main()
