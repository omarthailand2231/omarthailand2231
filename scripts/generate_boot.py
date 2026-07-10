#!/usr/bin/env python3
"""Generates boot.svg (dark) + boot-light.svg — a 24x7 split-flap board.

The AI (scripts/ai_message.py) has full creative range over all 7 rows —
a quip, a list, a status readout, whatever fits — falling back to a static
message if the API is unavailable. Claude status and local time are fed to
the AI as context only; they are not displayed as their own dedicated rows.
Every one of the 168 character cells scrambles through random glyphs before
landing on its final character (or blank), like a real Solari departure
board powering on.
"""
import random
from datetime import datetime, timedelta, timezone

import ai_message

DARK = {
    "bg": "#0d1117", "panel": "#161b22", "border": "#30363d",
    "flap_hi": "#232a34", "flap_lo": "#12161c", "flap_text": "#f0f3f7",
    "hinge": "#05070a", "idle": "#333c48",
    "dim": "#8b949e",
}
LIGHT = {
    "bg": "#f6f8fa", "panel": "#ffffff", "border": "#d0d7de",
    "flap_hi": "#f3f4f6", "flap_lo": "#dfe2e6", "flap_text": "#1f2328",
    "hinge": "#b8bfc7", "idle": "#c3c9d1",
    "dim": "#59636e",
}

STATUS_TEXT = {
    "none": "operational",
    "minor": "degraded",
    "major": "partial outage",
    "critical": "major outage",
    "unknown": "status unreachable",
}

FALLBACK_LINES = ["STILL SHIPPING", "STILL DEBUGGING"]

COLS = 24
ROWS = 7
CELL_W, CELL_H, GAP = 24, 34, 3
PAD = 20
CAPTION_H = 30
FONT_SIZE = 20

SCRAMBLE_POOL = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
FLIP_DUR = 0.055  # seconds per scramble step
# Rows power on top-to-bottom, like a real board waking up.
ROW_START = [0.15 + i * 0.32 for i in range(ROWS)]


def fetch_claude_status():
    import json
    import urllib.request

    try:
        req = urllib.request.Request(
            "https://status.claude.com/api/v2/status.json",
            headers={"User-Agent": "omar-boot-banner"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.load(r)
        indicator = data.get("status", {}).get("indicator", "unknown")
    except Exception:
        indicator = "unknown"
    if indicator not in ("none", "minor", "major", "critical"):
        indicator = "unknown"
    return indicator


def _flap_cell(p, x, y, target_char, delay):
    """One mechanical split-flap cell: scrambles through random glyphs and
    lands on target_char, or sits idle (a faint hinge pill) if it's blank."""
    parts = [
        f'<rect x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" rx="2.5" fill="{p["flap_lo"]}"/>',
        f'<rect x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H / 2}" rx="2.5" fill="{p["flap_hi"]}"/>',
        f'<rect x="{x}" y="{y + CELL_H / 2 - 3}" width="{CELL_W}" height="3" fill="{p["flap_lo"]}"/>',
        f'<line x1="{x}" y1="{y + CELL_H / 2}" x2="{x + CELL_W}" y2="{y + CELL_H / 2}" '
        f'stroke="{p["hinge"]}" stroke-width="1.2"/>',
    ]

    tx, ty = x + CELL_W / 2, y + CELL_H / 2 + FONT_SIZE * 0.35
    if target_char == " ":
        parts.append(
            f'<ellipse cx="{tx}" cy="{y + CELL_H / 2}" rx="{CELL_W * 0.18:.1f}" ry="2" fill="{p["idle"]}"/>'
        )

    n_flips = random.randint(4, 8)
    seq = [random.choice(SCRAMBLE_POOL) for _ in range(n_flips)] + [target_char]
    t = delay
    for i, ch in enumerate(seq):
        is_last = i == len(seq) - 1
        glyph = ch if ch != " " else ""
        anim = f'<animate attributeName="opacity" from="0" to="1" begin="{t:.3f}s" dur="0.001s" fill="freeze"/>'
        if not is_last:
            anim += (
                f'<animate attributeName="opacity" from="1" to="0" '
                f'begin="{t + FLIP_DUR:.3f}s" dur="0.001s" fill="freeze"/>'
            )
        parts.append(
            f'<text x="{tx}" y="{ty}" text-anchor="middle" font-weight="600" '
            f'fill="{p["flap_text"]}" opacity="0">{glyph}{anim}</text>'
        )
        t += FLIP_DUR
    return "".join(parts)


def build_svg(p, lines, now, filename):
    board_w = COLS * CELL_W + (COLS - 1) * GAP
    board_h = ROWS * CELL_H + (ROWS - 1) * GAP
    W = board_w + PAD * 2
    H = board_h + PAD * 2 + CAPTION_H

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="{FONT_SIZE}">',
        f'<rect width="{W}" height="{H}" rx="10" fill="{p["bg"]}"/>',
        f'<rect x="{PAD - 6}" y="{PAD - 6}" width="{board_w + 12}" height="{board_h + 12}" '
        f'rx="6" fill="{p["panel"]}" stroke="{p["border"]}"/>',
    ]

    for row in range(ROWS):
        text = (lines[row] if row < len(lines) else "").upper().ljust(COLS)[:COLS]
        y = PAD + row * (CELL_H + GAP)
        for col, ch in enumerate(text):
            x = PAD + col * (CELL_W + GAP)
            cell_delay = ROW_START[row] + col * 0.015 + random.uniform(0, 0.12)
            svg.append(_flap_cell(p, x, y, ch, cell_delay))

    caption_y = PAD + board_h + 22
    svg.append(
        f'<text x="{PAD}" y="{caption_y}" fill="{p["dim"]}" font-size="12">last refresh: {now}</text>'
    )
    svg.append("</svg>")
    with open(filename, "w") as f:
        f.write("".join(svg))


def main():
    indicator = fetch_claude_status()
    ict = timezone(timedelta(hours=7))
    now = datetime.now(ict).strftime("%Y-%m-%d %H:%M ICT")

    lines = ai_message.get_message(
        claude_status=STATUS_TEXT.get(indicator, "status unreachable"),
        ict_time=now,
    ) or FALLBACK_LINES

    build_svg(DARK, lines, now, "boot.svg")
    build_svg(LIGHT, lines, now, "boot-light.svg")
    source = "ai" if lines is not FALLBACK_LINES else "fallback"
    print(f"boot.svg + boot-light.svg written — message: {source} {lines!r}, claude: {indicator}")


if __name__ == "__main__":
    main()
