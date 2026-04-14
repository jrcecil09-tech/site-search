"""Land cover query — NLCD 2021 via MRLC WMS GetFeatureInfo.

Samples a 5×5 grid of points across the site bbox using the MRLC GeoServer
WMS GetFeatureInfo endpoint.  Each sample returns an NLCD pixel value; counts
are aggregated into a class breakdown and dominant-class summary.

WMS endpoint:
  https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2021_Land_Cover_L48/ows
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)

_NLCD_WMS_URL = (
    "https://www.mrlc.gov/geoserver/mrlc_display"
    "/NLCD_2021_Land_Cover_L48/ows"
)
_NLCD_LAYER = "NLCD_2021_Land_Cover_L48"
_GRID_SIZE  = 5   # 5×5 = 25 sample points per query
_TIMEOUT    = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)

# ── NLCD 2021 class catalogue ──────────────────────────────────────────────────
# Standard MRLC colour palette; group used for sidebar legend grouping.

_NLCD_CLASSES: dict[int, dict[str, str]] = {
    11: {"name": "Open Water",                  "group": "Water",        "color": "#476BA1"},
    12: {"name": "Perennial Ice/Snow",           "group": "Water",        "color": "#D1DDF9"},
    21: {"name": "Developed, Open Space",        "group": "Developed",    "color": "#DDC9C9"},
    22: {"name": "Developed, Low Intensity",     "group": "Developed",    "color": "#D99282"},
    23: {"name": "Developed, Medium Intensity",  "group": "Developed",    "color": "#D0021B"},
    24: {"name": "Developed, High Intensity",    "group": "Developed",    "color": "#AA0000"},
    31: {"name": "Barren Land",                  "group": "Barren",       "color": "#B2ADA3"},
    41: {"name": "Deciduous Forest",             "group": "Forest",       "color": "#6EA966"},
    42: {"name": "Evergreen Forest",             "group": "Forest",       "color": "#1D6330"},
    43: {"name": "Mixed Forest",                 "group": "Forest",       "color": "#B5C98E"},
    51: {"name": "Dwarf Scrub",                  "group": "Shrubland",    "color": "#CCB879"},
    52: {"name": "Shrub/Scrub",                  "group": "Shrubland",    "color": "#CCBA7C"},
    71: {"name": "Grassland/Herbaceous",         "group": "Herbaceous",   "color": "#E2E2C1"},
    72: {"name": "Sedge/Herbaceous",             "group": "Herbaceous",   "color": "#D0D181"},
    73: {"name": "Lichens",                      "group": "Herbaceous",   "color": "#A4CC51"},
    74: {"name": "Moss",                         "group": "Herbaceous",   "color": "#82BA9E"},
    81: {"name": "Pasture/Hay",                  "group": "Agriculture",  "color": "#DDD75C"},
    82: {"name": "Cultivated Crops",             "group": "Agriculture",  "color": "#AE7229"},
    90: {"name": "Woody Wetlands",               "group": "Wetlands",     "color": "#BBD7ED"},
    95: {"name": "Emergent Herbaceous Wetlands", "group": "Wetlands",     "color": "#71A4C1"},
}

# Codes that trigger a flag (CWA §404 relevance) or a review note
_FLAG_CLASSES   = {90, 95}     # wetlands
_REVIEW_CLASSES = {23, 24}     # high-intensity development


# ── Grid helpers ───────────────────────────────────────────────────────────────

def _grid_points(
    bbox: tuple[float, float, float, float],
    n: int,
) -> list[tuple[float, float]]:
    """Generate an n×n centred grid of (lat, lon) sample points within bbox."""
    minlon, minlat, maxlon, maxlat = bbox
    step_lon = (maxlon - minlon) / n
    step_lat = (maxlat - minlat) / n
    return [
        (minlat + step_lat * (row + 0.5), minlon + step_lon * (col + 0.5))
        for row in range(n)
        for col in range(n)
    ]


# ── Point sampler ──────────────────────────────────────────────────────────────

async def _sample_point(
    client: httpx.AsyncClient,
    lat: float,
    lon: float,
) -> int | None:
    """Return the NLCD pixel value at (lat, lon), or None on any failure."""
    eps = 0.00005   # ~5 m half-extent — creates a 1-pixel query box
    params: dict[str, str] = {
        "SERVICE":      "WMS",
        "VERSION":      "1.3.0",
        "REQUEST":      "GetFeatureInfo",
        "LAYERS":       _NLCD_LAYER,
        "QUERY_LAYERS": _NLCD_LAYER,
        "STYLES":       "",
        "CRS":          "CRS:84",
        "BBOX":         f"{lon - eps},{lat - eps},{lon + eps},{lat + eps}",
        "WIDTH":        "1",
        "HEIGHT":       "1",
        "FORMAT":       "image/png",
        "INFO_FORMAT":  "application/json",
        "I":            "0",
        "J":            "0",
    }
    try:
        resp = await client.get(_NLCD_WMS_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features") or []
        if features:
            props = features[0].get("properties") or {}
            # GeoServer returns the raster band as "Band_1" or the layer name
            raw = (
                props.get("Band_1")
                or props.get(_NLCD_LAYER)
                or props.get("NLCD_2021_Land_Cover_L48")
            )
            if raw is not None:
                return int(raw)
    except Exception as exc:
        log.debug("NLCD sample (%.5f, %.5f) failed: %s", lat, lon, exc)
    return None


# ── Result builder ─────────────────────────────────────────────────────────────

def _build_breakdown(
    codes: list[int],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Return (dominant_entry | None, sorted_breakdown_list) from raw codes."""
    if not codes:
        return None, []

    counts: dict[int, int] = {}
    for c in codes:
        counts[c] = counts.get(c, 0) + 1

    total = len(codes)
    breakdown: list[dict[str, Any]] = []
    for code, count in sorted(counts.items(), key=lambda x: -x[1]):
        info = _NLCD_CLASSES.get(code, {
            "name":  f"Class {code}",
            "group": "Unknown",
            "color": "#888888",
        })
        breakdown.append({
            "code":  code,
            "name":  info["name"],
            "group": info["group"],
            "color": info["color"],
            "count": count,
            "pct":   round(count / total * 100, 1),
        })

    return breakdown[0], breakdown


# ── Public query function ──────────────────────────────────────────────────────

async def query(ctx: Any) -> dict[str, Any]:
    """Sample NLCD 2021 land cover at a 5×5 grid across ctx.bbox.

    Returns dominant class, percentage breakdown, full class legend, and
    WMS display configuration for the map layer.  Non-fatal: returns an
    empty result on complete API failure rather than raising.
    """
    points = _grid_points(ctx.bbox, _GRID_SIZE)

    async with httpx.AsyncClient(
        timeout=_TIMEOUT,
        follow_redirects=True,
        trust_env=False,
    ) as client:
        raw_results = await asyncio.gather(
            *(_sample_point(client, lat, lon) for lat, lon in points),
            return_exceptions=True,
        )

    sampled_codes: list[int] = []
    for r in raw_results:
        if isinstance(r, int):
            sampled_codes.append(r)
        # BaseException instances are silently dropped (non-fatal per point)

    dominant, breakdown = _build_breakdown(sampled_codes)

    present_codes = {b["code"] for b in breakdown}
    flag   = bool(present_codes & _FLAG_CLASSES)
    review = bool(present_codes & _REVIEW_CLASSES)

    group_counts: dict[str, int] = {}
    for b in breakdown:
        group_counts[b["group"]] = group_counts.get(b["group"], 0) + b["count"]

    return {
        "source":         "NLCD 2021 · MRLC",
        "flag":           flag,
        "review":         review,
        "dominant_class": dominant["code"]  if dominant else None,
        "dominant_name":  dominant["name"]  if dominant else None,
        "dominant_color": dominant["color"] if dominant else None,
        "dominant_pct":   dominant["pct"]   if dominant else None,
        "sample_count":   len(sampled_codes),
        "grid_size":      _GRID_SIZE,
        "class_breakdown": breakdown,
        "group_summary":  group_counts,
        "all_classes": [
            {
                "code":  code,
                "name":  info["name"],
                "group": info["group"],
                "color": info["color"],
            }
            for code, info in sorted(_NLCD_CLASSES.items())
        ],
        "display": {
            "wms_url":      _NLCD_WMS_URL,
            "wms_layer":    _NLCD_LAYER,
            "opacity":      0.6,
            "flag_classes": sorted(_FLAG_CLASSES),
            "note": (
                "Wetland land cover detected — verify against NWI layer; "
                "CWA §404 jurisdiction may apply."
                if flag else ""
            ),
        },
    }
