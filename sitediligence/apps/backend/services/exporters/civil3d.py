"""Civil 3D compatible DXF export with survey point formatting."""

import ezdxf


def export_civil3d_dxf(site: dict, layers: list[dict]) -> bytes:
    """Export site data in Civil 3D-compatible DXF with COGO points and breaklines."""
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()

    # TODO: add Civil 3D-specific entities (AECC_COGO_POINT, surface breaklines)
    msp.add_text(
        f"Civil 3D Export: {site.get('name', 'Untitled')}",
        dxfattribs={"height": 1},
    )

    from io import BytesIO
    buf = BytesIO()
    doc.write(buf)
    return buf.getvalue()
