"""Shared constants for the game."""

SAVE_VERSION = 1
STARTING_DAY = 1
STARTING_COINS = 0
CASTS_PER_DAY = 5
STARTING_MAX_HP = 100
STARTING_ROD_ID = "twig_rod"
STARTING_WEAPON_ID = "driftwood_club"
FINAL_ROD_ID = "leviathan_rod"
BOSS_MONSTER_ID = "kraken_sovereign"

CATEGORY_FISH = "fish"
CATEGORY_TREASURE = "treasure"
CATEGORY_JUNK = "junk"
CATEGORY_MONSTER = "monster"

CATEGORIES = (CATEGORY_FISH, CATEGORY_TREASURE, CATEGORY_JUNK, CATEGORY_MONSTER)

RARITY_WEIGHTS = {
    "common": 50.0,
    "uncommon": 28.0,
    "rare": 14.0,
    "epic": 6.0,
    "legendary": 2.0,
    "mythic": 0.4,
}

ROD_TIER_TO_MONSTER_TIER = {
    1: 1,
    2: 1,
    3: 2,
    4: 2,
    5: 3,
    6: 3,
}
