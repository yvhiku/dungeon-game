"""UI system: HUD, inventory screen, controls overlay, game-over / victory."""

from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_UI_BG, COLOR_UI_BORDER, COLOR_UI_TEXT, COLOR_UI_HIGHLIGHT,
    COLOR_UI_DIM, COLOR_UI_TITLE, COLOR_UI_SUCCESS, COLOR_UI_DANGER,
    COLOR_HP_FILL, COLOR_HP_BG, COLOR_HP_BORDER,
    COLOR_WHITE, COLOR_BLACK,
    COLOR_GOLD, COLOR_POTION, COLOR_WEAPON, COLOR_ARMOR,
    TOTAL_FLOORS,
)
from items import ItemType

if TYPE_CHECKING:
    from player import Player
    from inventory import Inventory, EquipmentManager


class UIManager:

    def __init__(self):
        self.font_sm = pygame.font.SysFont("consolas", 14)
        self.font_md = pygame.font.SysFont("consolas", 18)
        self.font_lg = pygame.font.SysFont("consolas", 28)
        self.font_xl = pygame.font.SysFont("consolas", 48)

        self.show_inventory = False
        self.inv_cursor = 0

        self.messages: list[tuple[str, int]] = []

    # ── public api ───────────────────────────────────────────────────────

    def push_message(self, text: str, duration_ms: int = 2500):
        self.messages.append((text, pygame.time.get_ticks() + duration_ms))

    def toggle_inventory(self):
        self.show_inventory = not self.show_inventory
        self.inv_cursor = 0

    def move_cursor(self, delta: int, inv_size: int):
        if inv_size == 0:
            self.inv_cursor = 0
            return
        self.inv_cursor = (self.inv_cursor + delta) % inv_size

    # ── drawing ──────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, player: Player, floor: int,
             enemies_alive: int):
        self._prune_messages()
        self._draw_hud(surface, player, floor, enemies_alive)
        self._draw_messages(surface)

        if self.show_inventory and player.inventory and player.equipment:
            self._draw_inventory(surface, player.inventory, player.equipment, player)

    # ── controls screen ──────────────────────────────────────────────────

    def draw_controls(self, surface: pygame.Surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH // 2
        y = 100

        title = self.font_xl.render("Dungeon of Shadows", True, COLOR_UI_TITLE)
        surface.blit(title, (cx - title.get_width() // 2, y))
        y += 70

        subtitle = self.font_md.render("Controls", True, COLOR_UI_HIGHLIGHT)
        surface.blit(subtitle, (cx - subtitle.get_width() // 2, y))
        y += 40

        controls = [
            ("WASD / Arrow Keys", "Move"),
            ("SPACE", "Attack (melee arc)"),
            ("F", "Pick up items"),
            ("E / ENTER", "Use stairs (after clearing enemies)"),
            ("I", "Open / close inventory"),
            ("", ""),
            ("IN INVENTORY:", ""),
            ("Up / Down", "Navigate items"),
            ("E", "Equip weapon/armor or use potion"),
            ("X", "Drop item"),
            ("", ""),
            ("H", "Show this help screen"),
            ("R", "Restart (on game over / victory)"),
            ("Q", "Quit     (on game over / victory)"),
        ]

        left_x = cx - 200
        for key, action in controls:
            if key == "" and action == "":
                y += 10
                continue
            if action == "":
                t = self.font_md.render(key, True, COLOR_UI_TITLE)
                surface.blit(t, (left_x, y))
                y += 26
                continue
            kt = self.font_md.render(key, True, COLOR_UI_HIGHLIGHT)
            at = self.font_md.render(action, True, COLOR_UI_TEXT)
            surface.blit(kt, (left_x, y))
            surface.blit(at, (left_x + 220, y))
            y += 26

        y += 30
        prompt = self.font_lg.render("Press any key to start", True, COLOR_UI_SUCCESS)
        surface.blit(prompt, (cx - prompt.get_width() // 2, y))

    # ── game over / victory ──────────────────────────────────────────────

    def draw_game_over(self, surface: pygame.Surface, floor: int):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        self._center_text(surface, "GAME OVER", self.font_xl, COLOR_UI_DANGER, -40)
        self._center_text(surface, f"You fell on floor {floor}",
                          self.font_md, COLOR_UI_DIM, 20)
        self._center_text(surface, "Press R to restart  |  Press Q to quit",
                          self.font_md, COLOR_UI_TEXT, 60)

    def draw_victory(self, surface: pygame.Surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        self._center_text(surface, "VICTORY!", self.font_xl, COLOR_UI_TITLE, -40)
        self._center_text(surface, "The dungeon has been conquered!",
                          self.font_md, COLOR_UI_SUCCESS, 20)
        self._center_text(surface, "Press R to play again  |  Press Q to quit",
                          self.font_md, COLOR_UI_TEXT, 60)

    # ── HUD ──────────────────────────────────────────────────────────────

    def _draw_hud(self, surface: pygame.Surface, player: Player,
                  floor: int, enemies_alive: int):
        bar_x, bar_y, bar_w, bar_h = 16, 16, 200, 20
        pygame.draw.rect(surface, COLOR_HP_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fill = int(bar_w * player.hp / player.max_hp)
        if fill > 0:
            pygame.draw.rect(surface, COLOR_HP_FILL,
                             (bar_x, bar_y, fill, bar_h), border_radius=4)
        pygame.draw.rect(surface, COLOR_HP_BORDER,
                         (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)
        hp_txt = self.font_sm.render(f"HP {player.hp}/{player.max_hp}", True, COLOR_WHITE)
        surface.blit(hp_txt, (bar_x + 6, bar_y + 2))

        atk_txt = self.font_sm.render(
            f"ATK {player.attack_power}  DEF {player.defense}  Gold {player.inventory.gold if player.inventory else 0}",
            True, COLOR_UI_TEXT)
        surface.blit(atk_txt, (bar_x, bar_y + bar_h + 6))

        floor_txt = self.font_md.render(f"Floor {floor}/{TOTAL_FLOORS}", True, COLOR_UI_TITLE)
        surface.blit(floor_txt, (SCREEN_WIDTH - floor_txt.get_width() - 16, 16))

        if enemies_alive > 0:
            enem_txt = self.font_sm.render(f"Enemies: {enemies_alive}", True, COLOR_UI_DANGER)
            surface.blit(enem_txt, (SCREEN_WIDTH - enem_txt.get_width() - 16, 42))
        else:
            clear_txt = self.font_sm.render("Floor clear! Find the green stairs.", True, COLOR_UI_SUCCESS)
            surface.blit(clear_txt, (SCREEN_WIDTH - clear_txt.get_width() - 16, 42))

        eq_y = SCREEN_HEIGHT - 50
        if player.equipment:
            wpn = player.equipment.weapon
            arm = player.equipment.armor
            wpn_name = wpn.name if wpn else "---"
            arm_name = arm.name if arm else "---"
            eq_txt = self.font_sm.render(
                f"[Weapon: {wpn_name}]  [Armor: {arm_name}]", True, COLOR_UI_DIM)
            surface.blit(eq_txt, (16, eq_y))

        inv_hint = self.font_sm.render("[I] Inventory  [SPACE] Attack  [H] Help", True, COLOR_UI_DIM)
        surface.blit(inv_hint, (16, eq_y + 18))

    # ── inventory panel ──────────────────────────────────────────────────

    def _draw_inventory(self, surface: pygame.Surface,
                        inv, eq, player):
        panel_w, panel_h = 380, 480
        px = (SCREEN_WIDTH - panel_w) // 2
        py = (SCREEN_HEIGHT - panel_h) // 2

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((*COLOR_UI_BG, 230))
        pygame.draw.rect(panel, COLOR_UI_BORDER, (0, 0, panel_w, panel_h), 2, border_radius=6)
        surface.blit(panel, (px, py))

        title = self.font_lg.render("Inventory", True, COLOR_UI_TITLE)
        surface.blit(title, (px + (panel_w - title.get_width()) // 2, py + 10))

        eq_y = py + 50
        surface.blit(self.font_sm.render("-- Equipment --", True, COLOR_UI_DIM), (px + 16, eq_y))
        eq_y += 20
        wpn_color = COLOR_WEAPON if eq.weapon else COLOR_UI_DIM
        surface.blit(self.font_sm.render(
            f"Weapon: {eq.weapon.name if eq.weapon else 'None'} (ATK +{eq.weapon_bonus})",
            True, wpn_color), (px + 20, eq_y))
        eq_y += 18
        arm_color = COLOR_ARMOR if eq.armor else COLOR_UI_DIM
        surface.blit(self.font_sm.render(
            f"Armor:  {eq.armor.name if eq.armor else 'None'} (DEF +{eq.armor_bonus})",
            True, arm_color), (px + 20, eq_y))

        eq_y += 24
        surface.blit(self.font_sm.render(f"Gold: {inv.gold}", True, COLOR_GOLD), (px + 20, eq_y))

        eq_y += 28
        surface.blit(self.font_sm.render(
            f"-- Items ({len(inv)}/{inv.capacity}) --", True, COLOR_UI_DIM), (px + 16, eq_y))
        eq_y += 20

        if len(inv) == 0:
            empty_y = eq_y + 30
            msg = self.font_md.render("Inventory is empty", True, COLOR_UI_DIM)
            surface.blit(msg, (px + (panel_w - msg.get_width()) // 2, empty_y))
            hint2 = self.font_sm.render("Defeat enemies to get loot!", True, COLOR_UI_DIM)
            surface.blit(hint2, (px + (panel_w - hint2.get_width()) // 2, empty_y + 28))
            hint3 = self.font_sm.render("[F] to pick up nearby items", True, COLOR_UI_DIM)
            surface.blit(hint3, (px + (panel_w - hint3.get_width()) // 2, empty_y + 48))
        else:
            for i, item in enumerate(inv.items):
                color = self._item_color(item.item_type)
                if i == self.inv_cursor:
                    pygame.draw.rect(surface, (*COLOR_UI_HIGHLIGHT, 60),
                                     (px + 14, eq_y - 1, panel_w - 28, 18))
                    marker = "> "
                else:
                    marker = "  "
                txt = self.font_sm.render(f"{marker}{item.display_name}", True, color)
                surface.blit(txt, (px + 20, eq_y))
                eq_y += 18

        bottom_y = py + panel_h - 70
        pygame.draw.line(surface, COLOR_UI_BORDER, (px + 10, bottom_y), (px + panel_w - 10, bottom_y))

        if 0 <= self.inv_cursor < len(inv):
            sel = inv.items[self.inv_cursor]
            desc = self.font_sm.render(sel.description, True, COLOR_UI_TEXT)
            surface.blit(desc, (px + 20, bottom_y + 8))
            hint = "[E] Equip/Use  [X] Drop  [Up/Down] Navigate"
        elif len(inv) > 0:
            hint = "[Up/Down] Navigate"
        else:
            hint = ""
        if hint:
            surface.blit(self.font_sm.render(hint, True, COLOR_UI_DIM), (px + 20, bottom_y + 30))
        surface.blit(self.font_sm.render("[I] Close", True, COLOR_UI_DIM), (px + 20, bottom_y + 48))

    # ── floating messages ────────────────────────────────────────────────

    def _draw_messages(self, surface: pygame.Surface):
        now = pygame.time.get_ticks()
        y = SCREEN_HEIGHT // 2 - 40
        for text, expire in self.messages:
            remaining = expire - now
            alpha = min(255, max(0, int(remaining / 8)))
            txt = self.font_md.render(text, True, COLOR_UI_TEXT)
            txt.set_alpha(alpha)
            surface.blit(txt, ((SCREEN_WIDTH - txt.get_width()) // 2, y))
            y += 24

    def _prune_messages(self):
        now = pygame.time.get_ticks()
        self.messages = [(t, e) for t, e in self.messages if e > now]

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _item_color(it: ItemType):
        return {
            ItemType.WEAPON: COLOR_WEAPON,
            ItemType.ARMOR:  COLOR_ARMOR,
            ItemType.POTION: COLOR_POTION,
            ItemType.GOLD:   COLOR_GOLD,
        }.get(it, COLOR_UI_TEXT)

    def _center_text(self, surface: pygame.Surface, text: str,
                     font: pygame.font.Font, color, y_offset: int = 0):
        txt = font.render(text, True, color)
        surface.blit(txt, ((SCREEN_WIDTH - txt.get_width()) // 2,
                           SCREEN_HEIGHT // 2 + y_offset))
