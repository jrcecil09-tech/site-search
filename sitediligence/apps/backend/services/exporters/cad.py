"""DXF/CAD exporter using ezdxf."""

from __future__ import annotations

import logging
from io import StringIO
from typing import Any

import ezdxf
from ezdxf.document import Drawing

log = logging.getLogger(__name__)

# DXF layer colors (ACI palette indices)
_COLOR_BOUNDARY = 3    # green
_COLOR_LABELS   = 7    # white/black
_COLOR_FLAGS    = 1    # red


def export_site_to_dxf(site: dict, layers: list[dict]) -> bytes:
    """Export site GIS layers to a DXF file compatible with AutoCAD/BricsCAD."""
    doc: Drawing = ezdxf.new("R2010")
    msp = doc.modelspace()

    # TODO: iterate GeoJSON features, project to site CRS, add entities
    msp.add_text(
        f"SiteDiligence Export: {site.get('name', 'Untitled')}",
        dxfattribs={"height": 10},
    )

    buf = StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")


def export_soils_to_dxf(
    polygons_fc: dict[str, Any],
    summary_rows: list[dict[str, Any]],
) -> bytes:
    """Export soil map units to a DXF file.

    Creates four layer categories:
      SOILS-BOUNDARY      — outer polygon rings for all map units
      SOILS-{MUSYM}       — per-map-unit polygon fill layer (one layer per musym)
      SOILS-LABELS        — MUSYM text annotations at polygon centroids
      SOILS-FLAGS         — flag annotation text (one item per red/yellow flag)

    Parameters
    ----------
    polygons_fc:
        GeoJSON FeatureCollection of soil polygons (with ``mukey`` / ``musym``
        in each feature's properties).
    summary_rows:
        Processed summary rows from ``utils.soils_parser.process_all``; used
        for musym, muname, flag_level, and flags list.

    Returns
    -------
    bytes
        Raw DXF file bytes, ready to write to disk or return as an HTTP response.
    """
    doc: Drawing = ezdxf.new("R2010")
    msp = doc.modelspace()

    # ── Index summary rows by mukey ──────────────────────────────────────────
    summary_by_mukey: dict[str, dict[str, Any]] = {
        str(r.get("mukey", "")): r
        for r in summary_rows
        if r.get("mukey")
    }

    # ── Create fixed layers ───────────────────────────────────────────────────
    doc.layers.new("SOILS-BOUNDARY", dxfattribs={"color": _COLOR_BOUNDARY})
    doc.layers.new("SOILS-LABELS",   dxfattribs={"color": _COLOR_LABELS})
    doc.layers.new("SOILS-FLAGS",    dxfattribs={"color": _COLOR_FLAGS})

    created_layers: set[str] = {"SOILS-BOUNDARY", "SOILS-LABELS", "SOILS-FLAGS"}

    # ── Iterate features ──────────────────────────────────────────────────────
    for feat in polygons_fc.get("features") or []:
        props   = feat.get("properties") or {}
        geom    = feat.get("geometry")   or {}
        mukey   = str(props.get("mukey") or "").strip()
        musym   = str(props.get("musym") or summary_by_mukey.get(mukey, {}).get("musym") or mukey).strip()
        muname  = summary_by_mukey.get(mukey, {}).get("muname") or musym

        # ── Ensure per-musym layer ─────────────────────────────────────────
        musym_layer = f"SOILS-{musym}" if musym else "SOILS-UNKNOWN"
        if musym_layer not in created_layers:
            doc.layers.new(musym_layer, dxfattribs={"color": 5})  # blue
            created_layers.add(musym_layer)

        geom_type = geom.get("type", "")
        coords_sets: list[list[list[float]]] = []

        if geom_type == "Polygon":
            coords_sets = geom.get("coordinates") or []
        elif geom_type == "MultiPolygon":
            for poly in geom.get("coordinates") or []:
                coords_sets.extend(poly)

        # ── Draw each ring ─────────────────────────────────────────────────
        centroid_x: list[float] = []
        centroid_y: list[float] = []

        for ring in coords_sets:
            if len(ring) < 2:
                continue
            pts_2d = [(c[0], c[1]) for c in ring if len(c) >= 2]
            if not pts_2d:
                continue

            # Accumulate centroid estimate from exterior ring (first ring only)
            if not centroid_x:
                xs = [p[0] for p in pts_2d]
                ys = [p[1] for p in pts_2d]
                centroid_x.append(sum(xs) / len(xs))
                centroid_y.append(sum(ys) / len(ys))

            msp.add_lwpolyline(
                pts_2d,
                close=True,
                dxfattribs={"layer": "SOILS-BOUNDARY"},
            )
            msp.add_lwpolyline(
                pts_2d,
                close=True,
                dxfattribs={"layer": musym_layer},
            )

        # ── Label at centroid ──────────────────────────────────────────────
        if centroid_x:
            cx, cy = centroid_x[0], centroid_y[0]
            msp.add_text(
                musym,
                dxfattribs={
                    "layer":  "SOILS-LABELS",
                    "height": 0.0005,  # ~0.0005 decimal degrees ≈ readable at map scale
                    "insert": (cx, cy),
                },
            )

            # Add muname as secondary label slightly offset
            if muname and muname != musym:
                msp.add_text(
                    muname,
                    dxfattribs={
                        "layer":  "SOILS-LABELS",
                        "height": 0.0003,
                        "insert": (cx, cy - 0.001),
                    },
                )

        # ── Flag annotations ───────────────────────────────────────────────
        sr = summary_by_mukey.get(mukey, {})
        for flag in sr.get("flags") or []:
            if flag.get("level") in ("flag", "review") and centroid_x:
                cx, cy = centroid_x[0], centroid_y[0]
                flag_text = f"[{flag['code'].upper()}] {flag.get('message', '')[:60]}"
                msp.add_text(
                    flag_text,
                    dxfattribs={
                        "layer":  "SOILS-FLAGS",
                        "height": 0.0003,
                        "insert": (cx, cy - 0.002),
                    },
                )

    buf = StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")
