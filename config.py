"""Game-wide constants and configuration."""

from __future__ import annotations

# ── Display ──────────────────────────────────────────────────────────────
SCREEN_WIDTH  = 1024
SCREEN_HEIGHT = 768
FPS           = 60
TITLE         = "Dungeon of Shadows"
ZOOM          = 2       # 2x zoom: game renders at half-res then scales up

# ── Viewport (internal resolution the game world is drawn at) ────────────
VIEW_W = SCREEN_WIDTH  // ZOOM
VIEW_H = SCREEN_HEIGHT // ZOOM

# ── Tiles ────────────────────────────────────────────────────────────────
TILE_SIZE = 32
WALL      = 0
FLOOR     = 1
STAIRS    = 2

# ── Palette ──────────────────────────────────────────────────────────────
COLOR_BG        = (10, 10, 18)
COLOR_WALL      = (38, 42, 56)
COLOR_WALL_TOP  = (50, 55, 72)
COLOR_FLOOR     = (62, 66, 78)
COLOR_FLOOR_ALT = (58, 62, 74)
COLOR_STAIRS    = (50, 180, 90)

COLOR_PLAYER       = (70, 160, 255)
COLOR_PLAYER_DARK  = (40, 110, 200)
COLOR_ATTACK_ARC   = (140, 200, 255, 100)

COLOR_ENEMY        = (210, 55, 70)
COLOR_ENEMY_DARK   = (160, 35, 50)
COLOR_BOSS         = (190, 50, 230)
COLOR_BOSS_DARK    = (130, 30, 170)

COLOR_HP_FILL   = (200, 40, 40)
COLOR_HP_BG     = (50, 18, 18)
COLOR_HP_BORDER = (100, 30, 30)
COLOR_MP_FILL   = (50, 100, 220)

COLOR_GOLD      = (255, 210, 50)
COLOR_POTION    = (60, 210, 120)
COLOR_WEAPON    = (180, 180, 200)
COLOR_ARMOR     = (140, 120, 90)

COLOR_UI_BG       = (20, 20, 30)
COLOR_UI_BORDER   = (80, 80, 100)
COLOR_UI_TEXT      = (220, 220, 230)
COLOR_UI_HIGHLIGHT = (100, 140, 220)
COLOR_UI_DIM       = (120, 120, 140)
COLOR_UI_TITLE     = (255, 220, 80)
COLOR_UI_SUCCESS   = (80, 220, 120)
COLOR_UI_DANGER    = (220, 60, 70)

COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

# ── Player defaults ─────────────────────────────────────────────────────
PLAYER_SPEED      = 3
PLAYER_BASE_HP    = 120
PLAYER_BASE_ATK   = 14
PLAYER_BASE_DEF   = 3
PLAYER_SIZE       = 12     # collision radius – small so corridors feel roomy

ATTACK_RANGE    = 52
ATTACK_COOLDOWN = 400   # ms
ATTACK_DURATION = 200   # ms  (visual arc)

# ── Enemies ──────────────────────────────────────────────────────────────
ENEMY_SIZE         = 12
ENEMY_DETECT_RANGE = 200
ENEMY_SPEED        = 1.6
ENEMY_BASE_HP      = 30
ENEMY_BASE_ATK     = 6
ENEMY_KNOCKBACK    = 8

BOSS_SIZE      = 32
BOSS_HP_MUL    = 5.0
BOSS_ATK_MUL   = 2.0
BOSS_SPEED_MUL = 0.8

# ── Sprite rendering sizes (pixels) ─────────────────────────────────────
PLAYER_SPRITE_SIZE = (64, 64)
ENEMY_SPRITE_SIZE  = (56, 56)
BOSS_SPRITE_SIZE   = (80, 80)

# ── Floor-to-enemy-type mapping ─────────────────────────────────────────
#    (asset_pack, variant, display_name)
FLOOR_ENEMY_TYPE = {
    1:  ("skeleton-enemy", "Skeleton_Warrior",  "Skeleton Warrior"),
    2:  ("skeleton-enemy", "Skeleton_Spearman", "Skeleton Spearman"),
    3:  ("gorgon-enemy",   "Gorgon_1",          "Gorgon"),
    4:  ("gorgon-enemy",   "Gorgon_2",          "Gorgon Mage"),
    5:  ("minotaur-enemy", "Minotaur_1",        "Minotaur"),         # BOSS
    6:  ("yokai-enemy",    "Kitsune",            "Kitsune"),
    7:  ("yokai-enemy",    "Karasu_tengu",       "Karasu Tengu"),
    8:  ("gorgon-enemy",   "Gorgon_3",          "Elder Gorgon"),
    9:  ("yokai-enemy",    "Yamabushi_tengu",    "Yamabushi Tengu"),
    10: ("minotaur-enemy", "Minotaur_3",        "Minotaur Lord"),    # FINAL BOSS
}

PLAYER_SPRITE = ("knight-hero", "Knight_1")

# ── Dungeon generation ──────────────────────────────────────────────────
DUNGEON_WIDTH   = 60
DUNGEON_HEIGHT  = 45
ROOM_MIN_SIZE   = 4
ROOM_MAX_SIZE   = 10
ROOM_PADDING    = 2

BASE_ROOMS      = 5
ROOMS_PER_FLOOR = 1
MAX_ROOMS       = 12

ENEMIES_BASE      = 3
ENEMIES_PER_FLOOR = 1

BOSS_ROOM_W = 16
BOSS_ROOM_H = 14

# ── Floors ───────────────────────────────────────────────────────────────
TOTAL_FLOORS = 10
BOSS_FLOORS  = frozenset({5, 10})

# ── Inventory ────────────────────────────────────────────────────────────
INVENTORY_CAPACITY = 15

# ── Loot ─────────────────────────────────────────────────────────────────
LOOT_DROP_CHANCE      = 0.65
BOSS_RARE_DROP_CHANCE = 1.0
COMMON_WEIGHT = 70
RARE_WEIGHT   = 30

# ── Item pickup ──────────────────────────────────────────────────────────
AUTO_PICKUP_RANGE = 28   # pixels – walk-over auto-collect
MANUAL_PICKUP_RANGE = 48 # pixels – F key pickup

# ── Scaling helpers ──────────────────────────────────────────────────────
def enemy_hp(floor: int) -> int:
    return int(ENEMY_BASE_HP * (1 + 0.25 * (floor - 1)))

def enemy_atk(floor: int) -> int:
    return int(ENEMY_BASE_ATK * (1 + 0.18 * (floor - 1)))

def enemy_speed(floor: int) -> float:
    return ENEMY_SPEED + 0.08 * (floor - 1)

def rooms_for_floor(floor: int) -> int:
    if floor in BOSS_FLOORS:
        return 1
    return min(BASE_ROOMS + ROOMS_PER_FLOOR * (floor - 1), MAX_ROOMS)

def enemies_for_floor(floor: int) -> int:
    if floor in BOSS_FLOORS:
        return 1
    return ENEMIES_BASE + ENEMIES_PER_FLOOR * (floor - 1)
