from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from game.content import load_content
from game.state import GameState
from systems.shop import buy_next_rod, sell_all_category


class ShopTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.content = load_content()

    def test_sell_all_fish_matches_exact_values(self) -> None:
        state = GameState.new_game()
        state.inventory.fish = {"bluegill": 2, "carp": 1}

        result = sell_all_category(state, self.content, "fish")

        self.assertTrue(result.success)
        self.assertEqual(result.amount, 28)  # 2*8 + 1*12
        self.assertEqual(state.coins, 28)
        self.assertEqual(state.inventory.fish, {})

    def test_cannot_buy_rod_if_insufficient_coins(self) -> None:
        state = GameState.new_game()
        state.coins = 50

        result = buy_next_rod(state, self.content)

        self.assertFalse(result.success)
        self.assertEqual(state.equipped_rod_id, "twig_rod")
        self.assertEqual(state.coins, 50)


if __name__ == "__main__":
    unittest.main()
