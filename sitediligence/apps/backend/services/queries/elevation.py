"""USGS 3DEP Elevation query.

APIs:
  3DEP ImageServer getSamples
    https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/getSamples
    — samples elevation at a grid of points across the site bbox

  The National Map (TNM) Products API
    https://tnmapi.cr.usgs.gov/api/products
    — returns download links for 1/3 arc-second DEM tiles intersecting the bbox

Algorithm:
  1.  Build an N×N grid of lon/lat points across the bbox (default N=11 → 121 pts)
  2.  POST to 3DEP ImageServer getSamples to fetch all elevations in one request
  3.  Compute min/max/mean/std in feet; convert to metres
  4.  Estimate slope range (degrees) using numpy gradient across the elevation grid
  5.  Generate contour lines at 1 ft, 2 ft, and 5 ft intervals using marching squares
      implemented with scipy.interpolate + numpy iso-contouring
  6.  Query TNM API for 1/3 arc-second DEM products and return download URLs
"""

from __future__ import annotations

import asyncio
import logging
import math
from typing import Any

import httpx
import numpy as np
from scipy.interpolate import griddata

log = logging.getLogger(__name__)

_IMAGESERVER  = (
    "https://elevation.nationalmap.gov"
    "/arcgis/rest/services/3DEPElevation/ImageServer"
)
_SAMPLES_URL  = f"{_IMAGESERVER}/getSamples"
_TNM_PRODUCTS = "https://tnmapi.cr.usgs.gov/api/products"
_TIMEOUT      = httpx.Timeout(connect=8.0, read=45.0, write=8.0, pool=5.0)

_GRID_N = 11        # N×N grid → 121 sample points
_FINE_N = 50        # interpolation grid for contours
_FT_TO_M = 0.3048

# Contour interval labels and colours (feet)
_CONTOUR_INTERVALS = [
    {"interval_ft": 1,  "color": "#a3c4bc", "dash": "4,2"},
    {"interval_ft": 2,  "color": "#5b8db8", "dash": "6,2"},
    {"interval_ft": 5,  "color": "#1e40af", "dash": "solid"},
]


# ── Grid builder ──────────────────────────────────────────────────────────────

def _build_grid(
    bbox: tuple[float, float, float, float],
    n: int = _GRID_N,
) -> list[tuple[float, float]]:
    """Return a flat list of (lon, lat) points for an N×N grid across bbox."""
    minlon, minlat, maxlon, maxlat = bbox
    lons = np.linspace(minlon, maxlon, n)
    lats = np.linspace(minlat, maxlat, n)
    return [(float(lon), float(lat)) for lat in lats for lon in lons]


# ── 3DEP REST helpers ─────────────────────────────────────────────────────────

def _points_to_esri_multipoint(
    points: list[tuple[float, float]],
) -> dict:
    """Encode a list of (lon, lat) as an Esri JSON multipoint geometry."""
    return {
        "geometryType": "esriGeometryMultipoint",
        "geometry": {
            "points": [[lon, lat] for lon, lat in points],
            "spatialReference": {"wkid": 4326},
        },
    }


async def _fetch_samples(
    client: httpx.AsyncClient,
    points: list[tuple[float, float]],
) -> list[float | None]:
    """
    Call 3DEP ImageServer getSamples with a multipoint geometry.
    Returns a list of elevation values (feet) in point order; None on bad pixel.
    """
    payload = {
        "geometry": str({
            "points": [[lon, lat] for lon, lat in points],
            "spatialReference": {"wkid": 4326},
        }).replace("'", '"'),
        "geometryType": "esriGeometryMultipoint",
        "returnFirstValueOnly": "true",
        "interpolation":        "RSP_BilinearInterpolation",
        "outFields":            "*",
        "f":                    "json",
    }

    resp = await client.post(_SAMPLES_URL, data=payload)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        err = data["error"]
        raise RuntimeError(
            f"3DEP ImageServer error {err.get('code','?')}: {err.get('message', err)}"
        )

    samples = data.get("samples", [])
    values: list[float | None] = []
    for s in samples:
        raw = (s.get("attributes") or {}).get("Pixel Value") or s.get("value")
        try:
            v = float(raw) if raw not in (None, "", "NoData", -9999, "-9999") else None
            values.append(v)
        except (TypeError, ValueError):
            values.append(None)

    return values


async def _fetch_tnm_products(
    client: httpx.AsyncClient,
    bbox: tuple[float, float, float, float],
) -> list[dict]:
    """
    Query TNM Products API for 1/3 arc-second DEM tiles intersecting bbox.
    Returns a list of {title, download_url, size_mb} dicts (capped at 5).
    """
    minlon, minlat, maxlon, maxlat = bbox
    try:
        resp = await client.get(
            _TNM_PRODUCTS,
            params={
                "datasets":    "Digital Elevation Model (DEM) 1/3 arc-second",
                "bbox":        f"{minlon},{minlat},{maxlon},{maxlat}",
                "max":         "5",
                "outputFormat": "JSON",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        products = []
        for item in data.get("items", [])[:5]:
            url = (
                item.get("downloadURL")
                or item.get("urls", {}).get("GPX", "")
                or ""
            )
            products.append({
                "title":       item.get("title", "DEM tile"),
                "download_url": url,
                "size_mb":     round(item.get("sizeInBytes", 0) / 1_048_576, 1),
                "pub_date":    item.get("publicationDate", ""),
            })
        return products
    except Exception as exc:
        log.warning("TNM products query failed (non-fatal): %s", exc)
        return []


# ── Statistics ────────────────────────────────────────────────────────────────

def _compute_stats(
    values_ft: list[float],
    n: int,
    bbox: tuple[float, float, float, float],
) -> dict[str, Any]:
    """Compute elevation statistics and slope range from grid samples."""
    arr = np.array(values_ft, dtype=np.float64)
    arr = arr[np.isfinite(arr)]

    if arr.size == 0:
        return {
            "min_ft": None, "max_ft": None, "mean_ft": None, "std_ft": None,
            "min_m":  None, "max_m":  None, "mean_m":  None,
            "relief_ft": None,
            "slope_min_deg": None, "slope_max_deg": None, "slope_mean_deg": None,
        }

    min_ft  = float(np.min(arr))
    max_ft  = float(np.max(arr))
    mean_ft = float(np.mean(arr))
    std_ft  = float(np.std(arr))

    # Approximate cell size in meters for slope calculation
    minlon, minlat, maxlon, maxlat = bbox
    cell_m_x = (maxlon - minlon) / (n - 1) * 111_000 * math.cos(math.radians((minlat + maxlat) / 2))
    cell_m_y = (maxlat - minlat) / (n - 1) * 111_000
    cell_m   = (cell_m_x + cell_m_y) / 2

    # Reshape back to N×N for gradient; pad missing with mean
    full = np.full(n * n, mean_ft)
    full[:len(values_ft)] = [v if v is not None and np.isfinite(v) else mean_ft
                              for v in values_ft]
    grid = full.reshape(n, n)

    # Convert to metres for slope
    grid_m   = grid * _FT_TO_M
    dy, dx   = np.gradient(grid_m, cell_m)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    slope_deg = np.degrees(slope_rad)

    return {
        "min_ft":  round(min_ft,  1),
        "max_ft":  round(max_ft,  1),
        "mean_ft": round(mean_ft, 1),
        "std_ft":  round(std_ft,  1),
        "min_m":   round(min_ft  * _FT_TO_M, 1),
        "max_m":   round(max_ft  * _FT_TO_M, 1),
        "mean_m":  round(mean_ft * _FT_TO_M, 1),
        "relief_ft": round(max_ft - min_ft, 1),
        "slope_min_deg":  round(float(np.min(slope_deg)),  1),
        "slope_max_deg":  round(float(np.max(slope_deg)),  1),
        "slope_mean_deg": round(float(np.mean(slope_deg)), 1),
    }


# ── Contour generation ────────────────────────────────────────────────────────

def _generate_contours(
    points: list[tuple[float, float]],
    values_ft: list[float | None],
    bbox: tuple[float, float, float, float],
    fine_n: int = _FINE_N,
) -> list[dict[str, Any]]:
    """
    Interpolate the sparse elevation grid to a finer mesh and extract iso-contour
    line segments at 1 ft, 2 ft, and 5 ft intervals.

    Returns a list of contour FeatureCollections, one per interval.
    """
    # Filter out None / non-finite samples
    pts_valid: list[tuple[float, float]] = []
    vals_valid: list[float] = []
    for (lon, lat), v in zip(points, values_ft):
        if v is not None and np.isfinite(v):
            pts_valid.append((lon, lat))
            vals_valid.append(v)

    if len(pts_valid) < 4:
        return []

    # Interpolate to a regular fine grid
    minlon, minlat, maxlon, maxlat = bbox
    grid_lons = np.linspace(minlon, maxlon, fine_n)
    grid_lats = np.linspace(minlat, maxlat, fine_n)
    mesh_lon, mesh_lat = np.meshgrid(grid_lons, grid_lats)

    lon_arr = np.array([p[0] for p in pts_valid])
    lat_arr = np.array([p[1] for p in pts_valid])
    val_arr = np.array(vals_valid)

    interp = griddata(
        (lon_arr, lat_arr), val_arr,
        (mesh_lon, mesh_lat),
        method="cubic",
        fill_value=float(np.nanmean(val_arr)),
    )

    elev_min = float(np.nanmin(interp))
    elev_max = float(np.nanmax(interp))

    # No meaningful relief → skip contour generation
    if (elev_max - elev_min) < 0.1:
        return [
            {"interval_ft": cfg["interval_ft"], "color": cfg["color"],
             "dash": cfg["dash"], "level_count": 0, "features": []}
            for cfg in _CONTOUR_INTERVALS
        ]

    contour_sets = []
    for cfg in _CONTOUR_INTERVALS:
        interval = cfg["interval_ft"]
        # Determine levels within the elevation range
        first = math.ceil(elev_min / interval) * interval
        levels = np.arange(first, elev_max + interval, interval)
        levels = levels[(levels >= elev_min) & (levels <= elev_max)]

        features = []
        for level in levels:
            segs = _marching_squares_segments(interp, level, grid_lons, grid_lats)
            if segs:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "MultiLineString",
                        "coordinates": segs,
                    },
                    "properties": {
                        "elevation_ft": round(float(level), 1),
                        "elevation_m":  round(float(level) * _FT_TO_M, 2),
                        "interval_ft":  interval,
                    },
                })

        contour_sets.append({
            "interval_ft": interval,
            "color":       cfg["color"],
            "dash":        cfg["dash"],
            "level_count": len(levels),
            "features":    features,
        })

    return contour_sets


def _marching_squares_segments(
    grid: np.ndarray,
    level: float,
    lons: np.ndarray,
    lats: np.ndarray,
) -> list[list[list[float]]]:
    """
    Extract iso-contour line segments at `level` from a regular 2-D elevation grid
    using a simplified marching-squares approach.

    Returns a list of [lon, lat] coordinate pairs representing line segments.
    Each segment is a 2-element list: [[lon0, lat0], [lon1, lat1]].
    """
    rows, cols = grid.shape
    segments: list[list[list[float]]] = []

    def interp_edge(v0: float, v1: float, c0: float, c1: float) -> float:
        """Linear interpolation along an edge."""
        if abs(v1 - v0) < 1e-10:
            return (c0 + c1) / 2
        t = (level - v0) / (v1 - v0)
        return c0 + t * (c1 - c0)

    for r in range(rows - 1):
        for c in range(cols - 1):
            # Cell corners (value, lon, lat)
            v00, v01 = grid[r, c],   grid[r,   c + 1]
            v10, v11 = grid[r+1, c], grid[r+1, c + 1]
            x0, x1  = lons[c],   lons[c + 1]
            y0, y1  = lats[r],   lats[r + 1]

            # Bitmask: bit set if corner is above level
            mask = (
                (int(v00 >= level))
                | (int(v01 >= level) << 1)
                | (int(v11 >= level) << 2)
                | (int(v10 >= level) << 3)
            )
            if mask in (0, 15):
                continue  # entirely below or above

            # Midpoints on each edge (N, E, S, W)
            def north():   return [interp_edge(v00, v01, x0, x1), y0]
            def east():    return [x1, interp_edge(v01, v11, y0, y1)]
            def south():   return [interp_edge(v10, v11, x0, x1), y1]
            def west():    return [x0, interp_edge(v00, v10, y0, y1)]

            # 16-case lookup → pairs of edge midpoints that form segments
            _CASES: dict[int, list[list]] = {
                1:  [[north(), west()]],
                2:  [[north(), east()]],
                3:  [[west(), east()]],
                4:  [[east(), south()]],
                5:  [[north(), east()], [south(), west()]],
                6:  [[north(), south()]],
                7:  [[west(), south()]],
                8:  [[west(), south()]],
                9:  [[north(), south()]],
                10: [[north(), west()], [east(), south()]],
                11: [[east(), south()]],
                12: [[west(), east()]],
                13: [[north(), east()]],
                14: [[north(), west()]],
            }

            for seg in _CASES.get(mask, []):
                segments.append(seg)

    return segments


# ── Public entry point ────────────────────────────────────────────────────────

async def query(ctx: Any) -> dict[str, Any]:
    """
    Sample 3DEP elevation across a grid, compute stats/slope, generate contours,
    and fetch TNM download links for 1/3 arc-second DEM tiles.
    """
    points = _build_grid(ctx.bbox, _GRID_N)

    async with httpx.AsyncClient(timeout=_TIMEOUT, trust_env=False) as client:
        samples_result, tnm_result = await asyncio.gather(
            _fetch_samples(client, points),
            _fetch_tnm_products(client, ctx.bbox),
            return_exceptions=True,
        )

    if isinstance(samples_result, BaseException):
        log.error("3DEP getSamples failed: %s", samples_result)
        raise samples_result

    if isinstance(tnm_result, BaseException):
        log.warning("TNM products query failed (non-fatal): %s", tnm_result)
        tnm_result = []

    valid = [v for v in samples_result if v is not None and np.isfinite(v)]
    stats = _compute_stats(valid if valid else [], _GRID_N, ctx.bbox)

    contours = []
    if len(valid) >= 4:
        try:
            contours = _generate_contours(points, samples_result, ctx.bbox)
        except Exception as exc:
            log.warning("Contour generation failed (non-fatal): %s", exc)

    # Centroid elevation
    centroid_lon = (ctx.bbox[0] + ctx.bbox[2]) / 2
    centroid_lat = (ctx.bbox[1] + ctx.bbox[3]) / 2
    mid_idx = (_GRID_N * _GRID_N) // 2
    centroid_elev_ft = samples_result[mid_idx] if mid_idx < len(samples_result) else None

    return {
        "source": "USGS 3DEP (1/3 arc-second)",
        "centroid": {"lon": centroid_lon, "lat": centroid_lat},
        "centroid_elevation_ft": centroid_elev_ft,
        "centroid_elevation_m":  (
            round(centroid_elev_ft * _FT_TO_M, 1) if centroid_elev_ft is not None else None
        ),
        "grid_n": _GRID_N,
        "sample_count": len([v for v in samples_result if v is not None]),
        "stats": stats,
        "contours": contours,
        "dem_downloads": tnm_result,
        "flag": False,  # elevation is informational; no regulatory flag
        "display": {
            "overlay_color": "#78716c",
            "opacity": 0.5,
            "wms_url": f"{_IMAGESERVER}/WMSServer",
            "wms_layer": "3DEPElevation:Hillshade Gray",
        },
    }
