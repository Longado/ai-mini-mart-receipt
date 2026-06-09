# Receipt Styles And Screenshots Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add selectable HTML receipt styles and README screenshot assets for AI Mini Mart Receipt.

**Architecture:** Keep style selection inside `render_html()` and the CLI. Generate documentation screenshots with a separate script so runtime package behavior stays small.

**Tech Stack:** Python 3.9, stdlib `unittest`, package renderer, optional Pillow for screenshot generation.

---

### Task 1: Renderer And CLI Style Option

**Files:**
- Modify: `src/ai_mini_mart_receipt/render.py`
- Modify: `src/ai_mini_mart_receipt/cli.py`
- Test: `tests/test_render.py`

- [ ] **Step 1: Write the failing renderer and CLI tests**

Add tests that call:

```python
html = render_html(UsageSnapshot(input_tokens=1, output_tokens=2), "zh-CN", style="ledger")
self.assertIn("receipt-document--ledger", html)

with self.assertRaises(ValueError):
    render_html(UsageSnapshot(input_tokens=1, output_tokens=2), "zh-CN", style="unknown")
```

Also extend the CLI smoke test arguments with:

```python
"--style",
"ledger",
```

and assert the written HTML contains:

```python
"receipt-document--ledger"
```

- [ ] **Step 2: Run tests to verify red**

Run:

```bash
PYTHONPATH=src /usr/bin/python3 -m unittest tests.test_render.RenderTest tests.test_render.CliTest -v
```

Expected: failures because `render_html()` does not accept `style` yet and CLI does not define `--style`.

- [ ] **Step 3: Implement style validation and CSS classes**

Add:

```python
RECEIPT_STYLES = ("classic", "compact", "ledger")

def normalize_style(style: str) -> str:
    if style not in RECEIPT_STYLES:
        raise ValueError(f"unknown receipt style: {style}")
    return style
```

Change `render_html(snapshot, language="zh-CN")` to `render_html(snapshot, language="zh-CN", style="classic")`, add a document class `receipt-document receipt-document--{style}`, and add CSS overrides for `compact` and `ledger`.

In `cli.py`, import `RECEIPT_STYLES`, add `--style` choices, and pass `args.style` into `render_html()`.

- [ ] **Step 4: Run tests to verify green**

Run:

```bash
PYTHONPATH=src /usr/bin/python3 -m unittest tests.test_render.RenderTest tests.test_render.CliTest -v
```

Expected: selected tests pass.

### Task 2: Screenshot Assets And README

**Files:**
- Create: `scripts/generate_screenshots.py`
- Create: `docs/screenshots/classic.png`
- Create: `docs/screenshots/compact.png`
- Create: `docs/screenshots/ledger.png`
- Modify: `README.md`
- Test: `tests/test_render.py`

- [ ] **Step 1: Write the failing README screenshot test**

Add a test that reads `README.md` and asserts it references:

```python
"docs/screenshots/classic.png"
"docs/screenshots/compact.png"
"docs/screenshots/ledger.png"
"--style"
```

- [ ] **Step 2: Run test to verify red**

Run:

```bash
PYTHONPATH=src /usr/bin/python3 -m unittest tests.test_render.ProjectMetadataTest -v
```

Expected: failure because README has no screenshot section yet.

- [ ] **Step 3: Add screenshot generator and README section**

Create `scripts/generate_screenshots.py` to draw three PNG previews with sample receipt data and style-specific black-and-white layout. Update README with the screenshot grid and include `--style classic` in the Quick Start command.

- [ ] **Step 4: Generate screenshots**

Run:

```bash
PYTHONPATH=src /usr/bin/python3 scripts/generate_screenshots.py
```

Expected: three PNG files in `docs/screenshots/`.

- [ ] **Step 5: Run full verification**

Run:

```bash
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s tests -v
PYTHONPATH=src /usr/bin/python3 -m py_compile src/ai_mini_mart_receipt/*.py scripts/*.py
```

Expected: all tests and compile checks pass.
