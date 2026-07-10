#!/usr/bin/env python3
"""Fetches live Bangkok weather + rain radar and composites basemap/radar tiles into panel images."""
import base64
import io
import json
import math
import traceback
import urllib.request

LAT, LON = 13.7563, 100.5018
# Keep the visible map at zoom 8. RainViewer's 256px tiles stop at zoom 7,
# but its 512px zoom-7 tiles share the same global-pixel scale as 256px zoom 8
# tiles, preserving the requested close Bangkok view with actual reflectivity.
MAP_ZOOM = 8
BASEMAP_TILE_SIZE = 256
RADAR_ZOOM = 7
RADAR_TILE_SIZE = 512
GRID_W, GRID_H = 3, 2
PANEL_W, PANEL_H = 724, 280
# Slightly stronger than the basemap so actual precipitation echoes remain
# legible in the compact terminal panel.
RADAR_ALPHA = 0.80

WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    "&current=temperature_2m,precipitation,weather_code,wind_speed_10m"
)
RAINVIEWER_URL = "https://api.rainviewer.com/public/weather-maps.json"
RADAR_TILE = "https://tilecache.rainviewer.com{path}/{size}/{z}/{x}/{y}/2/1_1.png"
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


def _grid_origin(zoom, tile_size):
    """Top-left tile of the 3x2 grid and the panel crop offset inside it."""
    n = 2 ** zoom
    xf = (LON + 180.0) / 360.0 * n
    yf = (1.0 - math.asinh(math.tan(math.radians(LAT))) / math.pi) / 2.0 * n
    px, py = xf * tile_size, yf * tile_size
    x0 = int((px - PANEL_W / 2) // tile_size)
    y0 = int((py - PANEL_H / 2) // tile_size)
    return x0, y0, int(px - PANEL_W / 2) - x0 * tile_size, int(py - PANEL_H / 2) - y0 * tile_size


def _stitch(url_for, zoom, tile_size):
    from PIL import Image
    x0, y0, _, _ = _grid_origin(zoom, tile_size)
    grid = Image.new("RGBA", (GRID_W * tile_size, GRID_H * tile_size))
    for dx in range(GRID_W):
        for dy in range(GRID_H):
            raw = _get(url_for(x0 + dx, y0 + dy), binary=True)
            grid.paste(Image.open(io.BytesIO(raw)).convert("RGBA"), (dx * tile_size, dy * tile_size))
    return grid


def _panel_crop(grid, zoom, tile_size):
    _, _, left, top = _grid_origin(zoom, tile_size)
    return grid.crop((left, top, left + PANEL_W, top + PANEL_H))


def _compose(style, radar_panel):
    base_grid = _stitch(
        lambda x, y: BASEMAP_TILE.format(style=style, z=MAP_ZOOM, x=x, y=y),
        MAP_ZOOM,
        BASEMAP_TILE_SIZE,
    )
    base = _panel_crop(base_grid, MAP_ZOOM, BASEMAP_TILE_SIZE)
    base.alpha_composite(radar_panel)
    crop = base.convert("RGB")
    buf = io.BytesIO()
    crop.save(buf, "JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def fetch_radar():
    """Weather stats + composited dark/light radar maps, or None if anything fails."""
    try:
        cur = _get(WEATHER_URL)["current"]
        path = _get(RAINVIEWER_URL)["radar"]["past"][-1]["path"]
        radar_grid = _stitch(
            lambda x, y: RADAR_TILE.format(
                path=path, size=RADAR_TILE_SIZE, z=RADAR_ZOOM, x=x, y=y
            ),
            RADAR_ZOOM,
            RADAR_TILE_SIZE,
        )
        radar_panel = _panel_crop(radar_grid, RADAR_ZOOM, RADAR_TILE_SIZE)
        radar_panel.putalpha(radar_panel.getchannel("A").point(lambda v: int(v * RADAR_ALPHA)))
        return {
            "temp_c": float(cur["temperature_2m"]),
            "precip_mm": float(cur["precipitation"]),
            "wind_kmh": float(cur["wind_speed_10m"]),
            "condition": WMO_CODES.get(int(cur["weather_code"]), "unknown"),
            "map_dark_b64": _compose("dark_all", radar_panel),
            "map_light_b64": _compose("light_all", radar_panel),
        }
    except Exception:
        # Keep the banner alive on any failure, but leave the cause in the
        # Actions log so an API change is distinguishable from an outage.
        traceback.print_exc()
        return None


if __name__ == "__main__":
    d = fetch_radar()
    if d is None:
        print("no signal")
    else:
        print(f"{d['temp_c']:.1f}°C · rain {d['precip_mm']:.1f}mm · wind {d['wind_kmh']:.0f} km/h"
              f" · {d['condition']} · maps {len(d['map_dark_b64'])}+{len(d['map_light_b64'])} b64 chars")
