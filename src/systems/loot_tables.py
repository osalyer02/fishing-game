"""Loot selection helpers and rarity-weight tuning."""

from __future__ import annotations

from collections import defaultdict

from constants import RARITY_WEIGHTS
from game.rng import GameRng
from game.state import ContentDatabase, Fish, Rod


def adjusted_rarity_weights(rod: Rod) -> dict[str, float]:
    weights = dict(RARITY_WEIGHTS)
    total_target = sum(weights.values())

    non_common_keys = [k for k in weights if k != "common"]
    multiplier = 1.0 + (rod.fish_rarity_bonus / 100.0)
    for key in non_common_keys:
        weights[key] *= multiplier

    non_common_total = sum(weights[key] for key in non_common_keys)
    weights["common"] = max(0.01, total_target - non_common_total)
    return weights


def choose_fish(content: ContentDatabase, rod: Rod, rng: GameRng) -> Fish:
    by_rarity: dict[str, list[Fish]] = defaultdict(list)
    for fish in content.fish.values():
        by_rarity[fish.rarity].append(fish)

    rarity_weights = adjusted_rarity_weights(rod)
    rarity = rng.weighted_choice([(name, weight) for name, weight in rarity_weights.items()])
    return rng.choice(by_rarity[rarity])


def choose_treasure(content: ContentDatabase, rod: Rod, rng: GameRng):
    options = [t for t in content.treasure.values() if t.min_rod_tier <= rod.tier]
    weighted: list[tuple[object, float]] = []
    for item in options:
        quality_push = 1.0 + (rod.tier - item.min_rod_tier) * 0.3
        value_push = 1.0 + (item.sell_value / 400.0)
        weighted.append((item, max(0.1, quality_push * value_push)))
    return rng.weighted_choice(weighted)


def choose_junk(content: ContentDatabase, rng: GameRng):
    return rng.choice(list(content.junk.values()))


def normalize_category_weights(weights: dict[str, float]) -> dict[str, float]:
    safe = {k: max(0.0, v) for k, v in weights.items()}
    total = sum(safe.values())
    if total <= 0:
        return {"fish": 55.0, "treasure": 5.0, "junk": 35.0, "monster": 5.0}
    return {k: (v / total) * 100.0 for k, v in safe.items()}
