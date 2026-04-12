"""NWI Wetlands query — USFWS National Wetlands Inventory WMS."""

import httpx

NWI_WMS_URL = "https://www.fws.gov/wetlands/arcgis/services/Wetlands/MapServer/WMSServer"


async def query(ctx) -> dict:
    """Fetch NWI wetland features intersecting the site bbox."""
    # TODO: query NWI WFS/REST endpoint, clip to bbox+buffer, return GeoJSON
    return {"source": "NWI", "features": [], "note": "Not yet implemented"}
