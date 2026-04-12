"""Coordinate reference system detection and conversion utilities."""

from __future__ import annotations

from pyproj import CRS, Transformer


def reproject_geojson(
    geojson: dict,
    from_epsg: int,
    to_epsg: int,
) -> dict:
    """Reproject a GeoJSON geometry between EPSG codes."""
    import json
    from shapely.geometry import shape, mapping
    from shapely.ops import transform as shp_transform

    transformer = Transformer.from_crs(
        CRS.from_epsg(from_epsg), CRS.from_epsg(to_epsg), always_xy=True
    )
    geom = shape(geojson)
    reprojected = shp_transform(transformer.transform, geom)
    return mapping(reprojected)


def detect_crs_from_prj(prj_content: str) -> int | None:
    """Parse a .prj file string and return the EPSG code, or None if unknown."""
    try:
        crs = CRS.from_wkt(prj_content)
        auth = crs.to_authority()
        if auth and auth[0] == "EPSG":
            return int(auth[1])
    except Exception:
        pass
    return None


def epsg_to_wkt(epsg: int) -> str:
    return CRS.from_epsg(epsg).to_wkt()


COMMON_CRS = {
    4326: "WGS 84 (lat/lon)",
    3857: "Web Mercator",
    26910: "UTM Zone 10N",
    26911: "UTM Zone 11N",
    26912: "UTM Zone 12N",
    26913: "UTM Zone 13N",
    6933: "EASE-Grid 2.0 (equal-area)",
    2163: "US National Atlas Equal Area",
}
