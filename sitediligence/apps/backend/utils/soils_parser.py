"""Soil data processing — flag rules, summary tables, and site-level analysis.

All functions are pure Python with no external I/O.  They take the raw rows
returned by soils_tabular and soils_spatial and produce structured results
suitable for API responses, exports, and the PDF report.
"""

from __future__ import annotations

import logging
import re
from typing import Any

log = logging.getLogger(__name__)

FLAG_FLAG   = "flag"    # red — immediate attention
FLAG_REVIEW = "review"  # yellow — engineering review recommended
FLAG_INFO   = "info"    # blue — informational note
FLAG_PASS   = "pass"    # green — no issues


# ── Small helpers ──────────────────────────────────────────────────────────────

def _f(v: Any) -> float | None:
    """Safe cast to float; None on failure/None/empty."""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _s(v: Any) -> str | None:
    """Strip whitespace; None if falsy."""
    return str(v).strip() or None if v else None


# ── Bearing capacity classifier ───────────────────────────────────────────────

def _classify_bearing(label: str | None) -> str | None:
    """Map a bearing_capacity chiavalue string to a short category."""
    if not label:
        return None
    lower = label.lower()
    if "very low" in lower:
        return "Very low"
    if "very high" in lower or "high (>8000" in lower:
        return "Very high"
    if "low" in lower:
        return "Low"
    if "moderately high" in lower:
        return "Moderately high"
    if "moderate" in lower:
        return "Moderate"
    if "high" in lower:
        return "High"
    return None


# ── Flag rule engine ──────────────────────────────────────────────────────────

def apply_flags(row: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    """Apply all flag rules to a summary row dict.

    Returns (overall_flag_level, [flag_dict, ...]).
    Each flag dict: {"level": str, "code": str, "message": str}
    """
    flags: list[dict[str, Any]] = []

    def _add(level: str, code: str, msg: str) -> None:
        flags.append({"level": level, "code": code, "message": msg})

    hydric          = row.get("hydric", False)
    flood_freq      = _s(row.get("flood_freq"))
    depth_restrict  = _f(row.get("depth_to_restrict"))
    restrict_type   = _s(row.get("restrict_type")) or "unknown type"
    bearing_label   = _s(row.get("bearing_capacity_label"))
    corr_steel      = _s(row.get("corr_steel"))
    corr_concrete   = _s(row.get("corr_concrete"))
    lep_r           = _f(row.get("lep_r"))
    unified         = _s(row.get("unified_class")) or ""
    slope_r         = _f(row.get("slope_r"))
    farmland        = _s(row.get("farmland_class")) or ""
    ksat_r          = _f(row.get("ksat_r"))
    tax_order       = _s(row.get("tax_order")) or ""
    survey_old      = bool(row.get("survey_old"))

    # ── RED FLAGS ──────────────────────────────────────────────────────────────
    if hydric:
        _add(FLAG_FLAG, "hydric",
             "Hydric soils present — wetland indicator, CWA §404 review required")

    if flood_freq and flood_freq.lower() in ("frequent", "occasional"):
        _add(FLAG_FLAG, "flood_risk",
             f"Flooding risk ({flood_freq}) — confirm with FEMA flood data")

    if depth_restrict is not None and depth_restrict < 24:
        _add(FLAG_FLAG, "shallow_restrict",
             f"Shallow restrictive layer ({restrict_type}) at {depth_restrict:.0f} in "
             "— impacts foundations, utilities, and grading")

    if bearing_label == "Very low":
        _add(FLAG_FLAG, "bearing_low",
             "Very low bearing capacity (<1000 psf) — geotechnical investigation required")

    if corr_steel == "High":
        _add(FLAG_FLAG, "corr_steel",
             "High steel corrosion risk — underground utilities at risk")

    if lep_r is not None and lep_r > 6:
        _add(FLAG_FLAG, "shrink_swell",
             f"High shrink-swell potential (LEP={lep_r:.1f}%) — expansive soils present")

    if unified.upper() in ("PT", "OH", "OL"):
        _add(FLAG_FLAG, "organic_soils",
             f"Organic soils ({unified}) present — unsuitable for construction without "
             "soil improvement")

    # ── YELLOW FLAGS ──────────────────────────────────────────────────────────
    if depth_restrict is not None and 24 <= depth_restrict <= 60:
        _add(FLAG_REVIEW, "restrict_moderate",
             f"Restrictive layer ({restrict_type}) at {depth_restrict:.0f} in "
             "— review foundation and utility trench depths")

    if bearing_label == "Low":
        _add(FLAG_REVIEW, "bearing_moderate",
             "Low bearing capacity (1000–2000 psf) — structural foundation review recommended")

    if corr_concrete == "High":
        _add(FLAG_REVIEW, "corr_concrete",
             "High concrete corrosion risk — specify sulfate-resistant cement for foundations")

    if flood_freq and flood_freq.lower() == "rare":
        _add(FLAG_REVIEW, "flood_rare",
             "Rare flooding documented — site-specific floodplain evaluation recommended")

    if slope_r is not None and slope_r > 15:
        _add(FLAG_REVIEW, "steep_slope",
             f"Steep slopes ({slope_r:.0f}%) — grading permit likely required")

    if "prime" in farmland.lower():
        _add(FLAG_REVIEW, "prime_farmland",
             "Prime farmland present — check local agricultural preservation policies")

    if ksat_r is not None and ksat_r < 0.1:
        _add(FLAG_REVIEW, "low_perm",
             f"Very slow permeability ({ksat_r:.3f} μm/s) — stormwater infiltration "
             "likely not feasible")

    # ── INFO ──────────────────────────────────────────────────────────────────
    if tax_order.lower() == "vertisols":
        _add(FLAG_INFO, "vertisols",
             "Vertisols present — potential heaving from seasonal shrink-swell activity")

    if survey_old:
        _add(FLAG_INFO, "old_survey",
             "Soil survey older than 20 years — data reliability may be reduced; "
             "field verification recommended")

    # Determine overall level
    levels = {f["level"] for f in flags}
    if FLAG_FLAG   in levels: overall = FLAG_FLAG
    elif FLAG_REVIEW in levels: overall = FLAG_REVIEW
    elif FLAG_INFO  in levels: overall = FLAG_INFO
    else:                       overall = FLAG_PASS

    return overall, flags


# ── Summary row builder ───────────────────────────────────────────────────────

def build_summary_row(
    mukey: str,
    group_a: dict[str, Any] | None,
    dominant_comp: dict[str, Any] | None,
    engineering_rows: list[dict[str, Any]],
    restriction_rows: list[dict[str, Any]],
    flooding_rows: list[dict[str, Any]],
    hydric_row: dict[str, Any] | None,
    bearing_rows: list[dict[str, Any]],
    corr_rows: list[dict[str, Any]],
    survey_old: bool,
) -> dict[str, Any]:
    """Build a per-map-unit summary row from all tabular groups."""
    ga = group_a or {}
    dc = dominant_comp or {}

    # ── Slope range ──────────────────────────────────────────────────────────
    sl = _f(dc.get("slope_l"))
    sh = _f(dc.get("slope_h"))
    sr = _f(dc.get("slope_r"))
    if sl is not None and sh is not None:
        slope_range = f"{sl:.0f}–{sh:.0f}%"
    elif sr is not None:
        slope_range = f"{sr:.0f}%"
    else:
        slope_range = None

    # ── Engineering properties from horizon rows ──────────────────────────────
    def _first_valid(rows: list[dict], key: str) -> Any:
        for r in rows:
            v = r.get(key)
            if v is not None and v != "":
                return v
        return None

    unified  = _s(_first_valid(engineering_rows, "unified_class"))
    aashto   = _s(_first_valid(engineering_rows, "aashto_class"))
    ksat_r   = _f(_first_valid(engineering_rows, "ksat_r"))
    lep_r    = _f(_first_valid(engineering_rows, "lep_r"))
    ll_r     = _f(_first_valid(engineering_rows, "ll_r"))
    pi_r     = _f(_first_valid(engineering_rows, "pi_r"))
    om_r     = _f(_first_valid(engineering_rows, "om_r"))
    kwfact   = _s(_first_valid(engineering_rows, "kwfact"))

    # ── Bearing capacity ──────────────────────────────────────────────────────
    bc_raw   = _s(_first_valid(bearing_rows, "bearing_capacity"))
    bc_label = _classify_bearing(bc_raw)

    # ── Corrosivity from first horizon with values ────────────────────────────
    corr_steel    = _s(_first_valid(corr_rows, "corr_steel"))
    corr_concrete = _s(_first_valid(corr_rows, "corr_concrete"))

    # ── Shallowest restriction ────────────────────────────────────────────────
    sorted_restr = sorted(
        [r for r in restriction_rows if _f(r.get("resdept_r")) is not None],
        key=lambda r: _f(r["resdept_r"]) or 9999,
    )
    top_restr       = sorted_restr[0] if sorted_restr else None
    depth_to_restr  = _f(top_restr.get("resdept_r")) if top_restr else None
    restrict_type   = _s(top_restr.get("reskind"))   if top_restr else None
    restrict_hard   = _s(top_restr.get("reshard"))   if top_restr else None

    # ── Flooding ─────────────────────────────────────────────────────────────
    flood_row  = flooding_rows[0] if flooding_rows else {}
    flood_freq = _s(flood_row.get("flodfreqcl"))
    flood_dur  = _s(flood_row.get("floddurcl"))
    pond_freq  = _s(flood_row.get("pondfreqcl"))

    # ── Hydric ───────────────────────────────────────────────────────────────
    hr = hydric_row or {}
    hydric_rating   = _s(hr.get("hydricrating"))
    hydric          = bool(hydric_rating and hydric_rating.lower() in ("yes", "all"))
    hydric_criterion = _s(hr.get("hydric_criterion"))

    row: dict[str, Any] = {
        "mukey":              mukey,
        "musym":              _s(ga.get("musym")),
        "muname":             _s(ga.get("muname")),
        "mukind":             _s(ga.get("mukind")),
        "area_acres":         _f(ga.get("muacres")),
        "niccdcd":            _s(ga.get("niccdcd")),
        "farmland_class":     _s(ga.get("farmlndcl")),
        "dominant_series":    _s(dc.get("compname")),
        "dominant_pct":       _f(dc.get("comppct_r")),
        "hydrologic_group":   _s(dc.get("hydrgrp")) or _s(dc.get("hydgrp")),
        "drainage_class":     _s(dc.get("drainagecl")),
        "slope_range":        slope_range,
        "slope_r":            sr,
        "tax_order":          _s(dc.get("taxorder")),
        "tax_subgrp":         _s(dc.get("taxsubgrp")),
        "erocl":              _s(dc.get("erocl")),
        "tfact":              _f(dc.get("tfact")),
        # Engineering
        "unified_class":      unified,
        "aashto_class":       aashto,
        "ksat_r":             ksat_r,
        "lep_r":              lep_r,
        "liquid_limit":       ll_r,
        "plasticity_index":   pi_r,
        "om_r":               om_r,
        "kwfact":             kwfact,
        # Bearing
        "bearing_capacity_raw":   bc_raw,
        "bearing_capacity_label": bc_label,
        # Corrosivity
        "corr_steel":         corr_steel,
        "corr_concrete":      corr_concrete,
        # Restrictions
        "depth_to_restrict":  depth_to_restr,
        "restrict_type":      restrict_type,
        "restrict_hardness":  restrict_hard,
        # Flooding
        "flood_freq":         flood_freq,
        "flood_dur":          flood_dur,
        "pond_freq":          pond_freq,
        # Hydric
        "hydric":             hydric,
        "hydric_rating":      hydric_rating,
        "hydric_criterion":   hydric_criterion,
        # Survey age
        "survey_old":         survey_old,
        # Flags (populated below)
        "flag_level":         FLAG_PASS,
        "flags":              [],
    }

    flag_level, flags = apply_flags(row)
    row["flag_level"] = flag_level
    row["flags"]      = flags
    return row


# ── Infiltration / stormwater assessment ──────────────────────────────────────

def assess_infiltration(
    hydrologic_group: str | None,
    ksat_r: float | None,
) -> dict[str, Any]:
    """Estimate infiltration BMP feasibility from HSG and ksat."""
    hsg = (hydrologic_group or "").upper().strip().rstrip("/D")  # "B/D" → "B"

    _RATES = {
        "A": ("Fast (>20 μm/s)",         "High",     True),
        "B": ("Moderate (0.5–20 μm/s)", "Moderate", True),
        "C": ("Slow (0.1–0.5 μm/s)",    "Low",      False),
        "D": ("Very slow (<0.1 μm/s)",  "Low",      False),
    }
    if hsg and hsg[0] in _RATES:
        rate, recharge, feasible = _RATES[hsg[0]]
        note = (
            f"Hydrologic Group {hsg}: {rate} — "
            + ("infiltration BMPs (rain gardens, bioretention) are likely feasible."
               if feasible else
               "stormwater infiltration BMPs may not be feasible; routing/detention "
               "alternatives recommended.")
        )
    elif ksat_r is not None:
        if ksat_r > 20:
            rate, recharge, feasible = "Fast (>20 μm/s)", "High", True
        elif ksat_r >= 0.5:
            rate, recharge, feasible = "Moderate (0.5–20 μm/s)", "Moderate", True
        elif ksat_r >= 0.1:
            rate, recharge, feasible = "Slow (0.1–0.5 μm/s)", "Low", False
        else:
            rate, recharge, feasible = "Very slow (<0.1 μm/s)", "Low", False
        note = f"Ksat={ksat_r:.3f} μm/s: {rate}"
    else:
        rate, recharge, feasible = "Unknown", "Unknown", False
        note = "Insufficient data to assess infiltration feasibility"

    return {
        "bmp_feasible":        feasible,
        "percolation_rate":    rate,
        "groundwater_recharge": recharge,
        "note":                note,
    }


# ── Shrink-swell assessment ───────────────────────────────────────────────────

def assess_shrink_swell(lep_r: float | None) -> dict[str, Any]:
    """Classify LEP and provide engineering recommendation."""
    _RECS = {
        "Low":       "No special construction measures required for shrink-swell.",
        "Moderate":  "Monitor pavement and foundation performance; consider geotextile "
                     "stabilization beneath paved surfaces.",
        "High":      "Geotechnical investigation required; expansive soil mitigation "
                     "design needed for pavements and foundations.",
        "Very high": "Significant differential settlement and foundation damage risk; "
                     "special foundation design (piers, grade beams) required.",
    }
    if lep_r is None:
        cls = "Unknown"
        rec = "LEP data unavailable — field investigation recommended."
    elif lep_r < 3:
        cls = "Low"
    elif lep_r < 6:
        cls = "Moderate"
    elif lep_r < 9:
        cls = "High"
    else:
        cls = "Very high"

    return {
        "lep_r":          lep_r,
        "classification": cls,
        "recommendation": _RECS.get(cls, rec if lep_r is None else ""),
    }


# ── Land capability class ─────────────────────────────────────────────────────

_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8}


def _extract_class_num(niccdcd: str | None) -> int | None:
    """Extract the Roman numeral capability class number from niccdcd string."""
    if not niccdcd:
        return None
    m = re.match(r"^(VIII|VII|VI|IV|V|III|II|I)", niccdcd.strip().upper())
    return _ROMAN[m.group(1)] if m else None


def compute_capability_class(map_units: list[dict[str, Any]]) -> dict[str, Any]:
    """Area-weighted land capability class for all map units on site."""
    class_acres: dict[str, float] = {}
    total_acres = 0.0
    weighted_sum = 0.0

    for mu in map_units:
        acres    = _f(mu.get("area_acres")) or 0.0
        niccdcd  = _s(mu.get("niccdcd"))
        cls_num  = _extract_class_num(niccdcd)
        # Roman numeral prefix for display
        cls_label = re.match(r"^(VIII|VII|VI|IV|V|III|II|I)", (niccdcd or "").upper())
        cls_key   = cls_label.group(1) if cls_label else "Unknown"

        class_acres[cls_key] = class_acres.get(cls_key, 0.0) + acres
        total_acres += acres
        if cls_num:
            weighted_sum += cls_num * acres

    aw_class = round(weighted_sum / total_acres, 1) if total_acres > 0 else None
    dominant = max(class_acres, key=lambda k: class_acres[k]) if class_acres else None

    if aw_class is None:
        assessment = "Unknown"
    elif aw_class <= 2:
        assessment = "Minimal limitations for most land uses"
    elif aw_class <= 4:
        assessment = "Moderate limitations — some practices may be restricted"
    else:
        assessment = "Severe limitations — unsuitable for cultivation without significant improvements"

    return {
        "area_weighted_class": aw_class,
        "dominant_class":      dominant,
        "class_breakdown":     class_acres,
        "assessment":          assessment,
    }


# ── Suitability grid ──────────────────────────────────────────────────────────

def build_suitability_grid(
    interp_rows: list[dict[str, Any]],
    mukeys: list[str],
) -> dict[str, dict[str, Any]]:
    """Build {mukey: {use_short_name: {interphr, interphrc}}} grid."""
    grid: dict[str, dict[str, Any]] = {mk: {} for mk in mukeys}

    for row in interp_rows:
        mk       = _s(row.get("mukey"))
        rulename = _s(row.get("mrulename")) or ""
        # Strip the code prefix: "ENG - Dwellings Without Basements" → "Dwellings Without Basements"
        short    = re.sub(r"^[A-Z]{2,3}\s*-\s*", "", rulename).strip()
        interphr = _f(row.get("interphr"))
        interphrc = _s(row.get("interphrc"))

        if mk and mk in grid:
            grid[mk][short] = {"interphr": interphr, "interphrc": interphrc}

    return grid


# ── Top-level processor ───────────────────────────────────────────────────────

def process_all(
    mukeys: list[str],
    tabular: dict[str, list[dict[str, Any]]],
    survey_areas: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Process all tabular data into structured results.

    mukeys:       from spatial query or SDA discovery
    tabular:      dict from soils_tabular.get_all_tabular
    survey_areas: list from soils_spatial.get_survey_areas
    """
    survey_old = any(sa.get("survey_date_old") for sa in survey_areas)

    # Index rows by mukey for fast lookup
    def _by_mukey(rows: list[dict]) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for r in rows:
            mk = _s(r.get("mukey")) or ""
            out.setdefault(mk, []).append(r)
        return out

    mu_a   = {r["mukey"]: r for r in tabular.get("mapunit", []) if r.get("mukey")}
    comp_b = _by_mukey(tabular.get("components", []))
    restr  = _by_mukey(tabular.get("restrictions", []))
    eng    = _by_mukey(tabular.get("engineering", []))
    flood  = _by_mukey(tabular.get("flooding", []))
    hydric = _by_mukey(tabular.get("hydric", []))
    bearing = _by_mukey(tabular.get("bearing", []))
    corr   = _by_mukey(tabular.get("corrosivity", []))
    interp = tabular.get("interpretations", [])

    summary_rows: list[dict[str, Any]] = []
    infiltration_map: dict[str, Any] = {}
    shrink_swell_map: dict[str, Any] = {}

    for mk in mukeys:
        comp_rows  = comp_b.get(mk, [])
        dominant   = comp_rows[0] if comp_rows else None
        hydric_row = hydric.get(mk, [{}])[0] if hydric.get(mk) else None

        sr = build_summary_row(
            mukey           = mk,
            group_a         = mu_a.get(mk),
            dominant_comp   = dominant,
            engineering_rows = eng.get(mk, []),
            restriction_rows = restr.get(mk, []),
            flooding_rows   = flood.get(mk, []),
            hydric_row      = hydric_row,
            bearing_rows    = bearing.get(mk, []),
            corr_rows       = corr.get(mk, []),
            survey_old      = survey_old,
        )
        summary_rows.append(sr)

        infiltration_map[mk] = assess_infiltration(
            sr.get("hydrologic_group"), sr.get("ksat_r")
        )
        shrink_swell_map[mk] = assess_shrink_swell(sr.get("lep_r"))

    # Summary counts
    flag_counts: dict[str, int] = {FLAG_FLAG: 0, FLAG_REVIEW: 0, FLAG_INFO: 0, FLAG_PASS: 0}
    for sr in summary_rows:
        flag_counts[sr["flag_level"]] = flag_counts.get(sr["flag_level"], 0) + 1

    hydric_units  = [sr for sr in summary_rows if sr.get("hydric")]
    restrict_units = [sr for sr in summary_rows
                      if sr.get("depth_to_restrict") is not None
                      and (sr.get("depth_to_restrict") or 999) <= 60]
    flood_units   = [sr for sr in summary_rows
                     if (sr.get("flood_freq") or "").lower() in ("frequent", "occasional")]

    return {
        "map_units":           summary_rows,
        "flags_summary":       flag_counts,
        "hydric_present":      bool(hydric_units),
        "hydric_count":        len(hydric_units),
        "has_restrictions":    bool(restrict_units),
        "flood_risk_count":    len(flood_units),
        "capability_class":    compute_capability_class(summary_rows),
        "suitability_grid":    build_suitability_grid(interp, mukeys),
        "infiltration_by_mukey": infiltration_map,
        "shrink_swell_by_mukey": shrink_swell_map,
        "survey_areas":        survey_areas,
        "mukeys":              mukeys,
    }
