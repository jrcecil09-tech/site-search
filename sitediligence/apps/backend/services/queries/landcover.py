"""Land cover query — NLCD (National Land Cover Database)."""

NLCD_REST_URL = "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2021_Land_Cover_L48/wms"


async def query(ctx) -> dict:
    """Fetch NLCD land cover classification for the site bbox."""
    # TODO: query MRLC WMS/WCS, aggregate pixel counts by class
    return {
        "source": "NLCD 2021",
        "dominant_class": None,
        "class_breakdown": {},
        "note": "Not yet implemented",
    }
