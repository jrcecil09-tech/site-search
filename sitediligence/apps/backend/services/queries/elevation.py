"""Elevation query — USGS 3DEP / National Elevation Dataset."""

USGS_ELEVATION_URL = "https://epqs.nationalmap.gov/v1/json"
TNM_ELEVATION_URL = "https://tnmaccess.nationalmap.gov/api/v1"


async def query(ctx) -> dict:
    """Fetch elevation profile and slope data for the site."""
    # TODO: query USGS 3DEP point elevation service, compute slope/aspect
    return {"source": "USGS 3DEP", "elevation_m": None, "note": "Not yet implemented"}
