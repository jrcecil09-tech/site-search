"""NHD Streams and water bodies query — USGS National Hydrography Dataset."""

NHD_REST_URL = "https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer"


async def query(ctx) -> dict:
    """Fetch NHD flowlines and water bodies within buffer of site."""
    # TODO: query NHD REST service, return stream centerlines + polygons
    return {"source": "NHD", "features": [], "note": "Not yet implemented"}
