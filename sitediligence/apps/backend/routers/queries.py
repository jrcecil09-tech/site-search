"""Queries router — run GIS/federal data queries for a site."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()

AVAILABLE_QUERIES = [
    "wetlands",
    "flood_zones",
    "streams",
    "elevation",
    "soils",
    "zoning",
    "parcels",
    "epa",
    "historic",
    "cemeteries",
    "landcover",
    "utilities",
]


class QueryRequest(BaseModel):
    site_id: str
    query_types: list[str]
    bbox: tuple[float, float, float, float] | None = None
    buffer_meters: float = 1609.0  # 1 mile default


class QueryResult(BaseModel):
    query_type: str
    status: str
    data: dict | None = None
    error: str | None = None


@router.get("/available")
async def list_available_queries():
    return {"queries": AVAILABLE_QUERIES}


@router.post("/run")
async def run_queries(body: QueryRequest):
    invalid = [q for q in body.query_types if q not in AVAILABLE_QUERIES]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown query types: {invalid}",
        )
    # TODO: dispatch to services/queries/query_runner.py
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/results/{job_id}")
async def get_query_results(job_id: str):
    # TODO: fetch Celery task result
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
