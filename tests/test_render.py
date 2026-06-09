from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ai_mini_mart_receipt.models import UsageSnapshot
from ai_mini_mart_receipt.render import render_html, render_text, receipt_state, round_title
from scripts.generate_screenshots import stamp_text_offset, text_width


ROOT = Path(__file__).resolve().parents[1]


class ReceiptStateTest(unittest.TestCase):
    def test_cache_heavy_gets_cache_title(self):
        snap = UsageSnapshot(input_tokens=1000, cached_input_tokens=900, output_tokens=10)
        self.assertEqual(receipt_state(snap), "cache")
        self.assertEqual(round_title(snap, "zh-CN"), "缓存达人")

    def test_budget_gets_budget_title(self):
        snap = UsageSnapshot(input_tokens=100_000, output_tokens=1, estimate_usd=0.01)
        self.assertEqual(receipt_state(snap), "budget")
        self.assertEqual(round_title(snap, "zh-CN"), "预算警报")

    def test_reasoning_gets_reasoning_title(self):
        snap = UsageSnapshot(input_tokens=1000, output_tokens=100, reasoning_output_tokens=80)
        self.assertEqual(receipt_state(snap), "reasoning")
        self.assertEqual(round_title(snap, "zh-CN"), "推理加班")


class RenderTest(unittest.TestCase):
    def test_text_receipt_contains_generic_header_and_no_default_location(self):
        text = render_text(UsageSnapshot(input_tokens=1, output_tokens=2), "zh-CN")
        self.assertIn("AI MINI MART", text)
        self.assertNotIn("We" + "nge", text)
        self.assertNotIn(("We" + "nge").upper(), text)
        self.assertIn("感谢使用", text)

    def test_html_receipt_contains_custom_tip_controls_and_stamp(self):
        html = render_html(UsageSnapshot(input_tokens=1000, output_tokens=100, estimate_usd=0.25), "zh-CN")
        self.assertEqual(html.count('class="tip-option"'), 3)
        self.assertIn('data-tip-percent="15"', html)
        self.assertIn('data-tip-percent="18"', html)
        self.assertIn('data-tip-percent="20"', html)
        self.assertIn('id="tip-custom-input"', html)
        self.assertIn('data-tip-custom', html)
        self.assertIn('data-tip-stamp', html)
        self.assertIn("mini-mart-cashier-alive", html)
        self.assertNotIn("We" + "nge", html)
        self.assertNotIn(("We" + "nge").upper(), html)

    def test_html_receipt_accepts_named_style(self):
        html = render_html(UsageSnapshot(input_tokens=1, output_tokens=2), "zh-CN", style="ledger")
        self.assertIn("receipt-document--ledger", html)

    def test_html_receipt_rejects_unknown_style(self):
        with self.assertRaises(ValueError):
            render_html(UsageSnapshot(input_tokens=1, output_tokens=2), "zh-CN", style="unknown")


class CliTest(unittest.TestCase):
    def test_cli_writes_text_and_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            text_path = Path(tmp) / "receipt.txt"
            html_path = Path(tmp) / "receipt.html"
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "ai_mini_mart_receipt.cli",
                    "--input-tokens",
                    "1000",
                    "--cached-input-tokens",
                    "900",
                    "--output-tokens",
                    "100",
                    "--estimate-usd",
                    "0.25",
                    "--style",
                    "ledger",
                    "--write",
                    str(text_path),
                    "--write-html",
                    str(html_path),
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src"), "PYTHONIOENCODING": "utf-8"},
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("AI MINI MART", text_path.read_text(encoding="utf-8"))
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("mini-mart-cashier-cache", html)
            self.assertIn("receipt-document--ledger", html)

    def test_public_files_do_not_contain_old_private_brand(self):
        public_files = [
            ROOT / "README.md",
            ROOT / "pyproject.toml",
            ROOT / "src" / "ai_mini_mart_receipt" / "__init__.py",
            ROOT / "src" / "ai_mini_mart_receipt" / "cli.py",
            ROOT / "src" / "ai_mini_mart_receipt" / "models.py",
            ROOT / "src" / "ai_mini_mart_receipt" / "render.py",
            ROOT / "src" / "ai_mini_mart_receipt" / "assets.py",
        ]
        for path in public_files:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                marker = "We" + "nge"
                self.assertNotIn(marker, text)
                self.assertNotIn(marker.upper(), text)
                self.assertNotIn(marker.lower(), text)


class ProjectMetadataTest(unittest.TestCase):
    def test_project_declares_mit_license(self):
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn("MIT License", license_text)
        self.assertIn("Copyright (c) 2026 AI Mini Mart", license_text)
        self.assertIn("MIT License", readme)
        self.assertNotIn("No license has been selected yet", readme)
        self.assertIn('license = { text = "MIT" }', pyproject)

    def test_readme_references_screenshot_assets(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for screenshot in (
            "docs/screenshots/classic.png",
            "docs/screenshots/compact.png",
            "docs/screenshots/ledger.png",
        ):
            with self.subTest(screenshot=screenshot):
                self.assertIn(screenshot, readme)
                self.assertTrue((ROOT / screenshot).is_file())
        self.assertIn("--style", readme)


class ScreenshotGeneratorTest(unittest.TestCase):
    def test_paid_stamp_text_is_centered_inside_stamp(self):
        for scale in (3, 4):
            with self.subTest(scale=scale):
                stamp_width = 26 * scale
                left = stamp_text_offset("PAID", stamp_width, scale)
                right = stamp_width - left - text_width("PAID", scale)
                self.assertLessEqual(abs(left - right), scale)
                self.assertGreater(right, 0)


if __name__ == "__main__":
    unittest.main()
