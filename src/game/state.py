"""Dataclasses for runtime game state and static content."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from constants import (
    CASTS_PER_DAY,
    STARTING_COINS,
    STARTING_DAY,
    STARTING_MAX_HP,
    STARTING_ROD_ID,
    STARTING_WEAPON_ID,
)


@dataclass
class Inventory:
    fish: dict[str, int] = field(default_factory=dict)
    treasure: dict[str, int] = field(default_factory=dict)
    junk: dict[str, int] = field(default_factory=dict)

    def add_item(self, category: str, item_id: str, count: int = 1) -> None:
        target = self._bucket(category)
        target[item_id] = target.get(item_id, 0) + count

    def clear_category(self, category: str) -> dict[str, int]:
        target = self._bucket(category)
        sold = dict(target)
        target.clear()
        return sold

    def total_items(self) -> int:
        return sum(self.fish.values()) + sum(self.treasure.values()) + sum(self.junk.values())

    def _bucket(self, category: str) -> dict[str, int]:
        if category == "fish":
            return self.fish
        if category == "treasure":
            return self.treasure
        if category == "junk":
            return self.junk
        raise ValueError(f"Unknown inventory category: {category}")


@dataclass
class GameState:
    day: int
    coins: int
    casts_remaining: int
    player_hp: int
    player_max_hp: int
    equipped_rod_id: str
    equipped_weapon_id: str
    inventory: Inventory
    active_powerups: list[str]
    boss_defeated: bool
    boss_spawned: bool

    @classmethod
    def new_game(cls) -> "GameState":
        return cls(
            day=STARTING_DAY,
            coins=STARTING_COINS,
            casts_remaining=CASTS_PER_DAY,
            player_hp=STARTING_MAX_HP,
            player_max_hp=STARTING_MAX_HP,
            equipped_rod_id=STARTING_ROD_ID,
            equipped_weapon_id=STARTING_WEAPON_ID,
            inventory=Inventory(),
            active_powerups=[],
            boss_defeated=False,
            boss_spawned=False,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "day": self.day,
            "coins": self.coins,
            "casts_remaining": self.casts_remaining,
            "player_hp": self.player_hp,
            "player_max_hp": self.player_max_hp,
            "equipped_rod_id": self.equipped_rod_id,
            "equipped_weapon_id": self.equipped_weapon_id,
            "inventory": asdict(self.inventory),
            "active_powerups": list(self.active_powerups),
            "boss_defeated": self.boss_defeated,
            "boss_spawned": self.boss_spawned,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GameState":
        inv = payload.get("inventory", {})
        return cls(
            day=int(payload.get("day", STARTING_DAY)),
            coins=int(payload.get("coins", STARTING_COINS)),
            casts_remaining=int(payload.get("casts_remaining", CASTS_PER_DAY)),
            player_hp=int(payload.get("player_hp", STARTING_MAX_HP)),
            player_max_hp=int(payload.get("player_max_hp", STARTING_MAX_HP)),
            equipped_rod_id=str(payload.get("equipped_rod_id", STARTING_ROD_ID)),
            equipped_weapon_id=str(payload.get("equipped_weapon_id", STARTING_WEAPON_ID)),
            inventory=Inventory(
                fish=dict(inv.get("fish", {})),
                treasure=dict(inv.get("treasure", {})),
                junk=dict(inv.get("junk", {})),
            ),
            active_powerups=list(payload.get("active_powerups", [])),
            boss_defeated=bool(payload.get("boss_defeated", False)),
            boss_spawned=bool(payload.get("boss_spawned", False)),
        )


@dataclass(frozen=True)
class Rod:
    id: str
    name: str
    tier: int
    cost: int
    fish_rarity_bonus: int
    category_weights: dict[str, float]


@dataclass(frozen=True)
class Weapon:
    id: str
    name: str
    cost: int
    min_damage: int
    max_damage: int


@dataclass(frozen=True)
class Fish:
    id: str
    name: str
    rarity: str
    sell_value: int


@dataclass(frozen=True)
class Treasure:
    id: str
    name: str
    sell_value: int
    min_rod_tier: int


@dataclass(frozen=True)
class Junk:
    id: str
    name: str
    sell_value: int


@dataclass(frozen=True)
class Monster:
    id: str
    name: str
    tier: int
    hp: int
    attack: int
    reward: int
    boss: bool = False


@dataclass(frozen=True)
class PowerUp:
    id: str
    name: str
    cost: int
    description: str
    category_delta: dict[str, float]
    weapon_damage_bonus: int


@dataclass
class ContentDatabase:
    rods: dict[str, Rod]
    weapons: dict[str, Weapon]
    fish: dict[str, Fish]
    treasure: dict[str, Treasure]
    junk: dict[str, Junk]
    monsters: dict[str, Monster]
    powerups: dict[str, PowerUp]

    rod_order: list[str]
    weapon_order: list[str]

    def get_rod(self, rod_id: str) -> Rod:
        return self.rods[rod_id]

    def get_weapon(self, weapon_id: str) -> Weapon:
        return self.weapons[weapon_id]

    def next_rod_id(self, current_rod_id: str) -> str | None:
        idx = self.rod_order.index(current_rod_id)
        if idx + 1 >= len(self.rod_order):
            return None
        return self.rod_order[idx + 1]

    def next_weapon_id(self, current_weapon_id: str) -> str | None:
        idx = self.weapon_order.index(current_weapon_id)
        if idx + 1 >= len(self.weapon_order):
            return None
        return self.weapon_order[idx + 1]
