"""Soil WSS router — comprehensive NRCS Web Soil Survey endpoints."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from services.queries import soils_wss
from services.queries.soils_downloader import (
    _project_dir,
    create_shapefile_zip,
    save_all_exports,
)
from services.queries.query_runner import QueryContext

log     = logging.getLogger(__name__)
router  = APIRouter()


# ── Request / response models ──────────────────────────────────────────────────

class SoilsQueryRequest(BaseModel):
    site_id: str
    bbox: tuple[float, float, float, float]   # minLon, minLat, maxLon, maxLat
    buffer_meters: float = 0.0


class DownloadRequest(BaseModel):
    format: str = "geojson"  # "geojson" | "shapefile" | "csv"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/query", summary="Run comprehensive WSS soil query")
async def run_soils_query(body: SoilsQueryRequest) -> dict[str, Any]:
    """
    Run all spatial + tabular SSURGO queries for the given bbox.
    Returns map units, flags, engineering properties, suitability ratings,
    and paths to exported files.
    """
    ctx = QueryContext(
        site_id       = body.site_id,
        bbox          = body.bbox,
        buffer_meters = body.buffer_meters,
    )
    try:
        result = await soils_wss.query(ctx)
    except Exception as exc:
        log.error("WSS soil query failed for site %s: %s", body.site_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Soil data query failed: {exc}",
        )
    return result


@router.get("/{project_id}/polygons", summary="Soil map unit polygons (GeoJSON)")
async def get_polygons(project_id: str) -> Any:
    """Return the attributed soil polygon GeoJSON for a completed query."""
    path = _project_dir(project_id) / "soil_polygons_attributed.geojson"
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No soil polygons found for project {project_id}. "
                   "Run POST /query first.",
        )
    return FileResponse(str(path), media_type="application/geo+json")


@router.get("/{project_id}/summary", summary="Processed soil summary table")
async def get_summary(project_id: str) -> Any:
    """Return the processed soil summary JSON (map units + flags)."""
    path = _project_dir(project_id) / "soil_summary.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No summary found. Run /query first.")
    import json
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/{project_id}/engineering", summary="Engineering properties by horizon")
async def get_engineering(project_id: str) -> Any:
    """Return horizon-level engineering properties for the dominant components."""
    path = _project_dir(project_id) / "soil_summary.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No data found. Run /query first.")
    import json
    summary = json.loads(path.read_text(encoding="utf-8"))
    return {
        "map_units": [
            {
                "mukey":          mu["mukey"],
                "musym":          mu.get("musym"),
                "muname":         mu.get("muname"),
                "unified_class":  mu.get("unified_class"),
                "aashto_class":   mu.get("aashto_class"),
                "ksat_r":         mu.get("ksat_r"),
                "lep_r":          mu.get("lep_r"),
                "liquid_limit":   mu.get("liquid_limit"),
                "plasticity_index": mu.get("plasticity_index"),
                "bearing_capacity_label": mu.get("bearing_capacity_label"),
                "corr_steel":     mu.get("corr_steel"),
                "corr_concrete":  mu.get("corr_concrete"),
                "depth_to_restrict": mu.get("depth_to_restrict"),
                "restrict_type":  mu.get("restrict_type"),
            }
            for mu in summary.get("map_units", [])
        ]
    }


@router.get("/{project_id}/interpretations", summary="Land use suitability ratings")
async def get_interpretations(project_id: str) -> Any:
    """Return the suitability grid (cointerp ratings) per map unit."""
    path = _project_dir(project_id) / "soil_summary.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No data found. Run /query first.")
    import json
    summary = json.loads(path.read_text(encoding="utf-8"))
    return {"suitability_grid": summary.get("suitability_grid", {})}


@router.get("/{project_id}/flags", summary="Flagged soil conditions")
async def get_flags(project_id: str) -> Any:
    """Return all flagged conditions with severity and message."""
    path = _project_dir(project_id) / "soil_flags.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No flags found. Run /query first.")
    import json
    return json.loads(path.read_text(encoding="utf-8"))


@router.post("/{project_id}/download", summary="Download soil data package")
async def download_soils(project_id: str, body: DownloadRequest) -> Any:
    """
    Return a download URL / file for the requested format.

    Supported formats:
      geojson    — attributed GeoJSON (soil_polygons_attributed.geojson)
      shapefile  — shapefile zip (soil_mapunits_shapefiles.zip)
      csv        — CSV tables zip (tabular/*.csv)
    """
    base = _project_dir(project_id)
    fmt  = body.format.lower()

    if fmt == "geojson":
        target = base / "soil_polygons_attributed.geojson"
        media  = "application/geo+json"
    elif fmt == "shapefile":
        target = base / "soil_mapunits_shapefiles.zip"
        media  = "application/zip"
    elif fmt == "csv":
        # Zip CSV tables on the fly
        import zipfile
        from io import BytesIO
        buf = BytesIO()
        tabular_dir = base / "tabular"
        if not tabular_dir.exists():
            raise HTTPException(status_code=404, detail="No CSV tables found. Run /query first.")
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for csv_file in tabular_dir.glob("*.csv"):
                zf.write(csv_file, arcname=csv_file.name)
        buf.seek(0)
        from fastapi.responses import Response
        return Response(
            content=buf.read(),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="soils_{project_id}_tables.zip"'},
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown format '{fmt}'. Use: geojson, shapefile, csv",
        )

    if not target.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{fmt} export not found. Run POST /query first.",
        )

    return FileResponse(
        str(target),
        media_type=media,
        filename=target.name,
    )
