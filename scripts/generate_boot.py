#!/usr/bin/env python3
"""Generates boot.svg (dark) + boot-light.svg — animated boot banners with live Claude status."""
import json
import math
import urllib.request
from datetime import datetime, timedelta, timezone

import radar_bangkok

STATUS_URL = "https://status.claude.com/api/v2/status.json"

DARK = {
    "bg": "#0d1117", "panel": "#161b22", "border": "#30363d",
    "text": "#c9d1d9", "dim": "#8b949e", "dots": "#30363d",
    "green": "#3fb950", "yellow": "#d29922", "red": "#f85149",
    "accent": "#79c0ff",
}
LIGHT = {
    "bg": "#f6f8fa", "panel": "#ffffff", "border": "#d0d7de",
    "text": "#1f2328", "dim": "#59636e", "dots": "#d0d7de",
    "green": "#1a7f37", "yellow": "#9a6700", "red": "#cf222e",
    "accent": "#0969da",
}


def fetch_claude_status():
    try:
        req = urllib.request.Request(STATUS_URL, headers={"User-Agent": "omar-boot-banner"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.load(r)
        indicator = data.get("status", {}).get("indicator", "unknown")
    except Exception:
        indicator = "unknown"
    if indicator not in ("none", "minor", "major", "critical"):
        indicator = "unknown"
    return indicator


STATUS_MAP = {
    # indicator: (tag, color_key, status_text, mood)
    "none":     ("OK",   "green",  "operational",        "unbothered"),
    "minor":    ("WARN", "yellow", "degraded",           "mildly concerned"),
    "major":    ("FAIL", "red",    "partial outage",     "pacing the room"),
    "critical": ("FAIL", "red",    "major outage",       "devastated"),
    "unknown":  ("????", "dim",    "status unreachable", "suspicious"),
}


def build_svg(p, indicator, now, filename, radar):
    tag, ck, status_text, mood = STATUS_MAP[indicator]
    scolor = p[ck]

    # (tag, tag_color, label, detail, detail_color, burst_gap, pause_after)
    # Output prints instantly; the small gaps make a burst feel like a real
    # process emitting lines rather than a terminal typing them.
    lines = [
        ("OK", p["green"], "mounting /projects", "", p["dim"], 0.04, 0.0),
        ("OK", p["green"], "react runtime", "attached", p["dim"], 0.04, 0.0),
        ("OK", p["green"], "swift toolchain", "loaded", p["dim"], 0.04, 0.21),
        ("OK", p["green"], "sol.agent", "panic-stop armed", p["dim"], 0.04, 0.0),
        ("OK", p["green"], "blood_ai", "13k lines, refactoring", p["dim"], 0.04, 0.06),
        ("OK", p["green"], "sumo.bot", "listening on 127.0.0.1:67", p["dim"], 0.04, 0.0),
        ("OK", p["green"], "atom.cat", "roaming somewhere", p["dim"], 0.03, 0.0),
        (tag, scolor, "claude api", status_text, scolor, 0.04, 0.0),
        ("OK", p["green"], "omar.mood", mood, p["dim"], 0.03, 0.0),
    ]
    STALL = 0.6  # network wait before the claude api line — the one dramatic beat

    W, LH, PAD_TOP = 780, 26, 64
    # The post-boot prompt and its radar panel are intentionally part of the
    # terminal, rather than a separate card below it.
    ready_y = PAD_TOP + len(lines) * LH + 2 * LH - 10
    prompt_y = ready_y + LH + 4
    panel_y = prompt_y + 20
    # Radar failure collapses the panel to its single FAIL line instead of
    # leaving a blank framed void at the bottom of the card.
    panel_h = 356 if radar else 0
    H = panel_y + panel_h + 30
    INPUT_CHAR_DUR = 0.014
    boot_command = "$ boot omar.sys --verbose"
    boot_type_dur = len(boot_command) * INPUT_CHAR_DUR
    boot_begin = 0.05
    # Leave a natural beat after pressing Enter before the process responds.
    t = boot_begin + boot_type_dur + 0.08

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="15">',
        f'<rect width="{W}" height="{H}" rx="10" fill="{p["panel"]}" stroke="{p["border"]}"/>',
        f'<rect width="{W}" height="34" rx="10" fill="{p["bg"]}"/>',
        f'<rect y="24" width="{W}" height="10" fill="{p["bg"]}"/>',
        f'<line x1="0" y1="34" x2="{W}" y2="34" stroke="{p["border"]}"/>',
    ]
    for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        svg.append(f'<circle cx="{22 + i * 22}" cy="17" r="6" fill="{c}"/>')
    svg.append(f'<text x="{W//2}" y="22" text-anchor="middle" fill="{p["dim"]}" font-size="12">omar.sys — boot</text>')

    y = PAD_TOP
    svg.append(
        f'<clipPath id="boot-command"><rect x="28" y="{y - 18}" width="0" height="24">'
        f'<animate attributeName="width" from="0" to="{len(boot_command) * 9}" '
        f'begin="{boot_begin:.2f}s" dur="{boot_type_dur:.2f}s" fill="freeze"/>'
        f'</rect></clipPath>'
        f'<g clip-path="url(#boot-command)"><text x="28" y="{y}" fill="{p["accent"]}">{boot_command}</text></g>'
    )

    for tg, tc, label, detail, dc, burst_gap, pause_after in lines:
        y += LH
        if label == "claude api":
            # Progress dots during the stall, hidden when the API result prints.
            wait = [f'<g fill="{p["dim"]}">']
            for d in range(3):
                wait.append(
                    f'<text x="{28 + d * 12}" y="{y}" opacity="0">.'
                    f'<animate attributeName="opacity" to="1" begin="{t + 0.1 + d * 0.13:.2f}s" dur="0.01s" fill="freeze"/>'
                    f'</text>'
                )
            wait.append(f'<animate attributeName="opacity" to="0" begin="{t + STALL:.2f}s" dur="0.01s" fill="freeze"/></g>')
            svg.append("".join(wait))
            t += STALL
        dots = "." * max(2, 28 - len(label))
        detail_part = f' <tspan fill="{dc}">{detail}</tspan>' if detail else ""
        svg.append(
            f'<g opacity="0"><animate attributeName="opacity" to="1" begin="{t:.2f}s" dur="0.01s" fill="freeze"/>'
            f'<text x="28" y="{y}" fill="{p["text"]}">[ <tspan fill="{tc}">{tg}</tspan> ] '
            f'{label} <tspan fill="{p["dots"]}">{dots}</tspan>{detail_part}</text></g>'
        )
        t += burst_gap + pause_after

    y += LH * 2 - 10
    ready_begin = t + 0.08
    history_begin = ready_begin + 0.15
    svg.append(
        f'<g opacity="0"><animate attributeName="opacity" to="1" begin="{ready_begin:.2f}s" dur="0.01s" fill="freeze"/>'
        f'<text x="28" y="{y}" fill="{p["accent"]}">ready.</text>'
        f'<text x="96" y="{y}" fill="{p["dim"]}" font-size="12">last boot: {now}</text>'
        f'<g><set attributeName="opacity" to="0" begin="{history_begin:.2f}s" fill="freeze"/>'
        f'<rect x="86" y="{y - 13}" width="8" height="16" fill="{p["text"]}">'
        f'<animate attributeName="opacity" values="1;0;1" dur="0.65s" begin="{ready_begin + 0.05:.2f}s" repeatCount="1"/>'
        f'</rect></g></g>'
    )

    # History navigation starts just after the ready prompt settles.  Each
    # entry occupies the same line and is replaced immediately by the next.
    history = [
        "$ git push",
        "$ python3 scripts/generate_boot.py",
        "$ vim sol/PanicStop.swift",
        "$ python3 scripts/generate_boot.py",
    ]
    for i, command in enumerate(history):
        svg.append(
            f'<text x="28" y="{prompt_y}" fill="{p["text"]}" opacity="0">{command}'
            f'<animate attributeName="opacity" values="0;1;1;0" '
            f'keyTimes="0;0.01;0.99;1" begin="{history_begin + i * 0.15:.2f}s" '
            f'dur="0.15s" fill="freeze"/></text>'
        )

    radar_command = "$ python3 radar_bangkok.py"
    radar_type_dur = len(radar_command) * INPUT_CHAR_DUR
    type_begin = history_begin + len(history) * 0.15 + 0.04
    command_clip = "radar-command"
    svg.append(
        f'<clipPath id="{command_clip}"><rect x="28" y="{prompt_y - 18}" width="0" height="24">'
        f'<animate attributeName="width" from="0" to="{len(radar_command) * 9}" '
        f'begin="{type_begin:.2f}s" dur="{radar_type_dur:.2f}s" fill="freeze"/>'
        f'</rect></clipPath>'
        f'<g clip-path="url(#{command_clip})"><text x="28" y="{prompt_y}" fill="{p["accent"]}">{radar_command}</text></g>'
    )

    panel_begin = type_begin + radar_type_dur + 0.2
    if radar is None:
        svg.append(
            f'<g opacity="0"><animate attributeName="opacity" to="1" begin="{panel_begin:.2f}s" dur="0.01s" fill="freeze"/>'
            f'<text x="28" y="{panel_y}" fill="{p["red"]}">[ FAIL ] radar_bangkok.py ... no signal</text></g>'
        )
    else:
        map_b64 = radar["map_dark_b64"] if p is DARK else radar["map_light_b64"]
        stats = (
            f'{radar["temp_c"]:.1f}°C · rain {radar["precip_mm"]:.1f}mm · '
            f'wind {radar["wind_kmh"]:.0f} km/h · {radar["condition"]}'
        )
        map_y = panel_y + 36
        # Sweep radius reaches the map corners; the trailing wedge sits 30°
        # behind the clockwise-rotating beam.
        cx, cy, radius = 28 + 362, map_y + 140, 390
        wedge_x = cx + radius * math.cos(math.radians(30))
        wedge_y = cy - radius * math.sin(math.radians(30))
        svg.append(
            f'<g opacity="0"><animate attributeName="opacity" to="1" begin="{panel_begin:.2f}s" dur="0.01s" fill="freeze"/>'
            f'<rect x="28" y="{panel_y}" width="724" height="{panel_h}" rx="4" fill="{p["bg"]}" stroke="{p["border"]}"/>'
            f'<text x="42" y="{panel_y + 24}" fill="{p["accent"]}">── radar: bangkok ──</text>'
            f'<image x="28" y="{map_y}" width="724" height="280" preserveAspectRatio="none" '
            f'href="data:image/jpeg;base64,{map_b64}"/>'
            f'<clipPath id="radar-map"><rect x="28" y="{map_y}" width="724" height="280"/></clipPath>'
            f'<g clip-path="url(#radar-map)"><g>'
            f'<animateTransform attributeName="transform" type="rotate" '
            f'from="0 {cx} {cy}" to="360 {cx} {cy}" dur="5s" repeatCount="indefinite"/>'
            f'<path d="M{cx} {cy} L{wedge_x:.1f} {wedge_y:.1f} A{radius} {radius} 0 0 1 {cx + radius} {cy} Z" '
            f'fill="{p["green"]}" opacity="0.1"/>'
            f'<line x1="{cx}" y1="{cy}" x2="{cx + radius}" y2="{cy}" stroke="{p["green"]}" '
            f'stroke-width="2" opacity="0.45"/>'
            f'</g></g>'
            f'<text x="742" y="{map_y + 270}" text-anchor="end" fill="{p["text"]}" '
            f'font-size="9" opacity="0.78">© OSM © CARTO</text>'
            f'<text x="42" y="{panel_y + 338}" fill="{p["text"]}">{stats}</text>'
            f'</g>'
        )
    svg.append("</svg>")
    with open(filename, "w") as f:
        f.write("".join(svg))


def main():
    indicator = fetch_claude_status()
    radar = radar_bangkok.fetch_radar()
    ict = timezone(timedelta(hours=7))
    now = datetime.now(ict).strftime("%Y-%m-%d %H:%M ICT")
    build_svg(DARK, indicator, now, "boot.svg", radar)
    build_svg(LIGHT, indicator, now, "boot-light.svg", radar)
    radar_state = "live" if radar else "no signal"
    print(f"boot.svg + boot-light.svg written — claude: {indicator}, radar: {radar_state}")


if __name__ == "__main__":
    main()
