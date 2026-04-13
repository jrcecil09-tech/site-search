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
    """Pre-seeded Western NC fixture data for demos and sandbox environments."""
    return {
        "site_id": "demo-nc-35.5-82.5",
        "bbox": [-82.505, 35.495, -82.495, 35.505],
        "results": [
            {
                "query_type": "wetlands",
                "status": "success",
                "data": {
                    "source": "USFWS National Wetlands Inventory",
                    "wetlands_present": True,
                    "flag": True,
                    "wetland_count": 14,
                    "total_wetland_acres": 46.3,
                    "regulated_404_acres": 46.3,
                    "wetlands": [
                        {
                            "wetland_type": "Palustrine Forested",
                            "system": "Palustrine",
                            "attribute": "PFO1C",
                            "acres": 32.4,
                            "regulated_404": True,
                            "color": "#1a9850",
                        },
                        {
                            "wetland_type": "Palustrine Scrub-Shrub",
                            "system": "Palustrine",
                            "attribute": "PSS1C",
                            "acres": 8.7,
                            "regulated_404": True,
                            "color": "#1a9850",
                        },
                        {
                            "wetland_type": "Palustrine Emergent",
                            "system": "Palustrine",
                            "attribute": "PEM1C",
                            "acres": 5.2,
                            "regulated_404": True,
                            "color": "#1a9850",
                        },
                    ],
                    "summary": {
                        "wetlands_present": True,
                        "regulated_404": True,
                        "wetland_count": 14,
                        "total_wetland_acres": 46.3,
                        "regulated_404_acres": 46.3,
                        "by_system": {"Palustrine": 14},
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
                    "zone_count": 5,
                    "flood_zones": [
                        {
                            "fld_zone": "AE",
                            "zone_subtype": None,
                            "static_bfe": 2148.0,
                            "sfha": True,
                            "bfe_zone": True,
                            "is_floodway": False,
                            "firm_panel": "37021C0302E",
                            "area_sqm": 284000.0,
                            "color": "#f97316",
                        },
                        {
                            "fld_zone": "AE",
                            "zone_subtype": "FLOODWAY",
                            "static_bfe": 2148.0,
                            "sfha": True,
                            "bfe_zone": True,
                            "is_floodway": True,
                            "firm_panel": "37021C0302E",
                            "area_sqm": 62000.0,
                            "color": "#dc2626",
                        },
                        {
                            "fld_zone": "X",
                            "zone_subtype": "0.2 PCT ANNUAL CHANCE FLOOD HAZARD",
                            "static_bfe": None,
                            "sfha": False,
                            "bfe_zone": False,
                            "is_floodway": False,
                            "firm_panel": "37021C0302E",
                            "area_sqm": 98000.0,
                            "color": "#e5e7eb",
                        },
                    ],
                    "summary": {
                        "zones_found": ["AE", "X"],
                        "sfha_present": True,
                        "zone_ae_present": True,
                        "firm_panels": ["37021C0302E"],
                        "bfe_range_ft": {"min": 2148.0, "max": 2148.0},
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
            {
                "query_type": "streams",
                "status": "success",
                "data": {
                    "source": "USGS NHDPlus High Resolution",
                    "streams_present": True,
                    "flag": True,
                    "flowline_count": 8,
                    "waterbody_count": 1,
                    "buffer_ft": 500,
                    "streams": [
                        {
                            "name": "French Broad River",
                            "feature_type": "Stream/River",
                            "ftype_code": 460,
                            "stream_order": 7,
                            "length_km": 4.8,
                            "kind": "flowline",
                            "color": "#1e40af",
                        },
                        {
                            "name": "Swannanoa River",
                            "feature_type": "Stream/River",
                            "ftype_code": 460,
                            "stream_order": 5,
                            "length_km": 2.1,
                            "kind": "flowline",
                            "color": "#1e40af",
                        },
                        {
                            "name": "Bent Creek",
                            "feature_type": "Stream/River",
                            "ftype_code": 460,
                            "stream_order": 3,
                            "length_km": 0.8,
                            "kind": "flowline",
                            "color": "#1e40af",
                        },
                        {
                            "name": "Hominy Creek",
                            "feature_type": "Stream/River",
                            "ftype_code": 460,
                            "stream_order": 3,
                            "length_km": 0.6,
                            "kind": "flowline",
                            "color": "#1e40af",
                        },
                        {
                            "name": None,
                            "feature_type": "Stream/River",
                            "ftype_code": 460,
                            "stream_order": 2,
                            "length_km": 0.4,
                            "kind": "flowline",
                            "color": "#1e40af",
                        },
                        {
                            "name": None,
                            "feature_type": "Stream/River",
                            "ftype_code": 460,
                            "stream_order": 1,
                            "length_km": 0.2,
                            "kind": "flowline",
                            "color": "#1e40af",
                        },
                    ],
                    "waterbodies": [
                        {
                            "name": "Lake Julian",
                            "feature_type": "Reservoir",
                            "ftype_code": 436,
                            "area_sqkm": 1.21,
                            "kind": "waterbody",
                            "color": "#60a5fa",
                        },
                    ],
                    "summary": {
                        "flowline_count": 8,
                        "waterbody_count": 1,
                        "total_length_km": 8.9,
                        "max_stream_order": 7,
                        "stream_orders_present": [1, 2, 3, 5, 7],
                        "named_streams": ["Bent Creek", "French Broad River",
                                          "Hominy Creek", "Swannanoa River"],
                        "named_waterbodies": ["Lake Julian"],
                        "by_type": {"Stream/River": 6},
                        "high_order_stream": True,
                    },
                    "display": {
                        "overlay_color": "#1e40af",
                        "opacity": 0.8,
                        "wms_url": "https://hydro.nationalmap.gov/arcgis/services/NHDPlus_HR/MapServer/WMSServer",
                        "wms_layers": "2,10",
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
