"""HUD and inventory rendering."""

from __future__ import annotations

import pygame

from game.state import ContentDatabase, GameState
from ui.text import draw_lines, draw_text


def draw_top_hud(
    surface: pygame.Surface,
    small_font: pygame.font.Font,
    state: GameState,
    content: ContentDatabase,
) -> None:
    pygame.draw.rect(surface, (18, 30, 44), (0, 0, surface.get_width(), 18))
    pygame.draw.line(surface, (69, 106, 136), (0, 18), (surface.get_width(), 18), 1)

    rod = content.rods[state.equipped_rod_id]
    weapon = content.weapons[state.equipped_weapon_id]

    draw_text(surface, small_font, f"Day {state.day}", 4, 5)
    draw_text(surface, small_font, f"Coins: {state.coins}", 56, 5)
    draw_text(surface, small_font, f"Casts: {state.casts_remaining}", 134, 5)
    draw_text(surface, small_font, f"HP: {state.player_hp}/{state.player_max_hp}", 205, 5)
    draw_text(surface, small_font, rod.name, 4, 150, (180, 255, 220))
    draw_text(surface, small_font, weapon.name, 4, 160, (255, 210, 180))


def _inventory_lines(title: str, bucket: dict[str, int], names: dict[str, str]) -> list[str]:
    lines = [title]
    if not bucket:
        lines.append("  (empty)")
        return lines
    for item_id, count in sorted(bucket.items(), key=lambda kv: names.get(kv[0], kv[0])):
        lines.append(f"  {names.get(item_id, item_id)} x{count}")
    return lines


def draw_inventory_panel(
    surface: pygame.Surface,
    small_font: pygame.font.Font,
    state: GameState,
    content: ContentDatabase,
    x: int,
    y: int,
    w: int,
    h: int,
) -> None:
    pygame.draw.rect(surface, (14, 19, 30), (x, y, w, h), border_radius=4)
    pygame.draw.rect(surface, (55, 78, 105), (x, y, w, h), width=1, border_radius=4)

    fish_names = {k: v.name for k, v in content.fish.items()}
    treasure_names = {k: v.name for k, v in content.treasure.items()}
    junk_names = {k: v.name for k, v in content.junk.items()}

    lines = ["Inventory"]
    lines.extend(_inventory_lines("Fish:", state.inventory.fish, fish_names))
    lines.extend(_inventory_lines("Treasure:", state.inventory.treasure, treasure_names))
    lines.extend(_inventory_lines("Junk:", state.inventory.junk, junk_names))

    if state.active_powerups:
        lines.append("Power-ups:")
        for powerup_id in state.active_powerups:
            lines.append(f"  {content.powerups[powerup_id].name}")

    max_rows = (h - 10) // 9
    draw_lines(surface, small_font, lines[:max_rows], x + 5, y + 4, line_height=9)
