"""SSURGO Soils query — NRCS Web Soil Survey via Soil Data Access (SDA).

API:  https://sdmdataaccess.nrcs.usda.gov/tabular/post.rest
Body: query=<SQL>&format=JSON+PLUS   (application/x-www-form-urlencoded)
Response: {"Table": [["col1","col2",...], [row1_val1, row1_val2,...], ...]}

Spatial lookup function (T-SQL, SDA-specific):
    SDA_Get_Mukey_from_intersection_with_WktWgs84('{wkt}')

Queries (run in parallel):
  1. Component basics  — mukey/musym/muname, drainage class, hydric rating,
                         farmland classification, soil taxonomy subgroup
  2. Engineering interps — corrosion of steel/concrete, USCS class (cointerp)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)

_SDA_URL = "https://sdmdataaccess.nrcs.usda.gov/tabular/post.rest"
_TIMEOUT = httpx.Timeout(connect=10.0, read=45.0, write=10.0, pool=5.0)

# Drainage class → map display color (blue = wet, green = well-drained, amber = droughty)
_DRAINAGE_COLORS: dict[str, str] = {
    "Very poorly drained":          "#1e3a8a",
    "Poorly drained":               "#1d4ed8",
    "Somewhat poorly drained":      "#3b82f6",
    "Moderately well drained":      "#86efac",
    "Well drained":                 "#16a34a",
    "Somewhat excessively drained": "#fbbf24",
    "Excessively drained":          "#f59e0b",
}
_HYDRIC_COLOR   = "#1d4ed8"   # blue highlight for any hydric unit
_DEFAULT_COLOR  = "#a3a3a3"   # gray for unknown drainage

_WMS_URL   = "https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms"
_WMS_LAYER = "mapunitpoly"


# ── Geometry helpers ──────────────────────────────────────────────────────────

def _bbox_to_wkt(bbox: tuple[float, float, float, float]) -> str:
    """Convert (minLon, minLat, maxLon, maxLat) to a WKT POLYGON ring."""
    minlon, minlat, maxlon, maxlat = bbox
    return (
        f"POLYGON(({minlon} {minlat},{maxlon} {minlat},"
        f"{maxlon} {maxlat},{minlon} {maxlat},{minlon} {minlat}))"
    )


# ── SDA client ────────────────────────────────────────────────────────────────

async def _sda_query(client: httpx.AsyncClient, sql: str) -> dict:
    """POST a SQL query to SDA and return the parsed JSON body."""
    resp = await client.post(
        _SDA_URL,
        data={"query": sql, "format": "JSON+PLUS"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp.raise_for_status()
    return resp.json()


# ── Response parsing ──────────────────────────────────────────────────────────

def _parse_sda_table(data: dict) -> list[dict]:
    """
    Parse SDA 'JSON+PLUS' tabular response into a list of row dicts.

    Response: {"Table": [["col1","col2",...], [val1, val2,...], ...]}
    The first element is the column-header row; subsequent rows are data.
    Returns an empty list when the table is absent or has no data rows.
    """
    table = data.get("Table") or []
    if len(table) < 2:
        return []
    headers = [str(h).strip().lower() for h in table[0]]
    return [dict(zip(headers, row)) for row in table[1:]]


# ── Business logic ────────────────────────────────────────────────────────────

def _is_hydric(hydricrating: str | None) -> bool:
    """Return True when the SSURGO hydric rating indicates a hydric soil."""
    return (hydricrating or "").strip().lower() in ("yes", "all")


def _choose_color(drainage_class: str | None, is_hydric_soil: bool) -> str:
    if is_hydric_soil:
        return _HYDRIC_COLOR
    return _DRAINAGE_COLORS.get(drainage_class or "", _DEFAULT_COLOR)


def _build_map_units(
    comp_rows: list[dict],
    interp_by_cokey: dict[str, dict],
) -> list[dict]:
    """
    Group component rows by mukey and return one map-unit dict per mukey.

    The dominant component (majcompflag='Yes', highest comppct_r) supplies the
    unit-level attributes shown in the UI.  All components are stored in the
    'components' list for drill-down.
    """
    mu_buckets: dict[str, dict] = {}

    for row in comp_rows:
        mukey = str(row.get("mukey") or "").strip()
        if not mukey:
            continue

        if mukey not in mu_buckets:
            mu_buckets[mukey] = {
                "_best_pct": -1.0,
                "_dominant": None,
                "mukey":   mukey,
                "musym":   str(row.get("musym") or "").strip(),
                "muname":  str(row.get("muname") or "").strip(),
                "muacres": float(row.get("muacres") or 0),
                "components": [],
            }

        cokey    = str(row.get("cokey") or "").strip()
        comppct  = float(row.get("comppct_r") or 0)
        majflag  = str(row.get("majcompflag") or "").strip().lower() == "yes"
        drainage = str(row.get("drainagecl") or "").strip() or None
        hydric_r = str(row.get("hydricrating") or "").strip() or None
        hydric   = _is_hydric(hydric_r)
        interp   = interp_by_cokey.get(cokey, {})

        comp: dict[str, Any] = {
            "cokey":         cokey,
            "compname":      str(row.get("compname") or "").strip(),
            "comppct_r":     comppct,
            "majcompflag":   majflag,
            "drainagecl":    drainage,
            "hydricrating":  hydric_r,
            "hydric":        hydric,
            "farmlndcl":     str(row.get("farmlndcl") or "").strip() or None,
            "taxclname":     str(row.get("taxclname") or "").strip() or None,
            "taxorder":      str(row.get("taxorder") or "").strip() or None,
            "taxsubgrp":     str(row.get("taxsubgrp") or "").strip() or None,
            "corr_steel":    interp.get("corr_steel"),
            "corr_concrete": interp.get("corr_concrete"),
            "uscs_class":    interp.get("uscs_class"),
        }
        mu_buckets[mukey]["components"].append(comp)

        if majflag and comppct > mu_buckets[mukey]["_best_pct"]:
            mu_buckets[mukey]["_best_pct"]  = comppct
            mu_buckets[mukey]["_dominant"]  = comp

    result: list[dict] = []
    for mu_data in mu_buckets.values():
        comps    = mu_data["components"]
        dominant = mu_data["_dominant"] or (comps[0] if comps else {})
        hydric   = any(c["hydric"] for c in comps)
        drainage = dominant.get("drainagecl")

        result.append({
            "mukey":              mu_data["mukey"],
            "musym":              mu_data["musym"],
            "muname":             mu_data["muname"],
            "muacres":            mu_data["muacres"],
            "hydric":             hydric,
            "drainage_class":     drainage,
            "hydric_rating":      dominant.get("hydricrating"),
            "farmland_class":     dominant.get("farmlndcl"),
            "tax_class":          dominant.get("taxclname"),
            "dominant_component": dominant.get("compname"),
            "dominant_pct":       dominant.get("comppct_r"),
            "corr_steel":         dominant.get("corr_steel"),
            "corr_concrete":      dominant.get("corr_concrete"),
            "uscs_class":         dominant.get("uscs_class"),
            "color":              _choose_color(drainage, hydric),
            "components":         comps,
        })

    return result


def _build_summary(map_units: list[dict]) -> dict[str, Any]:
    hydric_units = [mu for mu in map_units if mu["hydric"]]
    drainage_counts: dict[str, int] = {}
    for mu in map_units:
        dc = mu.get("drainage_class") or "Unknown"
        drainage_counts[dc] = drainage_counts.get(dc, 0) + 1

    return {
        "map_unit_count":    len(map_units),
        "hydric_unit_count": len(hydric_units),
        "hydric_present":    bool(hydric_units),
        "drainage_classes":  drainage_counts,
        "hydric_unit_names": [mu["muname"] for mu in hydric_units[:5]],
    }


# ── Public entry point ────────────────────────────────────────────────────────

async def query(ctx: Any) -> dict[str, Any]:
    """
    Query SSURGO via SDA for soil map units intersecting ctx.bbox.

    Returns map unit attributes including drainage class, hydric rating,
    farmland classification, and engineering interpretations.
    """
    wkt = _bbox_to_wkt(ctx.bbox)

    sql_components = f"""
SELECT mu.mukey, mu.musym, mu.muname, mu.muacres,
       c.cokey, c.compname, c.comppct_r, c.majcompflag,
       c.drainagecl, c.hydricrating, c.farmlndcl,
       c.taxclname, c.taxorder, c.taxsubgrp
FROM mapunit AS mu
  INNER JOIN component AS c ON c.mukey = mu.mukey
WHERE mu.mukey IN (
  SELECT * FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('{wkt}')
)
ORDER BY mu.mukey, c.comppct_r DESC
""".strip()

    sql_interps = f"""
SELECT c.cokey, mu.mukey,
  MAX(CASE WHEN ci.mrulename = 'ENG - Corrosion of Steel'
           AND ci.ruledepth = 0 THEN ci.interphrc END) AS corr_steel,
  MAX(CASE WHEN ci.mrulename = 'ENG - Corrosion of Concrete'
           AND ci.ruledepth = 0 THEN ci.interphrc END) AS corr_concrete,
  MAX(CASE WHEN ci.mrulename LIKE '%Unified%'
           AND ci.ruledepth = 0 THEN ci.interphrc END) AS uscs_class
FROM mapunit AS mu
  INNER JOIN component AS c ON c.mukey = mu.mukey
  LEFT  JOIN cointerp  AS ci ON ci.cokey = c.cokey
WHERE mu.mukey IN (
  SELECT * FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('{wkt}')
)
GROUP BY c.cokey, mu.mukey
ORDER BY mu.mukey
""".strip()

    async with httpx.AsyncClient(timeout=_TIMEOUT, trust_env=False) as client:
        comp_result, interp_result = await asyncio.gather(
            _sda_query(client, sql_components),
            _sda_query(client, sql_interps),
            return_exceptions=True,
        )

    if isinstance(comp_result, BaseException):
        log.error("SSURGO components query failed: %s", comp_result)
        raise comp_result

    if isinstance(interp_result, BaseException):
        log.warning("SSURGO interps query failed (non-fatal): %s", interp_result)
        interp_result = {}

    comp_rows  = _parse_sda_table(comp_result)
    interp_rows = _parse_sda_table(interp_result)

    interp_by_cokey: dict[str, dict] = {
        str(r.get("cokey") or ""): {
            "corr_steel":    r.get("corr_steel"),
            "corr_concrete": r.get("corr_concrete"),
            "uscs_class":    r.get("uscs_class"),
        }
        for r in interp_rows
        if r.get("cokey")
    }

    map_units     = _build_map_units(comp_rows, interp_by_cokey)
    hydric_present = any(mu["hydric"] for mu in map_units)

    return {
        "source":         "NRCS Web Soil Survey SSURGO",
        "map_unit_count": len(map_units),
        "hydric_present": hydric_present,
        "hydric_count":   sum(1 for mu in map_units if mu["hydric"]),
        "flag":           hydric_present,
        "map_units":      map_units,
        "summary":        _build_summary(map_units),
        "display": {
            "wms_url":       _WMS_URL,
            "wms_layer":     _WMS_LAYER,
            "opacity":       0.55,
            "overlay_color": "#16a34a",
        },
    }
