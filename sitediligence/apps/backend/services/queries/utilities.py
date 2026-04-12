"""Utilities query — transmission lines, pipelines, substations."""

EIA_REST_URL = "https://services3.arcgis.com/bWPjFyq029ChCGur/arcgis/rest/services"
HIFLD_URL = "https://services1.arcgis.com/Hp6G80Pky0om7QvQ/arcgis/rest/services"


async def query(ctx) -> dict:
    """Fetch electric transmission lines and pipelines near the site."""
    # TODO: query HIFLD (Homeland Infrastructure Foundation-Level Data) services
    return {
        "source": "HIFLD / EIA",
        "transmission_lines": [],
        "pipelines": [],
        "substations": [],
        "note": "Not yet implemented",
    }
