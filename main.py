"""
Dungeon of Shadows — a 2D roguelike dungeon crawler.

Run:
    python lab4.py              # launch the game
    python lab4.py --seed 42    # deterministic dungeon

Requirements:
    pip install pygame-ce       # (or: pip install pygame)
"""

from __future__ import annotations
import argparse
import sys
import os

# Ensure sibling modules are importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description="Dungeon of Shadows")
    parser.add_argument("--seed", type=int, default=None,
                        help="Optional RNG seed for deterministic dungeons")
    args = parser.parse_args()

    try:
        import pygame
    except ImportError:
        print("pygame is required.  Install it with:")
        print("  pip install pygame-ce")
        print("  (or:  pip install pygame)")
        sys.exit(1)

    from game import Game
    game = Game(seed=args.seed)
    game.run()


if __name__ == "__main__":
    main()
