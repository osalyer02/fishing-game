"""Shop transactions for selling and buying."""

from __future__ import annotations

from dataclasses import dataclass

from constants import CATEGORY_FISH, CATEGORY_JUNK, CATEGORY_TREASURE
from game.state import ContentDatabase, GameState


@dataclass
class ShopResult:
    success: bool
    message: str
    amount: int = 0


def _item_value(content: ContentDatabase, category: str, item_id: str) -> int:
    if category == CATEGORY_FISH:
        return content.fish[item_id].sell_value
    if category == CATEGORY_TREASURE:
        return content.treasure[item_id].sell_value
    if category == CATEGORY_JUNK:
        return content.junk[item_id].sell_value
    raise ValueError(f"Unknown category: {category}")


def sell_all_category(state: GameState, content: ContentDatabase, category: str) -> ShopResult:
    sold = state.inventory.clear_category(category)
    if not sold:
        return ShopResult(False, f"No {category} to sell.", 0)

    total = 0
    for item_id, count in sold.items():
        total += _item_value(content, category, item_id) * count

    state.coins += total
    return ShopResult(True, f"Sold all {category} for {total} coins.", total)


def buy_rod(state: GameState, content: ContentDatabase, rod_id: str) -> ShopResult:
    rod = content.rods[rod_id]
    current = content.rods[state.equipped_rod_id]

    if rod.tier <= current.tier:
        return ShopResult(False, "Can only buy a higher-tier rod.")
    if state.coins < rod.cost:
        return ShopResult(False, "Not enough coins for that rod.")

    state.coins -= rod.cost
    state.equipped_rod_id = rod.id
    return ShopResult(True, f"Purchased and equipped {rod.name}.", -rod.cost)


def buy_next_rod(state: GameState, content: ContentDatabase) -> ShopResult:
    next_id = content.next_rod_id(state.equipped_rod_id)
    if not next_id:
        return ShopResult(False, "You already own the best rod.")
    return buy_rod(state, content, next_id)


def buy_weapon(state: GameState, content: ContentDatabase, weapon_id: str) -> ShopResult:
    weapon = content.weapons[weapon_id]
    current = content.weapons[state.equipped_weapon_id]

    if weapon.min_damage <= current.min_damage and weapon.max_damage <= current.max_damage:
        return ShopResult(False, "Can only buy a stronger weapon.")
    if state.coins < weapon.cost:
        return ShopResult(False, "Not enough coins for that weapon.")

    state.coins -= weapon.cost
    state.equipped_weapon_id = weapon.id
    return ShopResult(True, f"Purchased and equipped {weapon.name}.", -weapon.cost)


def buy_next_weapon(state: GameState, content: ContentDatabase) -> ShopResult:
    next_id = content.next_weapon_id(state.equipped_weapon_id)
    if not next_id:
        return ShopResult(False, "You already own the best weapon.")
    return buy_weapon(state, content, next_id)


def buy_powerup(state: GameState, content: ContentDatabase, powerup_id: str) -> ShopResult:
    powerup = content.powerups[powerup_id]

    if powerup.id in state.active_powerups:
        return ShopResult(False, "That power-up is already active today.")
    if state.coins < powerup.cost:
        return ShopResult(False, "Not enough coins for that power-up.")

    state.coins -= powerup.cost
    state.active_powerups.append(powerup.id)
    return ShopResult(True, f"Activated {powerup.name} for the day.", -powerup.cost)
