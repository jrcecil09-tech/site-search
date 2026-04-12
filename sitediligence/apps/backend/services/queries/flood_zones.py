"""FEMA NFHL Flood Zones query.

Endpoint: https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28
Layer 28: Flood Hazard Zone polygons (S_Fld_Haz_Ar)
Fields:   FLD_ZONE, BFE_DSGND, DFIRM_ID, FLOODWAY, SFHA_TF, DEPTH, SOURCE_CIT

Flood zone categories:
  Special Flood Hazard Areas (SFHA) — 1% annual chance (100-year) flood:
    A   Approximate study, no BFE
    AE  Detailed study, BFE assigned        ← primary regulatory zone
    AH  Ponding, BFE assigned
    AO  Sheet flow, average depth 1–3 ft
    AR  Restoration area
    A99 Protected by federal levee project
    VE  Coastal high-hazard, wave action, BFE assigned
    V   Coastal, wave action, no BFE
  Non-SFHA:
    X (shaded)   0.2% annual chance (500-year) flood
    X (unshaded) Minimal flood hazard
    D            Undetermined risk
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)

_NFHL_BASE = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer"
_LAYER_ID = 28  # Flood Hazard Zone (S_Fld_Haz_Ar)
_FIELDS = "FLD_ZONE,BFE_DSGND,DFIRM_ID,FLOODWAY,SFHA_TF,DEPTH,SOURCE_CIT"

# Separate connect/read timeouts — prevents "stream idle timeout" on slow ArcGIS servers
_TIMEOUT = httpx.Timeout(connect=8.0, read=30.0, write=8.0, pool=5.0)

# Zones that constitute Special Flood Hazard Areas
_SFHA_ZONES = frozenset({"A", "AE", "AH", "AO", "AR", "A99", "VE", "V"})

# Zones with assigned Base Flood Elevation (BFE)
_BFE_ZONES = frozenset({"AE", "AH", "VE"})

_ZONE_DESCRIPTIONS: dict[str, str] = {
    "A":    "SFHA — Approximate study, no BFE",
    "AE":   "SFHA — Detailed study, BFE available",
    "AH":   "SFHA — Ponding, BFE available",
    "AO":   "SFHA — Sheet flow (depth 1–3 ft)",
    "AR":   "SFHA — Restoration area",
    "A99":  "SFHA — Protected by federal levee",
    "VE":   "SFHA — Coastal high-hazard, wave action, BFE available",
    "V":    "SFHA — Coastal high-hazard, no BFE",
    "X":    "Non-SFHA (500-year or minimal hazard)",
    "D":    "Undetermined flood hazard",
}

# Map overlay colors by zone (orange palette for flood)
_ZONE_COLORS: dict[str, str] = {
    "AE":  "#f97316",  # orange — primary SFHA
    "VE":  "#ef4444",  # red    — coastal SFHA
    "A":   "#fb923c",  # light orange
    "AH":  "#f59e0b",  # amber
    "AO":  "#fbbf24",  # yellow-amber
    "AR":  "#fde68a",  # pale yellow
    "A99": "#fde68a",
    "V":   "#fca5a5",  # light red
    "X":   "#d1d5db",  # gray — non-SFHA
    "D":   "#e5e7eb",  # light gray
}

# Sentinel values FEMA uses to indicate "not applicable"
_BFE_NO_DATA = {-9999.0, -8888.0, -8889.0, 0.0}


# ── Main query function ───────────────────────────────────────────────────────

async def query(ctx: Any) -> dict[str, Any]:
    """Fetch FEMA NFHL flood zone polygons intersecting the site bbox.

    Returns flood zone features with designations, BFE values, FIRM panel
    numbers, and flags the site if any portion is in a Special Flood Hazard Area.
    """
    minlon, minlat, maxlon, maxlat = ctx.bbox

    params = {
        "geometry": f"{minlon},{minlat},{maxlon},{maxlat}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": _FIELDS,
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "json",
    }
    url = f"{_NFHL_BASE}/{_LAYER_ID}/query"

    async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    if "error" in data:
        err = data["error"]
        raise RuntimeError(
            f"FEMA NFHL API error {err.get('code', '?')}: {err.get('message', err)}"
        )

    features = data.get("features", [])
    zones, has_sfha, has_ae = _process_features(features)

    return {
        "source": "FEMA NFHL",
        "endpoint": url,
        "flag": has_sfha,
        "sfha_present": has_sfha,
        "zone_ae_present": has_ae,
        "zone_count": len(zones),
        "flood_zones": zones,
        "summary": _build_summary(zones, has_sfha, has_ae),
        "display": {
            "layer_type": "polygon",
            "zone_colors": _ZONE_COLORS,
            "default_color": "#f97316",
            "opacity": 0.5,
            "label": "FEMA Flood Zones (NFHL)",
        },
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _clean_bfe(raw: Any) -> float | None:
    """Return BFE in feet, or None if the value is a FEMA no-data sentinel."""
    if raw is None:
        return None
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return None
    return None if val in _BFE_NO_DATA or val < -100 else round(val, 1)


def _process_features(
    features: list[dict],
) -> tuple[list[dict], bool, bool]:
    zones: list[dict] = []
    has_sfha = False
    has_ae = False

    for feat in features:
        attr = feat.get("attributes") or {}
        zone = (attr.get("FLD_ZONE") or "").strip().upper()
        bfe = _clean_bfe(attr.get("BFE_DSGND"))
        dfirm_id = (attr.get("DFIRM_ID") or "").strip()
        floodway = (attr.get("FLOODWAY") or "").strip().upper() == "FLOODWAY"
        depth = _clean_bfe(attr.get("DEPTH"))

        # SFHA_TF: "T" = true (in SFHA), "F" = false, or rely on zone name
        sfha_tf = str(attr.get("SFHA_TF") or "").strip().upper()
        is_sfha = sfha_tf == "T" or zone in _SFHA_ZONES

        is_ae = zone in _BFE_ZONES

        if is_sfha:
            has_sfha = True
        if is_ae:
            has_ae = True

        zones.append(
            {
                "zone": zone,
                "description": _ZONE_DESCRIPTIONS.get(zone, f"Zone {zone}"),
                "sfha": is_sfha,
                "bfe_ft": bfe,
                "firm_panel": dfirm_id or None,
                "floodway": floodway,
                "depth_ft": depth,
                "color": _ZONE_COLORS.get(zone, "#f97316"),
                "geometry": feat.get("geometry"),
            }
        )

    return zones, has_sfha, has_ae


def _build_summary(
    zones: list[dict],
    has_sfha: bool,
    has_ae: bool,
) -> dict[str, Any]:
    zone_counts: dict[str, int] = {}
    firm_panels: list[str] = []
    bfe_values: list[float] = []

    for z in zones:
        name = z["zone"] or "Unknown"
        zone_counts[name] = zone_counts.get(name, 0) + 1
        if z.get("firm_panel") and z["firm_panel"] not in firm_panels:
            firm_panels.append(z["firm_panel"])
        if z.get("bfe_ft") is not None:
            bfe_values.append(z["bfe_ft"])

    if not zones:
        msg = "No flood zone data found — site may be outside FEMA-mapped area."
    elif not has_sfha:
        zones_str = ", ".join(sorted(zone_counts))
        msg = f"Site is in {zones_str} (non-SFHA). Minimal or moderate flood risk."
    else:
        zones_str = ", ".join(sorted(zone_counts))
        ae_note = " Zone AE — regulatory floodplain with BFE." if has_ae else ""
        msg = (
            f"Site intersects flood zone(s): {zones_str}.{ae_note} "
            "Flood insurance likely required. Consult local floodplain administrator."
        )

    return {
        "zones_found": zone_counts,
        "sfha_flag": has_sfha,
        "zone_ae_flag": has_ae,
        "firm_panels": firm_panels,
        "bfe_range_ft": (
            {"min": min(bfe_values), "max": max(bfe_values)} if bfe_values else None
        ),
        "message": msg,
    }
