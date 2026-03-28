"""Item hierarchy: Weapon, Armor, Potion, Gold."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class ItemType(Enum):
    WEAPON = auto()
    ARMOR  = auto()
    POTION = auto()
    GOLD   = auto()


@dataclass
class Item:
    name: str
    item_type: ItemType
    description: str = ""
    stackable: bool = False
    quantity: int = 1
    rarity: str = "common"  # "common" | "rare" | "epic"

    @property
    def display_name(self) -> str:
        if self.stackable and self.quantity > 1:
            return f"{self.name} x{self.quantity}"
        return self.name

    def stack_with(self, other: Item) -> bool:
        if (self.stackable and other.stackable
                and self.name == other.name
                and self.item_type == other.item_type):
            self.quantity += other.quantity
            return True
        return False


@dataclass
class Weapon(Item):
    attack_bonus: int = 0

    def __post_init__(self):
        self.item_type = ItemType.WEAPON
        if not self.description:
            self.description = f"ATK +{self.attack_bonus}"


@dataclass
class Armor(Item):
    defense_bonus: int = 0

    def __post_init__(self):
        self.item_type = ItemType.ARMOR
        if not self.description:
            self.description = f"DEF +{self.defense_bonus}"


@dataclass
class Potion(Item):
    heal_amount: int = 25

    def __post_init__(self):
        self.item_type = ItemType.POTION
        self.stackable = True
        if not self.description:
            self.description = f"Heals {self.heal_amount} HP"


@dataclass
class Gold(Item):
    amount: int = 0

    def __post_init__(self):
        self.item_type = ItemType.GOLD
        self.stackable = True
        self.name = "Gold"
        self.description = f"{self.amount} gold coins"
        self.quantity = self.amount


# ── Predefined item tables ──────────────────────────────────────────────

def _common_items(floor: int):
    return [
        Gold(name="Gold", amount=5 + floor * 3, item_type=ItemType.GOLD),
        Potion(name="Health Potion", heal_amount=20 + floor * 3, item_type=ItemType.POTION),
    ]


def _rare_items(floor: int):
    tier = (floor - 1) // 3  # 0, 1, 2, 3
    weapons = [
        Weapon(name="Iron Sword", attack_bonus=4 + tier * 3, item_type=ItemType.WEAPON, rarity="rare"),
        Weapon(name="War Axe", attack_bonus=6 + tier * 3, item_type=ItemType.WEAPON, rarity="rare"),
        Weapon(name="Shadow Blade", attack_bonus=8 + tier * 4, item_type=ItemType.WEAPON, rarity="epic"),
    ]
    armors = [
        Armor(name="Leather Armor", defense_bonus=3 + tier * 2, item_type=ItemType.ARMOR, rarity="rare"),
        Armor(name="Chain Mail", defense_bonus=5 + tier * 2, item_type=ItemType.ARMOR, rarity="rare"),
        Armor(name="Dark Plate", defense_bonus=7 + tier * 3, item_type=ItemType.ARMOR, rarity="epic"),
    ]
    return weapons + armors


ITEM_TABLES = {
    "common": _common_items,
    "rare": _rare_items,
}
