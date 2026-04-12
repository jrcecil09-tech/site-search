"""QGIS project (.qgz) exporter."""

import zipfile
from io import BytesIO


def export_qgis_project(site: dict, layers: list[dict]) -> bytes:
    """Generate a QGIS project file with all layers pre-loaded."""
    # TODO: build QGS XML from layer list, package with GeoJSON data files into .qgz
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("project.qgs", _minimal_qgs_xml(site))
    return buf.getvalue()


def _minimal_qgs_xml(site: dict) -> str:
    name = site.get("name", "Untitled")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<qgis version="3.28">
  <projectlayers/>
  <properties>
    <WMSServiceTitle type="QString">{name}</WMSServiceTitle>
  </properties>
</qgis>"""
