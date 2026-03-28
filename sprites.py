"""Sprite sheet loader and animation system for all characters."""

from __future__ import annotations
import os
import pygame
from typing import Dict, List, Optional, Tuple


ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
TILESET_DIR = os.path.join(ASSETS_DIR, "maptileset")
FRAME_SIZE = 128  # each frame in the source sheets is 128x128
TILESET_TILE_PX = 16  # each tile in the map tileset is 16x16


def load_strip(path: str, frame_w: int = FRAME_SIZE) -> List[pygame.Surface]:
    """Load a horizontal sprite strip and return a list of per-frame surfaces."""
    sheet = pygame.image.load(path).convert_alpha()
    w, h = sheet.get_size()
    count = w // frame_w
    frames: List[pygame.Surface] = []
    for i in range(count):
        rect = pygame.Rect(i * frame_w, 0, frame_w, h)
        frame = sheet.subsurface(rect).copy()
        frames.append(frame)
    return frames


def scale_frames(frames: List[pygame.Surface], size: Tuple[int, int]) -> List[pygame.Surface]:
    return [pygame.transform.scale(f, size) for f in frames]


def flip_frames(frames: List[pygame.Surface]) -> List[pygame.Surface]:
    return [pygame.transform.flip(f, True, False) for f in frames]


class AnimatedSprite:
    """Manages animation playback for one character."""

    def __init__(self, anims: Dict[str, List[pygame.Surface]],
                 default: str = "idle", fps: float = 10.0):
        self.anims = anims
        self._flipped: Dict[str, List[pygame.Surface]] = {}
        for name, frames in anims.items():
            self._flipped[name] = flip_frames(frames)

        self.current = default
        self.frame = 0
        self.timer = 0.0
        self.fps = fps
        self.facing_right = True
        self.done = False  # True when a one-shot anim finishes its last frame

    @property
    def frames(self) -> List[pygame.Surface]:
        bank = self.anims if self.facing_right else self._flipped
        return bank.get(self.current, bank.get("idle", []))

    def set(self, name: str, loop: bool = True, reset: bool = False):
        if name not in self.anims:
            return
        if name != self.current or reset:
            self.current = name
            self.frame = 0
            self.timer = 0.0
            self.done = False
            self._loop = loop

    def update(self, dt_ms: int):
        self.timer += dt_ms
        interval = 1000.0 / self.fps
        flist = self.frames
        if not flist:
            return
        while self.timer >= interval:
            self.timer -= interval
            if self.frame < len(flist) - 1:
                self.frame += 1
            elif getattr(self, "_loop", True):
                self.frame = 0
            else:
                self.done = True

    def draw(self, surface: pygame.Surface, cx: int, cy: int):
        """Draw the current frame centered at (cx, cy) in screen coords."""
        flist = self.frames
        if not flist:
            return
        idx = min(self.frame, len(flist) - 1)
        img = flist[idx]
        rect = img.get_rect(center=(cx, cy))
        surface.blit(img, rect)


# ── Character loaders ────────────────────────────────────────────────────

def _try_load(folder: str, names: List[str]) -> Optional[List[pygame.Surface]]:
    """Try to load a sprite strip from the first matching filename in folder."""
    for name in names:
        path = os.path.join(folder, name)
        if os.path.exists(path):
            return load_strip(path)
    return None


def load_character_anims(
    pack: str, variant: str, render_size: Tuple[int, int]
) -> Dict[str, List[pygame.Surface]]:
    """Load standard animations for a character pack/variant.

    Returns a dict with keys: idle, walk, attack, hurt, dead.
    Falls back gracefully if some sheets are missing.
    """
    folder = os.path.join(ASSETS_DIR, pack, variant)
    if not os.path.isdir(folder):
        return _placeholder_anims(render_size)

    raw: Dict[str, List[pygame.Surface]] = {}

    idle = _try_load(folder, ["Idle.png"])
    if idle:
        raw["idle"] = idle

    walk = _try_load(folder, ["Walk.png", "Run.png"])
    if walk:
        raw["walk"] = walk

    attack = _try_load(folder, ["Attack 1.png", "Attack_1.png", "Attack.png"])
    if attack:
        raw["attack"] = attack

    hurt = _try_load(folder, ["Hurt.png"])
    if hurt:
        raw["hurt"] = hurt

    dead = _try_load(folder, ["Dead.png"])
    if dead:
        raw["dead"] = dead

    if not raw:
        return _placeholder_anims(render_size)

    if "idle" not in raw:
        raw["idle"] = list(raw.values())[0]

    scaled: Dict[str, List[pygame.Surface]] = {}
    for name, frames in raw.items():
        scaled[name] = scale_frames(frames, render_size)

    return scaled


# ── Tileset tile loaders ──────────────────────────────────────────────

def _extract_tile(sheet: pygame.Surface, local_id: int, columns: int) -> pygame.Surface:
    """Extract a single 16x16 tile from a tileset sheet by its local index."""
    row = local_id // columns
    col = local_id % columns
    rect = pygame.Rect(col * TILESET_TILE_PX, row * TILESET_TILE_PX,
                       TILESET_TILE_PX, TILESET_TILE_PX)
    return sheet.subsurface(rect).copy()


def load_floor_tiles(target_size: int) -> Dict[str, pygame.Surface]:
    """Load floor tiles from the maptileset, scaled to *target_size*.

    Returns dict with keys ``floor`` and ``floor_alt``.
    Falls back to an empty dict when the asset file is missing.
    """
    sheet_path = os.path.join(TILESET_DIR, "PNG", "walls_floor.png")
    if not os.path.exists(sheet_path):
        return {}

    sheet = pygame.image.load(sheet_path).convert_alpha()

    COLUMNS = 17
    FIRSTGID = 377

    floor_main = _extract_tile(sheet, 515 - FIRSTGID, COLUMNS)
    floor_dark = _extract_tile(sheet, 627 - FIRSTGID, COLUMNS)

    sz = (target_size, target_size)
    return {
        "floor": pygame.transform.scale(floor_main, sz),
        "floor_alt": pygame.transform.scale(floor_dark, sz),
    }


def _placeholder_anims(size: Tuple[int, int]) -> Dict[str, List[pygame.Surface]]:
    """Generate colored rectangle placeholders when assets are missing."""
    surf = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(surf, (200, 200, 200), (0, 0, *size), 0, border_radius=4)
    pygame.draw.rect(surf, (100, 100, 100), (0, 0, *size), 2, border_radius=4)
    return {"idle": [surf], "walk": [surf], "attack": [surf],
            "hurt": [surf], "dead": [surf]}
