"""NWI Wetlands query — USFWS National Wetlands Inventory REST API.

Endpoint: https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services/Wetlands/MapServer/0
Fields:   ATTRIBUTE (NWI code), WETLAND_TYPE, ACRES, GLOBALID

NWI attribute code structure:
  1st char  = System:  P=Palustrine, E=Estuarine, R=Riverine, L=Lacustrine, M=Marine
  2nd char  = Subsystem (varies by system)
  3rd+      = Class (FO=Forested, EM=Emergent, SS=Scrub-Shrub, AB=Aquatic Bed, ...)
  Number    = Subclass
  Modifier  = Water regime (A=Temporarily Flooded, C=Seasonally Flooded, ...)
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)

_NWI_QUERY_URL = (
    "https://fwspublicservices.wim.usgs.gov"
    "/wetlandsmapservice/rest/services/Wetlands/MapServer/0/query"
)
_WMS_URL = (
    "https://fwspublicservices.wim.usgs.gov"
    "/wetlandsmapservice/rest/services/Wetlands/MapServer/WMSServer"
)
_FIELDS = "ATTRIBUTE,WETLAND_TYPE,ACRES,GLOBALID"

# Separate connect/read timeouts — prevents "stream idle timeout" on slow ArcGIS servers
_TIMEOUT = httpx.Timeout(connect=8.0, read=30.0, write=8.0, pool=5.0)

# NWI system letter → human label
_SYSTEMS: dict[str, str] = {
    "P": "Palustrine",
    "E": "Estuarine",
    "R": "Riverine",
    "L": "Lacustrine",
    "M": "Marine",
}

# Palustrine + Estuarine are jurisdictional under CWA § 404
_REGULATED_SYSTEMS = frozenset({"P", "E"})

# Map overlay colors per system (blue-green palette)
_SYSTEM_COLORS: dict[str, str] = {
    "Palustrine": "#1a9850",  # dark green
    "Estuarine":  "#2c7bb6",  # medium blue
    "Riverine":   "#74add1",  # light blue
    "Lacustrine": "#abd9e9",  # pale blue
    "Marine":     "#4575b4",  # navy blue
    "Unknown":    "#2c7bb6",
}


# ── NWI attribute code parser ─────────────────────────────────────────────────

def parse_nwi_code(attribute: str) -> dict[str, Any]:
    """Parse an NWI attribute code and return system label + CWA §404 flag.

    Examples:
      PEM1A → Palustrine Emergent, regulated
      PFO1A → Palustrine Forested, regulated
      E2EM1A → Estuarine Intertidal Emergent, regulated
      R4SBC  → Riverine Intermittent Shrub-Scrub, NOT regulated under §404
    """
    code = (attribute or "").strip()
    system_char = code[0].upper() if code else ""
    system = _SYSTEMS.get(system_char, "Unknown")
    return {
        "system": system,
        "system_code": system_char,
        "regulated_404": system_char in _REGULATED_SYSTEMS,
        "color": _SYSTEM_COLORS.get(system, _SYSTEM_COLORS["Unknown"]),
    }


# ── Main query function ───────────────────────────────────────────────────────

async def query(ctx: Any) -> dict[str, Any]:
    """Fetch NWI wetland polygons intersecting the site bounding box.

    Returns wetland features, total/regulated acreage, CWA §404 flag,
    and display configuration for the map overlay.
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

    async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(_NWI_QUERY_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    if "error" in data:
        err = data["error"]
        raise RuntimeError(
            f"NWI API error {err.get('code', '?')}: {err.get('message', err)}"
        )

    features = data.get("features", [])
    wetlands, total_acres, regulated_acres = _process_features(features)
    flag = len(wetlands) > 0

    return {
        "source": "USFWS NWI",
        "endpoint": _NWI_QUERY_URL,
        "flag": flag,
        "wetlands_present": flag,
        "wetland_count": len(wetlands),
        "total_wetland_acres": round(total_acres, 3),
        "regulated_404_acres": round(regulated_acres, 3),
        "wetlands": wetlands,
        "summary": _build_summary(wetlands, total_acres, regulated_acres),
        "display": {
            "layer_type": "polygon",
            "wms_url": _WMS_URL,
            "wms_layer": "Wetlands",
            "system_colors": _SYSTEM_COLORS,
            "default_color": "#2c7bb6",
            "opacity": 0.6,
            "label": "NWI Wetlands",
        },
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _process_features(
    features: list[dict],
) -> tuple[list[dict], float, float]:
    wetlands: list[dict] = []
    total_acres = 0.0
    regulated_acres = 0.0

    for feat in features:
        attr = feat.get("attributes") or {}
        code = (attr.get("ATTRIBUTE") or "").strip()
        wetland_type = attr.get("WETLAND_TYPE") or "Unknown"
        acres = float(attr.get("ACRES") or 0.0)
        parsed = parse_nwi_code(code)

        total_acres += acres
        if parsed["regulated_404"]:
            regulated_acres += acres

        wetlands.append(
            {
                "nwi_code": code,
                "wetland_type": wetland_type,
                "system": parsed["system"],
                "regulated_404": parsed["regulated_404"],
                "acres": round(acres, 3),
                "color": parsed["color"],
                "geometry": feat.get("geometry"),
            }
        )

    return wetlands, total_acres, regulated_acres


def _build_summary(
    wetlands: list[dict],
    total_acres: float,
    regulated_404_acres: float,
) -> dict[str, Any]:
    by_type: dict[str, float] = {}
    for w in wetlands:
        t = w["wetland_type"]
        by_type[t] = round(by_type.get(t, 0.0) + w["acres"], 3)

    if not wetlands:
        msg = "No wetlands identified within site boundary."
    else:
        msg = (
            f"{len(wetlands)} wetland polygon(s) totaling {total_acres:.2f} acres. "
            f"{regulated_404_acres:.2f} acres regulated under CWA §404."
        )

    return {
        "total_acres": round(total_acres, 3),
        "regulated_404_acres": round(regulated_404_acres, 3),
        "wetland_types": by_type,
        "cwa_404_flag": regulated_404_acres > 0,
        "message": msg,
    }
