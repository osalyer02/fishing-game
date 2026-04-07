# Fishing RPG (Python) - Full Build Specification

This repository will contain a complete single-player fishing RPG made in Python with simple 8/16-bit style visuals.

The goal of this README is to be implementation-ready: the next task should be to build the entire game directly from this document.

## 1) Game Overview

### Core fantasy
- You fish during the day to catch fish, treasure, junk, or monsters.
- You sell catches and buy upgrades from a shop.
- Better rods unlock better catches but also stronger monsters.
- You buy weapons to defeat monsters encountered while fishing.
- You can fish **5 times per in-game day**.
- You win by acquiring the final rod, fishing up the boss, and defeating it.

### Win/Lose states
- **Win:** Defeat the boss monster spawned by the final rod.
- **Soft fail states:** Running out of useful resources can stall progress, but the player can always continue fishing the next day.
- No permanent game-over is required in v1 (optional for later).

---

## 2) Technical Requirements

### Language and framework
- **Language:** Python 3.11+
- **Rendering/Input:** `pygame` (recommended)
- **Data:** JSON files for balance/content tables
- **Persistence:** JSON save file

### Recommended dependencies
- `pygame`
- `dataclasses` (built-in)
- `typing` (built-in)
- `json`, `random`, `pathlib`, `enum` (built-in)

### Target platforms
- Desktop (macOS/Windows/Linux)
- Windowed mode, fixed internal resolution (e.g. 320x180) with integer scaling

---

## 3) Visual/Audio Direction

### Art style
- Minimal 8/16-bit inspired sprites and tiles.
- Clear silhouettes and readable UI over detail.

### Scope rules
- Keep assets intentionally simple.
- Placeholder art/sound is acceptable in early milestones as long as hooks are clean.

### Screen layout
- Main fishing scene
- Combat overlay/scene
- Shop scene
- Inventory/Status panel
- Day summary popup

---

## 4) Gameplay Loop

1. Start day with 5 casts available.
2. For each cast, roll catch outcome based on rod stats:
   - Fish
   - Treasure
   - Junk
   - Monster
3. If Fish/Treasure/Junk: add to inventory.
4. If Monster: enter combat; must win to keep progressing safely.
5. After casts are spent, visit shop:
   - Sell fish/treasure/junk
   - Buy rod upgrades
   - Buy weapons
   - Buy temporary power-ups
6. End day and advance to next day.
7. Reach final rod -> fish boss encounter -> defeat boss -> win.

---

## 5) Core Systems Spec

### 5.1 Rod Progression

Each rod modifies:
- Catch category probabilities
- Fish rarity weight bonus
- Treasure quality bonus
- Monster strength tier access

### Rod tiers

| Tier | Rod Name | Cost (coins) | Category Bias | Fish Rarity Bonus | Notes |
|---|---:|---:|---:|---:|---|
| 1 | Twig Rod | 0 | High Junk, Low Treasure | +0 | Starter rod |
| 2 | Bamboo Rod | 120 | Less Junk | +5 | Early upgrade |
| 3 | Fiberglass Rod | 350 | Balanced | +12 | Midgame |
| 4 | Carbon Rod | 800 | More Fish/Treasure | +20 | Strong midgame |
| 5 | Master Angler Rod | 1600 | High Treasure, lower Junk | +30 | Endgame prep |
| 6 | Leviathan Rod (Final) | 3000 | Highest value tables | +40 | Enables boss |

> Only the final rod can trigger the boss encounter.

### 5.2 Catch Outcomes

Per cast, first roll outcome category by rod:

| Rod | Fish | Treasure | Junk | Monster |
|---|---:|---:|---:|---:|
| Twig | 55% | 5% | 35% | 5% |
| Bamboo | 58% | 8% | 28% | 6% |
| Fiberglass | 60% | 12% | 20% | 8% |
| Carbon | 62% | 16% | 12% | 10% |
| Master Angler | 60% | 22% | 8% | 10% |
| Leviathan | 55% | 25% | 5% | 15% |

All rows must total 100%.

### 5.3 Fish Species (Real Names)

Fish are grouped by rarity. Higher-tier rods increase higher-rarity odds.

### Fish table

| Rarity | Species | Sell Value |
|---|---|---:|
| Common | Bluegill | 8 |
| Common | Perch | 10 |
| Common | Carp | 12 |
| Common | Catfish | 14 |
| Uncommon | Trout | 24 |
| Uncommon | Bass | 28 |
| Uncommon | Walleye | 32 |
| Rare | Salmon | 55 |
| Rare | Pike | 62 |
| Rare | Tuna | 75 |
| Epic | Swordfish | 120 |
| Epic | Sturgeon | 145 |
| Legendary | Marlin | 220 |
| Legendary | Bluefin Tuna | 260 |
| Mythic | Coelacanth | 420 |

### Base rarity weights

| Rarity | Weight |
|---|---:|
| Common | 50 |
| Uncommon | 28 |
| Rare | 14 |
| Epic | 6 |
| Legendary | 2 |
| Mythic | 0.4 |

Rod rarity bonus should be applied by increasing non-common weights proportionally and reducing common weight to keep the sum stable.

### 5.4 Treasure Table

| Item | Sell Value | Min Rod Tier |
|---|---:|---:|
| Rusty Coin Pouch | 25 | 1 |
| Silver Necklace | 60 | 2 |
| Antique Ring | 110 | 3 |
| Golden Idol | 190 | 4 |
| Jeweled Crown | 320 | 5 |
| Sunken Relic Chest | 500 | 6 |

### 5.5 Junk Table

| Item | Sell Value |
|---|---:|
| Seaweed Clump | 1 |
| Torn Boot | 2 |
| Tin Can | 2 |
| Broken Lure | 3 |
| Driftwood | 1 |
| Old Net Scrap | 3 |

### 5.6 Monster System

Monster probability scales with rod tier (table above), and monster strength tier also scales with rod.

### Monster roster

| Tier | Monster | HP | Attack | Reward Coins |
|---|---|---:|---:|---:|
| 1 | River Slime | 20 | 4 | 15 |
| 1 | Bitefin Piranha | 24 | 5 | 18 |
| 2 | Eel Stalker | 36 | 7 | 30 |
| 2 | Reef Serpent | 42 | 8 | 36 |
| 3 | Abyss Maw | 60 | 11 | 60 |
| 3 | Dread Angler | 72 | 13 | 80 |

### Boss
- **Name:** Kraken Sovereign
- **Spawn condition:** First monster roll while Leviathan Rod is equipped and boss not yet defeated.
- **Stats:** HP 160, Attack 20, Reward 1000
- Defeating boss ends the game with victory screen.

### 5.7 Combat System

Turn-based, simple:
- Player turn options:
  - `Attack`
  - `Use Consumable` (optional in v1)
  - `Run` (optional; failure chance acceptable)
- Enemy turn:
  - Standard attack

### Player combat stats
- `Max HP` starts at 100
- `Current HP` persists within day and is fully restored at day start (or by inn item, optional)
- Damage formula:
  - `damage = max(1, weapon_power + rng(-2, +2) - enemy_defense_modifier)`
  - v1 can omit enemy defense modifier and use direct randomized power range.

### 5.8 Weapons

| Weapon | Cost | Damage Range |
|---|---:|---|
| Driftwood Club | 0 | 4-7 |
| Rusted Dagger | 80 | 7-11 |
| Iron Spear | 220 | 11-16 |
| Hunter Blade | 520 | 16-22 |
| Storm Trident | 1100 | 24-32 |

Player starts with Driftwood Club.

### 5.9 Shop System

### Must support
- Sell all fish
- Sell all treasure
- Sell all junk
- Buy rod upgrades (exactly one equipped rod)
- Buy weapons (exactly one equipped weapon)
- Buy temporary power-ups

### Temporary power-ups
Power-ups last until end of current day only.

| Power-up | Cost | Effect |
|---|---:|---|
| Lucky Bait | 120 | +10% fish chance, -5% junk, -5% monster |
| Magnet Hook | 140 | +10% treasure chance, -10% fish |
| Reinforced Line | 100 | -8% monster chance, redistributed to fish |
| Sharpening Stone | 90 | +3 weapon damage (combat) |

If multiple power-ups are allowed, define stacking rules explicitly (recommended v1: no stacking of same effect, different effects can stack).

### 5.10 Day System

- Each day grants exactly 5 casts.
- Day increments after player confirms end-day from shop screen.
- Daily state reset:
  - casts remaining reset to 5
  - temporary power-ups removed
  - player HP reset to max (recommended v1)

### 5.11 Economy and Balance Targets

Expected progression target (approximate, average play):
- Reach Rod 2 by Day 2-3
- Reach Rod 3 by Day 4-6
- Reach Rod 4 by Day 7-10
- Reach Rod 5 by Day 11-15
- Reach Final Rod by Day 16-22
- Boss kill around Day 18-25

Balance values in this README are starting points and can be tuned after playtesting.

---

## 6) Data Model (Implementation Contract)

Use dataclasses (or equivalent classes) for:

- `GameState`
  - `day: int`
  - `coins: int`
  - `casts_remaining: int`
  - `player_hp: int`
  - `player_max_hp: int`
  - `equipped_rod_id: str`
  - `equipped_weapon_id: str`
  - `inventory: Inventory`
  - `active_powerups: list[str]`
  - `boss_defeated: bool`
  - `boss_spawned: bool`

- `Inventory`
  - `fish: dict[str, int]`
  - `treasure: dict[str, int]`
  - `junk: dict[str, int]`

- `Rod`, `Weapon`, `Fish`, `Treasure`, `Junk`, `Monster`, `PowerUp`

### Save file
- Path: `save/game_save.json`
- Save triggers:
  - End of day
  - After purchases/sales
  - Before and after boss fight

Include version field for migration:
- `save_version: 1`

---

## 7) Recommended Project Structure

```text
fishing-game/
  README.md
  requirements.txt
  src/
    main.py
    config.py
    constants.py
    game/
      state.py
      loop.py
      save_load.py
      rng.py
    systems/
      fishing.py
      loot_tables.py
      combat.py
      shop.py
      economy.py
      progression.py
    content/
      rods.json
      weapons.json
      fish.json
      treasure.json
      junk.json
      monsters.json
      powerups.json
    ui/
      scenes.py
      hud.py
      menus.py
      text.py
    assets/
      sprites/
      fonts/
      sfx/
  tests/
    test_fishing_probs.py
    test_shop_transactions.py
    test_combat_outcomes.py
    test_boss_condition.py
```

---

## 8) Functional Requirements (Definition of Done)

The game is complete when all are true:

1. Player can fish 5 times/day.
2. Catch outcomes include fish, treasure, junk, and monsters.
3. Fish use real species names and sell for defined values.
4. Rod upgrades affect catch quality and risk profile.
5. Shop supports selling catches and buying rods/weapons/power-ups.
6. Monster encounters trigger combat and can be won/lost.
7. Stronger monsters appear as rod tier rises.
8. Final rod can be bought and can trigger boss encounter.
9. Boss can be defeated to trigger victory screen.
10. Save/load works and preserves progression.

---

## 9) Non-Functional Requirements

- Stable 60 FPS target on typical laptop hardware.
- Deterministic random mode for testing (seedable RNG).
- Code organized into systems/modules (no single giant file).
- Basic unit tests for fishing probabilities, combat, and shop economy.

---

## 10) Milestone Implementation Plan

### Milestone 1: Core skeleton
- Pygame window, scene manager, game state boot/save.
- Basic text UI and placeholder assets.

### Milestone 2: Fishing and loot
- Implement cast action, outcome rolls, inventory updates.
- Implement rod-based probability modifiers.

### Milestone 3: Shop and economy
- Sell flows and purchase flows for rods/weapons/power-ups.
- End-day progression and reset rules.

### Milestone 4: Combat and monsters
- Turn-based combat loop.
- Monster encounter integration with fishing.

### Milestone 5: Endgame
- Final rod acquisition.
- Boss spawn logic and victory sequence.

### Milestone 6: Polish
- UI polish, sprite pass, sound pass.
- Balance tuning from playtest data.
- Final QA and bugfixes.

---

## 11) Acceptance Test Checklist

- Start new game with:
  - Twig Rod
  - Driftwood Club
  - 0 coins
  - Day 1, 5 casts
- After 5 casts, no additional cast allowed until next day.
- Selling inventory increases coins by exact configured values.
- Cannot buy item if coins are insufficient.
- Equipping higher rod measurably increases average catch value over 500+ simulated casts.
- Monster encounter enters combat scene every time.
- Boss appears only with Leviathan Rod and only once before defeat.
- Defeating boss shows win screen and locks in victory state.
- Save/load preserves coins, day, inventory, gear, and boss flags.

---

## 12) Future Extensions (Post-v1)

- Multiple fishing zones with unique loot tables.
- Weather/time modifiers.
- Weapon abilities and status effects.
- Crafting and bait system.
- NPC quests and achievements.

---

## 13) Quick Start (for implementation phase)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

`requirements.txt` should include at least:

```text
pygame>=2.5
```

---

## 14) Web Version (GitHub Pages)

A browser-playable version of the game now lives in the [`docs/`](docs/) folder:

- `docs/index.html`
- `docs/styles.css`
- `docs/game.js`
- `docs/content/*.json`

### Run locally (quick static server)

```bash
python3 -m http.server 8000 --directory docs
```

Open:

- `http://localhost:8000`

### Publish on GitHub Pages

1. Push this repository to GitHub.
2. Open repository **Settings** -> **Pages**.
3. Under **Build and deployment**, set:
   - **Source:** `Deploy from a branch`
   - **Branch:** `main`
   - **Folder:** `/docs`
4. Save and wait for Pages to deploy.

After deployment, others can play online at your GitHub Pages URL.

Game progress in the web version is saved in browser `localStorage` for each player.

---

This README is the authoritative v1 game specification for implementation.
