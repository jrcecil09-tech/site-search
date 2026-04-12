"""EPA environmental records query — FRS, Superfund, RCRA, ECHO."""

EPA_FRS_URL = "https://ofmpub.epa.gov/frs_public2/frs_rest_services.get_facilities"
EPA_CERCLIS_URL = "https://enviro.epa.gov/enviro/efservice"
EPA_ECHO_URL = "https://echo.epa.gov/echo-rest-services"


async def query(ctx) -> dict:
    """Fetch EPA facility records within search radius of site."""
    # TODO: query EPA FRS, CERCLIS (Superfund), RCRA, and ECHO APIs
    return {
        "source": "EPA",
        "frs_facilities": [],
        "superfund_sites": [],
        "rcra_handlers": [],
        "echo_facilities": [],
        "note": "Not yet implemented",
    }
