"""Load immutable game content from JSON files."""

from __future__ import annotations

import json
from pathlib import Path

from game.state import ContentDatabase, Fish, Junk, Monster, PowerUp, Rod, Treasure, Weapon


CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"


def _load_json(filename: str) -> list[dict]:
    with (CONTENT_DIR / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_content() -> ContentDatabase:
    rod_rows = _load_json("rods.json")
    weapon_rows = _load_json("weapons.json")
    fish_rows = _load_json("fish.json")
    treasure_rows = _load_json("treasure.json")
    junk_rows = _load_json("junk.json")
    monster_rows = _load_json("monsters.json")
    powerup_rows = _load_json("powerups.json")

    rods = {
        row["id"]: Rod(
            id=row["id"],
            name=row["name"],
            tier=int(row["tier"]),
            cost=int(row["cost"]),
            fish_rarity_bonus=int(row["fish_rarity_bonus"]),
            category_weights={k: float(v) for k, v in row["category_weights"].items()},
        )
        for row in rod_rows
    }
    weapons = {
        row["id"]: Weapon(
            id=row["id"],
            name=row["name"],
            cost=int(row["cost"]),
            min_damage=int(row["min_damage"]),
            max_damage=int(row["max_damage"]),
        )
        for row in weapon_rows
    }
    fish = {
        row["id"]: Fish(
            id=row["id"],
            name=row["name"],
            rarity=row["rarity"],
            sell_value=int(row["sell_value"]),
        )
        for row in fish_rows
    }
    treasure = {
        row["id"]: Treasure(
            id=row["id"],
            name=row["name"],
            sell_value=int(row["sell_value"]),
            min_rod_tier=int(row["min_rod_tier"]),
        )
        for row in treasure_rows
    }
    junk = {
        row["id"]: Junk(
            id=row["id"],
            name=row["name"],
            sell_value=int(row["sell_value"]),
        )
        for row in junk_rows
    }
    monsters = {
        row["id"]: Monster(
            id=row["id"],
            name=row["name"],
            tier=int(row["tier"]),
            hp=int(row["hp"]),
            attack=int(row["attack"]),
            reward=int(row["reward"]),
            boss=bool(row.get("boss", False)),
        )
        for row in monster_rows
    }
    powerups = {
        row["id"]: PowerUp(
            id=row["id"],
            name=row["name"],
            cost=int(row["cost"]),
            description=row["description"],
            category_delta={k: float(v) for k, v in row.get("category_delta", {}).items()},
            weapon_damage_bonus=int(row.get("weapon_damage_bonus", 0)),
        )
        for row in powerup_rows
    }

    rod_order = [row["id"] for row in sorted(rod_rows, key=lambda r: int(r["tier"]))]
    weapon_order = [
        row["id"]
        for row in sorted(
            weapon_rows,
            key=lambda w: (int(w["min_damage"] + w["max_damage"]), int(w["cost"])),
        )
    ]

    return ContentDatabase(
        rods=rods,
        weapons=weapons,
        fish=fish,
        treasure=treasure,
        junk=junk,
        monsters=monsters,
        powerups=powerups,
        rod_order=rod_order,
        weapon_order=weapon_order,
    )
