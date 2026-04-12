"""PDF report exporter using ReportLab."""

from io import BytesIO


def generate_site_report(site: dict, layers: list[dict], observations: list[dict]) -> bytes:
    """Generate a multi-page PDF site diligence report."""
    # TODO: implement full ReportLab layout with cover page, maps, tables
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, 720, f"SiteDiligence Report: {site.get('name', 'Untitled')}")
    c.setFont("Helvetica", 12)
    c.drawString(72, 690, "Full report generation not yet implemented.")
    c.save()
    return buf.getvalue()
