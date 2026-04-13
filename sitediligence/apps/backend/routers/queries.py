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
    """Pre-seeded Denver, CO fixture data for demos and sandbox environments."""
    return {
        "site_id": "demo-denver-39.7-104.9",
        "bbox": [-104.905, 39.695, -104.895, 39.705],
        "results": [
            {
                "query_type": "wetlands",
                "status": "success",
                "data": {
                    "source": "USFWS National Wetlands Inventory",
                    "wetlands_present": True,
                    "flag": True,
                    "wetland_count": 7,
                    "total_wetland_acres": 18.4,
                    "regulated_404_acres": 18.4,
                    "wetlands": [
                        {
                            "wetland_type": "Palustrine Emergent",
                            "system": "Palustrine",
                            "attribute": "PEM1C",
                            "acres": 11.2,
                            "regulated_404": True,
                            "color": "#1a9850",
                        },
                        {
                            "wetland_type": "Palustrine Scrub-Shrub",
                            "system": "Palustrine",
                            "attribute": "PSS1C",
                            "acres": 7.2,
                            "regulated_404": True,
                            "color": "#1a9850",
                        },
                    ],
                    "summary": {
                        "wetlands_present": True,
                        "regulated_404": True,
                        "wetland_count": 7,
                        "total_wetland_acres": 18.4,
                        "regulated_404_acres": 18.4,
                        "by_system": {"Palustrine": 7},
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
                    "zone_count": 4,
                    "flood_zones": [
                        {
                            "fld_zone": "AE",
                            "zone_subtype": None,
                            "static_bfe": 5258.0,
                            "sfha": True,
                            "bfe_zone": True,
                            "is_floodway": False,
                            "firm_panel": "08031C0207F",
                            "area_sqm": 195000.0,
                            "color": "#f97316",
                        },
                        {
                            "fld_zone": "AE",
                            "zone_subtype": "FLOODWAY",
                            "static_bfe": 5258.0,
                            "sfha": True,
                            "bfe_zone": True,
                            "is_floodway": True,
                            "firm_panel": "08031C0207F",
                            "area_sqm": 41000.0,
                            "color": "#dc2626",
                        },
                        {
                            "fld_zone": "X",
                            "zone_subtype": "0.2 PCT ANNUAL CHANCE FLOOD HAZARD",
                            "static_bfe": None,
                            "sfha": False,
                            "bfe_zone": False,
                            "is_floodway": False,
                            "firm_panel": "08031C0207F",
                            "area_sqm": 88000.0,
                            "color": "#e5e7eb",
                        },
                    ],
                    "summary": {
                        "zones_found": ["AE", "X"],
                        "sfha_present": True,
                        "zone_ae_present": True,
                        "firm_panels": ["08031C0207F"],
                        "bfe_range_ft": {"min": 5258.0, "max": 5258.0},
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
                    "flowline_count": 5,
                    "waterbody_count": 1,
                    "buffer_ft": 500,
                    "streams": [
                        {
                            "name": "South Platte River",
                            "feature_type": "Stream/River",
                            "ftype_code": 460,
                            "stream_order": 7,
                            "length_km": 3.4,
                            "kind": "flowline",
                            "color": "#1e40af",
                        },
                        {
                            "name": "Cherry Creek",
                            "feature_type": "Stream/River",
                            "ftype_code": 460,
                            "stream_order": 4,
                            "length_km": 1.8,
                            "kind": "flowline",
                            "color": "#1e40af",
                        },
                        {
                            "name": "Weir Gulch",
                            "feature_type": "Stream/River",
                            "ftype_code": 460,
                            "stream_order": 2,
                            "length_km": 0.6,
                            "kind": "flowline",
                            "color": "#1e40af",
                        },
                        {
                            "name": None,
                            "feature_type": "Stream/River",
                            "ftype_code": 460,
                            "stream_order": 1,
                            "length_km": 0.3,
                            "kind": "flowline",
                            "color": "#1e40af",
                        },
                    ],
                    "waterbodies": [
                        {
                            "name": "Sloan Lake",
                            "feature_type": "Reservoir",
                            "ftype_code": 436,
                            "area_sqkm": 0.68,
                            "kind": "waterbody",
                            "color": "#60a5fa",
                        },
                    ],
                    "summary": {
                        "flowline_count": 5,
                        "waterbody_count": 1,
                        "total_length_km": 6.1,
                        "max_stream_order": 7,
                        "stream_orders_present": [1, 2, 4, 7],
                        "named_streams": ["Cherry Creek", "South Platte River",
                                          "Weir Gulch"],
                        "named_waterbodies": ["Sloan Lake"],
                        "by_type": {"Stream/River": 4},
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
            {
                "query_type": "soils",
                "status": "success",
                "data": {
                    "source": "NRCS Web Soil Survey SSURGO",
                    "map_unit_count": 4,
                    "hydric_present": True,
                    "hydric_count": 1,
                    "flag": True,
                    "map_units": [
                        {
                            "mukey": "490709",
                            "musym": "No",
                            "muname": "Norge loam, 0 to 1 percent slopes",
                            "muacres": 48.3,
                            "hydric": False,
                            "drainage_class": "Well drained",
                            "hydric_rating": "No",
                            "farmland_class": "Prime farmland",
                            "tax_class": "Fine-silty, mixed, superactive, thermic Udic Haplustolls",
                            "dominant_component": "Norge",
                            "dominant_pct": 80,
                            "corr_steel": "Low",
                            "corr_concrete": "High",
                            "uscs_class": "CL",
                            "color": "#16a34a",
                            "components": [],
                        },
                        {
                            "mukey": "490712",
                            "musym": "Re",
                            "muname": "Reinach fine sandy loam, 0 to 1 percent slopes",
                            "muacres": 22.1,
                            "hydric": False,
                            "drainage_class": "Well drained",
                            "hydric_rating": "No",
                            "farmland_class": "Farmland of statewide importance",
                            "tax_class": "Coarse-loamy, mixed, superactive, thermic Fluventic Haplustolls",
                            "dominant_component": "Reinach",
                            "dominant_pct": 85,
                            "corr_steel": "Low",
                            "corr_concrete": "Moderate",
                            "uscs_class": "SM",
                            "color": "#16a34a",
                            "components": [],
                        },
                        {
                            "mukey": "490718",
                            "musym": "Po",
                            "muname": "Port silt loam, 0 to 1 percent slopes",
                            "muacres": 31.5,
                            "hydric": False,
                            "drainage_class": "Moderately well drained",
                            "hydric_rating": "No",
                            "farmland_class": "Prime farmland",
                            "tax_class": "Fine-silty, mixed, superactive, thermic Cumulic Haplustolls",
                            "dominant_component": "Port",
                            "dominant_pct": 90,
                            "corr_steel": "Low",
                            "corr_concrete": "High",
                            "uscs_class": "ML",
                            "color": "#86efac",
                            "components": [],
                        },
                        {
                            "mukey": "490724",
                            "musym": "Gg",
                            "muname": "Gracemont fine sandy loam, frequently flooded",
                            "muacres": 9.8,
                            "hydric": True,
                            "drainage_class": "Somewhat poorly drained",
                            "hydric_rating": "Yes",
                            "farmland_class": "Not prime farmland",
                            "tax_class": "Coarse-loamy, mixed, superactive, nonacid, thermic Oxyaquic Ustifluvents",
                            "dominant_component": "Gracemont",
                            "dominant_pct": 90,
                            "corr_steel": "High",
                            "corr_concrete": "High",
                            "uscs_class": "SM",
                            "color": "#1d4ed8",
                            "components": [],
                        },
                    ],
                    "summary": {
                        "map_unit_count": 4,
                        "hydric_unit_count": 1,
                        "hydric_present": True,
                        "drainage_classes": {
                            "Well drained": 2,
                            "Moderately well drained": 1,
                            "Somewhat poorly drained": 1,
                        },
                        "hydric_unit_names": ["Gracemont fine sandy loam, frequently flooded"],
                    },
                    "display": {
                        "wms_url": "https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms",
                        "wms_layer": "mapunitpoly",
                        "opacity": 0.55,
                        "overlay_color": "#16a34a",
                    },
                },
                "error": None,
            },
            {
                "query_type": "elevation",
                "status": "success",
                "data": {
                    "source": "USGS 3DEP (1/3 arc-second)",
                    "centroid": {"lon": -104.9, "lat": 39.7},
                    "centroid_elevation_ft": 5279.8,
                    "centroid_elevation_m": 1609.3,
                    "grid_n": 11,
                    "sample_count": 121,
                    "stats": {
                        "min_ft": 5264.2,
                        "max_ft": 5303.7,
                        "mean_ft": 5281.4,
                        "std_ft": 8.6,
                        "min_m": 1604.5,
                        "max_m": 1616.5,
                        "mean_m": 1609.8,
                        "relief_ft": 39.5,
                        "slope_min_deg": 0.1,
                        "slope_max_deg": 4.8,
                        "slope_mean_deg": 1.2,
                    },
                    "contours": [
                        {
                            "interval_ft": 1,
                            "color": "#a3c4bc",
                            "dash": "4,2",
                            "level_count": 39,
                            "features": [],
                        },
                        {
                            "interval_ft": 2,
                            "color": "#5b8db8",
                            "dash": "6,2",
                            "level_count": 20,
                            "features": [],
                        },
                        {
                            "interval_ft": 5,
                            "color": "#1e40af",
                            "dash": "solid",
                            "level_count": 8,
                            "features": [],
                        },
                    ],
                    "dem_downloads": [
                        {
                            "title": "USGS 1/3 Arc Second DEM — n40w105",
                            "download_url": "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/n40w105/USGS_13_n40w105.tif",
                            "size_mb": 151.2,
                            "pub_date": "2022-08-12",
                        },
                    ],
                    "flag": False,
                    "display": {
                        "overlay_color": "#78716c",
                        "opacity": 0.5,
                        "wms_url": "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/WMSServer",
                        "wms_layer": "3DEPElevation:Hillshade Gray",
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
