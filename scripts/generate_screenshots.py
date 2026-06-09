#!/usr/bin/env python3
"""Generate README screenshot PNGs for the receipt styles.

This script intentionally uses only the Python standard library so documentation
previews can be regenerated without installing image dependencies.
"""

from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ai_mini_mart_receipt.models import UsageSnapshot, parse_timestamp
from ai_mini_mart_receipt.render import (
    LABELS,
    RECEIPT_STYLES,
    fmt_int,
    footer,
    money,
    product_name,
    receipt_id,
    rows,
    token_rows,
)


SCREENSHOTS = ROOT / "docs" / "screenshots"
BLACK = 0
WHITE = 255


STYLE = {
    "classic": {"width": 620, "pad": 46, "logo": 5, "text": 3, "small": 2, "rule": 4, "gap": 18},
    "compact": {"width": 500, "pad": 32, "logo": 3, "text": 2, "small": 2, "rule": 3, "gap": 12},
    "ledger": {"width": 620, "pad": 46, "logo": 4, "text": 3, "small": 2, "rule": 3, "gap": 14},
}


FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("111", "010", "010", "010", "010", "010", "111"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("010", "110", "010", "010", "010", "010", "111"),
    "2": ("11110", "00001", "00001", "01110", "10000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("10001", "10001", "10001", "11111", "00001", "00001", "00001"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01111", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "11110"),
    " ": ("0", "0", "0", "0", "0", "0", "0"),
    ".": ("0", "0", "0", "0", "0", "0", "1"),
    ",": ("0", "0", "0", "0", "0", "1", "1"),
    ":": ("0", "1", "1", "0", "1", "1", "0"),
    "#": ("01010", "11111", "01010", "01010", "11111", "01010", "01010"),
    "_": ("0", "0", "0", "0", "0", "0", "1"),
    "-": ("0", "0", "0", "111", "0", "0", "0"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "$": ("01111", "10100", "10100", "01110", "00101", "00101", "11110"),
    "%": ("10001", "00010", "00100", "01000", "10000", "00010", "10001"),
    "(": ("01", "10", "10", "10", "10", "10", "01"),
    ")": ("10", "01", "01", "01", "01", "01", "10"),
    "<": ("001", "010", "100", "010", "001", "000", "000"),
    ">": ("100", "010", "001", "010", "100", "000", "000"),
    "|": ("1", "1", "1", "1", "1", "1", "1"),
}


def sample_snapshot() -> UsageSnapshot:
    return UsageSnapshot(
        provider="OPENAI",
        model="gpt-5.5",
        input_tokens=147_880,
        cached_input_tokens=146_816,
        output_tokens=232,
        reasoning_output_tokens=115,
        context_window=258_400,
        estimate_usd=0.823218,
        timestamp="2026-06-09 10:24:18",
    )


def canvas(width: int, height: int) -> list[bytearray]:
    return [bytearray([WHITE]) * width for _ in range(height)]


def rect(pixels: list[bytearray], x: int, y: int, w: int, h: int, color: int = BLACK) -> None:
    height = len(pixels)
    width = len(pixels[0])
    for yy in range(max(0, y), min(height, y + h)):
        for xx in range(max(0, x), min(width, x + w)):
            pixels[yy][xx] = color


def outline(pixels: list[bytearray], x: int, y: int, w: int, h: int, thick: int = 2) -> None:
    rect(pixels, x, y, w, thick)
    rect(pixels, x, y + h - thick, w, thick)
    rect(pixels, x, y, thick, h)
    rect(pixels, x + w - thick, y, thick, h)


def hline(pixels: list[bytearray], x1: int, x2: int, y: int, thick: int) -> None:
    rect(pixels, x1, y, max(1, x2 - x1), thick)


def glyph(char: str) -> tuple[str, ...]:
    return FONT.get(char.upper(), FONT[" "])


def text_width(text: str, scale: int) -> int:
    width = 0
    for char in text.upper():
        width += (len(glyph(char)[0]) + 1) * scale
    return max(0, width - scale)


def draw_text(pixels: list[bytearray], x: int, y: int, text: str, scale: int) -> int:
    cursor = x
    for char in text.upper():
        rows_ = glyph(char)
        for gy, row in enumerate(rows_):
            for gx, bit in enumerate(row):
                if bit == "1":
                    rect(pixels, cursor + gx * scale, y + gy * scale, scale, scale)
        cursor += (len(rows_[0]) + 1) * scale
    return y + 7 * scale


def center_text(pixels: list[bytearray], y: int, text: str, scale: int) -> int:
    width = len(pixels[0])
    x = max(0, (width - text_width(text, scale)) // 2)
    return draw_text(pixels, x, y, text, scale)


def fit_text(text: str, max_width: int, scale: int) -> str:
    text = text.upper()
    if text_width(text, scale) <= max_width:
        return text
    suffix = "..."
    while text and text_width(text + suffix, scale) > max_width:
        text = text[:-1]
    return text + suffix if text else suffix


def draw_row(
    pixels: list[bytearray],
    y: int,
    pad: int,
    label: str,
    value: str,
    scale: int,
    ledger: bool = False,
) -> int:
    width = len(pixels[0])
    right = width - pad
    value = value.upper()
    value_width = text_width(value, scale)
    label = fit_text(label, max(20, right - pad - value_width - 18), scale)
    draw_text(pixels, pad, y, label, scale)
    draw_text(pixels, right - value_width, y, value, scale)
    row_height = 7 * scale + 11
    if ledger:
        hline(pixels, pad, right, y + row_height - 2, 1)
    return y + row_height


def draw_rule(pixels: list[bytearray], y: int, pad: int, thick: int = 3, double: bool = False) -> int:
    width = len(pixels[0])
    hline(pixels, pad, width - pad, y, thick)
    if double:
        hline(pixels, pad, width - pad, y + 7, 1)
        return y + 15
    return y + thick + 8


def draw_robot(pixels: list[bytearray], x: int, y: int, scale: int) -> None:
    def block(gx: int, gy: int, gw: int, gh: int) -> None:
        rect(pixels, x + gx * scale, y + gy * scale, gw * scale, gh * scale)

    def box(gx: int, gy: int, gw: int, gh: int, thick: int = 1) -> None:
        outline(pixels, x + gx * scale, y + gy * scale, gw * scale, gh * scale, thick * scale)

    box(8, 3, 16, 11, 2)
    block(6, 7, 2, 4)
    block(24, 7, 2, 4)
    block(11, 7, 3, 2)
    block(19, 7, 3, 2)
    block(13, 11, 6, 1)
    block(14, 14, 4, 2)
    block(10, 16, 12, 3)
    box(4, 18, 24, 7, 2)
    block(7, 21, 5, 1)
    block(20, 21, 5, 1)
    block(11, 25, 3, 4)
    block(18, 25, 3, 4)
    block(10, 29, 5, 1)
    block(17, 29, 5, 1)
    box(3, 12, 7, 2, 1)
    box(3, 14, 7, 2, 1)
    box(3, 16, 7, 2, 1)


def draw_stamp(pixels: list[bytearray], x: int, y: int, scale: int) -> None:
    outline(pixels, x, y, 26 * scale, 16 * scale, 2 * scale)
    outline(pixels, x + 2 * scale, y + 2 * scale, 22 * scale, 12 * scale, scale)
    draw_text(pixels, x + 5 * scale, y + 5 * scale, "PAID", scale)


def png_bytes(pixels: list[bytearray]) -> bytes:
    height = len(pixels)
    width = len(pixels[0])
    raw = b"".join(b"\x00" + bytes(row) for row in pixels)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def render_style(style: str) -> bytes:
    cfg = STYLE[style]
    snapshot = sample_snapshot()
    labels = LABELS["en"]
    pixels = canvas(cfg["width"], 1700)
    y = cfg["pad"]
    pad = cfg["pad"]

    if style == "ledger":
        outline(pixels, 20, 20, cfg["width"] - 40, 1660, 3)
        logo_box_y = y
        logo_box_h = 32 * cfg["logo"] + 32
        outline(pixels, pad, logo_box_y, cfg["width"] - pad * 2, logo_box_h, 2)
        y += 16

    robot_size = 32 * cfg["logo"]
    draw_robot(pixels, (cfg["width"] - robot_size) // 2, y, cfg["logo"])
    if style == "ledger":
        y = logo_box_y + logo_box_h + cfg["gap"]
    else:
        y += robot_size + cfg["gap"]
    y = center_text(pixels, y, "AI MINI MART", cfg["text"]) + cfg["gap"]
    if style == "ledger":
        y = draw_rule(pixels, y, pad, thick=2)
    y = center_text(pixels, y, labels["thanks"].format(product=product_name(snapshot)), cfg["small"]) + 8
    y = center_text(pixels, y, labels["receipt"].format(rid=receipt_id(snapshot)), cfg["small"]) + 8
    date_text = parse_timestamp(snapshot.timestamp).strftime("%Y-%m-%d %H:%M:%S")
    y = center_text(pixels, y, labels["date"].format(date=date_text), cfg["small"]) + cfg["gap"]

    y = draw_rule(pixels, y, pad, thick=cfg["rule"], double=style == "ledger")
    for label, value in rows(snapshot, "en"):
        y = draw_row(pixels, y, pad, label, value, cfg["text"], ledger=style == "ledger")
    y = draw_rule(pixels, y + cfg["gap"] // 2, pad, thick=2)
    y = draw_row(pixels, y, pad, labels["item"], labels["tokens"], cfg["text"], ledger=style == "ledger")
    y = draw_rule(pixels, y, pad, thick=2)
    for label, value in token_rows(snapshot, "en"):
        y = draw_row(pixels, y, pad, label, value, cfg["text"], ledger=style == "ledger")
    y = draw_rule(pixels, y + cfg["gap"], pad, thick=cfg["rule"], double=style == "ledger")
    y = draw_row(pixels, y, pad, labels["total"], f"{fmt_int(snapshot.normalized_total())} Tokens", cfg["text"], ledger=style == "ledger")
    y = draw_rule(pixels, y + cfg["gap"] // 2, pad, thick=2)
    y = draw_row(pixels, y, pad, labels["estimate"], money(snapshot.estimate_usd), cfg["text"], ledger=style == "ledger")
    y = draw_row(pixels, y, pad, labels["price"], snapshot.model, cfg["text"], ledger=style == "ledger")

    tip_percent = 18
    subtotal = float(snapshot.estimate_usd or 0.0)
    tip_amount = subtotal * tip_percent / 100
    y = draw_rule(pixels, y + cfg["gap"], pad, thick=2)
    y = draw_row(pixels, y, pad, labels["subtotal"], money(subtotal), cfg["text"], ledger=style == "ledger")
    y = draw_row(pixels, y, pad, f'{labels["tip"]} ({tip_percent}%)', money(tip_amount), cfg["text"], ledger=style == "ledger")
    y = draw_row(pixels, y, pad, labels["grand"], money(subtotal + tip_amount), cfg["text"], ledger=style == "ledger")

    stamp_scale = 3 if style == "compact" else 4
    stamp_width = 26 * stamp_scale
    draw_stamp(pixels, (cfg["width"] - stamp_width) // 2, y + cfg["gap"], stamp_scale)
    y += 16 * stamp_scale + cfg["gap"] * 2

    y = draw_rule(pixels, y, pad, thick=cfg["rule"], double=style == "ledger")
    y = center_text(pixels, y, footer(snapshot, "en"), cfg["small"]) + cfg["gap"]
    y = center_text(pixels, y, "|||| ||| || |||| | ||| || |||||", cfg["small"]) + 8
    y = center_text(pixels, y, receipt_id(snapshot), cfg["small"]) + pad
    cropped = pixels[: min(len(pixels), y)]
    return png_bytes(cropped)


def main() -> int:
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    for style in RECEIPT_STYLES:
        (SCREENSHOTS / f"{style}.png").write_bytes(render_style(style))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
