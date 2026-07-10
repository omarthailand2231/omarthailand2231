#!/usr/bin/env python3
"""Generates boot.svg (dark) + boot-light.svg — a 24x7 split-flap board.

Styled after ui.aceternity.com's "Text Flipping Board": tall rounded cells,
a hinge split-line with corner pins, and occasional colored flash tiles
during the scramble (a Vestaboard-style easter egg). Unlike that component
(React + Framer Motion, live/interactive), this is a static SVG generated
at build time — the "flip" is approximated with independently squished,
staggered top and bottom character halves via SMIL.

The AI (scripts/ai_message.py) has full creative range over all 7 rows —
a quip, a list, a status readout, whatever fits — falling back to a static
message if the API is unavailable. Claude status and local time are fed to
the AI as context only; they are not displayed as their own dedicated rows.
"""
import random
from datetime import datetime, timedelta, timezone

import ai_message
import fallback_messages

# GitHub's native canvas colours. The SVG itself stays transparent so the board
# feels integrated with the profile in either colour scheme.
DARK = {
    "cell_bg": "#161b22", "border": "#30363d", "split": "#21262d",
    "flap_text": "#c9d1d9",
}
LIGHT = {
    "cell_bg": "#f6f8fa", "border": "#d0d7de", "split": "#d8dee4",
    "flap_text": "#24292f",
}

# Vestaboard-style accent tiles that occasionally flash mid-scramble.
ACCENTS = [
    ("#da3633", "#ffffff"),
    ("#fb8500", "#ffffff"),
    ("#d29922", "#ffffff"),
    ("#2da44e", "#ffffff"),
    ("#0969da", "#ffffff"),
    ("#6f42c1", "#ffffff"),
    ("#eaeef2", "#0d1117"),
]
FLASH_CHANCE = 0.15

STATUS_TEXT = {
    "none": "operational",
    "minor": "degraded",
    "major": "partial outage",
    "critical": "major outage",
    "unknown": "status unreachable",
}

COLS = 24
ROWS = 7
CELL_W, CELL_H, GAP = 24, 46, 3
CELL_RX = 2
PAD = 18
FONT_SIZE = 19

SCRAMBLE_POOL = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
FLIP_DUR = 0.1  # seconds per flip step
FLIP_SQUISH_FRAC = 0.4  # fraction into each step where the cell is edge-on
HALF_FLIP_OFFSET = 0.045  # the top flap lands just before the bottom flap
# Rows power on top-to-bottom, like a real board waking up.
ROW_START = [0.15 + i * 0.3 for i in range(ROWS)]


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
    """One split-flap cell with independently animated top and bottom glyphs."""
    n = random.randint(4, 7)  # total glyphs shown, ending on target_char
    seq = [random.choice(SCRAMBLE_POOL) for _ in range(n - 1)] + [target_char]
    accents = [
        random.choice(ACCENTS) if (i < n - 1 and random.random() < FLASH_CHANCE) else None
        for i in range(n)
    ]

    cx, cy = x + CELL_W / 2, y + CELL_H / 2
    total_dur = n * FLIP_DUR

    def reveal_t(i, half_offset=0.0):
        return delay + i * FLIP_DUR + FLIP_SQUISH_FRAC * FLIP_DUR + half_offset

    # Cell body: rounded rect, fill flashes to an accent color and back
    # exactly when the corresponding glyph is revealed.
    bg_anims = []
    for i in range(1, n):
        if accents[i] is not None or accents[i - 1] is not None:
            col = accents[i][0] if accents[i] else p["cell_bg"]
            bg_anims.append(
                f'<animate attributeName="fill" to="{col}" begin="{reveal_t(i):.3f}s" dur="0.001s" fill="freeze"/>'
            )
    fill0 = accents[0][0] if accents[0] else p["cell_bg"]
    cell_id = f"{int(x)}-{int(y)}"
    top_clip = f"flap-top-{cell_id}"
    bottom_clip = f"flap-bottom-{cell_id}"
    parts = [
        f'<rect x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" rx="{CELL_RX}" ry="{CELL_RX}" '
        f'fill="{fill0}" stroke="{p["border"]}" stroke-width="1.2">{"".join(bg_anims)}</rect>',
        f'<defs>'
        f'<clipPath id="{top_clip}" clipPathUnits="userSpaceOnUse">'
        f'<rect x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H / 2}"/>'
        f'</clipPath>'
        f'<clipPath id="{bottom_clip}" clipPathUnits="userSpaceOnUse">'
        f'<rect x="{x}" y="{cy}" width="{CELL_W}" height="{CELL_H / 2}"/>'
        f'</clipPath>'
        f'</defs>',
    ]

    def glyph_half(half_offset):
        """Render a clipped half-character sequence with a staggered reveal."""
        glyph_parts = []
        for i, ch in enumerate(seq):
            is_last = i == n - 1
            glyph = ch if ch != " " else ""
            color = accents[i][1] if accents[i] else p["flap_text"]
            anim = (
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{reveal_t(i, half_offset):.3f}s" dur="0.001s" fill="freeze"/>'
            )
            if not is_last:
                anim += (
                    f'<animate attributeName="opacity" from="1" to="0" '
                    f'begin="{reveal_t(i + 1, half_offset):.3f}s" dur="0.001s" fill="freeze"/>'
                )
            glyph_parts.append(
                f'<text x="{cx}" y="{cy + FONT_SIZE * 0.35}" text-anchor="middle" font-weight="700" '
                f'fill="{color}" opacity="0">{glyph}{anim}</text>'
            )
        return "".join(glyph_parts)

    # Each half squishes around the seam independently. The small offset makes
    # the board briefly show different top/bottom halves while a flap turns.
    kt, sv = [0.0], [1]
    for i in range(n):
        kt.append(i * FLIP_DUR + FLIP_SQUISH_FRAC * FLIP_DUR)
        sv.append(0.05)
        kt.append((i + 1) * FLIP_DUR)
        sv.append(1)
    key_times = ";".join(f"{t / total_dur:.4f}" for t in kt)
    values = ";".join(f"1,{v}" for v in sv)

    def flip_half(clip_id, glyphs, half_offset):
        return (
            f'<g transform="translate({cx},{cy})"><g>'
            f'<animateTransform attributeName="transform" type="scale" '
            f'keyTimes="{key_times}" values="{values}" begin="{delay + half_offset:.3f}s" '
            f'dur="{total_dur:.3f}s" fill="freeze"/>'
            f'<g transform="translate({-cx},{-cy})" clip-path="url(#{clip_id})">{glyphs}</g>'
            f'</g></g>'
        )

    parts.extend([
        flip_half(top_clip, glyph_half(0), 0),
        flip_half(bottom_clip, glyph_half(HALF_FLIP_OFFSET), HALF_FLIP_OFFSET),
        # The seam and hinge pins are appended after the glyphs, keeping them
        # visibly above the character just like a physical split-flap board.
        f'<line x1="{x}" y1="{cy}" x2="{x + CELL_W}" y2="{cy}" stroke="{p["split"]}" stroke-width="1.25" stroke-opacity="0.8"/>',
        f'<rect x="{x - 0.5}" y="{cy - CELL_H * 0.15}" width="1.5" height="{CELL_H * 0.3}" rx="0.75" fill="{p["border"]}"/>',
        f'<rect x="{x + CELL_W - 1}" y="{cy - CELL_H * 0.15}" width="1.5" height="{CELL_H * 0.3}" rx="0.75" fill="{p["border"]}"/>',
    ])
    return "".join(parts)


def _format_board_lines(lines):
    """Return exactly ROWS board rows with the message centred in both axes."""
    display_lines = [line.upper()[:COLS].center(COLS) for line in lines[:ROWS]]
    first_message_row = (ROWS - len(display_lines)) // 2
    return (
        [" " * COLS] * first_message_row
        + display_lines
        + [" " * COLS] * (ROWS - first_message_row - len(display_lines))
    )


def build_svg(p, lines, _now, filename):
    board_w = COLS * CELL_W + (COLS - 1) * GAP
    board_h = ROWS * CELL_H + (ROWS - 1) * GAP
    W = board_w + PAD * 2
    H = board_h + PAD * 2

    board_x = (W - board_w) / 2

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="{FONT_SIZE}">',
    ]

    # Treat the board as a display, not a typewriter: centre the message block
    # vertically, then centre each line horizontally in its 24 cells.
    for row, text in enumerate(_format_board_lines(lines)):
        y = PAD + row * (CELL_H + GAP)
        for col, ch in enumerate(text):
            x = board_x + col * (CELL_W + GAP)
            cell_delay = ROW_START[row] + col * 0.014 + random.uniform(0, 0.1)
            svg.append(_flap_cell(p, x, y, ch, cell_delay))

    svg.append("</svg>")
    with open(filename, "w") as f:
        f.write("".join(svg))


def main():
    indicator = fetch_claude_status()
    ict = timezone(timedelta(hours=7))
    now = datetime.now(ict).strftime("%Y-%m-%d %H:%M ICT")

    ai_lines = ai_message.get_message(
        claude_status=STATUS_TEXT.get(indicator, "status unreachable"),
        ict_time=now,
    )
    lines = ai_lines or random.choice(fallback_messages.FALLBACK_MESSAGES)

    build_svg(DARK, lines, now, "boot.svg")
    build_svg(LIGHT, lines, now, "boot-light.svg")
    source = "ai" if ai_lines else "fallback"
    print(f"boot.svg + boot-light.svg written — message: {source} {lines!r}, claude: {indicator}")


if __name__ == "__main__":
    main()
