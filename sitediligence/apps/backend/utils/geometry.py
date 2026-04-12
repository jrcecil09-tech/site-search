"""GeoJSON and shapely geometry helpers."""

from __future__ import annotations

from shapely.geometry import box, mapping, shape
from shapely.geometry.base import BaseGeometry


def bbox_to_polygon(bbox: tuple[float, float, float, float]) -> dict:
    """Convert [minLon, minLat, maxLon, maxLat] to a GeoJSON Polygon."""
    minlon, minlat, maxlon, maxlat = bbox
    return mapping(box(minlon, minlat, maxlon, maxlat))


def buffer_point(lon: float, lat: float, meters: float) -> dict:
    """Buffer a WGS84 point by the given distance in meters, return GeoJSON polygon."""
    from pyproj import Transformer

    # Project to Web Mercator for metric buffering
    to_merc = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    to_wgs = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

    x, y = to_merc.transform(lon, lat)
    from shapely.geometry import Point
    buffered = Point(x, y).buffer(meters)

    # Reproject back to WGS84
    coords = [to_wgs.transform(px, py) for px, py in buffered.exterior.coords]
    return {"type": "Polygon", "coordinates": [coords]}


def geojson_to_shapely(geojson: dict) -> BaseGeometry:
    return shape(geojson)


def shapely_to_geojson(geom: BaseGeometry) -> dict:
    return mapping(geom)


def compute_area_m2(geojson_polygon: dict) -> float:
    """Compute area in square meters using an equal-area projection."""
    from pyproj import Transformer
    from shapely.ops import transform as shp_transform

    geom = shape(geojson_polygon)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)
    projected = shp_transform(transformer.transform, geom)
    return projected.area
