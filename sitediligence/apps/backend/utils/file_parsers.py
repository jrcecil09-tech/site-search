"""File format parsers — DXF, Shapefile, KML, GeoJSON ingestion."""

from __future__ import annotations

import json
from pathlib import Path


def parse_geojson(content: str | bytes) -> dict:
    """Parse and validate a GeoJSON string or bytes."""
    if isinstance(content, bytes):
        content = content.decode("utf-8")
    data = json.loads(content)
    if data.get("type") not in ("FeatureCollection", "Feature", "GeometryCollection"):
        raise ValueError(f"Invalid GeoJSON type: {data.get('type')}")
    return data


def parse_dxf(path: str | Path) -> list[dict]:
    """Read a DXF file and extract geometry as GeoJSON-style feature list."""
    import ezdxf

    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    features = []
    for entity in msp:
        try:
            if entity.dxftype() == "LWPOLYLINE":
                coords = [(p[0], p[1]) for p in entity.get_points()]
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coords},
                    "properties": {"layer": entity.dxf.layer},
                })
            elif entity.dxftype() == "POINT":
                pt = entity.dxf.location
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [pt.x, pt.y]},
                    "properties": {"layer": entity.dxf.layer},
                })
        except Exception:
            continue
    return features


def parse_shapefile(path: str | Path) -> dict:
    """Read a Shapefile and return a GeoJSON FeatureCollection."""
    import fiona
    from shapely.geometry import mapping, shape

    features = []
    with fiona.open(str(path)) as src:
        for record in src:
            features.append({
                "type": "Feature",
                "geometry": mapping(shape(record["geometry"])),
                "properties": dict(record["properties"]),
            })
    return {"type": "FeatureCollection", "features": features}
