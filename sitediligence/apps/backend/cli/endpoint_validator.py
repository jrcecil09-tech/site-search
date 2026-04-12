"""CLI: validate that all federal data API endpoints are reachable."""

import asyncio

import httpx
import typer

app = typer.Typer(help="Validate federal data API endpoint availability.")

ENDPOINTS = {
    "NWI Wetlands WMS": "https://www.fws.gov/wetlands/arcgis/services/Wetlands/MapServer/WMSServer?service=WMS&request=GetCapabilities",
    "FEMA NFHL WMS": "https://hazards.fema.gov/gis/nfhl/services/public/NFHLWMS/MapServer/WmsServer?service=WMS&request=GetCapabilities",
    "USGS 3DEP Elevation": "https://epqs.nationalmap.gov/v1/json?x=-77&y=38&units=Meters&output=json",
    "SSURGO Web Soil Survey": "https://sdmdataaccess.sc.egov.usda.gov/",
    "NHD Hydro": "https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer?f=json",
}


@app.command()
def validate(
    timeout: float = typer.Option(10.0, help="Request timeout in seconds"),
    verbose: bool = typer.Option(False, "-v", help="Show response details"),
):
    """Check all federal API endpoints and report status."""
    asyncio.run(_run(timeout, verbose))


async def _run(timeout: float, verbose: bool):
    results = []
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        tasks = [_check(client, name, url) for name, url in ENDPOINTS.items()]
        results = await asyncio.gather(*tasks)
    ok = sum(1 for _, status, _ in results if status < 400)
    for name, status, detail in results:
        icon = "✓" if status < 400 else "✗"
        line = f"  {icon} [{status}] {name}"
        if verbose:
            line += f" — {detail}"
        typer.echo(line)
    typer.echo(f"\n{ok}/{len(results)} endpoints reachable.")


async def _check(client: httpx.AsyncClient, name: str, url: str):
    try:
        resp = await client.get(url)
        return name, resp.status_code, url
    except Exception as exc:
        return name, 0, str(exc)


if __name__ == "__main__":
    app()
