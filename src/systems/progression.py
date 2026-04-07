"""Day progression and reset rules."""

from __future__ import annotations

from constants import CASTS_PER_DAY
from game.state import GameState


def can_end_day(state: GameState) -> bool:
    return state.casts_remaining <= 0


def advance_day(state: GameState) -> None:
    state.day += 1
    state.casts_remaining = CASTS_PER_DAY
    state.player_hp = state.player_max_hp
    state.active_powerups.clear()
