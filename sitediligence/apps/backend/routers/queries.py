"""Queries router — run GIS/federal data queries for a site."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from services.queries.query_runner import QueryContext, run_queries
from services.queries import wetlands as wetlands_mod, flood_zones as flood_zones_mod

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
async def run_query(body: QueryRequest):
    invalid = [q for q in body.query_types if q not in AVAILABLE_QUERIES]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown query types: {invalid}",
        )

    if body.bbox is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="bbox is required: [minLon, minLat, maxLon, maxLat]",
        )

    ctx = QueryContext(
        site_id=body.site_id,
        bbox=body.bbox,
        buffer_meters=body.buffer_meters,
        query_types=body.query_types,
    )
    results = await run_queries(ctx)
    return {
        "site_id": body.site_id,
        "bbox": body.bbox,
        "results": [
            {
                "query_type": r.query_type,
                "status": r.status,
                "data": r.data,
                "error": r.error,
            }
            for r in results
        ],
    }


@router.get("/demo")
async def get_demo_results():
    """Pre-seeded Louisiana fixture data for demos and sandbox environments."""
    return {
        "site_id": "demo-louisiana-30-90",
        "bbox": [-90.05, 29.95, -89.95, 30.05],
        "results": [
            {
                "query_type": "wetlands",
                "status": "success",
                "data": {
                    "source": "USFWS National Wetlands Inventory",
                    "wetlands_present": True,
                    "flag": True,
                    "wetland_count": 23,
                    "total_wetland_acres": 156.4,
                    "regulated_404_acres": 142.7,
                    "wetlands": [
                        {
                            "wetland_type": "Palustrine Emergent",
                            "system": "Palustrine",
                            "attribute": "PEM1C",
                            "acres": 48.3,
                            "regulated_404": True,
                            "color": "#1a9850",
                        },
                        {
                            "wetland_type": "Palustrine Scrub-Shrub",
                            "system": "Palustrine",
                            "attribute": "PSS1C",
                            "acres": 31.2,
                            "regulated_404": True,
                            "color": "#1a9850",
                        },
                        {
                            "wetland_type": "Palustrine Forested",
                            "system": "Palustrine",
                            "attribute": "PFO1A",
                            "acres": 44.8,
                            "regulated_404": True,
                            "color": "#1a9850",
                        },
                        {
                            "wetland_type": "Estuarine Emergent",
                            "system": "Estuarine",
                            "attribute": "E2EM1P",
                            "acres": 18.4,
                            "regulated_404": True,
                            "color": "#2c7bb6",
                        },
                        {
                            "wetland_type": "Palustrine Open Water",
                            "system": "Palustrine",
                            "attribute": "POW",
                            "acres": 13.9,
                            "regulated_404": True,
                            "color": "#1a9850",
                        },
                    ],
                    "summary": {
                        "wetlands_present": True,
                        "regulated_404": True,
                        "wetland_count": 23,
                        "total_wetland_acres": 156.4,
                        "regulated_404_acres": 142.7,
                        "by_system": {"Palustrine": 19, "Estuarine": 4},
                    },
                    "display": {
                        "overlay_color": "#1a9850",
                        "opacity": 0.7,
                        "wms_url": "https://www.fws.gov/wetlandsmapservice/services/Wetlands/MapServer/WMSServer",
                        "wms_layer": "0",
                    },
                },
                "error": None,
            },
            {
                "query_type": "flood_zones",
                "status": "success",
                "data": {
                    "source": "FEMA National Flood Hazard Layer",
                    "sfha_present": True,
                    "zone_ae_present": True,
                    "flag": True,
                    "zone_count": 6,
                    "flood_zones": [
                        {
                            "fld_zone": "AE",
                            "zone_subtype": None,
                            "static_bfe": 4.5,
                            "sfha": True,
                            "bfe_zone": True,
                            "is_floodway": False,
                            "firm_panel": "22071C0245G",
                            "area_sqm": 412000.0,
                            "color": "#f97316",
                        },
                        {
                            "fld_zone": "AE",
                            "zone_subtype": "FLOODWAY",
                            "static_bfe": 4.5,
                            "sfha": True,
                            "bfe_zone": True,
                            "is_floodway": True,
                            "firm_panel": "22071C0245G",
                            "area_sqm": 89000.0,
                            "color": "#dc2626",
                        },
                        {
                            "fld_zone": "X",
                            "zone_subtype": "0.2 PCT ANNUAL CHANCE FLOOD HAZARD",
                            "static_bfe": None,
                            "sfha": False,
                            "bfe_zone": False,
                            "is_floodway": False,
                            "firm_panel": "22071C0250G",
                            "area_sqm": 156000.0,
                            "color": "#e5e7eb",
                        },
                    ],
                    "summary": {
                        "zones_found": ["AE", "X"],
                        "sfha_present": True,
                        "zone_ae_present": True,
                        "firm_panels": ["22071C0245G", "22071C0250G"],
                        "bfe_range_ft": {"min": 4.5, "max": 4.5},
                    },
                    "display": {
                        "overlay_color": "#f97316",
                        "opacity": 0.5,
                        "wms_url": "https://hazards.fema.gov/arcgis/services/public/NFHL/MapServer/WMSServer",
                        "wms_layer": "28",
                    },
                },
                "error": None,
            },
        ],
    }


@router.get("/results/{job_id}")
async def get_query_results(job_id: str):
    # TODO: fetch Celery task result
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
