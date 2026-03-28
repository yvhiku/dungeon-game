"""Enemy and Boss entities with sprite animation and simple AI."""

from __future__ import annotations
import math
import random
import pygame
from typing import Optional, Dict, List, Tuple

from config import (
    ENEMY_SIZE, ENEMY_DETECT_RANGE, ENEMY_KNOCKBACK, TILE_SIZE,
    BOSS_SIZE, BOSS_HP_MUL, BOSS_ATK_MUL, BOSS_SPEED_MUL,
    ENEMY_SPRITE_SIZE, BOSS_SPRITE_SIZE,
    COLOR_HP_FILL, COLOR_HP_BG, COLOR_HP_BORDER,
    FLOOR_ENEMY_TYPE,
    enemy_hp, enemy_atk, enemy_speed,
)
from sprites import AnimatedSprite, load_character_anims


class Enemy:
    """Standard dungeon enemy with chase AI and animated sprites."""

    def __init__(self, x: float, y: float, floor: int,
                 sprite_pack: str = "", sprite_variant: str = "",
                 display_name: str = "Enemy"):
        self.x = x
        self.y = y
        self.radius = ENEMY_SIZE // 2

        self.max_hp = enemy_hp(floor)
        self.hp = self.max_hp
        self.atk = enemy_atk(floor)
        self.speed = enemy_speed(floor)
        self.detect_range = ENEMY_DETECT_RANGE

        self.alive = True
        self.dying = False       # playing death anim
        self.fully_dead = False  # death anim finished, remove from list
        self.hit_flash = 0
        self._wander_angle = random.random() * math.pi * 2
        self._wander_cd = 0
        self._attack_cd = 0

        self.floor = floor
        self.name = display_name

        render_size = ENEMY_SPRITE_SIZE
        anims = load_character_anims(sprite_pack, sprite_variant, render_size)
        self.sprite = AnimatedSprite(anims, default="idle", fps=8.0)

    # ── AI ───────────────────────────────────────────────────────────────

    def update(self, px: float, py: float, tilemap, dt_ms: int):
        if self.fully_dead:
            return

        if self.dying:
            self.sprite.update(dt_ms)
            if self.sprite.done:
                self.fully_dead = True
            return

        if not self.alive:
            return

        dist = math.hypot(px - self.x, py - self.y)

        if dist < self.detect_range:
            self._chase(px, py, tilemap, dt_ms)
            dx = px - self.x
            self.sprite.facing_right = dx >= 0
            if self._attack_cd <= 0:
                self.sprite.set("walk")
        else:
            self._wander(tilemap, dt_ms)
            self.sprite.set("idle")

        if self.hit_flash > 0:
            self.hit_flash = max(0, self.hit_flash - dt_ms)
        if self._attack_cd > 0:
            self._attack_cd = max(0, self._attack_cd - dt_ms)

        self.sprite.update(dt_ms)

    def _chase(self, px: float, py: float, tilemap, dt_ms: float):
        dx, dy = px - self.x, py - self.y
        dist = math.hypot(dx, dy)
        if dist < 1:
            return
        dx, dy = dx / dist * self.speed, dy / dist * self.speed
        nx, ny = self.x + dx, self.y + dy
        if tilemap.is_walkable(nx, self.y, self.radius):
            self.x = nx
        if tilemap.is_walkable(self.x, ny, self.radius):
            self.y = ny

    def _wander(self, tilemap, dt_ms: int):
        self._wander_cd -= dt_ms
        if self._wander_cd <= 0:
            self._wander_angle = random.random() * math.pi * 2
            self._wander_cd = random.randint(1000, 3000)
        spd = self.speed * 0.3
        dx = math.cos(self._wander_angle) * spd
        dy = math.sin(self._wander_angle) * spd
        nx, ny = self.x + dx, self.y + dy
        if tilemap.is_walkable(nx, ny, self.radius):
            self.x, self.y = nx, ny

    # ── combat ───────────────────────────────────────────────────────────

    def can_attack(self, px: float, py: float) -> bool:
        if self._attack_cd > 0 or not self.alive:
            return False
        dist = math.hypot(px - self.x, py - self.y)
        return dist < self.radius + 28

    def perform_attack(self) -> int:
        self._attack_cd = 800
        self.sprite.set("attack", loop=False, reset=True)
        return self.atk

    def take_damage(self, dmg: int):
        self.hp = max(0, self.hp - dmg)
        self.hit_flash = 120
        if self.hp <= 0:
            self.alive = False
            self.dying = True
            self.sprite.set("dead", loop=False, reset=True)
        else:
            self.sprite.set("hurt", loop=False, reset=True)

    def knockback_from(self, px: float, py: float):
        dx, dy = self.x - px, self.y - py
        dist = math.hypot(dx, dy)
        if dist < 0.1:
            dx, dy = 1, 0
            dist = 1
        dx, dy = dx / dist * ENEMY_KNOCKBACK, dy / dist * ENEMY_KNOCKBACK
        self.x += dx
        self.y += dy

    # ── render ───────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        if self.fully_dead:
            return
        sx, sy = int(self.x) - cam_x, int(self.y) - cam_y
        self.sprite.draw(surface, sx, sy)
        if not self.dying:
            self._draw_hp_bar(surface, sx, sy)

    def _draw_hp_bar(self, surface: pygame.Surface, sx: int, sy: int):
        bar_w = self.radius * 2 + 8
        bar_h = 4
        bx = sx - bar_w // 2
        by = sy - self.radius - 22
        pygame.draw.rect(surface, COLOR_HP_BG, (bx, by, bar_w, bar_h))
        fill_w = int(bar_w * self.hp / self.max_hp)
        pygame.draw.rect(surface, COLOR_HP_FILL, (bx, by, fill_w, bar_h))
        pygame.draw.rect(surface, COLOR_HP_BORDER, (bx, by, bar_w, bar_h), 1)


class Boss(Enemy):
    """Boss enemy with enhanced stats, bigger sprite, charge attack."""

    def __init__(self, x: float, y: float, floor: int,
                 sprite_pack: str = "", sprite_variant: str = "",
                 display_name: str = "Boss"):
        super().__init__(x, y, floor, sprite_pack, sprite_variant, display_name)
        self.max_hp = int(enemy_hp(floor) * BOSS_HP_MUL)
        self.hp = self.max_hp
        self.atk = int(enemy_atk(floor) * BOSS_ATK_MUL)
        self.speed = enemy_speed(floor) * BOSS_SPEED_MUL
        self.radius = BOSS_SIZE // 2
        self.detect_range = 400

        anims = load_character_anims(sprite_pack, sprite_variant, BOSS_SPRITE_SIZE)
        self.sprite = AnimatedSprite(anims, default="idle", fps=8.0)

        self._charge_cd = 0

    def update(self, px: float, py: float, tilemap, dt_ms: int):
        if self.dying:
            self.sprite.update(dt_ms)
            if self.sprite.done:
                self.fully_dead = True
            return
        if not self.alive:
            return
        if self._charge_cd > 0:
            self._charge_cd = max(0, self._charge_cd - dt_ms)
        super().update(px, py, tilemap, dt_ms)

    def _chase(self, px: float, py: float, tilemap, dt_ms: float):
        dist = math.hypot(px - self.x, py - self.y)
        spd = self.speed
        if self._charge_cd <= 0 and dist < 150:
            spd = self.speed * 2.5
            self._charge_cd = 3000
        dx, dy = px - self.x, py - self.y
        length = math.hypot(dx, dy)
        if length < 1:
            return
        dx, dy = dx / length * spd, dy / length * spd
        nx, ny = self.x + dx, self.y + dy
        if tilemap.is_walkable(nx, self.y, self.radius):
            self.x = nx
        if tilemap.is_walkable(self.x, ny, self.radius):
            self.y = ny


def create_enemy(x: float, y: float, floor: int, is_boss: bool = False) -> Enemy:
    """Factory: create the right enemy type for the given floor."""
    info = FLOOR_ENEMY_TYPE.get(floor, ("skeleton-enemy", "Skeleton_Warrior", "Enemy"))
    pack, variant, name = info
    if is_boss:
        return Boss(x, y, floor, pack, variant, name)
    return Enemy(x, y, floor, pack, variant, name)
