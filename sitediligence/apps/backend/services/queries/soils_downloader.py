"""Soil data file export — GeoJSON, shapefile zip, CSV tables.

Writes all outputs to {STORAGE_LOCAL_PATH}/soils/{project_id}/.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import geopandas as gpd
from pyproj import CRS
from shapely.geometry import shape

log = logging.getLogger(__name__)

_EXPORTS_BASE = Path(os.environ.get("STORAGE_LOCAL_PATH", "./data/storage")) / "soils"


# ── Path helpers ──────────────────────────────────────────────────────────────

def _project_dir(project_id: str) -> Path:
    """Return (and create) the export directory for a project."""
    d = _EXPORTS_BASE / project_id
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── GeoJSON ───────────────────────────────────────────────────────────────────

def save_geojson(project_id: str, filename: str, data: dict[str, Any]) -> Path:
    """Save a GeoJSON/dict as pretty-printed JSON.

    If filename starts with "tabular/" the tabular subdirectory is created.
    Returns the written Path.
    """
    base = _project_dir(project_id)
    target = base / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    return target


# ── CSV ───────────────────────────────────────────────────────────────────────

def save_csv(project_id: str, filename: str, rows: list[dict[str, Any]]) -> Path | None:
    """Save a list of dicts as CSV under tabular/ subdirectory.

    Returns the written Path, or None if rows is empty.
    """
    if not rows:
        return None

    tabular_dir = _project_dir(project_id) / "tabular"
    tabular_dir.mkdir(parents=True, exist_ok=True)
    target = tabular_dir / filename

    fieldnames = list(rows[0].keys())
    with target.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return target


# ── GeoDataFrame ──────────────────────────────────────────────────────────────

def geojson_to_geodataframe(geojson_fc: dict[str, Any]) -> gpd.GeoDataFrame | None:
    """Convert a GeoJSON FeatureCollection to a GeoDataFrame (EPSG:4326).

    Returns None when the FeatureCollection has no features or geometries.
    """
    features = geojson_fc.get("features") or []
    if not features:
        return None

    rows: list[dict[str, Any]] = []
    for feat in features:
        geom_dict = feat.get("geometry")
        if not geom_dict:
            continue
        try:
            geom = shape(geom_dict)
        except Exception:
            continue
        props = dict(feat.get("properties") or {})
        props["geometry"] = geom
        rows.append(props)

    if not rows:
        return None

    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    return gdf


# ── Shapefile zip ─────────────────────────────────────────────────────────────

def _utm_epsg(lon: float, lat: float) -> int:
    """Compute UTM EPSG code from a WGS84 centroid."""
    zone = int((lon + 180) / 6) + 1
    return 32600 + zone if lat >= 0 else 32700 + zone


def _truncate_columns(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Rename columns longer than 10 chars for shapefile DBF compatibility."""
    rename = {}
    seen: set[str] = set()
    for col in gdf.columns:
        if col == "geometry":
            continue
        short = col[:10]
        if short in seen:
            short = col[:8] + str(len(seen) % 100).zfill(2)
        seen.add(short)
        if short != col:
            rename[col] = short
    return gdf.rename(columns=rename) if rename else gdf


def create_shapefile_zip(
    project_id: str,
    geojson_fc: dict[str, Any],
    base_name: str,
) -> Path | None:
    """Convert a GeoJSON FeatureCollection to a multi-projection shapefile zip.

    Creates three projections:
      wgs84/         EPSG:4326
      web_mercator/  EPSG:3857
      utm/           UTM zone for the centroid

    Returns the Path to the zip file, or None if conversion fails.
    """
    gdf = geojson_to_geodataframe(geojson_fc)
    if gdf is None:
        log.warning("create_shapefile_zip: no features to export for %s", project_id)
        return None

    try:
        centroid = gdf.dissolve().centroid.iloc[0]
        utm_epsg = _utm_epsg(centroid.x, centroid.y)
    except Exception:
        utm_epsg = 32614  # fallback: UTM 14N (central US)

    projections = [
        ("wgs84",        "EPSG:4326"),
        ("web_mercator", "EPSG:3857"),
        ("utm",          f"EPSG:{utm_epsg}"),
    ]

    zip_path = _project_dir(project_id) / f"{base_name}_shapefiles.zip"

    try:
        with tempfile.TemporaryDirectory() as tmpdir, \
             zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:

            for folder, epsg in projections:
                try:
                    reprojected = gdf.to_crs(epsg)
                    safe_gdf    = _truncate_columns(reprojected)

                    shp_dir  = Path(tmpdir) / folder
                    shp_dir.mkdir()
                    shp_path = shp_dir / f"{base_name}.shp"
                    safe_gdf.to_file(str(shp_path), driver="ESRI Shapefile")

                    for ext in (".shp", ".dbf", ".shx", ".prj", ".cpg"):
                        p = shp_dir / f"{base_name}{ext}"
                        if p.exists():
                            zf.write(p, arcname=f"{folder}/{base_name}{ext}")
                except Exception as exc:
                    log.warning(
                        "Shapefile export for projection %s failed: %s", epsg, exc
                    )
    except Exception as exc:
        log.error("create_shapefile_zip failed: %s", exc)
        return None

    return zip_path


# ── Attributed GeoJSON ────────────────────────────────────────────────────────

def _attributed_fc(
    polygons_fc: dict[str, Any],
    summary_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Join summary attributes onto polygon features by mukey."""
    index = {str(r["mukey"]): r for r in summary_rows if r.get("mukey")}
    features: list[dict[str, Any]] = []

    for feat in polygons_fc.get("features", []):
        props = dict(feat.get("properties") or {})
        mk    = str(props.get("mukey") or "").strip()
        if mk in index:
            summary = dict(index[mk])
            summary.pop("flags", None)   # keep JSON lean; flags in separate file
            summary.pop("components", None)
            props.update(summary)
        features.append({
            "type":       "Feature",
            "geometry":   feat.get("geometry"),
            "properties": props,
        })

    return {"type": "FeatureCollection", "features": features}


# ── Master export ─────────────────────────────────────────────────────────────

def save_all_exports(
    project_id: str,
    spatial: dict[str, Any],
    tabular: dict[str, list[dict[str, Any]]],
    processed: dict[str, Any],
) -> dict[str, str]:
    """Save all soil export files for a project.

    Returns a dict {label: absolute_path_string}.
    """
    paths: dict[str, str] = {}
    summary_rows = processed.get("map_units", [])

    polygons_fc   = spatial.get("polygons",  {"type": "FeatureCollection", "features": []})
    lines_fc      = spatial.get("lines",     {"type": "FeatureCollection", "features": []})
    points_fc     = spatial.get("points",    {"type": "FeatureCollection", "features": []})

    # ── GeoJSON files ────────────────────────────────────────────────────────
    def _save(name: str, data: Any) -> None:
        p = save_geojson(project_id, name, data)
        paths[name] = str(p)

    _save("soil_polygons.geojson", polygons_fc)
    _save("soil_lines.geojson",    lines_fc)
    _save("soil_points.geojson",   points_fc)
    _save("soil_summary.json",     processed)

    # All flags flattened
    all_flags = [
        {"mukey": sr["mukey"], "muname": sr.get("muname"), **f}
        for sr in summary_rows
        for f in sr.get("flags", [])
    ]
    _save("soil_flags.json", {"flags": all_flags})

    # Attributed polygons (polygons + summary attributes joined)
    attr_fc = _attributed_fc(polygons_fc, summary_rows)
    _save("soil_polygons_attributed.geojson", attr_fc)

    # ── CSV tables ───────────────────────────────────────────────────────────
    csv_map = {
        "mapunit.csv":    tabular.get("mapunit", []),
        "components.csv": tabular.get("components", []),
        "chorizon.csv":   tabular.get("engineering", []),
        "cointerp.csv":   tabular.get("interpretations", []),
    }
    for fname, rows in csv_map.items():
        p = save_csv(project_id, fname, rows)
        if p:
            paths[f"tabular/{fname}"] = str(p)

    # ── Shapefile zip ────────────────────────────────────────────────────────
    shp_path = create_shapefile_zip(project_id, attr_fc, "soil_mapunits")
    if shp_path:
        paths["shapefile_zip"] = str(shp_path)

    return paths
