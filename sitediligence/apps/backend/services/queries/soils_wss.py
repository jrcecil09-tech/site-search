"""NRCS Web Soil Survey comprehensive data module.

Orchestrates spatial (WFS), tabular (SDA), processing (parser),
and file export (downloader) into a single unified result.

Mukey acquisition strategy:
  1. Try WFS MapunitPoly (returns polygons + mukeys)
  2. Fall back to SDA spatial function (faster, no geometry)
  3. If mukeys still empty, return no-data result
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from services.queries.soils_spatial  import (
    get_soil_polygons,
    get_soil_lines_and_points,
    get_survey_areas,
)
from services.queries.soils_tabular  import (
    discover_mukeys_by_bbox,
    get_all_tabular,
)
from services.queries.soils_downloader import save_all_exports
from utils.soils_parser              import process_all

log = logging.getLogger(__name__)


async def query(ctx: Any) -> dict[str, Any]:
    """
    Full NRCS WSS query for ctx.bbox.

    Steps:
      1. Parallel: WFS polygons + survey areas
      2. If WFS returned no mukeys, fall back to SDA spatial function
      3. Parallel: WFS lines/points + all 9 SDA tabular groups
      4. Process and flag
      5. Save exports to disk (non-fatal)

    Returns a comprehensive result dict.
    """
    # ── Step 1: Spatial ───────────────────────────────────────────────────────
    polygons_result, survey_areas = await asyncio.gather(
        get_soil_polygons(ctx),
        get_survey_areas(ctx),
    )

    mukeys: list[str] = polygons_result.get("mukeys", [])

    # ── Step 2: Mukey fallback ────────────────────────────────────────────────
    if not mukeys:
        log.info("WFS returned no mukeys — falling back to SDA spatial function")
        mukeys = await discover_mukeys_by_bbox(ctx.bbox)

    if not mukeys:
        return {
            "source":         "NRCS Web Soil Survey SSURGO",
            "map_unit_count": 0,
            "hydric_present": False,
            "flag":           False,
            "map_units":      [],
            "summary":        {},
            "mukeys":         [],
            "survey_areas":   survey_areas,
            "exports":        {},
            "display": {
                "wms_url":   "https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms",
                "wms_layer": "mapunitpoly",
                "opacity":   0.55,
            },
        }

    # ── Step 3: Lines/points + tabular (parallel) ─────────────────────────────
    (lines_fc, points_fc), tabular = await asyncio.gather(
        get_soil_lines_and_points(ctx),
        get_all_tabular(mukeys),
    )

    spatial = {
        "polygons":     polygons_result,
        "lines":        lines_fc,
        "points":       points_fc,
        "survey_areas": survey_areas,
        "mukeys":       mukeys,
    }

    # ── Step 4: Process ───────────────────────────────────────────────────────
    processed = process_all(mukeys, tabular, survey_areas)

    # ── Step 5: Export (non-fatal) ────────────────────────────────────────────
    export_paths: dict[str, str] = {}
    try:
        export_paths = save_all_exports(
            project_id = ctx.site_id,
            spatial    = spatial,
            tabular    = tabular,
            processed  = processed,
        )
    except Exception as exc:
        log.warning("Soil export failed (non-fatal): %s", exc)

    map_units   = processed.get("map_units", [])
    hydric_present = processed.get("hydric_present", False)

    return {
        "source":           "NRCS Web Soil Survey SSURGO",
        "map_unit_count":   len(map_units),
        "hydric_present":   hydric_present,
        "hydric_count":     processed.get("hydric_count", 0),
        "flag":             hydric_present,
        "mukeys":           mukeys,
        "map_units":        map_units,
        "flags_summary":    processed.get("flags_summary", {}),
        "has_restrictions": processed.get("has_restrictions", False),
        "flood_risk_count": processed.get("flood_risk_count", 0),
        "capability_class": processed.get("capability_class", {}),
        "suitability_grid": processed.get("suitability_grid", {}),
        "infiltration_by_mukey": processed.get("infiltration_by_mukey", {}),
        "shrink_swell_by_mukey": processed.get("shrink_swell_by_mukey", {}),
        "survey_areas":     survey_areas,
        "polygons":         polygons_result,
        "lines":            lines_fc,
        "points":           points_fc,
        "exports":          export_paths,
        "display": {
            "wms_url":       "https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms",
            "wms_layer":     "mapunitpoly",
            "opacity":       0.55,
            "overlay_color": "#16a34a",
        },
    }
