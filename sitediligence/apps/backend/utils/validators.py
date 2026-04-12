"""Input validation helpers."""

from __future__ import annotations

import re


def is_valid_bbox(bbox: tuple[float, float, float, float]) -> bool:
    minlon, minlat, maxlon, maxlat = bbox
    return (
        -180 <= minlon <= 180
        and -90 <= minlat <= 90
        and -180 <= maxlon <= 180
        and -90 <= maxlat <= 90
        and minlon < maxlon
        and minlat < maxlat
    )


def is_valid_coordinate(lon: float, lat: float) -> bool:
    return -180 <= lon <= 180 and -90 <= lat <= 90


def sanitize_filename(name: str) -> str:
    """Strip path separators and dangerous characters from a filename."""
    name = re.sub(r"[^\w\s\-.]", "_", name)
    # Strip leading dots AND leading underscores that came from path separators
    return name.strip().lstrip("._")[:255]


def validate_export_format(fmt: str) -> bool:
    allowed = {"pdf", "docx", "xlsx", "geojson", "kml", "shapefile", "dxf", "qgis", "arcgis"}
    return fmt in allowed
