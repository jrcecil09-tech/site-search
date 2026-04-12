"""Soils query — NRCS Web Soil Survey SSURGO data."""

SSURGO_REST_URL = "https://SDMDataAccess.sc.egov.usda.gov/Tabular/SDMTabularService/post.rest"
SSURGO_SPATIAL_URL = "https://sdmdataaccess.sc.egov.usda.gov/Spatial/SDMNAD83Geographic.wfs"


async def query(ctx) -> dict:
    """Fetch SSURGO soil map units and hydric soil classifications."""
    # TODO: query SSURGO spatial + tabular services, flag hydric soils
    return {"source": "NRCS SSURGO", "map_units": [], "hydric_present": None, "note": "Not yet implemented"}
