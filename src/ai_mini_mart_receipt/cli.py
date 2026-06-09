"""Command line entrypoint for AI Mini Mart token receipts."""

from __future__ import annotations

import argparse
from pathlib import Path

from .models import UsageSnapshot
from .render import RECEIPT_STYLES, render_html, render_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render an AI Mini Mart token receipt.")
    parser.add_argument("--provider", default="OPENAI")
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--input-tokens", type=int, default=0)
    parser.add_argument("--cached-input-tokens", type=int, default=0)
    parser.add_argument("--output-tokens", type=int, default=0)
    parser.add_argument("--reasoning-output-tokens", type=int, default=0)
    parser.add_argument("--total-tokens", type=int, default=0)
    parser.add_argument("--context-window", type=int)
    parser.add_argument("--estimate-usd", type=float)
    parser.add_argument("--location", default="")
    parser.add_argument("--timestamp", default="2026-06-05 09:44:18")
    parser.add_argument("--language", "--lang", choices=("en", "zh-CN", "zh"), default="zh-CN")
    parser.add_argument("--style", choices=RECEIPT_STYLES, default="classic")
    parser.add_argument("--output", choices=("text", "html"), default="text")
    parser.add_argument("--write", type=Path)
    parser.add_argument("--write-html", type=Path)
    return parser


def snapshot_from_args(args: argparse.Namespace) -> UsageSnapshot:
    return UsageSnapshot(
        provider=args.provider,
        model=args.model,
        input_tokens=args.input_tokens,
        cached_input_tokens=args.cached_input_tokens,
        output_tokens=args.output_tokens,
        reasoning_output_tokens=args.reasoning_output_tokens,
        total_tokens=args.total_tokens,
        context_window=args.context_window,
        estimate_usd=args.estimate_usd,
        location=args.location,
        timestamp=args.timestamp,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    snapshot = snapshot_from_args(args)
    language = "zh-CN" if args.language == "zh" else args.language
    text = render_text(snapshot, language)
    html = render_html(snapshot, language, style=args.style) if args.output == "html" or args.write_html else None
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text((html if args.output == "html" else text) + "\n", encoding="utf-8")
    if args.write_html:
        args.write_html.parent.mkdir(parents=True, exist_ok=True)
        args.write_html.write_text((html or render_html(snapshot, language, style=args.style)) + "\n", encoding="utf-8")
    if not args.write:
        print(html if args.output == "html" else text)
    elif args.write_html:
        print(f"wrote to: {args.write}")
        print(f"wrote to: {args.write_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
