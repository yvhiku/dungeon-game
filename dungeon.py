"""Procedural dungeon generation with rooms and L-shaped corridors."""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

from config import (
    DUNGEON_WIDTH, DUNGEON_HEIGHT,
    ROOM_MIN_SIZE, ROOM_MAX_SIZE, ROOM_PADDING,
    BOSS_ROOM_W, BOSS_ROOM_H,
    WALL, FLOOR, STAIRS,
    TILE_SIZE, BOSS_FLOORS,
    rooms_for_floor,
)


@dataclass
class Room:
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self) -> Tuple[int, int]:
        return self.x + self.w // 2, self.y + self.h // 2

    @property
    def inner(self) -> Tuple[int, int, int, int]:
        return self.x + 1, self.y + 1, self.w - 2, self.h - 2

    def intersects(self, other: Room, pad: int = ROOM_PADDING) -> bool:
        return not (
            self.x + self.w + pad <= other.x
            or other.x + other.w + pad <= self.x
            or self.y + self.h + pad <= other.y
            or other.y + other.h + pad <= self.y
        )


class TileMap:
    """2-D grid of tile IDs with pixel-level helpers."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.tiles: List[List[int]] = [
            [WALL] * width for _ in range(height)
        ]

    def __getitem__(self, pos: Tuple[int, int]) -> int:
        x, y = pos
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return WALL

    def __setitem__(self, pos: Tuple[int, int], val: int):
        x, y = pos
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x] = val

    def is_walkable(self, px: float, py: float, radius: int = 0) -> bool:
        """Check if a circle at pixel (px, py) with given radius is on floor/stairs."""
        corners = [
            (px - radius, py - radius),
            (px + radius, py - radius),
            (px - radius, py + radius),
            (px + radius, py + radius),
        ]
        for cx, cy in corners:
            tx, ty = int(cx) // TILE_SIZE, int(cy) // TILE_SIZE
            if self[tx, ty] == WALL:
                return False
        return True

    @property
    def pixel_width(self) -> int:
        return self.width * TILE_SIZE

    @property
    def pixel_height(self) -> int:
        return self.height * TILE_SIZE


class DungeonGenerator:

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def generate(self, floor: int) -> Tuple[TileMap, List[Room], Tuple[int, int], Tuple[int, int], List[Tuple[int, int]]]:
        """Return (tilemap, rooms, player_spawn_px, stairs_pos_tile, enemy_spawn_tiles)."""
        is_boss = floor in BOSS_FLOORS
        if is_boss:
            return self._generate_boss_floor(floor)
        return self._generate_normal_floor(floor)

    # ── normal floors ────────────────────────────────────────────────────

    def _generate_normal_floor(self, floor: int):
        target_rooms = rooms_for_floor(floor)
        tilemap = TileMap(DUNGEON_WIDTH, DUNGEON_HEIGHT)
        rooms: List[Room] = []

        for _ in range(target_rooms * 30):
            w = self.rng.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            h = self.rng.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            x = self.rng.randint(1, DUNGEON_WIDTH - w - 1)
            y = self.rng.randint(1, DUNGEON_HEIGHT - h - 1)
            candidate = Room(x, y, w, h)
            if not any(candidate.intersects(r) for r in rooms):
                rooms.append(candidate)
                if len(rooms) >= target_rooms:
                    break

        rooms.sort(key=lambda r: r.center[0] + r.center[1])

        for room in rooms:
            self._carve_room(tilemap, room)

        for i in range(len(rooms) - 1):
            self._carve_corridor(tilemap, rooms[i].center, rooms[i + 1].center)

        start_room = rooms[0]
        end_room = rooms[-1]
        sx, sy = start_room.center
        ex, ey = end_room.center
        tilemap[ex, ey] = STAIRS

        enemy_tiles = self._pick_enemy_spawns(rooms[1:], tilemap, floor)

        player_px = (sx * TILE_SIZE + TILE_SIZE // 2,
                     sy * TILE_SIZE + TILE_SIZE // 2)

        return tilemap, rooms, player_px, (ex, ey), enemy_tiles

    # ── boss floors ──────────────────────────────────────────────────────

    def _generate_boss_floor(self, floor: int):
        tilemap = TileMap(DUNGEON_WIDTH, DUNGEON_HEIGHT)
        rx = (DUNGEON_WIDTH - BOSS_ROOM_W) // 2
        ry = (DUNGEON_HEIGHT - BOSS_ROOM_H) // 2
        room = Room(rx, ry, BOSS_ROOM_W, BOSS_ROOM_H)
        self._carve_room(tilemap, room)

        cx, cy = room.center
        tilemap[cx, cy] = STAIRS

        px_spawn = (
            (rx + 2) * TILE_SIZE + TILE_SIZE // 2,
            (ry + BOSS_ROOM_H - 2) * TILE_SIZE + TILE_SIZE // 2,
        )

        boss_tile = (cx, cy - 2)

        return tilemap, [room], px_spawn, (cx, cy), [boss_tile]

    # ── helpers ──────────────────────────────────────────────────────────

    def _carve_room(self, tm: TileMap, room: Room):
        for yy in range(room.y, room.y + room.h):
            for xx in range(room.x, room.x + room.w):
                tm[xx, yy] = FLOOR

    def _carve_corridor(self, tm: TileMap, a: Tuple[int, int], b: Tuple[int, int]):
        ax, ay = a
        bx, by = b
        if self.rng.random() < 0.5:
            self._h_tunnel(tm, ax, bx, ay)
            self._v_tunnel(tm, ay, by, bx)
        else:
            self._v_tunnel(tm, ay, by, ax)
            self._h_tunnel(tm, ax, bx, by)

    @staticmethod
    def _h_tunnel(tm: TileMap, x1: int, x2: int, y: int):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for dy in (-1, 0, 1):
                if 0 <= y + dy < tm.height:
                    tm[x, y + dy] = FLOOR

    @staticmethod
    def _v_tunnel(tm: TileMap, y1: int, y2: int, x: int):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for dx in (-1, 0, 1):
                if 0 <= x + dx < tm.width:
                    tm[x + dx, y] = FLOOR

    def _pick_enemy_spawns(
        self, rooms: List[Room], tm: TileMap, floor: int
    ) -> List[Tuple[int, int]]:
        from config import enemies_for_floor

        count = enemies_for_floor(floor)
        tiles: List[Tuple[int, int]] = []
        for room in rooms:
            cx, cy = room.center
            if tm[cx, cy] in (FLOOR, STAIRS):
                tiles.append((cx, cy))
        while len(tiles) < count:
            room = self.rng.choice(rooms)
            tx = self.rng.randint(room.x + 1, room.x + room.w - 2)
            ty = self.rng.randint(room.y + 1, room.y + room.h - 2)
            if tm[tx, ty] == FLOOR and (tx, ty) not in tiles:
                tiles.append((tx, ty))
        return tiles[:count]
