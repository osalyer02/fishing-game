"""Text rendering utilities."""

from __future__ import annotations

import pygame


def draw_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    x: int,
    y: int,
    color: tuple[int, int, int] = (255, 255, 255),
) -> None:
    surface.blit(font.render(text, True, color), (x, y))


def draw_lines(
    surface: pygame.Surface,
    font: pygame.font.Font,
    lines: list[str],
    x: int,
    y: int,
    line_height: int = 10,
    color: tuple[int, int, int] = (255, 255, 255),
) -> None:
    for idx, line in enumerate(lines):
        draw_text(surface, font, line, x, y + idx * line_height, color)
