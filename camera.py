

from __future__ import annotations
from config import VIEW_W, VIEW_H


class Camera:

    def __init__(self, map_pixel_w: int, map_pixel_h: int):
        self.x = 0
        self.y = 0
        self.map_w = map_pixel_w
        self.map_h = map_pixel_h

    def update(self, target_x: float, target_y: float):
        self.x = int(target_x - VIEW_W // 2)
        self.y = int(target_y - VIEW_H // 2)

        self.x = max(0, min(self.x, self.map_w - VIEW_W))
        self.y = max(0, min(self.y, self.map_h - VIEW_H))

    def apply(self, wx: float, wy: float):
        return int(wx) - self.x, int(wy) - self.y
