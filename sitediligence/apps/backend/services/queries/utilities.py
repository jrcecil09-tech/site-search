"""Utilities query — electric transmission lines and infrastructure.

Queries the HIFLD/EIA ArcGIS Feature Service for electric transmission
lines within 1 mile of the site bbox.  Non-transmission utility types
(gas, water, sewer, telecom) are loaded from config/utilities.json as
placeholder entries that users configure with local GIS endpoints.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

import httpx

log = logging.getLogger(__name__)

_HIFLD_TRANSMISSION_URL = (
    "https://services1.arcgis.com/Hp6G80Pky0om7QvQ/arcgis/rest/services"
    "/Electric_Power_Transmission_Lines/FeatureServer/0/query"
)
_TIMEOUT      = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)
_BUFFER_MILES = 1.0

_CONFIG_PATH = (
    Path(__file__).parent.parent.parent / "config" / "utilities.json"
)

_COLOR_TRANSMISSION = "#F59E0B"


# ── Config loader ──────────────────────────────────────────────────────────────

def _load_config() -> dict[str, Any]:
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        log.warning("Could not load utilities.json: %s", exc)
        return {"layers": []}


# ── Bbox expansion ─────────────────────────────────────────────────────────────

def _expand_bbox(
    bbox: tuple[float, float, float, float],
    miles: float,
) -> tuple[float, float, float, float]:
    """Expand bbox by `miles` in each cardinal direction (approximate)."""
    minlon, minlat, maxlon, maxlat = bbox
    mid_lat = (minlat + maxlat) / 2.0
    lat_deg = miles / 69.0
    lon_deg = miles / (69.0 * math.cos(math.radians(mid_lat)))
    return (
        minlon - lon_deg, minlat - lat_deg,
        maxlon + lon_deg, maxlat + lat_deg,
    )


# ── Transmission line fetcher ──────────────────────────────────────────────────

async def _fetch_transmission_lines(
    client: httpx.AsyncClient,
    bbox: tuple[float, float, float, float],
) -> list[dict[str, Any]]:
    """Query HIFLD ArcGIS FeatureService for transmission lines within bbox."""
    minlon, minlat, maxlon, maxlat = bbox
    params: dict[str, str] = {
        "geometry":          f"{minlon},{minlat},{maxlon},{maxlat}",
        "geometryType":      "esriGeometryEnvelope",
        "inSR":              "4326",
        "spatialRel":        "esriSpatialRelIntersects",
        "outSR":             "4326",
        "outFields":         "VOLTAGE,TYPE,STATUS,OWNER,ID",
        "f":                 "geojson",
        "resultRecordCount": "200",
    }
    resp = await client.get(_HIFLD_TRANSMISSION_URL, params=params)
    resp.raise_for_status()

    fc = resp.json()
    lines: list[dict[str, Any]] = []

    for feat in fc.get("features") or []:
        props = feat.get("properties") or {}
        geom  = feat.get("geometry")  or {}

        # Normalise to list-of-coordinate-arrays (one per line segment)
        coords_list: list[list[list[float]]] = []
        g_type = geom.get("type", "")
        if g_type == "MultiLineString":
            coords_list = geom.get("coordinates") or []
        elif g_type == "LineString":
            raw = geom.get("coordinates") or []
            if raw:
                coords_list = [raw]

        if not coords_list:
            continue

        voltage_raw = props.get("VOLTAGE") or props.get("voltage")
        try:
            voltage_kv = float(str(voltage_raw).replace(",", "")) if voltage_raw else None
        except (TypeError, ValueError):
            voltage_kv = None

        lines.append({
            "id":          props.get("ID")     or props.get("id"),
            "owner":       props.get("OWNER")  or props.get("owner"),
            "voltage_kv":  voltage_kv,
            "type":        props.get("TYPE")   or props.get("type"),
            "status":      props.get("STATUS") or props.get("status"),
            "color":       _COLOR_TRANSMISSION,
            "category":    "transmission",
            "coordinates": coords_list,   # [[lon, lat], ...][]
        })

    return lines


# ── Voltage summariser ─────────────────────────────────────────────────────────

def _build_voltage_summary(lines: list[dict[str, Any]]) -> dict[str, Any]:
    voltages = [ln["voltage_kv"] for ln in lines if ln.get("voltage_kv")]
    if not voltages:
        return {"min_kv": None, "max_kv": None, "count": 0, "classes": []}

    classes = sorted({
        "≥500 kV" if v >= 500 else "115–499 kV" if v >= 115 else "<115 kV"
        for v in voltages
    })
    return {
        "min_kv":  min(voltages),
        "max_kv":  max(voltages),
        "count":   len(voltages),
        "classes": classes,
    }


# ── Public query function ──────────────────────────────────────────────────────

async def query(ctx: Any) -> dict[str, Any]:
    """Fetch electric transmission lines within 1 mile and load config stubs.

    Non-fatal: returns empty transmission list and error string on API failure.
    """
    cfg        = _load_config()
    all_layers = cfg.get("layers", [])
    search_bbox = _expand_bbox(ctx.bbox, _BUFFER_MILES)

    lines: list[dict[str, Any]] = []
    error: str | None = None
    try:
        async with httpx.AsyncClient(
            timeout=_TIMEOUT,
            follow_redirects=True,
            trust_env=False,
        ) as client:
            lines = await _fetch_transmission_lines(client, search_bbox)
    except Exception as exc:
        log.warning("Transmission line fetch failed (non-fatal): %s", exc)
        error = str(exc)

    voltage_summary = _build_voltage_summary(lines)

    placeholder_layers = [
        {
            "id":       lyr["id"],
            "name":     lyr["name"],
            "category": lyr.get("category", lyr["id"]),
            "color":    lyr.get("color", "#888888"),
            "weight":   lyr.get("weight", 2),
            "enabled":  lyr.get("enabled", False),
            "note":     lyr.get("note", ""),
            "source":   lyr.get("source"),
        }
        for lyr in all_layers
        if lyr.get("id") != "transmission"
    ]

    # Flag when high-voltage lines (≥115 kV) are found within the search buffer
    flag = bool(
        lines
        and voltage_summary.get("max_kv") is not None
        and voltage_summary["max_kv"] >= 115
    )

    return {
        "source":             "HIFLD / EIA",
        "flag":               flag,
        "transmission_count": len(lines),
        "transmission_lines": lines,
        "voltage_summary":    voltage_summary,
        "placeholder_layers": placeholder_layers,
        "error":              error,
        "display": {
            "color_transmission": _COLOR_TRANSMISSION,
            "color_gas":          "#F97316",
            "color_water":        "#3B82F6",
            "color_sewer":        "#92400E",
            "color_telecom":      "#8B5CF6",
            "buffer_miles":       _BUFFER_MILES,
        },
    }
