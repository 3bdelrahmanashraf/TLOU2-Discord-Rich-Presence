"""Generate promo/progress.svg, the progress chart embedded in README.md.

Run with:  py -3 promo/make_progress.py

Standard library only. The layout follows the progress charts used by AnyPS5:
a grey track with a green fill for completed work and an amber fill for work
that is still in progress.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

WIDTH = 920
BAR_X = 330
BAR_W = 460
BAR_H = 12
VALUE_X = 900

TRACK = "#6e7681"
GREEN = "#2ea043"
AMBER = "#d29922"
TEXT = "#1f2328"
MUTED = "#57606a"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

SECTIONS = [
    (
        "Overall",
        [
            ("Story - shipped in v1.1.0", 100, GREEN),
            ("No Return - in development, not shipped", 25, AMBER),
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
            ("Operator auto-detection", 20, AMBER),
            ("Encounter / location auto-detection", 15, AMBER),
            ("Large location + small operator art", 10, AMBER),
            ("Spec, docs and release", 10, AMBER),
        ],
    ),
]


def main() -> None:
    parts = []
    y = 26
    parts.append(
        f'<text x="20" y="{y}" font-family="{FONT}" font-size="18" '
        f'font-weight="600" fill="{TEXT}">Project progress</text>'
    )
    y += 22
    parts.append(
        f'<text x="20" y="{y}" font-family="{FONT}" font-size="12" '
        f'fill="{MUTED}">Snapshot of verified work, not a release schedule. '
        f'Green = done, amber = in progress.</text>'
    )
    y += 28

    for heading, rows in SECTIONS:
        parts.append(
            f'<text x="20" y="{y}" font-family="{FONT}" font-size="13" '
            f'font-weight="600" fill="{TEXT}">{escape(heading)}</text>'
        )
        y += 10
        for label, percent, color in rows:
            baseline = y + 11
            parts.append(
                f'<text x="20" y="{baseline}" font-family="{FONT}" '
                f'font-size="12" fill="{TEXT}">{escape(label)}</text>'
            )
            parts.append(
                f'<rect x="{BAR_X}" y="{y}" width="{BAR_W}" height="{BAR_H}" '
                f'rx="2" fill="{TRACK}"/>'
            )
            filled = BAR_W * percent / 100
            if filled:
                parts.append(
                    f'<rect x="{BAR_X}" y="{y}" width="{filled:.1f}" '
                    f'height="{BAR_H}" rx="2" fill="{color}"/>'
                )
            parts.append(
                f'<text x="{VALUE_X}" y="{baseline}" font-family="{FONT}" '
                f'font-size="12" text-anchor="end" fill="{TEXT}">{percent}%</text>'
            )
            y += 28
        y += 12

    height = y + 6
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" '
        f'aria-label="Progress bars for story and No Return support">\n'
        f'<rect width="{WIDTH}" height="{height}" fill="#ffffff"/>\n'
        + "\n".join(parts)
        + "\n</svg>\n"
    )
    out = Path(__file__).with_name("progress.svg")
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out} ({WIDTH}x{height})")


if __name__ == "__main__":
    main()
