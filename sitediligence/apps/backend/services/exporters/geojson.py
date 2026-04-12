"""GeoJSON / KML exporter."""

import json
from typing import Any


def export_geojson(layers: list[dict]) -> str:
    """Merge all layer FeatureCollections into a single GeoJSON file."""
    all_features: list[dict] = []
    for layer in layers:
        data = layer.get("data", {})
        all_features.extend(data.get("features", []))
    return json.dumps({"type": "FeatureCollection", "features": all_features}, indent=2)


def export_kml(layers: list[dict], name: str = "SiteDiligence Export") -> str:
    """Convert GeoJSON layers to a basic KML document."""
    placemarks = []
    for layer in layers:
        data = layer.get("data", {})
        for feat in data.get("features", []):
            geom = feat.get("geometry", {})
            props = feat.get("properties") or {}
            if geom.get("type") == "Point":
                lon, lat = geom["coordinates"][:2]
                label = props.get("name", "")
                placemarks.append(
                    f"  <Placemark><name>{label}</name>"
                    f"<Point><coordinates>{lon},{lat},0</coordinates></Point></Placemark>"
                )

    placemarks_str = "\n".join(placemarks)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
        f"<Document><name>{name}</name>\n{placemarks_str}\n</Document>\n</kml>"
    )
