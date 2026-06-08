"""Data model for AI Mini Mart receipt snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


DEFAULT_TIMESTAMP = "2026-06-05 09:44:18"


@dataclass
class UsageSnapshot:
    provider: str = "OPENAI"
    model: str = "gpt-5.5"
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_output_tokens: int = 0
    total_tokens: int = 0
    context_window: int | None = None
    estimate_usd: float | None = None
    location: str = ""
    timestamp: str = DEFAULT_TIMESTAMP

    def normalized_total(self) -> int:
        if self.total_tokens:
            return self.total_tokens
        return int(self.input_tokens) + int(self.output_tokens)


def parse_timestamp(value: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return datetime.now().replace(microsecond=0)
