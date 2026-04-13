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
            {
                "query_type": "epa",
                "status": "success",
                "data": {
                    "source": "EPA FRS / ECHO / Envirofacts",
                    "flag": True,
                    "frs_facilities": [
                        {
                            "registry_id": "110005432101",
                            "name": "Xcel Energy — Cherokee Generating Station",
                            "address": "6363 Larimer St",
                            "city": "Denver",
                            "state": "CO",
                            "lat": 39.714,
                            "lon": -104.972,
                            "programs": ["CAA", "RCRA"],
                            "category": "frs",
                            "color": "#6366f1",
                        },
                        {
                            "registry_id": "110005432102",
                            "name": "CDOT — Region 1 Headquarters",
                            "address": "2000 S Holly St",
                            "city": "Denver",
                            "state": "CO",
                            "lat": 39.691,
                            "lon": -104.889,
                            "programs": ["WATER"],
                            "category": "frs",
                            "color": "#6366f1",
                        },
                    ],
                    "echo_facilities": [
                        {
                            "registry_id": "110005432103",
                            "name": "Denver Drum & Barrel Co",
                            "lat": 39.703,
                            "lon": -104.898,
                            "compliance_status": {
                                "air": "No Violation Identified",
                                "water": "No Violation Identified",
                                "waste": "Significant Violation",
                            },
                            "total_violations": 4,
                            "formal_actions": 1,
                            "inspections": 3,
                            "has_violation": True,
                            "facility_type": "Waste Handler",
                            "category": "echo",
                            "color": "#6366f1",
                        },
                    ],
                    "superfund_sites": [
                        {
                            "site_id": "COD980717557",
                            "name": "South Platte River Industrial (Demo Site)",
                            "address": "1400 W Mississippi Ave",
                            "city": "Denver",
                            "state": "CO",
                            "status": "Active",
                            "npl_status": "Currently on the Final NPL",
                            "lat": 39.702,
                            "lon": -104.901,
                            "distance_miles": 0.17,
                            "category": "superfund",
                            "color": "#dc2626",
                        },
                    ],
                    "rcra_handlers": [
                        {
                            "handler_id": "COD000100417",
                            "name": "Denver Metal Finishing Inc",
                            "city": "Denver",
                            "state": "CO",
                            "active": True,
                            "lat": 39.706,
                            "lon": -104.895,
                            "category": "rcra",
                            "color": "#f97316",
                        },
                        {
                            "handler_id": "COD000100418",
                            "name": "Rocky Mountain Drum Service",
                            "city": "Denver",
                            "state": "CO",
                            "active": True,
                            "lat": 39.698,
                            "lon": -104.906,
                            "category": "rcra",
                            "color": "#f97316",
                        },
                    ],
                    "tri_facilities": [
                        {
                            "facility_id": "80211INDCH",
                            "name": "Industrial Chemical Co of Denver",
                            "city": "Denver",
                            "state": "CO",
                            "sic_code": "2819",
                            "lat": 39.708,
                            "lon": -104.910,
                            "category": "tri",
                            "color": "#eab308",
                        },
                    ],
                    "summary": {
                        "frs_count": 2,
                        "echo_count": 1,
                        "echo_violations": 1,
                        "formal_actions": 1,
                        "superfund_count": 1,
                        "superfund_near_count": 1,
                        "rcra_count": 2,
                        "tri_count": 1,
                        "superfund_flag": True,
                        "near_superfund_names": ["South Platte River Industrial (Demo Site)"],
                    },
                    "display": {
                        "color_superfund": "#dc2626",
                        "color_rcra": "#f97316",
                        "color_tri": "#eab308",
                        "color_frs": "#6366f1",
                        "buffer_miles": 1.0,
                    },
                },
                "error": None,
            },
            {
                "query_type": "historic",
                "status": "success",
                "data": {
                    "source": "NPS NRHP / USGS GNIS / State SHPOs",
                    "flag": True,
                    "nrhp_properties": [
                        {
                            "refnum": "5DV412",
                            "name": "Larimer Square Historic District",
                            "city": "Denver",
                            "state": "CO",
                            "county": "Denver",
                            "category": "District",
                            "date_listed": "1973-05-07",
                            "lat": 39.7467,
                            "lon": -104.9986,
                            "distance_miles": 0.06,
                            "near_flag": True,
                            "category_code": "nrhp",
                            "color": "#7c3aed",
                        },
                        {
                            "refnum": "5DV1",
                            "name": "Colorado State Capitol",
                            "city": "Denver",
                            "state": "CO",
                            "county": "Denver",
                            "category": "Building",
                            "date_listed": "1974-12-30",
                            "lat": 39.7392,
                            "lon": -104.9847,
                            "distance_miles": 0.52,
                            "near_flag": False,
                            "category_code": "nrhp",
                            "color": "#7c3aed",
                        },
                        {
                            "refnum": "5DV7",
                            "name": "Molly Brown House",
                            "city": "Denver",
                            "state": "CO",
                            "county": "Denver",
                            "category": "Building",
                            "date_listed": "1970-06-18",
                            "lat": 39.7321,
                            "lon": -104.9781,
                            "distance_miles": 0.78,
                            "near_flag": False,
                            "category_code": "nrhp",
                            "color": "#7c3aed",
                        },
                    ],
                    "cemeteries": [
                        {
                            "gnis_id": "203274",
                            "name": "Riverside Cemetery",
                            "state": "CO",
                            "county": "Denver",
                            "lat": 39.7608,
                            "lon": -104.9572,
                            "distance_miles": 0.09,
                            "near_flag": True,
                            "category_code": "cemetery",
                            "color": "#166534",
                        },
                    ],
                    "shpo_data": [
                        {"abbr": "AL", "name": "Alabama",       "url": "https://www.preserveala.org"},
                        {"abbr": "AK", "name": "Alaska",        "url": "https://dnr.alaska.gov/parks/oha/"},
                        {"abbr": "AZ", "name": "Arizona",       "url": "https://www.azstateparks.com/shpo"},
                        {"abbr": "AR", "name": "Arkansas",      "url": "https://www.arkansaspreservation.com"},
                        {"abbr": "CA", "name": "California",    "url": "https://ohp.parks.ca.gov"},
                        {"abbr": "CO", "name": "Colorado",      "url": "https://www.historycolorado.org/shpo"},
                        {"abbr": "CT", "name": "Connecticut",   "url": "https://portal.ct.gov/DECD/Historic-Preservation"},
                        {"abbr": "DE", "name": "Delaware",      "url": "https://history.delaware.gov/preservation/"},
                        {"abbr": "FL", "name": "Florida",       "url": "https://www.flheritage.com/preservation/shpo/"},
                        {"abbr": "GA", "name": "Georgia",       "url": "https://www.georgiashpo.org"},
                        {"abbr": "HI", "name": "Hawaii",        "url": "https://dlnr.hawaii.gov/shpd/"},
                        {"abbr": "ID", "name": "Idaho",         "url": "https://history.idaho.gov/shpo/"},
                        {"abbr": "IL", "name": "Illinois",      "url": "https://www2.illinois.gov/dnrhistoric"},
                        {"abbr": "IN", "name": "Indiana",       "url": "https://www.in.gov/dnr/historic-preservation/"},
                        {"abbr": "IA", "name": "Iowa",          "url": "https://iowaculture.gov/history/preservation"},
                        {"abbr": "KS", "name": "Kansas",        "url": "https://www.kshs.org/p/shpo/10431"},
                        {"abbr": "KY", "name": "Kentucky",      "url": "https://heritage.ky.gov"},
                        {"abbr": "LA", "name": "Louisiana",     "url": "https://www.crt.state.la.us/cultural-development/historic-preservation/"},
                        {"abbr": "ME", "name": "Maine",         "url": "https://www.maine.gov/mhpc/"},
                        {"abbr": "MD", "name": "Maryland",      "url": "https://mht.maryland.gov"},
                        {"abbr": "MA", "name": "Massachusetts", "url": "https://www.sec.state.ma.us/mhc/"},
                        {"abbr": "MI", "name": "Michigan",      "url": "https://www.michigan.gov/shpo"},
                        {"abbr": "MN", "name": "Minnesota",     "url": "https://www.mnhs.org/shpo"},
                        {"abbr": "MS", "name": "Mississippi",   "url": "https://www.mdah.ms.gov/preservation"},
                        {"abbr": "MO", "name": "Missouri",      "url": "https://mostateparks.com/page/55210/historic-preservation"},
                        {"abbr": "MT", "name": "Montana",       "url": "https://mhs.mt.gov/Shpo"},
                        {"abbr": "NE", "name": "Nebraska",      "url": "https://history.nebraska.gov/preservation/"},
                        {"abbr": "NV", "name": "Nevada",        "url": "https://shpo.nv.gov"},
                        {"abbr": "NH", "name": "New Hampshire", "url": "https://www.nh.gov/nhdhr/"},
                        {"abbr": "NJ", "name": "New Jersey",    "url": "https://www.nj.gov/dep/hpo/"},
                        {"abbr": "NM", "name": "New Mexico",    "url": "https://www.nmhistoricpreservation.org"},
                        {"abbr": "NY", "name": "New York",      "url": "https://parks.ny.gov/shpo/"},
                        {"abbr": "NC", "name": "North Carolina","url": "https://www.dncr.nc.gov/about-agency/divisions/state-historic-preservation-office"},
                        {"abbr": "ND", "name": "North Dakota",  "url": "https://www.history.nd.gov/hp/"},
                        {"abbr": "OH", "name": "Ohio",          "url": "https://www.ohiohistory.org/preservation"},
                        {"abbr": "OK", "name": "Oklahoma",      "url": "https://www.okhistory.org/shpo/"},
                        {"abbr": "OR", "name": "Oregon",        "url": "https://www.oregonheritage.org"},
                        {"abbr": "PA", "name": "Pennsylvania",  "url": "https://www.phmc.pa.gov/Preservation"},
                        {"abbr": "RI", "name": "Rhode Island",  "url": "https://www.preservation.ri.gov"},
                        {"abbr": "SC", "name": "South Carolina","url": "https://shpo.sc.gov"},
                        {"abbr": "SD", "name": "South Dakota",  "url": "https://history.sd.gov/preservation/"},
                        {"abbr": "TN", "name": "Tennessee",     "url": "https://tn.gov/environment/program-areas/na-natural-areas/shpo.html"},
                        {"abbr": "TX", "name": "Texas",         "url": "https://www.thc.texas.gov"},
                        {"abbr": "UT", "name": "Utah",          "url": "https://history.utah.gov/shpo/"},
                        {"abbr": "VT", "name": "Vermont",       "url": "https://accd.vermont.gov/historic-preservation/shpo"},
                        {"abbr": "VA", "name": "Virginia",      "url": "https://www.dhr.virginia.gov"},
                        {"abbr": "WA", "name": "Washington",    "url": "https://www.dahp.wa.gov"},
                        {"abbr": "WV", "name": "West Virginia", "url": "https://www.wvculture.org/shpo/"},
                        {"abbr": "WI", "name": "Wisconsin",     "url": "https://www.wisconsinhistory.org/preservation"},
                        {"abbr": "WY", "name": "Wyoming",       "url": "https://wyoparks.wyo.gov/index.php/shpo"},
                        {"abbr": "DC", "name": "District of Columbia", "url": "https://planning.dc.gov/page/historic-preservation-office"},
                    ],
                    "summary": {
                        "nrhp_count": 3,
                        "nrhp_near_count": 1,
                        "cemetery_count": 1,
                        "cemetery_near_count": 1,
                        "section_106_required": True,
                        "near_nrhp_names": ["Larimer Square Historic District"],
                        "near_cemetery_names": ["Riverside Cemetery"],
                    },
                    "display": {
                        "color_nrhp": "#7c3aed",
                        "color_cemetery": "#166534",
                        "buffer_miles": 1.0,
                        "flag_distance_ft": 500,
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
