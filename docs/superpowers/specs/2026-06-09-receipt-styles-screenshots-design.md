# Receipt Styles And Screenshots Design

## Goal

Add a small visual layer to AI Mini Mart Receipt so the public GitHub repo shows multiple printable receipt styles and real preview screenshots.

## Scope

This version adds three HTML receipt styles:

- `classic`: the current thermal receipt look, kept as the default.
- `compact`: a denser receipt for quick printing and narrow previews.
- `ledger`: a sharper ruled receipt that reads like a tiny accounting slip.

Text receipts stay unchanged. Token totals, title selection, tip presets, custom tip behavior, and language switching stay unchanged.

## Interface

The CLI gets one new option:

```bash
--style classic|compact|ledger
```

`render_html()` also accepts the same style string. Invalid styles raise `ValueError` in library use and are rejected by argparse in CLI use.

## Assets

Add `docs/screenshots/` with one PNG per style:

- `classic.png`
- `compact.png`
- `ledger.png`

The screenshots are generated from representative sample receipt data. They are documentation assets, not runtime package assets.

## README

The README gets a `Screenshots` section before Quick Start and mentions the new `--style` option in the example command.

## Testing

Unit tests cover:

- HTML rendering includes the selected style class.
- Invalid render styles fail.
- CLI accepts `--style ledger` and writes styled HTML.
- README references all screenshot PNGs.

Existing tests continue to cover tip presets, custom tip controls, generic branding, license metadata, and CLI smoke output.
