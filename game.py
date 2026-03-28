"""Main Game class: orchestrates the game loop and all subsystems."""

from __future__ import annotations
import math
import pygame
from typing import List, Optional

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, VIEW_W, VIEW_H, ZOOM,
    FPS, TITLE, TILE_SIZE,
    WALL, FLOOR, STAIRS, TOTAL_FLOORS, BOSS_FLOORS,
    COLOR_BG, COLOR_WALL, COLOR_WALL_TOP, COLOR_FLOOR, COLOR_FLOOR_ALT,
    COLOR_STAIRS, COLOR_BLACK,
    AUTO_PICKUP_RANGE, MANUAL_PICKUP_RANGE,
    FLOOR_ENEMY_TYPE,
)
from dungeon import DungeonGenerator, TileMap
from player import Player
from enemy import Enemy, Boss, create_enemy
from camera import Camera
from inventory import Inventory, EquipmentManager
from items import Item, Potion, Weapon, Armor, ItemType
from loot import LootManager
from ui import UIManager
from sprites import load_floor_tiles


class DroppedItem:
    """Item lying on the dungeon floor."""
    def __init__(self, x: float, y: float, item: Item):
        self.x = x
        self.y = y
        self.item = item
        self.bob_phase = 0.0


class Game:

    def __init__(self, seed: Optional[int] = None):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        self.game_surface = pygame.Surface((VIEW_W, VIEW_H))

        self.dungeon_gen = DungeonGenerator(seed)
        self.loot_mgr = LootManager()
        self.ui = UIManager()
        self.floor_tiles = load_floor_tiles(TILE_SIZE)

        self.state = "playing"  # playing | game_over | victory | controls
        self.floor = 0
        self.player: Optional[Player] = None
        self.enemies: List[Enemy] = []
        self.drops: List[DroppedItem] = []
        self.tilemap: Optional[TileMap] = None
        self.camera: Optional[Camera] = None
        self.stairs_tile = (0, 0)

        self._start_new_game()

    # ── game lifecycle ───────────────────────────────────────────────────

    def _start_new_game(self):
        self.floor = 0
        self.state = "controls"
        self.player = Player(0, 0)
        self.player.inventory = Inventory()
        self.player.equipment = EquipmentManager()
        self._load_floor()

    def _load_floor(self):
        self.floor += 1
        self.drops.clear()
        self.ui.show_inventory = False

        tilemap, rooms, spawn, stairs, enemy_tiles = self.dungeon_gen.generate(self.floor)
        self.tilemap = tilemap
        self.stairs_tile = stairs
        self.camera = Camera(tilemap.pixel_width, tilemap.pixel_height)

        self.player.x, self.player.y = spawn
        self.player.hp = self.player.max_hp
        self.player.alive = True

        self.enemies = []
        is_boss = self.floor in BOSS_FLOORS
        for et in enemy_tiles:
            ex = et[0] * TILE_SIZE + TILE_SIZE // 2
            ey = et[1] * TILE_SIZE + TILE_SIZE // 2
            self.enemies.append(create_enemy(ex, ey, self.floor, is_boss=is_boss))

        floor_label = f"Floor {self.floor}"
        if is_boss:
            info = FLOOR_ENEMY_TYPE.get(self.floor)
            boss_name = info[2] if info else "Boss"
            floor_label += f" — BOSS: {boss_name}"
        self.ui.push_message(floor_label, 3000)

    # ── main loop ────────────────────────────────────────────────────────

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self._handle_event(event)

            if self.state == "playing":
                self._update(dt)

            self._render()
            pygame.display.flip()

        pygame.quit()

    # ── event handling ───────────────────────────────────────────────────

    def _handle_event(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return

        # Controls screen: any key dismisses
        if self.state == "controls":
            self.state = "playing"
            return

        if self.state in ("game_over", "victory"):
            if event.key == pygame.K_r:
                self._start_new_game()
            elif event.key == pygame.K_q:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        # In-game keys
        if event.key in (pygame.K_i, pygame.K_ESCAPE):
            if self.ui.show_inventory:
                self.ui.show_inventory = False
                return
            if event.key == pygame.K_i:
                self.ui.toggle_inventory()
                return

        if self.ui.show_inventory:
            self._handle_inventory_input(event.key)
            return

        if event.key == pygame.K_SPACE:
            self._player_attack()
        elif event.key == pygame.K_f:
            self._try_pickup_manual()
        elif event.key in (pygame.K_RETURN, pygame.K_e):
            self._try_stairs()
        elif event.key == pygame.K_h:
            self.state = "controls"

    def _handle_inventory_input(self, key):
        inv = self.player.inventory
        eq = self.player.equipment
        if inv is None or eq is None:
            return

        if key in (pygame.K_UP, pygame.K_w):
            self.ui.move_cursor(-1, len(inv))
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.ui.move_cursor(1, len(inv))
        elif key == pygame.K_e:
            item = inv.get(self.ui.inv_cursor)
            if item is None:
                return
            if isinstance(item, (Weapon, Armor)):
                eq.equip(item, inv)
                self.ui.push_message(f"Equipped {item.name}")
                if self.ui.inv_cursor >= len(inv):
                    self.ui.inv_cursor = max(0, len(inv) - 1)
            elif isinstance(item, Potion):
                if self.player.hp >= self.player.max_hp:
                    self.ui.push_message("HP is already full")
                    return
                self.player.heal(item.heal_amount)
                self.ui.push_message(f"Healed {item.heal_amount} HP")
                if item.quantity > 1:
                    item.quantity -= 1
                else:
                    inv.remove(self.ui.inv_cursor)
                    if self.ui.inv_cursor >= len(inv):
                        self.ui.inv_cursor = max(0, len(inv) - 1)
                self.ui.show_inventory = False
        elif key == pygame.K_x:
            removed = inv.remove(self.ui.inv_cursor)
            if removed:
                self.ui.push_message(f"Dropped {removed.display_name}")
                self.drops.append(DroppedItem(self.player.x, self.player.y, removed))
                if self.ui.inv_cursor >= len(inv):
                    self.ui.inv_cursor = max(0, len(inv) - 1)

    # ── player actions ───────────────────────────────────────────────────

    def _player_attack(self):
        if not self.player.try_attack():
            return
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if self.player.attack_hits(enemy.x, enemy.y, enemy.radius):
                enemy.take_damage(self.player.attack_power)
                enemy.knockback_from(self.player.x, self.player.y)
                if not enemy.alive:
                    self._on_enemy_killed(enemy)

    def _on_enemy_killed(self, enemy: Enemy):
        if isinstance(enemy, Boss):
            drops = self.loot_mgr.roll_boss_drop(self.floor)
            for d in drops:
                self.drops.append(DroppedItem(enemy.x, enemy.y, d))
                self.ui.push_message(f"Boss dropped: {d.name}!")
        else:
            drop = self.loot_mgr.roll_enemy_drop(self.floor)
            if drop:
                self.drops.append(DroppedItem(enemy.x, enemy.y, drop))
                self.ui.push_message(f"Dropped: {drop.name}")

    def _auto_pickup(self):
        """Pick up items automatically when the player walks over them."""
        for drop in self.drops[:]:
            dist = math.hypot(drop.x - self.player.x, drop.y - self.player.y)
            if dist < AUTO_PICKUP_RANGE:
                if self.player.inventory.add(drop.item):
                    self.ui.push_message(f"Picked up {drop.item.display_name}")
                    self.drops.remove(drop)

    def _try_pickup_manual(self):
        """Pick up nearest item within manual range on F key."""
        if not self.drops:
            return
        nearest = None
        best_dist = MANUAL_PICKUP_RANGE + 1
        for drop in self.drops:
            dist = math.hypot(drop.x - self.player.x, drop.y - self.player.y)
            if dist < best_dist:
                best_dist = dist
                nearest = drop
        if nearest is None:
            return
        if self.player.inventory.add(nearest.item):
            self.ui.push_message(f"Picked up {nearest.item.display_name}")
            self.drops.remove(nearest)
        else:
            self.ui.push_message("Inventory full!")

    def _try_stairs(self):
        sx, sy = self.stairs_tile
        spx = sx * TILE_SIZE + TILE_SIZE // 2
        spy = sy * TILE_SIZE + TILE_SIZE // 2
        dist = math.hypot(spx - self.player.x, spy - self.player.y)

        alive_count = sum(1 for e in self.enemies if e.alive)
        if alive_count > 0:
            self.ui.push_message(f"Defeat all enemies first! ({alive_count} remaining)")
            return
        if dist > TILE_SIZE * 1.5:
            self.ui.push_message("Move to the stairs first!")
            return

        if self.floor >= TOTAL_FLOORS:
            self.state = "victory"
        else:
            self._load_floor()

    # ── update ───────────────────────────────────────────────────────────

    def _update(self, dt_ms: int):
        if not self.player.alive:
            self.state = "game_over"
            return

        keys = pygame.key.get_pressed()
        if not self.ui.show_inventory:
            self.player.handle_input(keys, self.tilemap)
        self.player.update(dt_ms)

        for enemy in self.enemies:
            enemy.update(self.player.x, self.player.y, self.tilemap, dt_ms)
            if enemy.alive and enemy.can_attack(self.player.x, self.player.y):
                dmg = enemy.perform_attack()
                self.player.take_damage(dmg)

        self.enemies = [e for e in self.enemies if not e.fully_dead]

        self.camera.update(self.player.x, self.player.y)

        self._auto_pickup()

        for drop in self.drops:
            drop.bob_phase += dt_ms * 0.004

    # ── rendering ────────────────────────────────────────────────────────

    def _render(self):
        gs = self.game_surface
        gs.fill(COLOR_BG)

        if self.tilemap:
            self._draw_tilemap(gs)
            self._draw_drops(gs)
            for enemy in self.enemies:
                enemy.draw(gs, self.camera.x, self.camera.y)
            self.player.draw(gs, self.camera.x, self.camera.y)

        scaled = pygame.transform.scale(gs, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen.blit(scaled, (0, 0))

        alive_count = sum(1 for e in self.enemies if e.alive)
        self.ui.draw(self.screen, self.player, self.floor, alive_count)

        if self.state == "game_over":
            self.ui.draw_game_over(self.screen, self.floor)
        elif self.state == "victory":
            self.ui.draw_victory(self.screen)
        elif self.state == "controls":
            self.ui.draw_controls(self.screen)

    def _draw_tilemap(self, surf: pygame.Surface):
        cam = self.camera
        start_tx = max(0, cam.x // TILE_SIZE)
        start_ty = max(0, cam.y // TILE_SIZE)
        end_tx = min(self.tilemap.width, (cam.x + VIEW_W) // TILE_SIZE + 2)
        end_ty = min(self.tilemap.height, (cam.y + VIEW_H) // TILE_SIZE + 2)

        for ty in range(start_ty, end_ty):
            for tx in range(start_tx, end_tx):
                tile = self.tilemap[tx, ty]
                sx = tx * TILE_SIZE - cam.x
                sy = ty * TILE_SIZE - cam.y

                if tile == WALL:
                    pygame.draw.rect(surf, COLOR_WALL, (sx, sy, TILE_SIZE, TILE_SIZE))
                    below = self.tilemap[tx, ty + 1]
                    if below in (FLOOR, STAIRS):
                        pygame.draw.rect(surf, COLOR_WALL_TOP,
                                         (sx, sy + TILE_SIZE - 6, TILE_SIZE, 6))
                elif tile == FLOOR:
                    ft = self.floor_tiles
                    if ft:
                        key = "floor" if (tx + ty) % 2 == 0 else "floor_alt"
                        surf.blit(ft[key], (sx, sy))
                    else:
                        col = COLOR_FLOOR if (tx + ty) % 2 == 0 else COLOR_FLOOR_ALT
                        pygame.draw.rect(surf, col, (sx, sy, TILE_SIZE, TILE_SIZE))
                elif tile == STAIRS:
                    ft = self.floor_tiles
                    if ft:
                        surf.blit(ft["floor"], (sx, sy))
                    else:
                        pygame.draw.rect(surf, COLOR_FLOOR, (sx, sy, TILE_SIZE, TILE_SIZE))
                    alive_count = sum(1 for e in self.enemies if e.alive)
                    stair_col = COLOR_STAIRS if alive_count == 0 else (80, 80, 80)
                    inner = 6
                    for step in range(3):
                        r = pygame.Rect(sx + inner + step * 2, sy + inner + step * 2,
                                        TILE_SIZE - 2 * (inner + step * 2),
                                        TILE_SIZE - 2 * (inner + step * 2))
                        if r.width > 0 and r.height > 0:
                            pygame.draw.rect(surf, stair_col, r, 1)

    def _draw_drops(self, surf: pygame.Surface):
        for drop in self.drops:
            sx, sy = self.camera.apply(drop.x, drop.y)
            bob = int(math.sin(drop.bob_phase) * 3)
            sy += bob

            it = drop.item.item_type
            if it == ItemType.GOLD:
                col = (255, 210, 50)
            elif it == ItemType.POTION:
                col = (60, 210, 120)
            elif it == ItemType.WEAPON:
                col = (180, 180, 200)
            elif it == ItemType.ARMOR:
                col = (140, 120, 90)
            else:
                col = (200, 200, 200)

            pygame.draw.circle(surf, col, (sx, sy), 6)
            pygame.draw.circle(surf, (255, 255, 255), (sx - 1, sy - 1), 2)
