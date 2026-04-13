"""USGS NHD Streams query — NHDPlus High Resolution REST API.

Endpoint:  https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer
Layer 2:   NHDFlowline  — stream centerlines (GNIS_Name, StreamOrde, FType, LengthKM)
Layer 10:  NHDWaterbody — lakes, reservoirs, ponds (GNIS_Name, FType, AreaSqKm)

Buffer:    500 ft (152.4 m) applied to site bbox before querying.
Flag:      Raised when any stream of Strahler order ≥ 4 is present (notable waterway).
"""

from __future__ import annotations

import asyncio
import logging
import math
from typing import Any

import httpx

log = logging.getLogger(__name__)

_NHD_BASE      = "https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer"
_FLOWLINE_LAYER  = 2
_WATERBODY_LAYER = 10
_BUFFER_FT = 500.0
_BUFFER_M  = _BUFFER_FT * 0.3048  # 152.4 m

# Separate connect/read timeouts — prevents stream idle timeout on slow NHD servers
_TIMEOUT = httpx.Timeout(connect=8.0, read=30.0, write=8.0, pool=5.0)

# NHD FType catalogue (flowlines)
_FLOWLINE_FTYPE: dict[int, str] = {
    334: "Connector",
    336: "Canal/Ditch",
    420: "Underground Conduit",
    428: "Pipeline",
    460: "Stream/River",
    558: "Artificial Path",
    566: "Coastline",
}

# NHD FType catalogue (waterbodies)
_WATERBODY_FTYPE: dict[int, str] = {
    361: "Ice Mass",
    378: "Playa",
    390: "Lake/Pond",
    436: "Reservoir",
    493: "Estuary",
}

# Strahler order ≥ this value triggers the high-order flag
_HIGH_ORDER_THRESHOLD = 4

_FLOWLINE_COLOR  = "#1e40af"  # deep blue
_WATERBODY_COLOR = "#60a5fa"  # lighter blue fill


# ── Geometry ──────────────────────────────────────────────────────────────────

def _buffer_bbox(
    bbox: tuple[float, float, float, float],
    meters: float = _BUFFER_M,
) -> tuple[float, float, float, float]:
    """Expand bbox symmetrically by `meters` in all four directions."""
    minlon, minlat, maxlon, maxlat = bbox
    center_lat = (minlat + maxlat) / 2.0
    lat_deg = meters / 111_000.0
    lon_deg = meters / (111_000.0 * math.cos(math.radians(center_lat)))
    return (
        round(minlon - lon_deg, 6),
        round(minlat - lat_deg, 6),
        round(maxlon + lon_deg, 6),
        round(maxlat + lat_deg, 6),
    )


# ── Feature parsers ───────────────────────────────────────────────────────────

def _parse_flowline(attrs: dict[str, Any]) -> dict[str, Any]:
    """Normalise one NHD Flowline attributes dict."""
    ftype_code = int(attrs.get("FType") or 0)
    ftype_name = _FLOWLINE_FTYPE.get(ftype_code, "Stream/River")

    order_raw = (
        attrs.get("StreamOrde")   # NHDPlus_HR primary field name
        or attrs.get("StreamOrder")
        or attrs.get("STRAHLER")
        or 0
    )
    stream_order = int(order_raw) if order_raw else 0
    name = (attrs.get("GNIS_Name") or "").strip() or None
    length_km = round(float(attrs.get("LengthKM") or 0.0), 3)

    return {
        "name": name,
        "feature_type": ftype_name,
        "ftype_code": ftype_code,
        "stream_order": stream_order,
        "length_km": length_km,
        "kind": "flowline",
        "color": _FLOWLINE_COLOR,
    }


def _parse_waterbody(attrs: dict[str, Any]) -> dict[str, Any]:
    """Normalise one NHD Waterbody attributes dict."""
    ftype_code = int(attrs.get("FType") or 0)
    ftype_name = _WATERBODY_FTYPE.get(ftype_code, "Water Body")
    name = (attrs.get("GNIS_Name") or "").strip() or None
    area_sqkm = round(float(attrs.get("AreaSqKm") or 0.0), 4)

    return {
        "name": name,
        "feature_type": ftype_name,
        "ftype_code": ftype_code,
        "area_sqkm": area_sqkm,
        "kind": "waterbody",
        "color": _WATERBODY_COLOR,
    }


# ── Summary ───────────────────────────────────────────────────────────────────

def _build_summary(
    flowlines: list[dict[str, Any]],
    waterbodies: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate statistics across flowline and waterbody feature lists."""
    total_km  = round(sum(f["length_km"] for f in flowlines), 3)
    orders    = sorted({f["stream_order"] for f in flowlines if f["stream_order"]})
    max_order = max(orders, default=0)

    named_streams = sorted({f["name"] for f in flowlines if f["name"]})[:10]
    named_bodies  = sorted({w["name"] for w in waterbodies if w["name"]})[:5]

    by_type: dict[str, int] = {}
    for f in flowlines:
        by_type[f["feature_type"]] = by_type.get(f["feature_type"], 0) + 1

    return {
        "flowline_count": len(flowlines),
        "waterbody_count": len(waterbodies),
        "total_length_km": total_km,
        "max_stream_order": max_order,
        "stream_orders_present": orders,
        "named_streams": named_streams,
        "named_waterbodies": named_bodies,
        "by_type": by_type,
        "high_order_stream": max_order >= _HIGH_ORDER_THRESHOLD,
    }


# ── NHD REST helper ───────────────────────────────────────────────────────────

async def _query_layer(
    client: httpx.AsyncClient,
    layer_id: int,
    bbox: tuple[float, float, float, float],
    out_fields: str,
) -> list[dict[str, Any]]:
    """Query one NHDPlus_HR MapServer layer and return raw feature list."""
    minlon, minlat, maxlon, maxlat = bbox
    resp = await client.get(
        f"{_NHD_BASE}/{layer_id}/query",
        params={
            "geometry":     f"{minlon},{minlat},{maxlon},{maxlat}",
            "geometryType": "esriGeometryEnvelope",
            "inSR":         "4326",
            "outSR":        "4326",
            "outFields":    out_fields,
            "returnGeometry": "false",
            "f":            "json",
        },
    )
    resp.raise_for_status()
    payload = resp.json()
    if "error" in payload:
        err = payload["error"]
        raise RuntimeError(
            f"NHD API error {err.get('code', '?')}: {err.get('message', err)}"
        )
    return payload.get("features", [])


# ── Public entry point ────────────────────────────────────────────────────────

async def query(ctx: Any) -> dict[str, Any]:
    """Fetch NHD flowlines and water bodies within 500 ft of the site boundary.

    Flowline failure is fatal (raises). Waterbody failure is non-fatal
    (logged, treated as empty list) so a partial result is still returned.
    """
    buffered = _buffer_bbox(ctx.bbox)

    async with httpx.AsyncClient(timeout=_TIMEOUT, trust_env=False) as client:
        fl_result, wb_result = await asyncio.gather(
            _query_layer(
                client, _FLOWLINE_LAYER, buffered,
                "GNIS_Name,StreamOrde,FType,FCode,LengthKM",
            ),
            _query_layer(
                client, _WATERBODY_LAYER, buffered,
                "GNIS_Name,FType,FCode,AreaSqKm",
            ),
            return_exceptions=True,
        )

    if isinstance(fl_result, BaseException):
        log.error("NHD Flowline query failed: %s", fl_result)
        raise fl_result

    if isinstance(wb_result, BaseException):
        log.warning("NHD Waterbody query non-fatal: %s", wb_result)
        wb_result = []

    flowlines   = [_parse_flowline(f["attributes"])  for f in fl_result]
    waterbodies = [_parse_waterbody(f["attributes"]) for f in wb_result]

    # Deduplicate flowlines by (name, ftype_code, stream_order)
    seen: set[tuple] = set()
    unique_flowlines: list[dict] = []
    for f in flowlines:
        key = (f["name"], f["ftype_code"], f["stream_order"])
        if key not in seen:
            seen.add(key)
            unique_flowlines.append(f)

    summary = _build_summary(unique_flowlines, waterbodies)

    return {
        "source": "USGS NHDPlus High Resolution",
        "streams_present": bool(unique_flowlines or waterbodies),
        "flag": summary["high_order_stream"],
        "flowline_count": len(unique_flowlines),
        "waterbody_count": len(waterbodies),
        "buffer_ft": int(_BUFFER_FT),
        "streams": unique_flowlines[:50],
        "waterbodies": waterbodies[:20],
        "summary": summary,
        "display": {
            "overlay_color": _FLOWLINE_COLOR,
            "opacity": 0.8,
            "wms_url": f"{_NHD_BASE}/WMSServer",
            "wms_layers": "2,10",
        },
    }
