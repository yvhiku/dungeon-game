"""Inventory storage and equipment manager."""

from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

from config import INVENTORY_CAPACITY
from items import Item, ItemType, Weapon, Armor, Potion, Gold

if TYPE_CHECKING:
    from player import Player


class Inventory:
    """Fixed-capacity item bag with stacking support."""

    def __init__(self, capacity: int = INVENTORY_CAPACITY):
        self.capacity = capacity
        self.items: List[Item] = []
        self.gold: int = 0

    @property
    def full(self) -> bool:
        return len(self.items) >= self.capacity

    def add(self, item: Item) -> bool:
        if isinstance(item, Gold):
            self.gold += item.amount
            return True

        if item.stackable:
            for existing in self.items:
                if existing.name == item.name and existing.item_type == item.item_type:
                    existing.stack_with(item)
                    return True

        if self.full:
            return False
        self.items.append(item)
        return True

    def remove(self, index: int) -> Optional[Item]:
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None

    def get(self, index: int) -> Optional[Item]:
        if 0 <= index < len(self.items):
            return self.items[index]
        return None

    def __len__(self) -> int:
        return len(self.items)


class EquipmentManager:
    """Manage equipped weapon and armor, applying stat bonuses."""

    def __init__(self):
        self.weapon: Optional[Weapon] = None
        self.armor: Optional[Armor] = None

    @property
    def weapon_bonus(self) -> int:
        return self.weapon.attack_bonus if self.weapon else 0

    @property
    def armor_bonus(self) -> int:
        return self.armor.defense_bonus if self.armor else 0

    def equip(self, item: Item, inventory: Inventory) -> Optional[Item]:
        """Equip item from inventory. Returns previously equipped item (put back in inv)."""
        old: Optional[Item] = None
        if isinstance(item, Weapon):
            old = self.weapon
            self.weapon = item
        elif isinstance(item, Armor):
            old = self.armor
            self.armor = item
        else:
            return None

        if item in inventory.items:
            inventory.items.remove(item)
        if old is not None:
            inventory.add(old)
        return old

    def unequip_weapon(self, inventory: Inventory) -> bool:
        if self.weapon is None:
            return False
        if inventory.full:
            return False
        inventory.add(self.weapon)
        self.weapon = None
        return True

    def unequip_armor(self, inventory: Inventory) -> bool:
        if self.armor is None:
            return False
        if inventory.full:
            return False
        inventory.add(self.armor)
        self.armor = None
        return True
