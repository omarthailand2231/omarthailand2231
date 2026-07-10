#!/usr/bin/env python3
"""Generates boot.svg (dark) + boot-light.svg — animated boot banners with live Claude status."""
import json
import urllib.request
from datetime import datetime, timedelta, timezone

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


def build_svg(p, indicator, now, filename):
    tag, ck, status_text, mood = STATUS_MAP[indicator]
    scolor = p[ck]

    # (tag, tag_color, label, detail, detail_color, type_dur, pause_after)
    lines = [
        ("OK", p["green"], "mounting /projects", "", p["dim"], 0.15, 0.0),
        ("OK", p["green"], "react runtime", "attached", p["dim"], 0.2, 0.05),
        ("OK", p["green"], "swift toolchain", "loaded", p["dim"], 0.25, 0.9),
        ("OK", p["green"], "sol.agent", "panic-stop armed", p["dim"], 0.3, 0.15),
        ("OK", p["green"], "blood_ai", "13k lines, refactoring", p["dim"], 0.35, 0.4),
        ("OK", p["green"], "sumo.bot", "listening on 127.0.0.1:67", p["dim"], 0.2, 0.1),
        ("OK", p["green"], "atom.cat", "roaming somewhere", p["dim"], 0.15, 0.05),
        (tag, scolor, "claude api", status_text, scolor, 0.3, 0.1),
        ("OK", p["green"], "omar.mood", mood, p["dim"], 0.15, 0.0),
    ]
    STALL = 1.4  # network wait before the claude api line

    W, LH, PAD_TOP = 780, 26, 64
    H = PAD_TOP + (len(lines) + 2) * LH + 24
    t = 0.9

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
        f'<g opacity="0"><animate attributeName="opacity" to="1" begin="0.2s" dur="0.01s" fill="freeze"/>'
        f'<text x="28" y="{y}" fill="{p["accent"]}">$ boot omar.sys --verbose</text></g>'
    )

    for i, (tg, tc, label, detail, dc, type_dur, pause_after) in enumerate(lines):
        y += LH
        if label == "claude api":
            # progress dots during the stall, hidden the instant the wipe starts
            wait = [f'<g fill="{p["dim"]}">']
            for d in range(3):
                wait.append(
                    f'<text x="{28 + d * 12}" y="{y}" opacity="0">.'
                    f'<animate attributeName="opacity" to="1" begin="{t + 0.3 + d * 0.35:.2f}s" dur="0.01s" fill="freeze"/>'
                    f'</text>'
                )
            wait.append(f'<animate attributeName="opacity" to="0" begin="{t + STALL:.2f}s" dur="0.01s" fill="freeze"/></g>')
            svg.append("".join(wait))
            t += STALL
        cid = f"c{i}"
        svg.append(f'<clipPath id="{cid}"><rect x="0" y="{y - 18}" width="0" height="24">'
                   f'<animate attributeName="width" from="0" to="{W}" begin="{t:.2f}s" dur="{type_dur}s" fill="freeze"/>'
                   f'</rect></clipPath>')
        dots = "." * max(2, 28 - len(label))
        detail_part = f' <tspan fill="{dc}">{detail}</tspan>' if detail else ""
        svg.append(
            f'<g clip-path="url(#{cid})">'
            f'<text x="28" y="{y}" fill="{p["text"]}">[ <tspan fill="{tc}">{tg}</tspan> ] '
            f'{label} <tspan fill="{p["dots"]}">{dots}</tspan>{detail_part}</text></g>'
        )
        t += type_dur + pause_after

    y += LH * 2 - 10
    svg.append(
        f'<g opacity="0"><animate attributeName="opacity" to="1" begin="{t + 0.3:.2f}s" dur="0.01s" fill="freeze"/>'
        f'<text x="28" y="{y}" fill="{p["accent"]}">ready.</text>'
        f'<text x="96" y="{y}" fill="{p["dim"]}" font-size="12">last boot: {now}</text>'
        f'<rect x="70" y="{y - 13}" width="9" height="16" fill="{p["text"]}">'
        f'<animate attributeName="opacity" values="1;0;1" dur="1.1s" begin="{t + 0.4:.2f}s" repeatCount="indefinite"/>'
        f'</rect></g>'
    )
    svg.append("</svg>")
    with open(filename, "w") as f:
        f.write("".join(svg))


def main():
    indicator = fetch_claude_status()
    ict = timezone(timedelta(hours=7))
    now = datetime.now(ict).strftime("%Y-%m-%d %H:%M ICT")
    build_svg(DARK, indicator, now, "boot.svg")
    build_svg(LIGHT, indicator, now, "boot-light.svg")
    print(f"boot.svg + boot-light.svg written — claude: {indicator}")


if __name__ == "__main__":
    main()
