"""Parcels query — county assessor / FGDC parcel data."""

REGRID_API_URL = "https://app.regrid.com/api/v1"


async def query(ctx) -> dict:
    """Fetch parcel boundaries, APN, owner, and assessment data."""
    # TODO: query Regrid or county open data for parcel geometry + attributes
    return {
        "source": "county_assessor",
        "parcels": [],
        "note": "Not yet implemented — requires Regrid API key or county data source",
    }
