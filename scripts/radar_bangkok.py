#!/usr/bin/env python3
"""Fetches live Bangkok weather + rain radar and composites basemap/radar tiles into panel images."""
import base64
import io
import json
import math
import urllib.request

LAT, LON = 13.7563, 100.5018
ZOOM = 8
TILE = 256
GRID_W, GRID_H = 3, 2
PANEL_W, PANEL_H = 724, 280
RADAR_ALPHA = 0.65

WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    "&current=temperature_2m,precipitation,weather_code,wind_speed_10m"
)
RAINVIEWER_URL = "https://api.rainviewer.com/public/weather-maps.json"
RADAR_TILE = "https://tilecache.rainviewer.com{path}/256/{z}/{x}/{y}/2/1_1.png"
BASEMAP_TILE = "https://basemaps.cartocdn.com/{style}/{z}/{x}/{y}.png"

WMO_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "rime fog",
    51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    56: "freezing drizzle", 57: "freezing drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain",
    66: "freezing rain", 67: "freezing rain",
    71: "light snow", 73: "snow", 75: "heavy snow", 77: "snow grains",
    80: "light showers", 81: "showers", 82: "violent showers",
    85: "snow showers", 86: "snow showers",
    95: "thunderstorm", 96: "thunderstorm + hail", 99: "thunderstorm + hail",
}


def _get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": "omar-boot-banner"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read() if binary else json.load(r)


def _grid_origin():
    """Top-left tile of the 3x2 grid and the panel crop offset inside it."""
    n = 2 ** ZOOM
    xf = (LON + 180.0) / 360.0 * n
    yf = (1.0 - math.asinh(math.tan(math.radians(LAT))) / math.pi) / 2.0 * n
    px, py = xf * TILE, yf * TILE
    x0 = int((px - PANEL_W / 2) // TILE)
    y0 = int((py - PANEL_H / 2) // TILE)
    return x0, y0, int(px - PANEL_W / 2) - x0 * TILE, int(py - PANEL_H / 2) - y0 * TILE


def _stitch(url_for):
    from PIL import Image
    x0, y0, _, _ = _grid_origin()
    grid = Image.new("RGBA", (GRID_W * TILE, GRID_H * TILE))
    for dx in range(GRID_W):
        for dy in range(GRID_H):
            raw = _get(url_for(x0 + dx, y0 + dy), binary=True)
            grid.paste(Image.open(io.BytesIO(raw)).convert("RGBA"), (dx * TILE, dy * TILE))
    return grid


def _compose(style, radar_grid):
    base = _stitch(lambda x, y: BASEMAP_TILE.format(style=style, z=ZOOM, x=x, y=y))
    base.alpha_composite(radar_grid)
    _, _, left, top = _grid_origin()
    crop = base.crop((left, top, left + PANEL_W, top + PANEL_H)).convert("RGB")
    buf = io.BytesIO()
    crop.save(buf, "JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def fetch_radar():
    """Weather stats + composited dark/light radar maps, or None if anything fails."""
    try:
        cur = _get(WEATHER_URL)["current"]
        path = _get(RAINVIEWER_URL)["radar"]["past"][-1]["path"]
        radar_grid = _stitch(lambda x, y: RADAR_TILE.format(path=path, z=ZOOM, x=x, y=y))
        radar_grid.putalpha(radar_grid.getchannel("A").point(lambda v: int(v * RADAR_ALPHA)))
        return {
            "temp_c": float(cur["temperature_2m"]),
            "precip_mm": float(cur["precipitation"]),
            "wind_kmh": float(cur["wind_speed_10m"]),
            "condition": WMO_CODES.get(int(cur["weather_code"]), "unknown"),
            "map_dark_b64": _compose("dark_all", radar_grid),
            "map_light_b64": _compose("light_all", radar_grid),
        }
    except Exception:
        return None


if __name__ == "__main__":
    d = fetch_radar()
    if d is None:
        print("no signal")
    else:
        print(f"{d['temp_c']:.1f}°C · rain {d['precip_mm']:.1f}mm · wind {d['wind_kmh']:.0f} km/h"
              f" · {d['condition']} · maps {len(d['map_dark_b64'])}+{len(d['map_light_b64'])} b64 chars")
