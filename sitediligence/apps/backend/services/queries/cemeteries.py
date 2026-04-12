"""Cemeteries query — USGS GNIS and state GIS datasets."""

GNIS_REST_URL = "https://geonames.usgs.gov/apex/f?p=138:1:0"
GNIS_QUERY_URL = "https://services.nationalmap.gov/arcgis/rest/services/TNMAccess/MapServer"


async def query(ctx) -> dict:
    """Fetch known cemeteries from USGS GNIS within search radius."""
    # TODO: query USGS GNIS feature class 'Cemetery', supplement with state data
    return {
        "source": "USGS GNIS",
        "cemeteries": [],
        "note": "Not yet implemented",
    }
