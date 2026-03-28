"""Loot drop manager with rarity-weighted tables."""

from __future__ import annotations
import random
from typing import Optional, List

from items import Item, ITEM_TABLES
from config import LOOT_DROP_CHANCE, BOSS_RARE_DROP_CHANCE, COMMON_WEIGHT, RARE_WEIGHT


class LootManager:

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def roll_enemy_drop(self, floor: int) -> Optional[Item]:
        if self.rng.random() > LOOT_DROP_CHANCE:
            return None
        return self._pick_item(floor, boss=False)

    def roll_boss_drop(self, floor: int) -> List[Item]:
        drops: List[Item] = []
        rare = self._pick_from_table("rare", floor)
        if rare:
            drops.append(rare)
        common = self._pick_from_table("common", floor)
        if common:
            drops.append(common)
        return drops

    def _pick_item(self, floor: int, boss: bool) -> Optional[Item]:
        roll = self.rng.randint(1, 100)
        if boss or roll > COMMON_WEIGHT:
            return self._pick_from_table("rare", floor)
        return self._pick_from_table("common", floor)

    def _pick_from_table(self, rarity: str, floor: int) -> Optional[Item]:
        factory = ITEM_TABLES.get(rarity)
        if not factory:
            return None
        pool = factory(floor)
        if not pool:
            return None
        return self.rng.choice(pool)
