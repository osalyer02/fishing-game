"""Persist and restore game state."""

from __future__ import annotations

import json
from pathlib import Path

from constants import SAVE_VERSION
from game.state import GameState


DEFAULT_SAVE_PATH = Path(__file__).resolve().parent.parent.parent / "save" / "game_save.json"


def load_game(save_path: Path = DEFAULT_SAVE_PATH) -> GameState:
    if not save_path.exists():
        return GameState.new_game()

    with save_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    # v1 only: forward compatibility fallback to new game if malformed.
    if payload.get("save_version") != SAVE_VERSION:
        return GameState.new_game()

    return GameState.from_dict(payload.get("state", {}))


def save_game(state: GameState, save_path: Path = DEFAULT_SAVE_PATH) -> None:
    save_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "save_version": SAVE_VERSION,
        "state": state.to_dict(),
    }
    with save_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
