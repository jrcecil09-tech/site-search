"""FEMA NFHL Flood Zones query."""

FEMA_NFHL_URL = "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer"


async def query(ctx) -> dict:
    """Fetch FEMA flood zone designations for the site bbox."""
    # TODO: query FEMA NFHL REST API, return flood zone polygons + FIRM panel info
    return {"source": "FEMA NFHL", "features": [], "note": "Not yet implemented"}
