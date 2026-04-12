"""Zoning query — municipal/county zoning via local open data portals."""


async def query(ctx) -> dict:
    """Fetch zoning designations for the site parcel.

    Note: Zoning data is not available from a single federal source.
    This module queries state/county open data APIs where available,
    and falls back to the FGDC National Zoning Atlas when published.
    """
    # TODO: detect jurisdiction from coordinates, query appropriate open data API
    return {
        "source": "local_jurisdiction",
        "zoning_code": None,
        "zoning_description": None,
        "note": "Jurisdiction-specific — not yet implemented",
    }
