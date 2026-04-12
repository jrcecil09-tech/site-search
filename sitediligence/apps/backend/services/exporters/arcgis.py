"""ArcGIS package exporter (.mpkx / File Geodatabase via Shapefile)."""

import io
import zipfile


def export_shapefile_zip(site: dict, layers: list[dict]) -> bytes:
    """Export all vector layers as shapefiles in a zip archive."""
    # TODO: use fiona to write each layer as a shapefile into the zip
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt", f"SiteDiligence export for: {site.get('name', 'Untitled')}\n")
    return buf.getvalue()
