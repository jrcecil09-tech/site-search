"""EPA environmental records — FRS, ECHO, and Envirofacts (Superfund / RCRA / TRI).

Sub-queries (all run in parallel; all failures are non-fatal):

  1. EPA FRS  — Facility Registry Service
     https://ofmpub.epa.gov/frs_public2/frs_rest_services.get_facilities
     Regulated facilities within 1 mile: name, programs (AIR/WATER/WASTE…),
     address, coordinates.

  2. EPA ECHO — Enforcement and Compliance History Online
     https://echo.epa.gov/rest-services/facility_search/facilities
     Facilities with compliance/enforcement history within 1 mile: violation
     counts, formal actions, program-level compliance status.

  3. EPA Envirofacts — three nested parallel queries:
       a. SEMS_ACTIVE_SITES  → Superfund (CERCLA) active sites
       b. RCR_HANDLER        → RCRA hazardous waste handlers
       c. TRI_FACILITY       → Toxic Release Inventory reporters

Flag: raised when any Superfund site centroid is within 0.5 miles of the
      site bbox centroid.
"""

from __future__ import annotations

import asyncio
import logging
import math
from typing import Any

import httpx

log = logging.getLogger(__name__)

# ── Endpoint constants ────────────────────────────────────────────────────────

_FRS_URL          = "https://ofmpub.epa.gov/frs_public2/frs_rest_services.get_facilities"
_ECHO_URL         = "https://echo.epa.gov/rest-services/facility_search/facilities"
_ENVIROFACTS_BASE = "https://enviro.epa.gov/enviro/efservice"

# Exported for tests — full URL prefix before the bbox path segments
_SEMS_URL_BASE = f"{_ENVIROFACTS_BASE}/SEMS_ACTIVE_SITES"
_RCRA_URL_BASE = f"{_ENVIROFACTS_BASE}/RCR_HANDLER"
_TRI_URL_BASE  = f"{_ENVIROFACTS_BASE}/TRI_FACILITY"

_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)

_BUFFER_MILES         = 1.0
_SUPERFUND_FLAG_MILES = 0.5

# Map marker colours per category
_COLOR_SUPERFUND = "#dc2626"   # red
_COLOR_RCRA      = "#f97316"   # orange
_COLOR_TRI       = "#eab308"   # yellow
_COLOR_FRS       = "#6366f1"   # indigo


# ── Geometry ──────────────────────────────────────────────────────────────────

def _buffer_bbox_miles(
    bbox: tuple[float, float, float, float],
    miles: float = _BUFFER_MILES,
) -> tuple[float, float, float, float]:
    """Expand bbox symmetrically by `miles` in all four directions."""
    minlon, minlat, maxlon, maxlat = bbox
    center_lat = (minlat + maxlat) / 2.0
    meters  = miles * 1_609.344
    lat_deg = meters / 111_000.0
    lon_deg = meters / (111_000.0 * math.cos(math.radians(center_lat)))
    return (
        round(minlon - lon_deg, 6),
        round(minlat - lat_deg, 6),
        round(maxlon + lon_deg, 6),
        round(maxlat + lat_deg, 6),
    )


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in miles between two WGS-84 points."""
    R = 3_958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi    = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


# ── Parsers ───────────────────────────────────────────────────────────────────

def _safe_float(val: Any) -> float | None:
    """Convert to float; return None on failure or sentinel values."""
    if val in (None, "", "N/A", "NA"):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _parse_frs_facility(raw: dict) -> dict[str, Any]:
    pgm_list = raw.get("PGMSYSList") or raw.get("InterestTypes") or []
    programs: list[str] = []
    if isinstance(pgm_list, list):
        for p in pgm_list:
            if isinstance(p, dict):
                acr = p.get("PGMSystemAcronym") or p.get("Acronym") or ""
                if acr:
                    programs.append(str(acr))
            elif p:
                programs.append(str(p))
    return {
        "registry_id": str(raw.get("RegistryId") or raw.get("RegistryID") or ""),
        "name":        str(raw.get("FacilityName") or raw.get("PrimaryName") or "Unknown"),
        "address":     str(raw.get("LocationAddress") or ""),
        "city":        str(raw.get("CityName") or ""),
        "state":       str(raw.get("StateCode") or ""),
        "lat":         _safe_float(raw.get("Latitude83") or raw.get("latitude83")),
        "lon":         _safe_float(raw.get("Longitude83") or raw.get("longitude83")),
        "programs":    programs,
        "category":    "frs",
        "color":       _COLOR_FRS,
    }


def _parse_echo_facility(raw: dict) -> dict[str, Any]:
    total_v = int(raw.get("TotalViolations") or 0)
    formal  = int(raw.get("FormalEnforcementActions") or 0)
    return {
        "registry_id":       str(raw.get("RegistryID") or ""),
        "name":              str(raw.get("FacilityName") or "Unknown"),
        "lat":               _safe_float(raw.get("Latitude") or raw.get("FacilityLatitude")),
        "lon":               _safe_float(raw.get("Longitude") or raw.get("FacilityLongitude")),
        "compliance_status": {
            "air":   str(raw.get("CAAStatus") or ""),
            "water": str(raw.get("CWAStatus") or ""),
            "waste": str(raw.get("RCRAStatus") or ""),
        },
        "total_violations":  total_v,
        "formal_actions":    formal,
        "inspections":       int(raw.get("InspectionCount") or 0),
        "has_violation":     total_v > 0 or formal > 0,
        "facility_type":     str(raw.get("FacilityTypeName") or ""),
        "category":          "echo",
        "color":             _COLOR_FRS,
    }


def _parse_cercla_site(
    raw: dict,
    site_lat: float,
    site_lon: float,
) -> dict[str, Any]:
    lat  = _safe_float(raw.get("LATITUDE84") or raw.get("latitude84"))
    lon  = _safe_float(raw.get("LONGITUDE84") or raw.get("longitude84"))
    dist = (
        round(_haversine_miles(site_lat, site_lon, lat, lon), 2)
        if lat is not None and lon is not None
        else None
    )
    return {
        "site_id":        str(raw.get("SITE_ID") or raw.get("site_id") or ""),
        "name":           str(raw.get("SITE_NAME") or raw.get("site_name") or "Unknown"),
        "address":        str(raw.get("ADDRESS_TEXT") or raw.get("address_text") or ""),
        "city":           str(raw.get("CITY_NAME") or raw.get("city_name") or ""),
        "state":          str(raw.get("STATE_CODE") or raw.get("state_code") or ""),
        "status":         str(raw.get("CURRENT_SITE_STATUS") or raw.get("current_site_status") or ""),
        "npl_status":     str(raw.get("NPL_STATUS") or raw.get("npl_status") or ""),
        "lat":            lat,
        "lon":            lon,
        "distance_miles": dist,
        "category":       "superfund",
        "color":          _COLOR_SUPERFUND,
    }


def _parse_rcra_handler(raw: dict) -> dict[str, Any]:
    activity = str(raw.get("CURRENT_RECORD_ACTIVITY") or raw.get("current_record_activity") or "")
    return {
        "handler_id": str(raw.get("HANDLER_ID") or raw.get("handler_id") or ""),
        "name":       str(raw.get("FACILITY_NAME") or raw.get("facility_name") or "Unknown"),
        "city":       str(raw.get("CITY_NAME") or raw.get("city_name") or ""),
        "state":      str(raw.get("STATE_CODE") or raw.get("state_code") or ""),
        "active":     activity.strip().upper() == "Y",
        "lat":        _safe_float(raw.get("LATITUDE_DECIMAL_DEG") or raw.get("latitude_decimal_deg")),
        "lon":        _safe_float(raw.get("LONGITUDE_DECIMAL_DEG") or raw.get("longitude_decimal_deg")),
        "category":   "rcra",
        "color":      _COLOR_RCRA,
    }


def _parse_tri_facility(raw: dict) -> dict[str, Any]:
    return {
        "facility_id": str(raw.get("TRI_FACILITY_ID") or raw.get("tri_facility_id") or ""),
        "name":        str(raw.get("FACILITY_NAME") or raw.get("facility_name") or "Unknown"),
        "city":        str(raw.get("CITY") or raw.get("city") or ""),
        "state":       str(raw.get("STATE_ABBR") or raw.get("state_abbr") or ""),
        "sic_code":    str(raw.get("SIC_CODE") or raw.get("sic_code") or ""),
        "lat":         _safe_float(raw.get("LATITUDE82") or raw.get("latitude82")),
        "lon":         _safe_float(raw.get("LONGITUDE82") or raw.get("longitude82")),
        "category":    "tri",
        "color":       _COLOR_TRI,
    }


# ── API fetch helpers ─────────────────────────────────────────────────────────

async def _fetch_frs(
    client: httpx.AsyncClient,
    center_lat: float,
    center_lon: float,
) -> list[dict]:
    resp = await client.get(_FRS_URL, params={
        "latitude83":    center_lat,
        "longitude83":   center_lon,
        "search_radius": _BUFFER_MILES,
        "output":        "JSON",
    })
    resp.raise_for_status()
    return (resp.json().get("Results") or {}).get("Facilities") or []


async def _fetch_echo(
    client: httpx.AsyncClient,
    buffered: tuple[float, float, float, float],
) -> list[dict]:
    minlon, minlat, maxlon, maxlat = buffered
    resp = await client.get(_ECHO_URL, params={
        "output":  "JSON",
        "p_c1lat": minlat,
        "p_c1lon": minlon,
        "p_c2lat": maxlat,
        "p_c2lon": maxlon,
    })
    resp.raise_for_status()
    return (resp.json().get("Results") or {}).get("Facilities") or []


async def _fetch_cercla(
    client: httpx.AsyncClient,
    minlat: float, maxlat: float,
    minlon: float, maxlon: float,
) -> list[dict]:
    url = (
        f"{_SEMS_URL_BASE}"
        f"/LATITUDE84/{minlat}/{maxlat}"
        f"/LONGITUDE84/{minlon}/{maxlon}/JSON"
    )
    resp = await client.get(url)
    resp.raise_for_status()
    return resp.json() or []


async def _fetch_rcra(
    client: httpx.AsyncClient,
    minlat: float, maxlat: float,
    minlon: float, maxlon: float,
) -> list[dict]:
    url = (
        f"{_RCRA_URL_BASE}"
        f"/LATITUDE_DECIMAL_DEG/{minlat}/{maxlat}"
        f"/LONGITUDE_DECIMAL_DEG/{minlon}/{maxlon}/JSON"
    )
    resp = await client.get(url)
    resp.raise_for_status()
    return resp.json() or []


async def _fetch_tri(
    client: httpx.AsyncClient,
    minlat: float, maxlat: float,
    minlon: float, maxlon: float,
) -> list[dict]:
    url = (
        f"{_TRI_URL_BASE}"
        f"/LATITUDE82/{minlat}/{maxlat}"
        f"/LONGITUDE82/{minlon}/{maxlon}/JSON"
    )
    resp = await client.get(url)
    resp.raise_for_status()
    return resp.json() or []


async def _fetch_all_envirofacts(
    client: httpx.AsyncClient,
    minlat: float, maxlat: float,
    minlon: float, maxlon: float,
) -> dict[str, list]:
    """Run CERCLA, RCRA, TRI in parallel; individual failures return []."""
    cercla_r, rcra_r, tri_r = await asyncio.gather(
        _fetch_cercla(client, minlat, maxlat, minlon, maxlon),
        _fetch_rcra(client, minlat, maxlat, minlon, maxlon),
        _fetch_tri(client, minlat, maxlat, minlon, maxlon),
        return_exceptions=True,
    )
    return {
        "cercla": _unwrap(cercla_r, "Envirofacts CERCLA", []),
        "rcra":   _unwrap(rcra_r,   "Envirofacts RCRA",   []),
        "tri":    _unwrap(tri_r,    "Envirofacts TRI",    []),
    }


# ── Risk summary ──────────────────────────────────────────────────────────────

def _build_risk_summary(
    frs: list[dict],
    echo: list[dict],
    superfund: list[dict],
    rcra: list[dict],
    tri: list[dict],
) -> dict[str, Any]:
    violations   = sum(1 for f in echo if f["has_violation"])
    formal_act   = sum(f["formal_actions"] for f in echo)
    near_sf = [
        s for s in superfund
        if s["distance_miles"] is not None
        and s["distance_miles"] <= _SUPERFUND_FLAG_MILES
    ]
    return {
        "frs_count":            len(frs),
        "echo_count":           len(echo),
        "echo_violations":      violations,
        "formal_actions":       formal_act,
        "superfund_count":      len(superfund),
        "superfund_near_count": len(near_sf),
        "rcra_count":           len(rcra),
        "tri_count":            len(tri),
        "superfund_flag":       len(near_sf) > 0,
        "near_superfund_names": [s["name"] for s in near_sf[:3]],
    }


# ── Utility ───────────────────────────────────────────────────────────────────

def _unwrap(result: Any, label: str, default: Any) -> Any:
    """Return result if not an exception; otherwise log and return default."""
    if isinstance(result, BaseException):
        log.warning("%s query failed (non-fatal): %s", label, result)
        return default
    return result


# ── Public entry point ────────────────────────────────────────────────────────

async def query(ctx: Any) -> dict[str, Any]:
    """
    Query EPA FRS, ECHO, and Envirofacts for environmental records within 1 mile
    of the site bbox.  All sub-queries are non-fatal.  Flag is raised when any
    Superfund site centroid is within 0.5 miles of the site bbox centroid.
    """
    buffered = _buffer_bbox_miles(ctx.bbox)
    minlon, minlat, maxlon, maxlat = buffered
    center_lat = (ctx.bbox[1] + ctx.bbox[3]) / 2
    center_lon = (ctx.bbox[0] + ctx.bbox[2]) / 2

    async with httpx.AsyncClient(timeout=_TIMEOUT, trust_env=False) as client:
        frs_r, echo_r, env_r = await asyncio.gather(
            _fetch_frs(client, center_lat, center_lon),
            _fetch_echo(client, buffered),
            _fetch_all_envirofacts(client, minlat, maxlat, minlon, maxlon),
            return_exceptions=True,
        )

    frs_raw  = _unwrap(frs_r,  "FRS",        [])
    echo_raw = _unwrap(echo_r, "ECHO",       [])
    env_dict = _unwrap(env_r,  "Envirofacts", {"cercla": [], "rcra": [], "tri": []})

    frs_list  = [_parse_frs_facility(f) for f in frs_raw]
    echo_list = [_parse_echo_facility(f) for f in echo_raw]
    superfund = [_parse_cercla_site(s, center_lat, center_lon) for s in env_dict.get("cercla", [])]
    rcra      = [_parse_rcra_handler(r) for r in env_dict.get("rcra", [])]
    tri       = [_parse_tri_facility(t) for t in env_dict.get("tri", [])]

    summary = _build_risk_summary(frs_list, echo_list, superfund, rcra, tri)

    return {
        "source":           "EPA FRS / ECHO / Envirofacts",
        "flag":             summary["superfund_flag"],
        "frs_facilities":   frs_list[:50],
        "echo_facilities":  echo_list[:50],
        "superfund_sites":  superfund[:20],
        "rcra_handlers":    rcra[:20],
        "tri_facilities":   tri[:20],
        "summary":          summary,
        "display": {
            "color_superfund": _COLOR_SUPERFUND,
            "color_rcra":      _COLOR_RCRA,
            "color_tri":       _COLOR_TRI,
            "color_frs":       _COLOR_FRS,
            "buffer_miles":    _BUFFER_MILES,
        },
    }
