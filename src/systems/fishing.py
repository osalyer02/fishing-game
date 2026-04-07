"""Fishing resolution pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from constants import (
    BOSS_MONSTER_ID,
    CATEGORY_FISH,
    CATEGORY_JUNK,
    CATEGORY_MONSTER,
    CATEGORY_TREASURE,
    FINAL_ROD_ID,
    ROD_TIER_TO_MONSTER_TIER,
)
from game.rng import GameRng
from game.state import ContentDatabase, GameState, Monster
from systems.loot_tables import choose_fish, choose_junk, choose_treasure, normalize_category_weights


@dataclass
class CatchResult:
    category: str
    item_id: str | None = None
    item_name: str | None = None
    sell_value: int = 0
    monster: Monster | None = None
    message: str = ""


def _apply_powerup_probabilities(
    base_weights: dict[str, float],
    powerup_ids: list[str],
    content: ContentDatabase,
) -> dict[str, float]:
    adjusted = dict(base_weights)
    for powerup_id in powerup_ids:
        powerup = content.powerups.get(powerup_id)
        if not powerup:
            continue
        for key, delta in powerup.category_delta.items():
            adjusted[key] = adjusted.get(key, 0.0) + delta
    return normalize_category_weights(adjusted)


def _roll_category(state: GameState, content: ContentDatabase, rng: GameRng) -> str:
    rod = content.get_rod(state.equipped_rod_id)
    weights = _apply_powerup_probabilities(rod.category_weights, state.active_powerups, content)
    table = [(key, weights[key]) for key in ("fish", "treasure", "junk", "monster")]
    return str(rng.weighted_choice(table))


def resolve_monster_encounter(state: GameState, content: ContentDatabase, rng: GameRng) -> Monster:
    rod = content.get_rod(state.equipped_rod_id)

    if rod.id == FINAL_ROD_ID and not state.boss_defeated and not state.boss_spawned:
        state.boss_spawned = True
        return content.monsters[BOSS_MONSTER_ID]

    max_tier = ROD_TIER_TO_MONSTER_TIER.get(rod.tier, 1)
    candidates = [m for m in content.monsters.values() if (not m.boss) and m.tier <= max_tier]
    weighted = [(m, 1.0 + (m.tier * 0.25) + (m.reward / 100.0)) for m in candidates]
    return rng.weighted_choice(weighted)


def cast_line(state: GameState, content: ContentDatabase, rng: GameRng) -> CatchResult:
    if state.casts_remaining <= 0:
        return CatchResult(category="none", message="No casts left today. Visit the shop and end your day.")

    state.casts_remaining -= 1
    category = _roll_category(state, content, rng)

    if category == CATEGORY_FISH:
        fish = choose_fish(content, content.get_rod(state.equipped_rod_id), rng)
        state.inventory.add_item(CATEGORY_FISH, fish.id)
        return CatchResult(
            category=CATEGORY_FISH,
            item_id=fish.id,
            item_name=fish.name,
            sell_value=fish.sell_value,
            message=f"Caught fish: {fish.name} (value {fish.sell_value})",
        )

    if category == CATEGORY_TREASURE:
        treasure = choose_treasure(content, content.get_rod(state.equipped_rod_id), rng)
        state.inventory.add_item(CATEGORY_TREASURE, treasure.id)
        return CatchResult(
            category=CATEGORY_TREASURE,
            item_id=treasure.id,
            item_name=treasure.name,
            sell_value=treasure.sell_value,
            message=f"Recovered treasure: {treasure.name} (value {treasure.sell_value})",
        )

    if category == CATEGORY_JUNK:
        junk = choose_junk(content, rng)
        state.inventory.add_item(CATEGORY_JUNK, junk.id)
        return CatchResult(
            category=CATEGORY_JUNK,
            item_id=junk.id,
            item_name=junk.name,
            sell_value=junk.sell_value,
            message=f"Pulled up junk: {junk.name} (value {junk.sell_value})",
        )

    monster = resolve_monster_encounter(state, content, rng)
    return CatchResult(
        category=CATEGORY_MONSTER,
        item_id=monster.id,
        item_name=monster.name,
        sell_value=monster.reward,
        monster=monster,
        message=f"A monster strikes: {monster.name}!",
    )
