"""Orchestrates parallel execution of multiple query modules for a site."""

import asyncio
from dataclasses import dataclass, field
from typing import Any

from services.queries import (
    cemeteries,
    epa,
    elevation,
    flood_zones,
    historic,
    landcover,
    parcels,
    soils,
    streams,
    utilities,
    wetlands,
    zoning,
)

QUERY_MODULES: dict[str, Any] = {
    "wetlands": wetlands,
    "flood_zones": flood_zones,
    "streams": streams,
    "elevation": elevation,
    "soils": soils,
    "zoning": zoning,
    "parcels": parcels,
    "epa": epa,
    "historic": historic,
    "cemeteries": cemeteries,
    "landcover": landcover,
    "utilities": utilities,
}


@dataclass
class QueryContext:
    site_id: str
    bbox: tuple[float, float, float, float]  # minLon, minLat, maxLon, maxLat
    buffer_meters: float = 1609.0
    query_types: list[str] = field(default_factory=list)


@dataclass
class QueryResult:
    query_type: str
    status: str  # "success" | "error" | "no_data"
    data: dict | None = None
    error: str | None = None


async def run_queries(ctx: QueryContext) -> list[QueryResult]:
    """Run requested query modules concurrently and return results."""
    tasks = []
    for qt in ctx.query_types:
        module = QUERY_MODULES.get(qt)
        if module is None:
            tasks.append(_error_result(qt, f"Unknown query type: {qt}"))
        else:
            tasks.append(_run_one(qt, module, ctx))
    return await asyncio.gather(*tasks)


async def _run_one(query_type: str, module: Any, ctx: QueryContext) -> QueryResult:
    try:
        data = await module.query(ctx)
        return QueryResult(query_type=query_type, status="success", data=data)
    except Exception as exc:
        return QueryResult(query_type=query_type, status="error", error=str(exc))


async def _error_result(query_type: str, msg: str) -> QueryResult:
    return QueryResult(query_type=query_type, status="error", error=msg)
