"""Generate Nova's README badges as static SVGs. Run: python docs/img/badges/generate_badges.py"""
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent

LABEL_BG = "#0d1222"
COLORS = {
    "blue": ("#6c8cff", "#ffffff"),
    "purple": ("#a855f7", "#ffffff"),
    "cyan": ("#22d3ee", "#05070f"),
    "green": ("#34d399", "#05070f"),
    "gray": ("#8b95b2", "#05070f"),
}

# Badge list
BADGES = [
    ("version",      "version",      "1.0",          "purple"),
    ("license",      "license",      "MIT",          "cyan"),
    ("runtime",      "runtime",      "Python 3.10+", "blue"),
    ("dependencies", "dependencies", "none",         "green"),
]

# Glyph widths for 11px Verdana-like text (DejaVu Sans metrics)
_REG = [3.5,4.41,5.06,9.22,7,10.45,8.58,3.02,4.29,4.29,5.5,9.22,3.5,3.97,3.5,3.71,7,7,7,7,7,7,7,7,7,7,3.71,3.71,9.22,9.22,9.22,5.84,11,7.53,7.55,7.68,8.47,6.95,6.33,8.52,8.27,3.24,3.24,7.21,6.13,9.49,8.23,8.66,6.63,8.66,7.64,6.98,6.72,8.05,7.53,10.88,7.54,6.72,7.54,4.29,3.71,4.29,9.22,5.5,5.5,6.74,6.98,6.05,6.98,6.77,3.87,6.98,6.97,3.06,3.06,6.37,3.06,10.72,6.97,6.73,6.98,6.98,4.52,5.73,4.31,6.97,6.51,9,6.51,6.51,5.77,7,3.71,7,9.22]
_BOLD = [3.83,5.02,5.73,9.22,7.65,11.02,9.59,3.37,5.03,5.03,5.75,9.22,4.18,4.57,4.18,4.02,7.65,7.65,7.65,7.65,7.65,7.65,7.65,7.65,7.65,7.65,4.4,4.4,9.22,9.22,9.22,6.38,11,8.51,8.38,8.07,9.13,7.51,7.51,9.03,9.21,4.09,4.09,8.52,7.01,10.95,9.21,9.35,8.06,9.35,8.47,7.92,7.5,8.93,8.51,12.13,8.48,7.97,7.98,5.03,4.02,5.03,9.22,5.5,5.5,7.42,7.87,6.52,7.87,7.46,4.79,7.87,7.83,3.77,3.77,7.32,3.77,11.46,7.83,7.56,7.87,7.87,5.42,6.55,5.26,7.83,7.17,10.16,7.1,7.17,6.4,7.83,4.02,7.83,9.22]
PAD = 8


def text_w(text: str, bold: bool = False) -> int:
    widths = _BOLD if bold else _REG
    return round(sum(widths[ord(ch) - 32] if 32 <= ord(ch) <= 126 else 8 for ch in text))


def make(label: str, value: str, colour: str) -> str:
    fill, ink = COLORS[colour]
    label_w, value_w = text_w(label) + 2 * PAD, text_w(value, True) + 2 * PAD
    width = label_w + value_w
    title = escape(f"{label}: {value}")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" role="img" aria-label="{title}">
  <title>{title}</title>
  <rect width="{label_w}" height="20" fill="{LABEL_BG}"/>
  <rect x="{label_w}" width="{value_w}" height="20" fill="{fill}"/>
  <g font-family="Verdana,'DejaVu Sans',Geneva,sans-serif" font-size="11" text-anchor="middle">
    <text x="{label_w / 2:.1f}" y="14" fill="#e8ecf7" textLength="{text_w(label)}" lengthAdjust="spacingAndGlyphs">{escape(label)}</text>
    <text x="{label_w + value_w / 2:.1f}" y="14" fill="{ink}" font-weight="bold" textLength="{text_w(value, True)}" lengthAdjust="spacingAndGlyphs">{escape(value)}</text>
  </g>
</svg>
'''


if __name__ == "__main__":
    for name, label, value, colour in BADGES:
        (HERE / f"{name}.svg").write_text(make(label, value, colour), encoding="utf-8")
    print(f"wrote {len(BADGES)} badges to {HERE}")
