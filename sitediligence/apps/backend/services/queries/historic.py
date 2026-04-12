"""Historic properties query — NRHP / Section 106."""

NPS_NRHP_URL = "https://npgallery.nps.gov/GetAsset"
NPS_REST_URL = "https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services"


async def query(ctx) -> dict:
    """Fetch National Register of Historic Places listings near the site."""
    # TODO: query NPS NRHP database, SHPO GIS layers
    return {
        "source": "NPS NRHP",
        "listed_properties": [],
        "eligible_properties": [],
        "note": "Not yet implemented",
    }
