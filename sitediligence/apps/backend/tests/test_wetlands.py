"""Wetlands query tests — unit (mocked) + integration (live NWI API).

Integration tests hit the real USFWS NWI REST API with Louisiana coordinates
(30.0, -90.0) — one of the most wetland-dense regions in the US.
"""

from __future__ import annotations

import json
import pytest
import respx
import httpx

from services.queries.wetlands import (
    query,
    parse_nwi_code,
    _build_summary,
    _process_features,
)
from services.queries.query_runner import QueryContext

# ── Test coordinates — Louisiana near New Orleans ─────────────────────────────

# ~0.05° buffer ≈ 5 km — small enough for fast API response
LA_CTX = QueryContext(
    site_id="test-la-wetlands",
    bbox=(-90.05, 29.95, -89.95, 30.05),
    buffer_meters=1609.0,
)

NWI_URL = (
    "https://fwspublicservices.wim.usgs.gov"
    "/wetlandsmapservice/rest/services/Wetlands/MapServer/0/query"
)

# ── Mock fixtures ─────────────────────────────────────────────────────────────

MOCK_FEATURES = [
    {
        "attributes": {
            "ATTRIBUTE": "PEM1A",
            "WETLAND_TYPE": "Freshwater Emergent Wetland",
            "ACRES": 12.5,
            "GLOBALID": "{AAA-111}",
        },
        "geometry": {"rings": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
    },
    {
        "attributes": {
            "ATTRIBUTE": "PFO1A",
            "WETLAND_TYPE": "Freshwater Forested/Shrub Wetland",
            "ACRES": 7.3,
            "GLOBALID": "{BBB-222}",
        },
        "geometry": {"rings": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
    },
    {
        "attributes": {
            "ATTRIBUTE": "E2EM1P",
            "WETLAND_TYPE": "Estuarine and Marine Wetland",
            "ACRES": 3.1,
            "GLOBALID": "{CCC-333}",
        },
        "geometry": {"rings": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
    },
    {
        "attributes": {
            "ATTRIBUTE": "POND",
            "WETLAND_TYPE": "Freshwater Pond",
            "ACRES": 0.8,
            "GLOBALID": "{DDD-444}",
        },
        "geometry": {"rings": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
    },
]

MOCK_RESPONSE = {"features": MOCK_FEATURES}
EMPTY_RESPONSE = {"features": []}


# ── Unit: parse_nwi_code ──────────────────────────────────────────────────────

def test_parse_palustrine():
    result = parse_nwi_code("PEM1A")
    assert result["system"] == "Palustrine"
    assert result["system_code"] == "P"
    assert result["regulated_404"] is True
    assert result["color"] == "#1a9850"


def test_parse_estuarine():
    result = parse_nwi_code("E2EM1P")
    assert result["system"] == "Estuarine"
    assert result["regulated_404"] is True
    assert result["color"] == "#2c7bb6"


def test_parse_riverine_not_regulated():
    result = parse_nwi_code("R4SBC")
    assert result["system"] == "Riverine"
    assert result["regulated_404"] is False


def test_parse_lacustrine():
    result = parse_nwi_code("L2USH")
    assert result["system"] == "Lacustrine"
    assert result["regulated_404"] is False


def test_parse_marine():
    result = parse_nwi_code("M2AB3H")
    assert result["system"] == "Marine"
    assert result["regulated_404"] is False


def test_parse_empty_code():
    result = parse_nwi_code("")
    assert result["system"] == "Unknown"
    assert result["regulated_404"] is False


def test_parse_none_code():
    result = parse_nwi_code(None)
    assert result["system"] == "Unknown"
    assert result["regulated_404"] is False


# ── Unit: _process_features ───────────────────────────────────────────────────

def test_process_features_acreage():
    wetlands, total, regulated = _process_features(MOCK_FEATURES)
    assert len(wetlands) == 4
    # PEM1A (12.5) + PFO1A (7.3) + E2EM1P (3.1) regulated; POND is P-system too
    # Actually POND starts with P? No — "POND" starts with P but it's not a valid NWI code
    # parse_nwi_code("POND") → P = Palustrine → regulated
    assert total == pytest.approx(23.7, abs=0.01)
    assert regulated == pytest.approx(23.7, abs=0.01)  # all are P or E


def test_process_features_empty():
    wetlands, total, regulated = _process_features([])
    assert wetlands == []
    assert total == 0.0
    assert regulated == 0.0


def test_process_features_missing_attrs():
    features = [{"attributes": {}, "geometry": None}]
    wetlands, total, regulated = _process_features(features)
    assert len(wetlands) == 1
    assert wetlands[0]["nwi_code"] == ""
    assert wetlands[0]["acres"] == 0.0


# ── Unit: _build_summary ──────────────────────────────────────────────────────

def test_build_summary_with_wetlands():
    wetlands, total, regulated = _process_features(MOCK_FEATURES)
    summary = _build_summary(wetlands, total, regulated)
    assert summary["cwa_404_flag"] is True
    assert summary["total_acres"] == pytest.approx(23.7, abs=0.01)
    assert "wetland_types" in summary
    assert "Freshwater Emergent Wetland" in summary["wetland_types"]
    assert "§404" in summary["message"]


def test_build_summary_no_wetlands():
    summary = _build_summary([], 0.0, 0.0)
    assert summary["cwa_404_flag"] is False
    assert summary["total_acres"] == 0.0
    assert "No wetlands" in summary["message"]


# ── Unit: full query — mocked HTTP ───────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_query_mock_wetlands_present():
    respx.get(NWI_URL).mock(
        return_value=httpx.Response(200, json=MOCK_RESPONSE)
    )
    result = await query(LA_CTX)

    assert result["source"] == "USFWS NWI"
    assert result["flag"] is True
    assert result["wetlands_present"] is True
    assert result["wetland_count"] == 4
    assert result["total_wetland_acres"] == pytest.approx(23.7, abs=0.01)
    assert result["regulated_404_acres"] > 0
    assert "summary" in result
    assert result["summary"]["cwa_404_flag"] is True
    assert "display" in result
    assert result["display"]["layer_type"] == "polygon"


@pytest.mark.asyncio
@respx.mock
async def test_query_mock_no_wetlands():
    respx.get(NWI_URL).mock(
        return_value=httpx.Response(200, json=EMPTY_RESPONSE)
    )
    result = await query(LA_CTX)

    assert result["flag"] is False
    assert result["wetlands_present"] is False
    assert result["wetland_count"] == 0
    assert result["total_wetland_acres"] == 0.0
    assert result["summary"]["cwa_404_flag"] is False
    assert "No wetlands" in result["summary"]["message"]


@pytest.mark.asyncio
@respx.mock
async def test_query_mock_api_error():
    respx.get(NWI_URL).mock(
        return_value=httpx.Response(200, json={"error": {"code": 400, "message": "Bad request"}})
    )
    with pytest.raises(RuntimeError, match="NWI API error"):
        await query(LA_CTX)


@pytest.mark.asyncio
@respx.mock
async def test_query_mock_http_500():
    respx.get(NWI_URL).mock(return_value=httpx.Response(500))
    with pytest.raises(httpx.HTTPStatusError):
        await query(LA_CTX)


# ── Integration: real NWI API — Louisiana (30.0, -90.0) ──────────────────────

@pytest.mark.asyncio
@pytest.mark.integration
async def test_integration_louisiana_wetlands():
    """Louisiana near New Orleans — should have abundant wetlands."""
    result = await query(LA_CTX)

    assert result["source"] == "USFWS NWI"
    assert result["flag"] is True, "Expected wetlands in Louisiana near lat=30, lon=-90"
    assert result["wetlands_present"] is True
    assert result["wetland_count"] > 0
    assert result["total_wetland_acres"] > 0.0
    assert result["regulated_404_acres"] > 0.0, "Expected regulated wetlands (P/E system)"

    # Structural checks
    assert "wetlands" in result
    for w in result["wetlands"]:
        assert "nwi_code" in w
        assert "wetland_type" in w
        assert "system" in w
        assert "regulated_404" in w
        assert "acres" in w
        assert "color" in w

    # Summary card
    summary = result["summary"]
    assert summary["cwa_404_flag"] is True
    assert "§404" in summary["message"]
    assert len(summary["wetland_types"]) > 0

    # Display config
    display = result["display"]
    assert display["layer_type"] == "polygon"
    assert "system_colors" in display
    assert display["opacity"] == 0.6
