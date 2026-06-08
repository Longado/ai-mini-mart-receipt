#!/usr/bin/env python3
"""Generate deterministic AI Mini Mart 1-bit-style PNG assets."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src" / "ai_mini_mart_receipt" / "assets"
GRID = 32
SIZE = 256
SCALE = SIZE // GRID
BLACK = 0
WHITE = 255


def canvas() -> list[list[int]]:
    return [[WHITE for _ in range(GRID)] for _ in range(GRID)]


def rect(pixels: list[list[int]], x: int, y: int, w: int, h: int, color: int = BLACK) -> None:
    for yy in range(max(0, y), min(GRID, y + h)):
        for xx in range(max(0, x), min(GRID, x + w)):
            pixels[yy][xx] = color


def outline(pixels: list[list[int]], x: int, y: int, w: int, h: int, thick: int = 1) -> None:
    rect(pixels, x, y, w, thick)
    rect(pixels, x, y + h - thick, w, thick)
    rect(pixels, x, y, thick, h)
    rect(pixels, x + w - thick, y, thick, h)


def draw_robot(pixels: list[list[int]], mood: str) -> None:
    outline(pixels, 8, 3, 16, 11, 2)
    rect(pixels, 6, 7, 2, 4)
    rect(pixels, 24, 7, 2, 4)
    rect(pixels, 14, 14, 4, 2)
    rect(pixels, 10, 16, 12, 3)
    outline(pixels, 4, 18, 24, 7, 2)
    rect(pixels, 7, 21, 5, 1)
    rect(pixels, 20, 21, 5, 1)
    rect(pixels, 11, 25, 3, 4)
    rect(pixels, 18, 25, 3, 4)
    rect(pixels, 10, 29, 5, 1)
    rect(pixels, 17, 29, 5, 1)
    if mood == "budget":
        rect(pixels, 11, 7, 4, 1)
        rect(pixels, 18, 7, 4, 1)
        rect(pixels, 12, 8, 2, 1)
        rect(pixels, 20, 8, 2, 1)
        rect(pixels, 14, 11, 4, 1)
    elif mood == "reasoning":
        rect(pixels, 11, 7, 2, 2)
        rect(pixels, 19, 7, 2, 2)
        rect(pixels, 14, 11, 4, 1)
    elif mood == "cache":
        rect(pixels, 11, 7, 3, 2)
        rect(pixels, 19, 7, 3, 2)
        rect(pixels, 13, 11, 6, 1)
    else:
        rect(pixels, 11, 7, 4, 1)
        rect(pixels, 18, 7, 4, 1)
        rect(pixels, 13, 11, 6, 1)


def add_cache_props(pixels: list[list[int]]) -> None:
    for y in (12, 14, 16):
        outline(pixels, 3, y, 7, 2)
        rect(pixels, 5, y + 1, 1, 1)
        rect(pixels, 8, y + 1, 1, 1)
    rect(pixels, 23, 15, 2, 3)
    rect(pixels, 26, 14, 2, 4)
    rect(pixels, 29, 13, 2, 5)


def add_budget_props(pixels: list[list[int]]) -> None:
    outline(pixels, 22, 13, 7, 8)
    rect(pixels, 24, 15, 3, 1)
    rect(pixels, 23, 17, 5, 1)
    rect(pixels, 24, 19, 3, 1)
    rect(pixels, 5, 14, 5, 1)
    rect(pixels, 6, 15, 5, 1)
    rect(pixels, 7, 16, 4, 1)


def add_reasoning_props(pixels: list[list[int]]) -> None:
    rect(pixels, 15, 0, 2, 1)
    outline(pixels, 13, 1, 6, 5)
    rect(pixels, 15, 6, 2, 2)
    rect(pixels, 12, 2, 1, 1)
    rect(pixels, 19, 2, 1, 1)
    rect(pixels, 11, 5, 1, 1)
    rect(pixels, 20, 5, 1, 1)


def add_alive_props(pixels: list[list[int]]) -> None:
    outline(pixels, 6, 14, 5, 4)
    rect(pixels, 8, 15, 2, 1)
    rect(pixels, 8, 17, 2, 1)
    outline(pixels, 23, 14, 4, 4)
    rect(pixels, 24, 16, 2, 1)


FONT = {
    "P": ("1110", "1001", "1001", "1110", "1000", "1000", "1000"),
    "A": ("0110", "1001", "1001", "1111", "1001", "1001", "1001"),
    "I": ("111", "010", "010", "010", "010", "010", "111"),
    "D": ("1110", "1001", "1001", "1001", "1001", "1001", "1110"),
}


def draw_text(pixels: list[list[int]], text: str, x: int, y: int) -> None:
    cursor = x
    for char in text:
        glyph = FONT[char]
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    rect(pixels, cursor + gx, y + gy, 1, 1)
        cursor += len(glyph[0]) + 1


def robot_asset(mood: str) -> list[list[int]]:
    pixels = canvas()
    draw_robot(pixels, mood)
    if mood == "cache":
        add_cache_props(pixels)
    elif mood == "budget":
        add_budget_props(pixels)
    elif mood == "reasoning":
        add_reasoning_props(pixels)
    else:
        add_alive_props(pixels)
    return pixels


def stamp_paid() -> list[list[int]]:
    pixels = canvas()
    outline(pixels, 3, 8, 26, 16, 2)
    outline(pixels, 5, 10, 22, 12, 1)
    draw_text(pixels, "PAID", 7, 13)
    rect(pixels, 1, 6, 4, 1)
    rect(pixels, 27, 25, 4, 1)
    return pixels


def png_bytes(logical: list[list[int]]) -> bytes:
    rows: list[bytes] = []
    for row in logical:
        scaled_row = bytes(value for value in row for _ in range(SCALE))
        for _ in range(SCALE):
            rows.append(b"\x00" + scaled_row)
    raw = b"".join(rows)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 0, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def write_asset(name: str, logical: list[list[int]]) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / name).write_bytes(png_bytes(logical))


def main() -> int:
    write_asset("mini-mart-cashier-alive.png", robot_asset("alive"))
    write_asset("mini-mart-cashier-budget.png", robot_asset("budget"))
    write_asset("mini-mart-cashier-cache.png", robot_asset("cache"))
    write_asset("mini-mart-cashier-reasoning.png", robot_asset("reasoning"))
    write_asset("mini-mart-stamp-paid.png", stamp_paid())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
