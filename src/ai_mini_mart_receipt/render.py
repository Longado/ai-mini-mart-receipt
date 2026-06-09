"""Render AI Mini Mart text and HTML receipts."""

from __future__ import annotations

import hashlib
import html
import math
import unicodedata

from .assets import asset_data_uri
from .models import UsageSnapshot, parse_timestamp


WIDTH = 48
TIP_PRESETS = (15, 18, 20)
RECEIPT_STYLES = ("classic", "compact", "ledger")


LABELS = {
    "en": {
        "thanks": "THANK YOU FOR CODING WITH {product}",
        "receipt": "RECEIPT #: {rid}",
        "date": "DATE: {date}",
        "location": "LOCATION: {location}",
        "title": "ROUND TITLE",
        "provider": "PROVIDER",
        "model": "MODEL",
        "context": "CONTEXT USED",
        "item": "ITEM",
        "tokens": "TOKENS",
        "input": "Input Tokens",
        "output": "Output Tokens",
        "cached": "Cache Read Tokens",
        "reasoning": "Reasoning Tokens",
        "total": "TOTAL",
        "estimate": "USD ESTIMATE",
        "price": "PRICE MAP",
        "subtotal": "SUBTOTAL",
        "tip": "TIP",
        "grand": "GRAND TOTAL",
        "tip_toggle": "Add tip",
        "custom": "Custom",
        "apply": "Apply",
        "custom_footer": "CUSTOM TIP ENTERED. AI MINI MART STAMPED THE SLIP.",
    },
    "zh-CN": {
        "thanks": "感谢使用 {product}",
        "receipt": "小票号: {rid}",
        "date": "日期: {date}",
        "location": "地点: {location}",
        "title": "本轮称号",
        "provider": "供应商",
        "model": "模型",
        "context": "已用上下文",
        "item": "项目",
        "tokens": "TOKEN",
        "input": "输入 Tokens",
        "output": "输出 Tokens",
        "cached": "缓存读取",
        "reasoning": "推理 Tokens",
        "total": "总计",
        "estimate": "USD 预估",
        "price": "价格映射",
        "subtotal": "小计",
        "tip": "小费",
        "grand": "应付总额",
        "tip_toggle": "加一点小费",
        "custom": "自定义",
        "apply": "应用",
        "custom_footer": "自定义小费已入账，AI Mini Mart 盖章放行。",
    },
}


ASCII_LOGO = (
    "    ██████████",
    "  ██  ▀  ▀  ██",
    "  ██  ▄▄▄▄  ██",
    "  ████████████",
    "    ██ ██ ██",
    " ██████████████",
    " █  ▄      ▄  █",
    " ██████████████",
    "    ██    ██",
    "    ██    ██",
)


def language_key(language: str) -> str:
    return "zh-CN" if language.lower().startswith("zh") else "en"


def normalize_style(style: str) -> str:
    if style not in RECEIPT_STYLES:
        raise ValueError(f"unknown receipt style: {style}")
    return style


def visual_width(text: str) -> int:
    width = 0
    for char in text:
        width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return width


def center(text: str, width: int = WIDTH) -> str:
    pad = max(0, math.floor((width - visual_width(text)) / 2))
    return " " * pad + text


def kv(left: str, right: str, width: int = WIDTH) -> str:
    right = str(right)
    room = max(1, width - visual_width(right) - 1)
    left = trim(left, room)
    spaces = max(1, width - visual_width(left) - visual_width(right))
    return left + " " * spaces + right


def trim(text: str, limit: int) -> str:
    result = ""
    width = 0
    for char in text:
        char_width = 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
        if width + char_width > limit:
            break
        result += char
        width += char_width
    return result


def fmt_int(value: int | None) -> str:
    return f"{int(value or 0):,}"


def money(amount: float | None) -> str:
    if amount is None:
        return "UNMAPPED"
    if 0 < amount < 0.000001:
        return "<$0.000001"
    return f"${amount:.6f}"


def product_name(snapshot: UsageSnapshot) -> str:
    model = snapshot.model.lower()
    if "gpt" in model:
        return "ChatGPT"
    if "claude" in model:
        return "Claude"
    return snapshot.model or "AI"


def receipt_id(snapshot: UsageSnapshot) -> str:
    stamp = parse_timestamp(snapshot.timestamp)
    date_part = stamp.strftime("%Y%m%d_%H%M%S")
    seed = f"{snapshot.provider}:{snapshot.model}:{snapshot.normalized_total()}:{date_part}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:6].upper()
    return f"CX_{date_part}_{digest}"


def receipt_state(snapshot: UsageSnapshot) -> str:
    total = snapshot.normalized_total()
    estimate = float(snapshot.estimate_usd or 0.0)
    cache_heavy = snapshot.input_tokens > 0 and snapshot.cached_input_tokens >= int(snapshot.input_tokens * 0.8)
    high_cost = total >= 100_000 or estimate >= 0.50
    reasoning_heavy = snapshot.reasoning_output_tokens >= max(64, snapshot.output_tokens // 3)
    if cache_heavy:
        return "cache"
    if high_cost:
        return "budget"
    if reasoning_heavy:
        return "reasoning"
    return "alive"


def round_title(snapshot: UsageSnapshot, language: str) -> str:
    titles = {
        "zh-CN": {
            "cache": "缓存达人",
            "budget": "预算警报",
            "reasoning": "推理加班",
            "alive": "预算正常",
        },
        "en": {
            "cache": "CACHE PRO",
            "budget": "BUDGET ALERT",
            "reasoning": "REASONING OVERTIME",
            "alive": "BUDGET NORMAL",
        },
    }
    return titles[language_key(language)][receipt_state(snapshot)]


def footer(snapshot: UsageSnapshot, language: str) -> str:
    state = receipt_state(snapshot)
    zh = {
        "cache": "缓存很努力，账单很克制。",
        "budget": "窗口没爆，余额先爆了。",
        "reasoning": "灯还亮着，推理还在加班。",
        "alive": "思考得很认真，结账也很认真。",
    }
    en = {
        "cache": "CACHE DID SOME OF THE LIFTING.",
        "budget": "THE REGISTER NOTICED THE BILL.",
        "reasoning": "THE LIGHT STAYED ON FOR REASONING.",
        "alive": "THE BUDGET IS STILL BREATHING.",
    }
    return zh[state] if language_key(language) == "zh-CN" else en[state]


def context_value(snapshot: UsageSnapshot) -> str:
    used = fmt_int(snapshot.input_tokens)
    if snapshot.context_window:
        return f"{used}/{fmt_int(snapshot.context_window)}"
    return used


def barcode(seed: str) -> str:
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    parts = ["|", "||", "| ", " ||", "|||", " |"]
    raw = "".join(parts[int(char, 16) % len(parts)] for char in digest)
    return center(raw[:32])


def rows(snapshot: UsageSnapshot, language: str) -> list[tuple[str, str]]:
    labels = LABELS[language_key(language)]
    result = [
        (labels["title"], round_title(snapshot, language)),
        (labels["provider"], snapshot.provider.upper()),
        (labels["model"], snapshot.model),
        (labels["context"], context_value(snapshot)),
    ]
    return result


def token_rows(snapshot: UsageSnapshot, language: str) -> list[tuple[str, str]]:
    labels = LABELS[language_key(language)]
    result = [
        (labels["input"], fmt_int(snapshot.input_tokens)),
        (labels["output"], fmt_int(snapshot.output_tokens)),
    ]
    if snapshot.cached_input_tokens:
        result.append((labels["cached"], fmt_int(snapshot.cached_input_tokens)))
    if snapshot.reasoning_output_tokens:
        result.append((labels["reasoning"], fmt_int(snapshot.reasoning_output_tokens)))
    return result


def render_text(snapshot: UsageSnapshot, language: str = "zh-CN") -> str:
    lang = language_key(language)
    labels = LABELS[lang]
    rid = receipt_id(snapshot)
    date_text = parse_timestamp(snapshot.timestamp).strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = []
    lines.extend(center(line) for line in ASCII_LOGO)
    lines.append(center("AI MINI MART"))
    lines.append(center(labels["thanks"].format(product=product_name(snapshot))))
    lines.append(center(labels["receipt"].format(rid=rid)))
    lines.append(center(labels["date"].format(date=date_text)))
    if snapshot.location:
        lines.append(center(labels["location"].format(location=snapshot.location)))
    lines.append("━" * WIDTH)
    lines.extend(kv(label, value) for label, value in rows(snapshot, lang))
    lines.append("─" * WIDTH)
    lines.append(kv(labels["item"], labels["tokens"]))
    lines.append("─" * WIDTH)
    lines.extend(kv(label, value) for label, value in token_rows(snapshot, lang))
    lines.append("━" * WIDTH)
    lines.append(kv(labels["total"], f"{fmt_int(snapshot.normalized_total())} Tokens"))
    lines.append("─" * WIDTH)
    lines.append(kv(labels["estimate"], money(snapshot.estimate_usd)))
    lines.append(kv(labels["price"], snapshot.model))
    lines.append("━" * WIDTH)
    lines.append(center(footer(snapshot, lang)))
    lines.append("")
    lines.append(barcode(rid))
    lines.append(center(rid))
    return "\n".join(lines)


def _html_rows(row_items: list[tuple[str, str]]) -> str:
    return "\n".join(
        f'<div class="receipt-row"><span>{html.escape(label)}</span><span>{html.escape(value)}</span></div>'
        for label, value in row_items
    )


def _article(snapshot: UsageSnapshot, language: str, active: bool) -> str:
    lang = language_key(language)
    labels = LABELS[lang]
    rid = receipt_id(snapshot)
    state = receipt_state(snapshot)
    logo_uri = asset_data_uri(f"mini-mart-cashier-{state}.png")
    stamp_uri = asset_data_uri("mini-mart-stamp-paid.png")
    date_text = parse_timestamp(snapshot.timestamp).strftime("%Y-%m-%d %H:%M:%S")
    cls = "receipt" if active else "receipt receipt--hidden"
    location = (
        f'<div class="receipt-meta">{html.escape(labels["location"].format(location=snapshot.location))}</div>'
        if snapshot.location else ""
    )
    return f"""
<article class="{cls}" data-language="{lang}">
  <header class="receipt-header">
    <div class="receipt-logo-shell"><img class="receipt-logo-image receipt-logo-image--mini-mart-cashier-{state}" src="{logo_uri}" alt="" /></div>
    <div class="receipt-logo-label">AI MINI MART</div>
    <div class="receipt-thanks">{html.escape(labels["thanks"].format(product=product_name(snapshot)))}</div>
    <div class="receipt-meta">{html.escape(labels["receipt"].format(rid=rid))}</div>
    <div class="receipt-meta">{html.escape(labels["date"].format(date=date_text))}</div>
    {location}
  </header>
  <div class="receipt-rule strong"></div>
  {_html_rows(rows(snapshot, lang))}
  <div class="receipt-rule"></div>
  {_html_rows([(labels["item"], labels["tokens"])])}
  <div class="receipt-rule"></div>
  {_html_rows(token_rows(snapshot, lang))}
  <div class="receipt-rule strong"></div>
  <div class="receipt-total">{_html_rows([(labels["total"], f"{fmt_int(snapshot.normalized_total())} Tokens")])}</div>
  <div class="receipt-rule"></div>
  {_html_rows([(labels["estimate"], money(snapshot.estimate_usd)), (labels["price"], snapshot.model)])}
  <section class="receipt-tip-summary" hidden>
    <div class="receipt-rule"></div>
    {_html_rows([(labels["subtotal"], money(snapshot.estimate_usd))])}
    <div class="receipt-row"><span data-tip-line-label>{html.escape(labels["tip"])} (0%)</span><span data-tip-amount></span></div>
    <div class="receipt-row receipt-total"><span>{html.escape(labels["grand"])}</span><span data-tip-grand-total></span></div>
    <div class="receipt-tip-stamp" data-tip-stamp hidden><img class="receipt-tip-stamp-image" src="{stamp_uri}" alt="PAID" /></div>
  </section>
  <footer class="receipt-footer">
    <div class="receipt-rule strong"></div>
    <div class="receipt-footer-line" data-receipt-footer>{html.escape(footer(snapshot, lang))}</div>
    <pre class="receipt-barcode">{html.escape(barcode(rid).strip())}</pre>
    <div class="receipt-barcode-id">{html.escape(rid)}</div>
  </footer>
</article>
"""


def _tip_config(snapshot: UsageSnapshot, language: str) -> dict[str, object]:
    lang = language_key(language)
    labels = LABELS[lang]
    amount = float(snapshot.estimate_usd or 0.0)
    options = []
    for percent in TIP_PRESETS:
        tip_amount = amount * percent / 100
        options.append({
            "percent": percent,
            "tipAmount": money(tip_amount),
            "grandTotal": money(amount + tip_amount),
            "footer": labels["custom_footer"] if percent == 20 else footer(snapshot, lang),
        })
    return {
        "amount": amount,
        "currencySymbol": "$",
        "tipLabel": labels["tip"],
        "defaultFooter": footer(snapshot, lang),
        "customFooter": labels["custom_footer"],
        "options": options,
    }


def render_html(snapshot: UsageSnapshot, language: str = "zh-CN", style: str = "classic") -> str:
    page_lang = language_key(language)
    style = normalize_style(style)
    tip_config = {
        "defaultLanguage": page_lang,
        "labels": {
            lang: {
                "toggle": LABELS[lang]["tip_toggle"],
                "custom": LABELS[lang]["custom"],
                "apply": LABELS[lang]["apply"],
            }
            for lang in ("en", "zh-CN")
        },
        "tip": {lang: _tip_config(snapshot, lang) for lang in ("en", "zh-CN")},
    }
    import json
    config_json = json.dumps(tip_config, ensure_ascii=False).replace("</", "<\\/")
    buttons = "\n".join(
        f'<button class="tip-option" type="button" data-tip-percent="{percent}">{percent}%</button>'
        for percent in TIP_PRESETS
    )
    articles = _article(snapshot, "en", page_lang == "en") + _article(snapshot, "zh-CN", page_lang == "zh-CN")
    return f"""<!DOCTYPE html>
<html lang="{page_lang}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(receipt_id(snapshot))} · AI Mini Mart Receipt</title>
  <style>
    :root {{ --paper: #fff; --ink: #151515; --page: #ececec; --receipt-width: 80mm; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 12px 0 24px; background: var(--page); color: var(--ink); font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
    .receipt-document--compact {{ --receipt-width: 72mm; --page: #f6f6f6; }}
    .receipt-document--ledger {{ --page: #e5e5e5; }}
    .print-toolbar {{ display: flex; justify-content: center; margin-bottom: 12px; }}
    .print-button {{ border: 0; border-radius: 999px; padding: 10px 18px; background: #1b1c1f; color: #fff; font: inherit; cursor: pointer; }}
    .receipt-page {{ display: flex; flex-direction: column; align-items: center; gap: 10px; }}
    .receipt {{ width: min(var(--receipt-width), calc(100vw - 24px)); background: var(--paper); padding: 7mm 4mm 5mm; overflow: hidden; }}
    .receipt-document--compact .receipt {{ padding: 4.8mm 3.2mm 4.2mm; }}
    .receipt-document--ledger .receipt {{ border: .45mm solid var(--ink); padding: 6mm 4mm 4.8mm; }}
    .receipt--hidden {{ display: none; }}
    .receipt-header, .receipt-footer {{ text-align: center; }}
    .receipt-logo-shell {{ min-height: 26mm; display: flex; align-items: center; justify-content: center; }}
    .receipt-logo-image {{ width: 24mm; image-rendering: pixelated; }}
    .receipt-logo-label {{ margin-top: 3mm; font-size: 4.3mm; letter-spacing: .08em; }}
    .receipt-thanks, .receipt-meta {{ margin-top: 1mm; font-size: 3.2mm; line-height: 1.35; }}
    .receipt-rule {{ border-top: .35mm solid var(--ink); margin: 3.5mm 0; }}
    .receipt-rule.strong {{ border-top-width: .55mm; }}
    .receipt-row {{ display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 4mm; font-size: 3.45mm; line-height: 1.32; }}
    .receipt-document--compact .receipt-logo-shell {{ min-height: 18mm; }}
    .receipt-document--compact .receipt-logo-image {{ width: 18mm; }}
    .receipt-document--compact .receipt-logo-label {{ margin-top: 1.8mm; font-size: 3.8mm; }}
    .receipt-document--compact .receipt-thanks, .receipt-document--compact .receipt-meta {{ font-size: 2.85mm; }}
    .receipt-document--compact .receipt-rule {{ margin: 2.4mm 0; }}
    .receipt-document--compact .receipt-row {{ font-size: 3.05mm; line-height: 1.24; gap: 2.4mm; }}
    .receipt-document--ledger .receipt-logo-shell {{ min-height: 24mm; border: .25mm solid var(--ink); margin-bottom: 2.4mm; }}
    .receipt-document--ledger .receipt-logo-label {{ border-top: .25mm solid var(--ink); border-bottom: .25mm solid var(--ink); padding: 1.2mm 0; }}
    .receipt-document--ledger .receipt-rule {{ border-top: .25mm double var(--ink); margin: 2.8mm 0; }}
    .receipt-document--ledger .receipt-rule.strong {{ border-top-width: .55mm; }}
    .receipt-document--ledger .receipt-row {{ border-bottom: .2mm solid var(--ink); padding: 1.05mm 0; }}
    .receipt-document--ledger .receipt-total .receipt-row, .receipt-document--ledger .receipt-tip-summary .receipt-row {{ border-bottom-width: .35mm; }}
    .receipt-total {{ font-weight: 700; }}
    .receipt-footer-line {{ font-size: 3.55mm; line-height: 1.35; overflow-wrap: break-word; }}
    .receipt-barcode {{ margin: 3.6mm 0 1.4mm; font-size: 3.15mm; line-height: 1; overflow: hidden; }}
    .receipt-barcode-id {{ font-size: 3.15mm; word-break: break-all; }}
    .receipt-language-panel, .receipt-tip-panel {{ width: min(var(--receipt-width), calc(100vw - 24px)); background: rgba(255,255,255,.55); padding: 3mm 4mm; text-align: center; }}
    .language-option, .tip-option, .tip-custom-apply {{ border: .25mm solid var(--ink); background: var(--paper); color: var(--ink); font: inherit; font-size: 3mm; padding: 1.8mm 2.6mm; cursor: pointer; }}
    .language-option.is-selected, .tip-option.is-selected, .tip-custom-apply.is-selected {{ background: var(--ink); color: var(--paper); }}
    .tip-options {{ display: flex; justify-content: center; flex-wrap: wrap; gap: 1.5mm; margin-top: 2mm; }}
    .tip-custom {{ display: inline-flex; align-items: center; gap: 1.2mm; }}
    .tip-custom-label {{ font-size: 3mm; }}
    .tip-custom-input {{ width: 13mm; border: .25mm solid var(--ink); font: inherit; font-size: 3mm; padding: 1.55mm 1mm; text-align: right; }}
    .receipt-tip-summary {{ margin-top: 2.8mm; }}
    .tip-options[hidden], .receipt-tip-summary[hidden], .receipt-tip-stamp[hidden] {{ display: none !important; }}
    .receipt-tip-stamp {{ display: flex; justify-content: center; margin-top: 2.6mm; }}
    .receipt-tip-stamp-image {{ width: 18mm; image-rendering: pixelated; transform: rotate(-3deg); }}
    @page {{ size: 80mm auto; margin: 0; }}
    @media print {{ body {{ background: #fff; padding: 0; }} .print-toolbar, .receipt-language-panel, .receipt-tip-panel {{ display: none; }} .receipt {{ width: var(--receipt-width); margin: 0 auto; }} }}
  </style>
</head>
<body class="receipt-document receipt-document--{style}" data-receipt-style="{style}">
  <div class="print-toolbar"><button class="print-button" type="button" onclick="window.print()">Print receipt</button></div>
  <main class="receipt-page">
    {articles}
    <section class="receipt-language-panel">
      <button class="language-option{' is-selected' if page_lang == 'en' else ''}" type="button" data-language-button="en">EN</button>
      <button class="language-option{' is-selected' if page_lang == 'zh-CN' else ''}" type="button" data-language-button="zh-CN">中文</button>
    </section>
    <section class="receipt-tip-panel">
      <label class="tip-toggle"><input id="tip-toggle" type="checkbox" /> <span id="tip-toggle-label">{html.escape(LABELS[page_lang]["tip_toggle"])}</span></label>
      <div class="tip-options" id="tip-options" hidden>
        {buttons}
        <div class="tip-custom">
          <label class="tip-custom-label" for="tip-custom-input" data-tip-custom-label>{html.escape(LABELS[page_lang]["custom"])}</label>
          <input id="tip-custom-input" class="tip-custom-input" type="number" min="0" max="100" step="0.1" inputmode="decimal" placeholder="%" />
          <button class="tip-custom-apply" type="button" data-tip-custom>{html.escape(LABELS[page_lang]["apply"])}</button>
        </div>
      </div>
    </section>
  </main>
  <script id="tip-config" type="application/json">{config_json}</script>
  <script>
    (() => {{
      const config = JSON.parse(document.getElementById('tip-config').textContent || '{{}}');
      let activeLanguage = config.defaultLanguage || 'zh-CN';
      let selectedPercent = null;
      let selectedIsCustom = false;
      const toggle = document.getElementById('tip-toggle');
      const optionsWrap = document.getElementById('tip-options');
      const buttons = Array.from(document.querySelectorAll('[data-tip-percent]'));
      const customInput = document.getElementById('tip-custom-input');
      const customButton = document.querySelector('[data-tip-custom]');
      const langButtons = Array.from(document.querySelectorAll('[data-language-button]'));
      const receiptFor = (lang) => document.querySelector(`.receipt[data-language="${{lang}}"]`);
      const tipConfigFor = (lang) => (config.tip || {{}})[lang] || null;
      const displayPercent = (value) => String(value).replace(/\\.00$/, '').replace(/(\\.\\d)0$/, '$1');
      const normalizePercent = (value) => {{
        const percent = Number(value);
        if (!Number.isFinite(percent) || percent <= 0) return null;
        return Math.min(Math.round(percent * 100) / 100, 100);
      }};
      const formatMoney = (amount) => amount > 0 && amount < 0.000001 ? '<$0.000001' : `$${{amount.toFixed(6)}}`;
      const optionFor = (lang, percent, custom) => {{
        const cfg = tipConfigFor(lang);
        if (!cfg) return null;
        if (!custom) return (cfg.options || []).find((item) => String(item.percent) === String(percent));
        const normalized = normalizePercent(percent);
        if (normalized === null) return null;
        const tipAmount = Number(cfg.amount || 0) * normalized / 100;
        return {{ percent: displayPercent(normalized), tipAmount: formatMoney(tipAmount), grandTotal: formatMoney(Number(cfg.amount || 0) + tipAmount), footer: cfg.customFooter }};
      }};
      const resetReceipt = (lang) => {{
        const receipt = receiptFor(lang);
        const cfg = tipConfigFor(lang);
        if (!receipt || !cfg) return;
        receipt.querySelector('.receipt-tip-summary').hidden = true;
        receipt.querySelector('[data-tip-stamp]').hidden = true;
        receipt.querySelector('[data-tip-line-label]').textContent = `${{cfg.tipLabel}} (0%)`;
        receipt.querySelector('[data-tip-amount]').textContent = '';
        receipt.querySelector('[data-tip-grand-total]').textContent = '';
        receipt.querySelector('[data-receipt-footer]').textContent = cfg.defaultFooter || '';
      }};
      const applyReceipt = (lang) => {{
        const receipt = receiptFor(lang);
        const cfg = tipConfigFor(lang);
        const option = optionFor(lang, selectedPercent, selectedIsCustom);
        if (!receipt || !cfg || !option) return resetReceipt(lang);
        receipt.querySelector('.receipt-tip-summary').hidden = false;
        receipt.querySelector('[data-tip-stamp]').hidden = false;
        receipt.querySelector('[data-tip-line-label]').textContent = `${{cfg.tipLabel}} (${{option.percent}}%)`;
        receipt.querySelector('[data-tip-amount]').textContent = option.tipAmount;
        receipt.querySelector('[data-tip-grand-total]').textContent = option.grandTotal;
        receipt.querySelector('[data-receipt-footer]').textContent = option.footer;
      }};
      const sync = () => {{
        for (const receipt of document.querySelectorAll('.receipt[data-language]')) {{
          const lang = receipt.dataset.language;
          if (toggle.checked && selectedPercent) applyReceipt(lang);
          else resetReceipt(lang);
        }}
      }};
      buttons.forEach((button) => {{
        button.addEventListener('click', () => {{
          selectedPercent = button.dataset.tipPercent;
          selectedIsCustom = false;
          buttons.forEach((candidate) => candidate.classList.toggle('is-selected', candidate === button));
          customButton.classList.remove('is-selected');
          sync();
        }});
      }});
      const applyCustom = () => {{
        selectedPercent = normalizePercent(customInput.value);
        selectedIsCustom = selectedPercent !== null;
        buttons.forEach((button) => button.classList.remove('is-selected'));
        customButton.classList.toggle('is-selected', selectedIsCustom);
        sync();
      }};
      customButton.addEventListener('click', applyCustom);
      customInput.addEventListener('input', () => {{ if (toggle.checked) applyCustom(); }});
      toggle.addEventListener('change', () => {{
        optionsWrap.hidden = !toggle.checked;
        if (!toggle.checked) {{
          selectedPercent = null;
          selectedIsCustom = false;
          buttons.forEach((button) => button.classList.remove('is-selected'));
          customButton.classList.remove('is-selected');
        }}
        sync();
      }});
      langButtons.forEach((button) => button.addEventListener('click', () => {{
        activeLanguage = button.dataset.languageButton;
        document.documentElement.lang = activeLanguage;
        for (const receipt of document.querySelectorAll('.receipt[data-language]')) {{
          receipt.classList.toggle('receipt--hidden', receipt.dataset.language !== activeLanguage);
        }}
        langButtons.forEach((candidate) => candidate.classList.toggle('is-selected', candidate === button));
        document.getElementById('tip-toggle-label').textContent = config.labels[activeLanguage].toggle;
        document.querySelector('[data-tip-custom-label]').textContent = config.labels[activeLanguage].custom;
        customButton.textContent = config.labels[activeLanguage].apply;
      }}));
      sync();
    }})();
  </script>
</body>
</html>
"""
