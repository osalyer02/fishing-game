"""Economy helpers."""

from __future__ import annotations

from constants import CATEGORY_FISH, CATEGORY_JUNK, CATEGORY_TREASURE
from game.state import ContentDatabase, GameState


def inventory_value(state: GameState, content: ContentDatabase) -> int:
    total = 0

    for item_id, count in state.inventory.fish.items():
        total += content.fish[item_id].sell_value * count
    for item_id, count in state.inventory.treasure.items():
        total += content.treasure[item_id].sell_value * count
    for item_id, count in state.inventory.junk.items():
        total += content.junk[item_id].sell_value * count

    return total


def inventory_count_by_category(state: GameState, category: str) -> int:
    if category == CATEGORY_FISH:
        return sum(state.inventory.fish.values())
    if category == CATEGORY_TREASURE:
        return sum(state.inventory.treasure.values())
    if category == CATEGORY_JUNK:
        return sum(state.inventory.junk.values())
    raise ValueError(f"Unknown category: {category}")
