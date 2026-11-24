"""Generate promo/progress.svg, the progress chart embedded in README.md.

Run with:  py -3 promo/make_progress.py

Standard library only. Colours follow GitHub's light-theme design tokens; the
layout was inspired by the AnyPS5 progress page.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

WIDTH = 920
BAR_X = 330
BAR_W = 440
BAR_H = 10
VALUE_X = 892

# GitHub dark-theme colours
BG = "#0d1117"
TEXT = "#e6edf3"
MUTED = "#8b949e"
BORDER = "#30363d"
SUBTLE = "#161b22"
GREEN = "#2ea043"  # success emphasis
AMBER = "#d29922"  # attention emphasis
BLUE = "#58a6ff"  # accent

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

SECTIONS = [
    (
        "Overall stages",
        [
            ("Story mode (v1.1.0 shipped)", 100, GREEN),
            ("Universal No Return plan", 40, AMBER),
            ("Current-build snapshot capture", 20, AMBER),
            ("Current-build profile & validation", 10, AMBER),
            ("Memory resolver implementation", 0, AMBER),
            ("Status, art, docs & release", 5, AMBER),
        ],
    ),
    (
        "Overall",
        [
            ("Story - shipped in v1.1.0", 100, GREEN),
            ("No Return - in development, not shipped", 35, AMBER),
        ],
    ),
    (
        "Story - detailed (v1.1.0)",
        [
            ("Save parsing (params.json)", 100, GREEN),
            ("Load-menu detection (USR-DATA last access)", 100, GREEN),
            ('Character + "Playing as ..."', 100, GREEN),
            ("Mission art (46 asset keys)", 100, GREEN),
            ("Docs, checklist and release", 100, GREEN),
        ],
    ),
    (
        "No Return - detailed (not shipped)",
        [
            ("Save fields decoded (difficulty, time, collectibles)", 100, GREEN),
            ("Status lines (mode, gamble, timer)", 30, AMBER),
            ("Operator auto-detection", 45, AMBER),
            ("Encounter / location auto-detection", 25, AMBER),
            ("Live score / kill field map", 45, AMBER),
            ("Large location + small operator art", 10, AMBER),
            ("Spec, docs and release", 10, AMBER),
        ],
    ),
]


def main() -> None:
    body: list[str] = []

    # Header
    body.append(f'<rect x="16" y="18" width="4" height="18" rx="2" fill="{BLUE}"/>')
    body.append(
        f'<text x="28" y="32" font-family="{FONT}" font-size="18" '
        f'font-weight="600" fill="{TEXT}">Project progress</text>'
    )
    body.append(
        f'<text x="28" y="54" font-family="{FONT}" font-size="12" '
        f'fill="{MUTED}">Snapshot of verified work, not a release schedule.</text>'
    )
    body.append(f'<rect x="28" y="68" width="9" height="9" rx="2" fill="{GREEN}"/>')
    body.append(
        f'<text x="43" y="76" font-family="{FONT}" font-size="11" '
        f'fill="{MUTED}">done</text>'
    )
    body.append(f'<rect x="94" y="68" width="9" height="9" rx="2" fill="{AMBER}"/>')
    body.append(
        f'<text x="109" y="76" font-family="{FONT}" font-size="11" '
        f'fill="{MUTED}">in progress</text>'
    )

    y = 100
    for heading, rows in SECTIONS:
        body.append(
            f'<text x="28" y="{y}" font-family="{FONT}" font-size="13" '
            f'font-weight="600" fill="{TEXT}">{escape(heading)}</text>'
        )
        body.append(
            f'<rect x="28" y="{y + 7}" width="{WIDTH - 56}" height="1" '
            f'fill="{BORDER}"/>'
        )
        y += 18
        for index, (label, percent, color) in enumerate(rows):
            row_y = y - 10
            if index % 2 == 0:
                body.append(
                    f'<rect x="16" y="{row_y}" width="{WIDTH - 32}" height="26" '
                    f'rx="6" fill="{SUBTLE}"/>'
                )
            baseline = y + 6
            body.append(
                f'<text x="28" y="{baseline}" font-family="{FONT}" '
                f'font-size="12" fill="{TEXT}">{escape(label)}</text>'
            )
            body.append(
                f'<rect x="{BAR_X}" y="{y - 3}" width="{BAR_W}" height="{BAR_H}" '
                f'rx="5" fill="{BORDER}"/>'
            )
            filled = BAR_W * percent / 100
            if filled:
                body.append(
                    f'<rect x="{BAR_X}" y="{y - 3}" width="{filled:.1f}" '
                    f'height="{BAR_H}" rx="5" fill="{color}"/>'
                )
            body.append(
                f'<text x="{VALUE_X}" y="{baseline}" font-family="{MONO}" '
                f'font-size="12" font-weight="600" text-anchor="end" '
                f'fill="{TEXT}">{percent}%</text>'
            )
            y += 28
        y += 14

    height = y + 2
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" '
        f'aria-label="Progress bars for story and No Return support">\n'
        f'<rect width="{WIDTH}" height="{height}" fill="{BG}"/>\n'
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" '
        f'rx="8" fill="none" stroke="{BORDER}"/>\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )
    out = Path(__file__).with_name("progress-dark.svg")
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out} ({WIDTH}x{height})")


if __name__ == "__main__":
    main()
