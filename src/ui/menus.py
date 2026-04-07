"""Reusable menu widgets."""

from __future__ import annotations

import pygame

from ui.text import draw_text


def draw_key_hint(
    surface: pygame.Surface,
    font: pygame.font.Font,
    key: str,
    label: str,
    x: int,
    y: int,
    key_color: tuple[int, int, int] = (255, 220, 120),
    text_color: tuple[int, int, int] = (240, 240, 240),
) -> None:
    draw_text(surface, font, f"[{key}]", x, y, key_color)
    draw_text(surface, font, label, x + 26, y, text_color)
