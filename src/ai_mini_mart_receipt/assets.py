"""Asset loading helpers."""

from __future__ import annotations

from base64 import b64encode
from functools import lru_cache
from pathlib import Path


ASSET_DIR = Path(__file__).resolve().parent / "assets"


@lru_cache(maxsize=None)
def asset_data_uri(name: str) -> str:
    path = ASSET_DIR / name
    data = path.read_bytes()
    return "data:image/png;base64," + b64encode(data).decode("ascii")
