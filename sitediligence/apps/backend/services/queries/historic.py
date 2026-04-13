"""Historic & Archaeological records module.

Sub-queries (all non-fatal, run in parallel):

  1. NPS NRHP (National Register of Historic Places)
     ArcGIS Feature Service — listed properties within 1 mile of site bbox.
     Returns name, NRHP reference number, category, date listed, distance.
     Flag: any NRHP property within 500 ft of site centroid.

  2. USGS GNIS Cemeteries
     Geographic Names Information System — cemetery features within 500 ft.
     Returns feature name, GNIS ID, coordinates, distance.
     Flag: any cemetery within 500 ft.

  3. State SHPO Placeholder (static)
     Structured list of all 50 state SHPO websites with consulting instructions.
     No API call required.

Flag: raised when any NRHP property OR cemetery is within 500 ft of the site
      bbox centroid.
"""

from __future__ import annotations

import asyncio
import logging
import math
import re
from typing import Any

import httpx

log = logging.getLogger(__name__)

# ── Endpoint constants ─────────────────────────────────────────────────────────

# NPS NRHP — ArcGIS Feature Service (public, no API key required)
_NRHP_URL = (
    "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services"
    "/NR_Locations_Feature_Layer_pub/FeatureServer/0/query"
)

# USGS GNIS — Geographic Names REST API
_GNIS_URL = "https://geonames.usgs.gov/api/geonames/names"

_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)

# Buffer for NRHP query (1 mile)
_NRHP_BUFFER_MILES = 1.0

# Cemetery search buffer — slightly larger than flag threshold to capture
# features that just cross the boundary
_CEMETERY_BUFFER_MILES = 0.15   # ~800 ft

# Flag threshold — 500 ft
_FLAG_FEET   = 500
_FLAG_MILES  = _FLAG_FEET / 5_280.0   # ≈ 0.09470 miles

# Map marker colours
_COLOR_NRHP      = "#7c3aed"   # violet/purple
_COLOR_CEMETERY  = "#166534"   # dark green


# ── Geometry helpers ───────────────────────────────────────────────────────────

def _buffer_bbox_miles(
    bbox: tuple[float, float, float, float],
    miles: float,
) -> tuple[float, float, float, float]:
    """Expand bbox symmetrically by `miles` in all four directions."""
    minlon, minlat, maxlon, maxlat = bbox
    centre_lat = (minlat + maxlat) / 2.0
    metres  = miles * 1_609.344
    lat_deg = metres / 111_000.0
    lon_deg = metres / (111_000.0 * math.cos(math.radians(centre_lat)))
    return (
        round(minlon - lon_deg, 6),
        round(minlat - lat_deg, 6),
        round(maxlon + lon_deg, 6),
        round(maxlat + lat_deg, 6),
    )


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in miles between two WGS-84 points."""
    R = 3_958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi    = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _safe_float(val: Any) -> float | None:
    """Convert to float; return None on failure or sentinel values."""
    if val in (None, "", "N/A", "NA", "null"):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


# ── NRHP date parser ───────────────────────────────────────────────────────────

def _parse_nrhp_date(raw: Any) -> str | None:
    """Parse NRHP certified date to 'YYYY-MM-DD' string.

    The ArcGIS service may return epoch milliseconds (int/float) or a
    formatted date string in various formats.
    """
    if raw is None:
        return None
    # Epoch milliseconds from ArcGIS
    if isinstance(raw, (int, float)):
        try:
            import datetime
            dt = datetime.datetime.utcfromtimestamp(raw / 1_000)
            return dt.strftime("%Y-%m-%d")
        except (OSError, OverflowError, ValueError):
            return None
    s = str(raw).strip()
    if not s:
        return None
    # "MM/DD/YYYY" or "MM-DD-YYYY"
    m = re.match(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", s)
    if m:
        return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    # "YYYY-MM-DD" already
    m2 = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m2:
        return s[:10]
    return s[:10] if len(s) >= 10 else s


# ── NRHP parser ────────────────────────────────────────────────────────────────

def _parse_nrhp_feature(
    raw: dict[str, Any],
    site_lat: float,
    site_lon: float,
) -> dict[str, Any]:
    """Convert one NRHP ArcGIS feature record to a normalised dict."""
    attrs = raw.get("attributes") or {}

    # Some versions of the feature service use different field name capitalisation
    def _get(*keys: str) -> Any:
        for k in keys:
            v = attrs.get(k)
            if v is not None:
                return v
        return None

    lat  = _safe_float(_get("LATITUDE",  "Latitude",  "latitude"))
    lon  = _safe_float(_get("LONGITUDE", "Longitude", "longitude"))
    dist = (
        round(_haversine_miles(site_lat, site_lon, lat, lon), 4)
        if lat is not None and lon is not None
        else None
    )
    name = str(_get("PROPERTYNAME", "PropertyName", "RESOURCE_NAME") or "Unknown")
    cat  = str(_get("CATEGORY",     "Category")     or "").strip()
    date = _parse_nrhp_date(_get("CERTIFIEDDATE", "CertifiedDate", "LISTED_DATE"))

    return {
        "refnum":         str(_get("REFNUM", "RefNum", "REFNUMBER") or ""),
        "name":           name,
        "city":           str(_get("CITY",   "City")   or ""),
        "state":          str(_get("STATE",  "State")  or ""),
        "county":         str(_get("COUNTY", "County") or ""),
        "category":       cat,
        "date_listed":    date,
        "lat":            lat,
        "lon":            lon,
        "distance_miles": dist,
        "near_flag":      (dist is not None and dist <= _FLAG_MILES),
        "category_code":  "nrhp",
        "color":          _COLOR_NRHP,
    }


# ── GNIS cemetery parser ───────────────────────────────────────────────────────

def _parse_gnis_cemetery(
    raw: dict[str, Any],
    site_lat: float,
    site_lon: float,
) -> dict[str, Any]:
    """Convert one GNIS feature record to a normalised cemetery dict."""
    lat = _safe_float(
        raw.get("PRIM_LAT_DEC") or raw.get("prim_lat_dec")
        or raw.get("latitude")  or raw.get("LATITUDE")
    )
    lon = _safe_float(
        raw.get("PRIM_LONG_DEC") or raw.get("prim_long_dec")
        or raw.get("longitude")  or raw.get("LONGITUDE")
    )
    dist = (
        round(_haversine_miles(site_lat, site_lon, lat, lon), 4)
        if lat is not None and lon is not None
        else None
    )
    name = str(
        raw.get("FEATURE_NAME") or raw.get("feature_name")
        or raw.get("name")      or "Unknown"
    )
    gnis_id = str(
        raw.get("FEATURE_ID") or raw.get("feature_id")
        or raw.get("id")      or ""
    )
    return {
        "gnis_id":        gnis_id,
        "name":           name,
        "state":          str(raw.get("STATE_ALPHA") or raw.get("state") or ""),
        "county":         str(raw.get("COUNTY_NAME") or raw.get("county") or ""),
        "lat":            lat,
        "lon":            lon,
        "distance_miles": dist,
        "near_flag":      (dist is not None and dist <= _FLAG_MILES),
        "category_code":  "cemetery",
        "color":          _COLOR_CEMETERY,
    }


# ── Fetch helpers ──────────────────────────────────────────────────────────────

async def _fetch_nrhp(
    client: httpx.AsyncClient,
    buffered: tuple[float, float, float, float],
) -> list[dict[str, Any]]:
    """Query NRHP ArcGIS Feature Service for listed properties within buffered bbox."""
    minlon, minlat, maxlon, maxlat = buffered
    resp = await client.get(_NRHP_URL, params={
        "geometry":     f"{minlon},{minlat},{maxlon},{maxlat}",
        "geometryType": "esriGeometryEnvelope",
        "inSR":         "4326",
        "spatialRel":   "esriSpatialRelIntersects",
        "outFields":    (
            "PROPERTYNAME,REFNUM,STATE,COUNTY,CITY,"
            "CATEGORY,CERTIFIEDDATE,LATITUDE,LONGITUDE"
        ),
        "returnGeometry": "false",
        "resultRecordCount": 100,
        "f": "json",
    })
    resp.raise_for_status()
    return resp.json().get("features") or []


async def _fetch_gnis_cemeteries(
    client: httpx.AsyncClient,
    buffered: tuple[float, float, float, float],
) -> list[dict[str, Any]]:
    """Query USGS GNIS for cemetery features within buffered bbox."""
    minlon, minlat, maxlon, maxlat = buffered
    resp = await client.get(_GNIS_URL, params={
        "featureCode": "Cemetery",
        "north":       maxlat,
        "south":       minlat,
        "east":        maxlon,
        "west":        minlon,
        "maxRows":     100,
    })
    resp.raise_for_status()
    data = resp.json()
    # Response may be {"features": [...]} or a direct list
    if isinstance(data, list):
        return data
    return data.get("features") or data.get("items") or []


# ── Utility ────────────────────────────────────────────────────────────────────

def _unwrap(result: Any, label: str, default: Any) -> Any:
    """Return result if not an exception; log warning and return default otherwise."""
    if isinstance(result, BaseException):
        log.warning("%s query failed (non-fatal): %s", label, result)
        return default
    return result


# ── SHPO static data ───────────────────────────────────────────────────────────

_SHPO_DATA: list[dict[str, str]] = [
    {"abbr": "AL", "name": "Alabama",       "url": "https://www.preserveala.org"},
    {"abbr": "AK", "name": "Alaska",        "url": "https://dnr.alaska.gov/parks/oha/"},
    {"abbr": "AZ", "name": "Arizona",       "url": "https://www.azstateparks.com/shpo"},
    {"abbr": "AR", "name": "Arkansas",      "url": "https://www.arkansaspreservation.com"},
    {"abbr": "CA", "name": "California",    "url": "https://ohp.parks.ca.gov"},
    {"abbr": "CO", "name": "Colorado",      "url": "https://www.historycolorado.org/shpo"},
    {"abbr": "CT", "name": "Connecticut",   "url": "https://portal.ct.gov/DECD/Historic-Preservation"},
    {"abbr": "DE", "name": "Delaware",      "url": "https://history.delaware.gov/preservation/"},
    {"abbr": "FL", "name": "Florida",       "url": "https://www.flheritage.com/preservation/shpo/"},
    {"abbr": "GA", "name": "Georgia",       "url": "https://www.georgiashpo.org"},
    {"abbr": "HI", "name": "Hawaii",        "url": "https://dlnr.hawaii.gov/shpd/"},
    {"abbr": "ID", "name": "Idaho",         "url": "https://history.idaho.gov/shpo/"},
    {"abbr": "IL", "name": "Illinois",      "url": "https://www2.illinois.gov/dnrhistoric"},
    {"abbr": "IN", "name": "Indiana",       "url": "https://www.in.gov/dnr/historic-preservation/"},
    {"abbr": "IA", "name": "Iowa",          "url": "https://iowaculture.gov/history/preservation"},
    {"abbr": "KS", "name": "Kansas",        "url": "https://www.kshs.org/p/shpo/10431"},
    {"abbr": "KY", "name": "Kentucky",      "url": "https://heritage.ky.gov"},
    {"abbr": "LA", "name": "Louisiana",     "url": "https://www.crt.state.la.us/cultural-development/historic-preservation/"},
    {"abbr": "ME", "name": "Maine",         "url": "https://www.maine.gov/mhpc/"},
    {"abbr": "MD", "name": "Maryland",      "url": "https://mht.maryland.gov"},
    {"abbr": "MA", "name": "Massachusetts", "url": "https://www.sec.state.ma.us/mhc/"},
    {"abbr": "MI", "name": "Michigan",      "url": "https://www.michigan.gov/shpo"},
    {"abbr": "MN", "name": "Minnesota",     "url": "https://www.mnhs.org/shpo"},
    {"abbr": "MS", "name": "Mississippi",   "url": "https://www.mdah.ms.gov/preservation"},
    {"abbr": "MO", "name": "Missouri",      "url": "https://mostateparks.com/page/55210/historic-preservation"},
    {"abbr": "MT", "name": "Montana",       "url": "https://mhs.mt.gov/Shpo"},
    {"abbr": "NE", "name": "Nebraska",      "url": "https://history.nebraska.gov/preservation/"},
    {"abbr": "NV", "name": "Nevada",        "url": "https://shpo.nv.gov"},
    {"abbr": "NH", "name": "New Hampshire", "url": "https://www.nh.gov/nhdhr/"},
    {"abbr": "NJ", "name": "New Jersey",    "url": "https://www.nj.gov/dep/hpo/"},
    {"abbr": "NM", "name": "New Mexico",    "url": "https://www.nmhistoricpreservation.org"},
    {"abbr": "NY", "name": "New York",      "url": "https://parks.ny.gov/shpo/"},
    {"abbr": "NC", "name": "North Carolina","url": "https://www.dncr.nc.gov/about-agency/divisions/state-historic-preservation-office"},
    {"abbr": "ND", "name": "North Dakota",  "url": "https://www.history.nd.gov/hp/"},
    {"abbr": "OH", "name": "Ohio",          "url": "https://www.ohiohistory.org/preservation"},
    {"abbr": "OK", "name": "Oklahoma",      "url": "https://www.okhistory.org/shpo/"},
    {"abbr": "OR", "name": "Oregon",        "url": "https://www.oregonheritage.org"},
    {"abbr": "PA", "name": "Pennsylvania",  "url": "https://www.phmc.pa.gov/Preservation"},
    {"abbr": "RI", "name": "Rhode Island",  "url": "https://www.preservation.ri.gov"},
    {"abbr": "SC", "name": "South Carolina","url": "https://shpo.sc.gov"},
    {"abbr": "SD", "name": "South Dakota",  "url": "https://history.sd.gov/preservation/"},
    {"abbr": "TN", "name": "Tennessee",     "url": "https://tn.gov/environment/program-areas/na-natural-areas/shpo.html"},
    {"abbr": "TX", "name": "Texas",         "url": "https://www.thc.texas.gov"},
    {"abbr": "UT", "name": "Utah",          "url": "https://history.utah.gov/shpo/"},
    {"abbr": "VT", "name": "Vermont",       "url": "https://accd.vermont.gov/historic-preservation/shpo"},
    {"abbr": "VA", "name": "Virginia",      "url": "https://www.dhr.virginia.gov"},
    {"abbr": "WA", "name": "Washington",    "url": "https://www.dahp.wa.gov"},
    {"abbr": "WV", "name": "West Virginia", "url": "https://www.wvculture.org/shpo/"},
    {"abbr": "WI", "name": "Wisconsin",     "url": "https://www.wisconsinhistory.org/preservation"},
    {"abbr": "WY", "name": "Wyoming",       "url": "https://wyoparks.wyo.gov/index.php/shpo"},
    {"abbr": "DC", "name": "District of Columbia", "url": "https://planning.dc.gov/page/historic-preservation-office"},
]


# ── Summary builder ────────────────────────────────────────────────────────────

def _build_summary(
    nrhp: list[dict[str, Any]],
    cemeteries: list[dict[str, Any]],
) -> dict[str, Any]:
    near_nrhp  = [p for p in nrhp       if p.get("near_flag")]
    near_cem   = [c for c in cemeteries if c.get("near_flag")]
    return {
        "nrhp_count":       len(nrhp),
        "nrhp_near_count":  len(near_nrhp),
        "cemetery_count":   len(cemeteries),
        "cemetery_near_count": len(near_cem),
        "section_106_required": len(near_nrhp) > 0,
        "near_nrhp_names":  [p["name"] for p in near_nrhp[:3]],
        "near_cemetery_names": [c["name"] for c in near_cem[:3]],
    }


# ── Public entry point ─────────────────────────────────────────────────────────

async def query(ctx: Any) -> dict[str, Any]:
    """
    Query NRHP, USGS GNIS cemeteries, and return static SHPO data for the site
    bbox.  All API calls are non-fatal.  Flag is raised when any NRHP listed
    property or cemetery is within 500 ft of the site bbox centroid.

    ctx.bbox = (minLon, minLat, maxLon, maxLat)
    """
    site_lat = (ctx.bbox[1] + ctx.bbox[3]) / 2.0
    site_lon = (ctx.bbox[0] + ctx.bbox[2]) / 2.0

    nrhp_buf     = _buffer_bbox_miles(ctx.bbox, _NRHP_BUFFER_MILES)
    cemetery_buf = _buffer_bbox_miles(ctx.bbox, _CEMETERY_BUFFER_MILES)

    async with httpx.AsyncClient(timeout=_TIMEOUT, trust_env=False) as client:
        nrhp_r, cem_r = await asyncio.gather(
            _fetch_nrhp(client, nrhp_buf),
            _fetch_gnis_cemeteries(client, cemetery_buf),
            return_exceptions=True,
        )

    raw_nrhp  = _unwrap(nrhp_r, "NRHP",             [])
    raw_cem   = _unwrap(cem_r,  "GNIS Cemeteries",  [])

    nrhp_list  = [_parse_nrhp_feature(f, site_lat, site_lon) for f in raw_nrhp]
    cem_list   = [_parse_gnis_cemetery(c, site_lat, site_lon) for c in raw_cem]

    # Sort by distance
    nrhp_list.sort(key=lambda p: (p["distance_miles"] is None, p["distance_miles"] or 0))
    cem_list.sort( key=lambda c: (c["distance_miles"] is None, c["distance_miles"] or 0))

    summary = _build_summary(nrhp_list, cem_list)
    flag    = summary["nrhp_near_count"] > 0 or summary["cemetery_near_count"] > 0

    return {
        "source":          "NPS NRHP / USGS GNIS / State SHPOs",
        "flag":            flag,
        "nrhp_properties": nrhp_list[:50],
        "cemeteries":      cem_list[:30],
        "shpo_data":       _SHPO_DATA,
        "summary":         summary,
        "display": {
            "color_nrhp":        _COLOR_NRHP,
            "color_cemetery":    _COLOR_CEMETERY,
            "buffer_miles":      _NRHP_BUFFER_MILES,
            "flag_distance_ft":  _FLAG_FEET,
        },
    }
