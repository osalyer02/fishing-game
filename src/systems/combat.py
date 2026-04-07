"""Turn-based combat routines."""

from __future__ import annotations

from dataclasses import dataclass

from game.rng import GameRng
from game.state import ContentDatabase, GameState, Monster, Weapon


@dataclass
class CombatEncounter:
    monster: Monster
    enemy_hp: int
    finished: bool = False
    player_won: bool = False


@dataclass
class CombatTurnResult:
    log: list[str]
    combat_over: bool
    player_won: bool


def start_encounter(monster: Monster) -> CombatEncounter:
    return CombatEncounter(monster=monster, enemy_hp=monster.hp)


def _weapon_bonus_from_powerups(state: GameState, content: ContentDatabase) -> int:
    total = 0
    for powerup_id in state.active_powerups:
        p = content.powerups.get(powerup_id)
        if p:
            total += p.weapon_damage_bonus
    return total


def roll_player_damage(weapon: Weapon, state: GameState, content: ContentDatabase, rng: GameRng) -> int:
    base = rng.randint(weapon.min_damage, weapon.max_damage)
    jitter = rng.randint(-2, 2)
    total = base + jitter + _weapon_bonus_from_powerups(state, content)
    return max(1, total)


def roll_enemy_damage(monster: Monster, rng: GameRng) -> int:
    return max(1, monster.attack + rng.randint(-2, 2))


def player_attack(
    game_state: GameState,
    encounter: CombatEncounter,
    content: ContentDatabase,
    rng: GameRng,
) -> CombatTurnResult:
    if encounter.finished:
        return CombatTurnResult(["Combat already resolved."], True, encounter.player_won)

    weapon = content.get_weapon(game_state.equipped_weapon_id)
    player_damage = roll_player_damage(weapon, game_state, content, rng)
    encounter.enemy_hp -= player_damage

    log = [f"You hit {encounter.monster.name} for {player_damage}."]

    if encounter.enemy_hp <= 0:
        encounter.finished = True
        encounter.player_won = True
        game_state.coins += encounter.monster.reward
        if encounter.monster.boss:
            game_state.boss_defeated = True
        log.append(f"{encounter.monster.name} is defeated! Reward +{encounter.monster.reward} coins.")
        return CombatTurnResult(log, True, True)

    enemy_damage = roll_enemy_damage(encounter.monster, rng)
    game_state.player_hp = max(0, game_state.player_hp - enemy_damage)
    log.append(f"{encounter.monster.name} strikes back for {enemy_damage}.")

    if game_state.player_hp <= 0:
        encounter.finished = True
        encounter.player_won = False
        coin_loss = max(5, int(game_state.coins * 0.2)) if game_state.coins > 0 else 0
        game_state.coins = max(0, game_state.coins - coin_loss)
        game_state.player_hp = 1
        log.append(f"You were overwhelmed and washed ashore. Lost {coin_loss} coins.")
        return CombatTurnResult(log, True, False)

    return CombatTurnResult(log, False, False)


def attempt_run(game_state: GameState, encounter: CombatEncounter, rng: GameRng) -> CombatTurnResult:
    if encounter.finished:
        return CombatTurnResult(["Combat already resolved."], True, encounter.player_won)

    if rng.random() < 0.35:
        encounter.finished = True
        encounter.player_won = False
        return CombatTurnResult(["You escaped the fight!"], True, False)

    enemy_damage = roll_enemy_damage(encounter.monster, rng)
    game_state.player_hp = max(0, game_state.player_hp - enemy_damage)
    log = [f"Escape failed! {encounter.monster.name} hits for {enemy_damage}."]

    if game_state.player_hp <= 0:
        encounter.finished = True
        encounter.player_won = False
        game_state.player_hp = 1
        log.append("You barely survive and crawl back to shore.")
        return CombatTurnResult(log, True, False)

    return CombatTurnResult(log, False, False)
