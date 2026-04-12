"""Flood zones query tests — unit (mocked) + integration (live FEMA NFHL API).

Integration tests hit the real FEMA NFHL REST API with Louisiana coordinates
(30.0, -90.0) — New Orleans is largely in Zone AE, ideal for testing.
"""

from __future__ import annotations

import pytest
import respx
import httpx

from services.queries.flood_zones import (
    query,
    _clean_bfe,
    _process_features,
    _build_summary,
)
from services.queries.query_runner import QueryContext

# ── Test coordinates — Louisiana near New Orleans ─────────────────────────────

LA_CTX = QueryContext(
    site_id="test-la-flood",
    bbox=(-90.05, 29.95, -89.95, 30.05),
    buffer_meters=1609.0,
)

NFHL_URL = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"

# ── Mock fixtures ─────────────────────────────────────────────────────────────

MOCK_FEATURES_MIXED = [
    {
        "attributes": {
            "FLD_ZONE": "AE",
            "BFE_DSGND": 5.0,
            "DFIRM_ID": "22071C0210E",
            "FLOODWAY": "AE",
            "SFHA_TF": "T",
            "DEPTH": None,
            "SOURCE_CIT": "STUDY1",
        },
        "geometry": {"rings": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
    },
    {
        "attributes": {
            "FLD_ZONE": "AE",
            "BFE_DSGND": 3.0,
            "DFIRM_ID": "22071C0210E",
            "FLOODWAY": "NP",
            "SFHA_TF": "T",
            "DEPTH": None,
            "SOURCE_CIT": "STUDY1",
        },
        "geometry": {"rings": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
    },
    {
        "attributes": {
            "FLD_ZONE": "X",
            "BFE_DSGND": -9999.0,
            "DFIRM_ID": "22071C0210E",
            "FLOODWAY": "NP",
            "SFHA_TF": "F",
            "DEPTH": None,
            "SOURCE_CIT": "STUDY1",
        },
        "geometry": {"rings": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
    },
]

MOCK_FEATURES_X_ONLY = [
    {
        "attributes": {
            "FLD_ZONE": "X",
            "BFE_DSGND": -9999.0,
            "DFIRM_ID": "01001C0100E",
            "FLOODWAY": "NP",
            "SFHA_TF": "F",
            "DEPTH": None,
            "SOURCE_CIT": "STUDY1",
        },
        "geometry": {"rings": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
    }
]

MOCK_FEATURES_VE = [
    {
        "attributes": {
            "FLD_ZONE": "VE",
            "BFE_DSGND": 14.0,
            "DFIRM_ID": "12086C0480L",
            "FLOODWAY": "NP",
            "SFHA_TF": "T",
            "DEPTH": None,
            "SOURCE_CIT": "STUDY1",
        },
        "geometry": {"rings": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
    }
]

MOCK_RESPONSE_MIXED = {"features": MOCK_FEATURES_MIXED}
MOCK_RESPONSE_X_ONLY = {"features": MOCK_FEATURES_X_ONLY}
MOCK_RESPONSE_VE = {"features": MOCK_FEATURES_VE}
EMPTY_RESPONSE = {"features": []}


# ── Unit: _clean_bfe ──────────────────────────────────────────────────────────

def test_clean_bfe_valid():
    assert _clean_bfe(5.0) == 5.0
    assert _clean_bfe(14.5) == 14.5
    assert _clean_bfe("12.0") == 12.0


def test_clean_bfe_fema_sentinels():
    assert _clean_bfe(-9999.0) is None
    assert _clean_bfe(-8888.0) is None
    assert _clean_bfe(-8889.0) is None
    assert _clean_bfe(0.0) is None


def test_clean_bfe_below_threshold():
    assert _clean_bfe(-200.0) is None


def test_clean_bfe_none():
    assert _clean_bfe(None) is None


def test_clean_bfe_rounding():
    assert _clean_bfe(5.678) == 5.7


# ── Unit: _process_features ───────────────────────────────────────────────────

def test_process_features_ae_sets_flags():
    zones, has_sfha, has_ae = _process_features(MOCK_FEATURES_MIXED)
    assert has_sfha is True
    assert has_ae is True
    assert len(zones) == 3


def test_process_features_x_only_no_sfha():
    zones, has_sfha, has_ae = _process_features(MOCK_FEATURES_X_ONLY)
    assert has_sfha is False
    assert has_ae is False
    assert len(zones) == 1
    assert zones[0]["zone"] == "X"


def test_process_features_ve_is_sfha():
    zones, has_sfha, has_ae = _process_features(MOCK_FEATURES_VE)
    assert has_sfha is True
    assert has_ae is True  # VE is in _BFE_ZONES


def test_process_features_bfe_sentinel_stripped():
    zones, _, _ = _process_features(MOCK_FEATURES_MIXED)
    x_zone = next(z for z in zones if z["zone"] == "X")
    assert x_zone["bfe_ft"] is None


def test_process_features_bfe_preserved():
    zones, _, _ = _process_features(MOCK_FEATURES_MIXED)
    ae_zone = next(z for z in zones if z["zone"] == "AE")
    assert ae_zone["bfe_ft"] == 5.0


def test_process_features_floodway_flag():
    zones, _, _ = _process_features(MOCK_FEATURES_MIXED)
    # First feature has FLOODWAY="AE" (not the string "FLOODWAY"), so floodway=False
    assert zones[0]["floodway"] is False


def test_process_features_empty():
    zones, has_sfha, has_ae = _process_features([])
    assert zones == []
    assert has_sfha is False
    assert has_ae is False


# ── Unit: _build_summary ──────────────────────────────────────────────────────

def test_build_summary_sfha_message():
    zones, has_sfha, has_ae = _process_features(MOCK_FEATURES_MIXED)
    summary = _build_summary(zones, has_sfha, has_ae)
    assert summary["sfha_flag"] is True
    assert summary["zone_ae_flag"] is True
    assert "AE" in summary["zones_found"]
    assert "X" in summary["zones_found"]
    assert "Zone AE" in summary["message"]
    assert len(summary["firm_panels"]) == 1


def test_build_summary_bfe_range():
    zones, has_sfha, has_ae = _process_features(MOCK_FEATURES_MIXED)
    summary = _build_summary(zones, has_sfha, has_ae)
    assert summary["bfe_range_ft"] is not None
    assert summary["bfe_range_ft"]["min"] == 3.0
    assert summary["bfe_range_ft"]["max"] == 5.0


def test_build_summary_no_sfha():
    zones, has_sfha, has_ae = _process_features(MOCK_FEATURES_X_ONLY)
    summary = _build_summary(zones, has_sfha, has_ae)
    assert summary["sfha_flag"] is False
    assert "non-SFHA" in summary["message"]
    assert summary["bfe_range_ft"] is None


def test_build_summary_empty():
    summary = _build_summary([], False, False)
    assert "outside FEMA" in summary["message"] or "No flood zone" in summary["message"]


# ── Unit: full query — mocked HTTP ───────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_query_mock_ae_zones():
    respx.get(NFHL_URL).mock(
        return_value=httpx.Response(200, json=MOCK_RESPONSE_MIXED)
    )
    result = await query(LA_CTX)

    assert result["source"] == "FEMA NFHL"
    assert result["flag"] is True
    assert result["sfha_present"] is True
    assert result["zone_ae_present"] is True
    assert result["zone_count"] == 3
    assert "summary" in result
    assert result["summary"]["sfha_flag"] is True
    assert result["summary"]["zone_ae_flag"] is True
    assert "display" in result
    assert result["display"]["default_color"] == "#f97316"


@pytest.mark.asyncio
@respx.mock
async def test_query_mock_no_sfha():
    respx.get(NFHL_URL).mock(
        return_value=httpx.Response(200, json=MOCK_RESPONSE_X_ONLY)
    )
    result = await query(LA_CTX)

    assert result["flag"] is False
    assert result["sfha_present"] is False
    assert result["zone_ae_present"] is False
    assert result["zone_count"] == 1
    assert result["summary"]["sfha_flag"] is False


@pytest.mark.asyncio
@respx.mock
async def test_query_mock_ve_coastal_zone():
    respx.get(NFHL_URL).mock(
        return_value=httpx.Response(200, json=MOCK_RESPONSE_VE)
    )
    result = await query(LA_CTX)

    assert result["flag"] is True
    assert result["sfha_present"] is True
    assert result["zone_ae_present"] is True  # VE is a BFE zone
    ve_zone = result["flood_zones"][0]
    assert ve_zone["zone"] == "VE"
    assert ve_zone["bfe_ft"] == 14.0
    assert ve_zone["sfha"] is True


@pytest.mark.asyncio
@respx.mock
async def test_query_mock_empty():
    respx.get(NFHL_URL).mock(
        return_value=httpx.Response(200, json=EMPTY_RESPONSE)
    )
    result = await query(LA_CTX)

    assert result["flag"] is False
    assert result["zone_count"] == 0
    assert "outside FEMA" in result["summary"]["message"] or "No flood zone" in result["summary"]["message"]


@pytest.mark.asyncio
@respx.mock
async def test_query_mock_api_error():
    respx.get(NFHL_URL).mock(
        return_value=httpx.Response(200, json={"error": {"code": 400, "message": "Invalid geometry"}})
    )
    with pytest.raises(RuntimeError, match="FEMA NFHL API error"):
        await query(LA_CTX)


@pytest.mark.asyncio
@respx.mock
async def test_query_mock_http_500():
    respx.get(NFHL_URL).mock(return_value=httpx.Response(500))
    with pytest.raises(httpx.HTTPStatusError):
        await query(LA_CTX)


# ── Integration: real FEMA NFHL API — Louisiana (30.0, -90.0) ────────────────

@pytest.mark.asyncio
@pytest.mark.integration
async def test_integration_louisiana_flood_zones():
    """New Orleans area is mostly Zone AE — should flag SFHA."""
    result = await query(LA_CTX)

    assert result["source"] == "FEMA NFHL"
    assert result["zone_count"] > 0, "Expected flood zone data for New Orleans"
    assert result["flag"] is True, "Expected SFHA in New Orleans (Zone AE)"
    assert result["sfha_present"] is True
    assert result["zone_ae_present"] is True, "Expected Zone AE in New Orleans"

    # At least one AE zone
    ae_zones = [z for z in result["flood_zones"] if z["zone"] == "AE"]
    assert len(ae_zones) > 0

    # FIRM panel numbers should be present
    summary = result["summary"]
    assert summary["sfha_flag"] is True
    assert summary["zone_ae_flag"] is True
    assert len(summary["firm_panels"]) > 0
    assert summary["bfe_range_ft"] is not None, "Zone AE should have BFE values"
    assert "Zone AE" in summary["message"]

    # Structural checks on zone records
    for z in result["flood_zones"]:
        assert "zone" in z
        assert "description" in z
        assert "sfha" in z
        assert "bfe_ft" in z
        assert "firm_panel" in z
        assert "floodway" in z
        assert "color" in z

    # Display config
    display = result["display"]
    assert display["layer_type"] == "polygon"
    assert "zone_colors" in display
    assert "AE" in display["zone_colors"]
