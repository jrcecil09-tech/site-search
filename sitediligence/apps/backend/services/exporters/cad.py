"""DXF/CAD exporter using ezdxf."""

import ezdxf
from ezdxf.document import Drawing


def export_site_to_dxf(site: dict, layers: list[dict]) -> bytes:
    """Export site GIS layers to a DXF file compatible with AutoCAD/BricsCAD."""
    doc: Drawing = ezdxf.new("R2010")
    msp = doc.modelspace()

    # TODO: iterate GeoJSON features, project to site CRS, add entities
    msp.add_text(
        f"SiteDiligence Export: {site.get('name', 'Untitled')}",
        dxfattribs={"height": 10},
    )

    from io import BytesIO
    buf = BytesIO()
    doc.write(buf)
    return buf.getvalue()
