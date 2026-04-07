from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from game.content import load_content
from game.rng import GameRng
from game.state import GameState
from systems.combat import player_attack, start_encounter


class CombatOutcomeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.content = load_content()

    def test_player_can_defeat_tier1_monster(self) -> None:
        state = GameState.new_game()
        state.equipped_weapon_id = "iron_spear"
        rng = GameRng(7)

        monster = self.content.monsters["river_slime"]
        encounter = start_encounter(monster)

        turns = 0
        while not encounter.finished and turns < 20:
            result = player_attack(state, encounter, self.content, rng)
            turns += 1

        self.assertTrue(encounter.finished)
        self.assertTrue(encounter.player_won)
        self.assertGreaterEqual(state.coins, monster.reward)


if __name__ == "__main__":
    unittest.main()
