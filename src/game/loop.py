"""Main pygame loop and scene orchestration."""

from __future__ import annotations

import pygame

import config
from constants import CATEGORY_FISH, CATEGORY_JUNK, CATEGORY_MONSTER, CATEGORY_TREASURE
from game.content import load_content
from game.rng import GameRng
from game.save_load import load_game, save_game
from systems.combat import CombatEncounter, attempt_run, player_attack, start_encounter
from systems.fishing import CatchResult, cast_line
from systems.progression import advance_day, can_end_day
from systems.shop import buy_next_rod, buy_next_weapon, buy_powerup, sell_all_category
from ui.hud import draw_inventory_panel, draw_top_hud
from ui.menus import draw_key_hint
from ui.scenes import Scene
from ui.text import draw_lines, draw_text


class FishingGameApp:
    def __init__(self, seed: int | None = None) -> None:
        pygame.init()
        pygame.display.set_caption(config.TITLE)

        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        self.internal_surface = pygame.Surface((config.INTERNAL_WIDTH, config.INTERNAL_HEIGHT))
        self.clock = pygame.time.Clock()

        self.small_font = pygame.font.Font(None, 14)
        self.normal_font = pygame.font.Font(None, 18)
        self.big_font = pygame.font.Font(None, 30)

        self.content = load_content()
        self.state = load_game()
        self.rng = GameRng(seed)

        self.scene = Scene.VICTORY if self.state.boss_defeated else Scene.FISHING
        self.event_message: str | None = "Welcome to Fishing RPG. Cast 5 times, then shop and end day."
        self.event_level: str = "info"
        self.event_expires_ms: int = pygame.time.get_ticks() + 2600

        self.last_catch: CatchResult | None = None
        self.current_encounter: CombatEncounter | None = None
        self.day_summary: list[str] | None = None
        self.frame = 0
        self.sprite_cache: dict[tuple[str, tuple[int, int, int]], pygame.Surface] = {}

    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if not self.handle_event(event):
                    running = False
                    break

            self.draw()
            pygame.display.flip()
            self.frame += 1
            self.clock.tick(config.FPS)

        pygame.quit()

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.QUIT:
            return False

        if event.type != pygame.KEYDOWN:
            return True

        if self.scene == Scene.FISHING and self.day_summary is not None:
            self.day_summary = None
            return True

        if self.scene == Scene.FISHING:
            self._on_fishing_key(event.key)
        elif self.scene == Scene.SHOP:
            self._on_shop_key(event.key)
        elif self.scene == Scene.COMBAT:
            self._on_combat_key(event.key)
        elif self.scene == Scene.VICTORY:
            self._on_victory_key(event.key)

        return True

    def _on_fishing_key(self, key: int) -> None:
        if key == pygame.K_f:
            result = cast_line(self.state, self.content, self.rng)
            self.last_catch = result
            if result.category == CATEGORY_FISH:
                self._notify(result.message, level="success")
            elif result.category == CATEGORY_MONSTER:
                self._notify(result.message, level="error")
            elif result.category == "none":
                self._notify(result.message, level="error")
            else:
                self._notify(result.message, level="warning")

            if result.category == CATEGORY_MONSTER and result.monster is not None:
                if result.monster.boss:
                    save_game(self.state)  # Required pre-boss checkpoint.
                self.current_encounter = start_encounter(result.monster)
                self.scene = Scene.COMBAT
                self._notify("Combat begins: [A]ttack, [R]un", level="error")

            if self.state.casts_remaining <= 0:
                self._notify("No casts left. Visit the shop [S].", level="warning")

        if key == pygame.K_s:
            self.scene = Scene.SHOP
            self._notify("Entered shop. Sell, upgrade, and end day when ready.", level="info")

    def _on_shop_key(self, key: int) -> None:
        if key == pygame.K_b:
            self.scene = Scene.FISHING
            self._notify("Back at the lake.", level="info")
            return

        if key == pygame.K_1:
            result = sell_all_category(self.state, self.content, CATEGORY_FISH)
            self._transaction_feedback(result.success, result.message)
        elif key == pygame.K_2:
            result = sell_all_category(self.state, self.content, CATEGORY_TREASURE)
            self._transaction_feedback(result.success, result.message)
        elif key == pygame.K_3:
            result = sell_all_category(self.state, self.content, CATEGORY_JUNK)
            self._transaction_feedback(result.success, result.message)
        elif key == pygame.K_4:
            result = buy_next_rod(self.state, self.content)
            self._transaction_feedback(result.success, result.message)
        elif key == pygame.K_5:
            result = buy_next_weapon(self.state, self.content)
            self._transaction_feedback(result.success, result.message)
        elif key == pygame.K_6:
            result = buy_powerup(self.state, self.content, "lucky_bait")
            self._transaction_feedback(result.success, result.message)
        elif key == pygame.K_7:
            result = buy_powerup(self.state, self.content, "magnet_hook")
            self._transaction_feedback(result.success, result.message)
        elif key == pygame.K_8:
            result = buy_powerup(self.state, self.content, "reinforced_line")
            self._transaction_feedback(result.success, result.message)
        elif key == pygame.K_9:
            result = buy_powerup(self.state, self.content, "sharpening_stone")
            self._transaction_feedback(result.success, result.message)
        elif key == pygame.K_e:
            if not can_end_day(self.state):
                self._notify("Spend all 5 casts before ending the day.", level="error")
                return
            old_day = self.state.day
            advance_day(self.state)
            save_game(self.state)
            self.scene = Scene.FISHING
            self.day_summary = [
                f"Day {old_day} Complete",
                "You rest at the harbor inn.",
                f"Day {self.state.day} begins with {self.state.casts_remaining} casts.",
                "Temporary power-ups faded.",
                "(Press any key)",
            ]
            self._notify(f"A new dawn: Day {self.state.day}.", level="system")

    def _on_combat_key(self, key: int) -> None:
        if not self.current_encounter:
            self.scene = Scene.FISHING
            return

        if key == pygame.K_r and self.current_encounter.monster.boss:
            self._notify("You cannot flee the Kraken Sovereign.", level="error")
            return

        if key == pygame.K_a:
            turn = player_attack(self.state, self.current_encounter, self.content, self.rng)
            self._notify(
                " ".join(turn.log),
                level=self._combat_level(" ".join(turn.log), turn.combat_over, turn.player_won),
            )
            self._resolve_combat_if_over(turn.combat_over, turn.player_won)
        elif key == pygame.K_r:
            turn = attempt_run(self.state, self.current_encounter, self.rng)
            self._notify(
                " ".join(turn.log),
                level=self._combat_level(" ".join(turn.log), turn.combat_over, turn.player_won),
            )
            self._resolve_combat_if_over(turn.combat_over, turn.player_won)

    def _on_victory_key(self, key: int) -> None:
        if key == pygame.K_q:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        elif key == pygame.K_n:
            self.state = self.state.new_game()
            save_game(self.state)
            self.scene = Scene.FISHING
            self.current_encounter = None
            self.last_catch = None
            self.day_summary = ["New game started.", "The lake is calm.", "(Press any key)"]
            self._notify("Fresh start: Day 1.", level="system")

    def _resolve_combat_if_over(self, combat_over: bool, player_won: bool) -> None:
        if not combat_over or not self.current_encounter:
            return

        monster = self.current_encounter.monster
        if monster.boss:
            save_game(self.state)  # Required post-boss checkpoint.

        if player_won and monster.boss and self.state.boss_defeated:
            self.scene = Scene.VICTORY
            self._notify("The Kraken Sovereign falls. You are legend!", level="success", duration_ms=3600)
        else:
            self.scene = Scene.FISHING
            self._notify("Combat resolved. Return to fishing.", level="info")

        self.current_encounter = None

    def _transaction_feedback(self, success: bool, message: str) -> None:
        self._notify(message, level="info" if success else "error")
        if success:
            save_game(self.state)

    def _notify(self, message: str, level: str = "info", duration_ms: int = 2400) -> None:
        self.event_message = message
        self.event_level = level
        self.event_expires_ms = pygame.time.get_ticks() + duration_ms

    def _combat_level(self, message: str, combat_over: bool, player_won: bool) -> str:
        lowered = message.lower()
        if "escaped" in lowered:
            return "info"
        if player_won:
            return "success"
        if combat_over:
            return "error"
        return "warning"

    def _sprite(self, key: str, base_color: tuple[int, int, int]) -> pygame.Surface:
        cache_key = (key, base_color)
        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key]

        size = 24
        sprite = pygame.Surface((size, size), pygame.SRCALPHA)
        border = tuple(max(0, c - 60) for c in base_color)
        bright = tuple(min(255, c + 40) for c in base_color)
        pygame.draw.rect(sprite, border, (0, 0, size, size), border_radius=3)
        pygame.draw.rect(sprite, bright, (1, 1, size - 2, size - 2), border_radius=3)

        seed = abs(hash(key))
        cell = 5
        for y in range(4):
            for x in range(4):
                bit = (seed >> (x + y * 4)) & 1
                if bit:
                    color = (
                        max(0, bright[0] - x * 10),
                        max(0, bright[1] - y * 10),
                        min(255, bright[2] + (x + y) * 4),
                    )
                    pygame.draw.rect(sprite, color, (2 + x * cell, 2 + y * cell, cell - 1, cell - 1))

        self.sprite_cache[cache_key] = sprite
        return sprite

    def draw(self) -> None:
        if self.scene == Scene.FISHING:
            self._draw_fishing_scene()
        elif self.scene == Scene.SHOP:
            self._draw_shop_scene()
        elif self.scene == Scene.COMBAT:
            self._draw_combat_scene()
        else:
            self._draw_victory_scene()

        scaled = pygame.transform.scale(self.internal_surface, self.screen.get_size())
        self.screen.blit(scaled, (0, 0))

    def _draw_fishing_scene(self) -> None:
        s = self.internal_surface
        s.fill((86, 170, 230))

        for i in range(0, 100, 8):
            pygame.draw.rect(s, (70 + i // 5, 145 + i // 6, 215), (0, i, 206, 8))
        for i in range(100, 180, 7):
            pygame.draw.rect(s, (20, 90 + (i % 14), 140 + (i % 12)), (0, i, 206, 7))

        # Simple animated water streaks for retro motion.
        wave = (self.frame // 8) % 12
        for i in range(10):
            x = (i * 20 + wave * 3) % 200
            pygame.draw.line(s, (130, 220, 255), (x, 116 + (i % 3) * 2), (x + 12, 116 + (i % 3) * 2), 1)

        # Dock and angler silhouette.
        pygame.draw.rect(s, (98, 67, 43), (0, 105, 84, 18))
        pygame.draw.rect(s, (65, 42, 28), (8, 95, 8, 10))
        pygame.draw.rect(s, (65, 42, 28), (26, 95, 8, 10))
        pygame.draw.rect(s, (220, 180, 120), (36, 89, 5, 5))
        pygame.draw.rect(s, (30, 40, 60), (34, 94, 9, 11))
        pygame.draw.line(s, (195, 150, 90), (43, 95), (70, 75), 2)
        pygame.draw.line(s, (230, 230, 230), (70, 75), (95, 126), 1)

        draw_top_hud(s, self.small_font, self.state, self.content)
        draw_inventory_panel(s, self.small_font, self.state, self.content, 206, 20, 112, 158)

        draw_text(s, self.normal_font, "Lake Evershade", 8, 24, (240, 250, 255))
        draw_key_hint(s, self.small_font, "F", "Cast line", 8, 38)
        draw_key_hint(s, self.small_font, "S", "Open shop", 8, 48)

        if self.last_catch:
            self._draw_catch_card(s)

        if self.day_summary is not None:
            self._draw_popup(s, self.day_summary)

        self._draw_event_banner(s)

    def _draw_catch_card(self, surface: pygame.Surface) -> None:
        if not self.last_catch:
            return

        category_color = {
            CATEGORY_FISH: (85, 190, 130),
            CATEGORY_TREASURE: (210, 180, 70),
            CATEGORY_JUNK: (150, 150, 150),
            CATEGORY_MONSTER: (195, 80, 80),
        }.get(self.last_catch.category, (120, 120, 120))

        pygame.draw.rect(surface, (20, 30, 40), (8, 62, 190, 34), border_radius=4)
        pygame.draw.rect(surface, category_color, (8, 62, 190, 34), width=1, border_radius=4)

        icon = self._sprite(self.last_catch.item_id or "unknown", category_color)
        surface.blit(icon, (12, 67))
        draw_text(surface, self.small_font, self.last_catch.item_name or "", 40, 69)
        draw_text(surface, self.small_font, f"Value: {self.last_catch.sell_value}", 40, 80, (220, 220, 190))

    def _draw_shop_scene(self) -> None:
        s = self.internal_surface
        s.fill((38, 32, 24))
        pygame.draw.rect(s, (64, 54, 39), (0, 20, 206, 120))
        pygame.draw.rect(s, (90, 74, 52), (0, 140, 206, 40))
        for i in range(0, 206, 12):
            pygame.draw.line(s, (52, 44, 33), (i, 20), (i, 180), 1)

        draw_top_hud(s, self.small_font, self.state, self.content)
        draw_inventory_panel(s, self.small_font, self.state, self.content, 206, 20, 112, 158)

        draw_text(s, self.normal_font, "Harbor Shop", 8, 24, (255, 225, 170))

        next_rod_id = self.content.next_rod_id(self.state.equipped_rod_id)
        next_weapon_id = self.content.next_weapon_id(self.state.equipped_weapon_id)
        next_rod_label = "Max rod owned"
        next_weapon_label = "Max weapon owned"
        if next_rod_id:
            r = self.content.rods[next_rod_id]
            next_rod_label = f"Buy next rod ({r.name}) - {r.cost}"
        if next_weapon_id:
            w = self.content.weapons[next_weapon_id]
            next_weapon_label = f"Buy next weapon ({w.name}) - {w.cost}"

        options = [
            "1 Sell all fish",
            "2 Sell all treasure",
            "3 Sell all junk",
            f"4 {next_rod_label}",
            f"5 {next_weapon_label}",
            "6 Lucky Bait (120)",
            "7 Magnet Hook (140)",
            "8 Reinforced Line (100)",
            "9 Sharpening Stone (90)",
            "E End day (requires 0 casts)",
            "B Return to lake",
        ]
        draw_lines(s, self.small_font, options, 8, 41, line_height=10)

        self._draw_event_banner(s)

    def _draw_combat_scene(self) -> None:
        s = self.internal_surface
        s.fill((25, 10, 14))
        pygame.draw.rect(s, (53, 18, 26), (0, 0, 206, 180))

        draw_top_hud(s, self.small_font, self.state, self.content)

        encounter = self.current_encounter
        if not encounter:
            draw_text(s, self.normal_font, "No active encounter.", 10, 60)
            self._draw_event_banner(s)
            return

        monster = encounter.monster
        color = (205, 70, 70) if monster.boss else (145, 85, 180)
        sprite = pygame.transform.scale(self._sprite(monster.id, color), (72, 72))
        s.blit(sprite, (20, 46))

        draw_text(s, self.normal_font, monster.name, 102, 48, (245, 225, 225))
        draw_text(s, self.small_font, f"Enemy HP: {max(0, encounter.enemy_hp)}/{monster.hp}", 102, 62)
        draw_text(s, self.small_font, f"Enemy ATK: {monster.attack}", 102, 72)

        # Enemy HP bar.
        pygame.draw.rect(s, (42, 42, 42), (102, 84, 90, 8))
        hp_ratio = max(0.0, min(1.0, encounter.enemy_hp / monster.hp))
        pygame.draw.rect(s, (220, 78, 78), (102, 84, int(90 * hp_ratio), 8))

        draw_key_hint(s, self.small_font, "A", "Attack", 8, 126)
        draw_key_hint(s, self.small_font, "R", "Run", 8, 136)
        if monster.boss:
            draw_text(s, self.small_font, "Boss fight: no escape.", 8, 146, (255, 180, 180))

        draw_inventory_panel(s, self.small_font, self.state, self.content, 206, 20, 112, 158)
        self._draw_event_banner(s)

    def _draw_victory_scene(self) -> None:
        s = self.internal_surface
        s.fill((8, 20, 36))

        for i in range(0, 320, 10):
            pygame.draw.line(s, (20 + i // 20, 40 + i // 16, 70 + i // 10), (i, 0), (i - 90, 180), 1)

        draw_text(s, self.big_font, "VICTORY", 104, 32, (255, 236, 152))
        draw_text(s, self.normal_font, "Kraken Sovereign Defeated", 66, 62, (220, 245, 255))
        draw_text(s, self.small_font, f"Final Day: {self.state.day}", 112, 86)
        draw_text(s, self.small_font, f"Final Coins: {self.state.coins}", 106, 96)

        draw_key_hint(s, self.small_font, "N", "New game", 104, 122)
        draw_key_hint(s, self.small_font, "Q", "Quit", 104, 132)

        draw_text(s, self.small_font, "Harbor songs will remember your name.", 72, 148, (208, 228, 245))
        self._draw_event_banner(s)

    def _draw_event_banner(self, surface: pygame.Surface) -> None:
        now = pygame.time.get_ticks()
        if not self.event_message or now >= self.event_expires_ms:
            self.event_message = None
            return

        styles = {
            "error": {"bg": (52, 18, 24), "accent": (235, 82, 92), "text": (255, 226, 230)},
            "success": {"bg": (18, 44, 28), "accent": (92, 222, 120), "text": (226, 255, 236)},
            "warning": {"bg": (56, 40, 16), "accent": (246, 192, 90), "text": (255, 244, 219)},
            "system": {"bg": (22, 30, 58), "accent": (133, 180, 250), "text": (222, 236, 255)},
            "info": {"bg": (20, 30, 42), "accent": (118, 194, 242), "text": (230, 246, 255)},
        }
        style = styles.get(self.event_level, styles["info"])

        x, y, w, h = 8, 146, 190, 28
        pygame.draw.rect(surface, (8, 10, 14), (x + 1, y + 2, w, h), border_radius=5)
        pygame.draw.rect(surface, style["bg"], (x, y, w, h), border_radius=5)
        pygame.draw.rect(surface, style["accent"], (x, y, w, h), width=1, border_radius=5)
        pygame.draw.rect(surface, style["accent"], (x + 2, y + 2, 3, h - 4), border_radius=2)
        draw_text(surface, self.small_font, self.event_message[:58], x + 10, y + 10, style["text"])

    def _draw_popup(self, surface: pygame.Surface, lines: list[str]) -> None:
        box = pygame.Rect(52, 52, 216, 76)
        pygame.draw.rect(surface, (12, 20, 30), box, border_radius=6)
        pygame.draw.rect(surface, (98, 144, 182), box, width=2, border_radius=6)
        draw_lines(surface, self.normal_font, lines, box.x + 14, box.y + 10, line_height=14)


def run_game(seed: int | None = None) -> None:
    app = FishingGameApp(seed=seed)
    app.run()
