"""Player entity with sprite animation, movement, melee attack, and stats."""

from __future__ import annotations
import math
import pygame
from typing import TYPE_CHECKING

from config import (
    PLAYER_SPEED, PLAYER_BASE_HP, PLAYER_BASE_ATK, PLAYER_BASE_DEF,
    PLAYER_SIZE, ATTACK_RANGE, ATTACK_COOLDOWN, ATTACK_DURATION,
    TILE_SIZE, PLAYER_SPRITE, PLAYER_SPRITE_SIZE,
)
from sprites import AnimatedSprite, load_character_anims

if TYPE_CHECKING:
    from dungeon import TileMap
    from inventory import Inventory, EquipmentManager


class Player:

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.radius = PLAYER_SIZE // 2

        self.max_hp = PLAYER_BASE_HP
        self.hp = self.max_hp
        self.base_atk = PLAYER_BASE_ATK
        self.base_def = PLAYER_BASE_DEF

        self.speed = PLAYER_SPEED
        self.facing = 0.0
        self.moving = False

        self._attack_cd = 0
        self._attack_timer = 0
        self.attacking = False
        self._hurt_timer = 0

        self.alive = True

        self.inventory: Inventory | None = None
        self.equipment: EquipmentManager | None = None

        pack, variant = PLAYER_SPRITE
        anims = load_character_anims(pack, variant, PLAYER_SPRITE_SIZE)
        self.sprite = AnimatedSprite(anims, default="idle", fps=10.0)

    # ── stats ────────────────────────────────────────────────────────────

    @property
    def attack_power(self) -> int:
        bonus = self.equipment.weapon_bonus if self.equipment else 0
        return self.base_atk + bonus

    @property
    def defense(self) -> int:
        bonus = self.equipment.armor_bonus if self.equipment else 0
        return self.base_def + bonus

    # ── movement ─────────────────────────────────────────────────────────

    def handle_input(self, keys, tilemap: TileMap):
        dx = dy = 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1

        self.moving = dx != 0 or dy != 0
        if not self.moving:
            return

        length = math.hypot(dx, dy)
        dx, dy = dx / length * self.speed, dy / length * self.speed
        self.facing = math.atan2(dy, dx)

        if dx != 0:
            self.sprite.facing_right = dx > 0

        nx, ny = self.x + dx, self.y + dy
        if tilemap.is_walkable(nx, self.y, self.radius):
            self.x = nx
        if tilemap.is_walkable(self.x, ny, self.radius):
            self.y = ny

    # ── attack ───────────────────────────────────────────────────────────

    def try_attack(self) -> bool:
        if self._attack_cd > 0:
            return False
        self.attacking = True
        self._attack_timer = ATTACK_DURATION
        self._attack_cd = ATTACK_COOLDOWN
        self.sprite.set("attack", loop=False, reset=True)
        return True

    def attack_hits(self, ex: float, ey: float, eradius: int) -> bool:
        if not self.attacking:
            return False
        dist = math.hypot(ex - self.x, ey - self.y)
        if dist > ATTACK_RANGE + eradius:
            return False
        if dist < self.radius + eradius + 8:
            return True
        angle_to = math.atan2(ey - self.y, ex - self.x)
        diff = (angle_to - self.facing + math.pi) % (2 * math.pi) - math.pi
        return abs(diff) < math.pi / 2

    # ── damage ───────────────────────────────────────────────────────────

    def take_damage(self, raw: int):
        effective = max(1, raw - self.defense)
        self.hp = max(0, self.hp - effective)
        self._hurt_timer = 200
        if self.hp <= 0:
            self.alive = False
            self.sprite.set("dead", loop=False)
        else:
            self.sprite.set("hurt", loop=False)

    def heal(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)

    # ── update ───────────────────────────────────────────────────────────

    def update(self, dt_ms: int):
        if self._attack_cd > 0:
            self._attack_cd = max(0, self._attack_cd - dt_ms)
        if self._attack_timer > 0:
            self._attack_timer = max(0, self._attack_timer - dt_ms)
            if self._attack_timer == 0:
                self.attacking = False
        if self._hurt_timer > 0:
            self._hurt_timer = max(0, self._hurt_timer - dt_ms)

        if not self.alive:
            pass
        elif self.attacking:
            pass  # attack anim already set
        elif self._hurt_timer > 0:
            pass  # hurt anim already set
        elif self.moving:
            self.sprite.set("walk")
        else:
            self.sprite.set("idle")

        self.sprite.update(dt_ms)

    # ── rendering ────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        sx = int(self.x) - cam_x
        sy = int(self.y) - cam_y

        if self.attacking and self._attack_timer > 0:
            self._draw_attack_arc(surface, sx, sy)

        self.sprite.draw(surface, sx, sy)

    def _draw_attack_arc(self, surface: pygame.Surface, sx: int, sy: int):
        arc_surf = pygame.Surface((ATTACK_RANGE * 2, ATTACK_RANGE * 2), pygame.SRCALPHA)
        cx, cy = ATTACK_RANGE, ATTACK_RANGE
        num_pts = 12
        start_a = self.facing - math.pi / 2
        end_a = self.facing + math.pi / 2
        points = [(cx, cy)]
        for i in range(num_pts + 1):
            a = start_a + (end_a - start_a) * i / num_pts
            points.append((cx + int(math.cos(a) * ATTACK_RANGE),
                           cy + int(math.sin(a) * ATTACK_RANGE)))
        pygame.draw.polygon(arc_surf, (140, 200, 255, 50), points)
        surface.blit(arc_surf, (sx - ATTACK_RANGE, sy - ATTACK_RANGE))
