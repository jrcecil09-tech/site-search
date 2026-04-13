"""Tests for services/queries/epa.py"""

from __future__ import annotations

import re

import pytest
import respx
import httpx

from services.queries.epa import (
    _FRS_URL,
    _ECHO_URL,
    _SEMS_URL_BASE,
    _RCRA_URL_BASE,
    _TRI_URL_BASE,
    _BUFFER_MILES,
    _SUPERFUND_FLAG_MILES,
    _COLOR_SUPERFUND,
    _COLOR_RCRA,
    _COLOR_TRI,
    _COLOR_FRS,
    _buffer_bbox_miles,
    _haversine_miles,
    _safe_float,
    _parse_frs_facility,
    _parse_echo_facility,
    _parse_cercla_site,
    _parse_rcra_handler,
    _parse_tri_facility,
    _build_risk_summary,
    query,
)
from services.queries.query_runner import QueryContext

# ── Context fixture ───────────────────────────────────────────────────────────

CHICAGO_CTX = QueryContext(
    site_id="test-chicago",
    bbox=(-87.605, 41.795, -87.595, 41.805),
)
CENTER_LAT = (41.795 + 41.805) / 2   # 41.8
CENTER_LON = (-87.605 + -87.595) / 2  # -87.6

# ── Mock response builders ────────────────────────────────────────────────────

def _frs_resp(n: int = 2) -> httpx.Response:
    return httpx.Response(200, json={"Results": {"Facilities": [
        {
            "RegistryId": f"11000100{i}",
            "FacilityName": f"Facility {i}",
            "LocationAddress": f"{i} Industrial Blvd",
            "CityName": "Chicago",
            "StateCode": "IL",
            "Latitude83": str(41.800 + i * 0.001),
            "Longitude83": str(-87.600 + i * 0.001),
            "PGMSYSList": [{"PGMSystemAcronym": "CAA"}, {"PGMSystemAcronym": "RCRA"}],
        }
        for i in range(n)
    ]}})


def _echo_resp(violations: bool = True) -> httpx.Response:
    return httpx.Response(200, json={"Results": {"Facilities": [
        {
            "RegistryID": "110001234567",
            "FacilityName": "Republic Industries LLC",
            "Latitude": "41.797",
            "Longitude": "-87.601",
            "CAAStatus": "No Violation Identified",
            "CWAStatus": "No Violation Identified",
            "RCRAStatus": "Significant Violation" if violations else "No Violation Identified",
            "TotalViolations": 3 if violations else 0,
            "FormalEnforcementActions": 1 if violations else 0,
            "InspectionCount": 2,
            "FacilityTypeName": "Waste Handler",
        }
    ]}})


def _cercla_resp(lat: float = 41.804, lon: float = -87.603) -> httpx.Response:
    return httpx.Response(200, json=[{
        "SITE_ID": "ILD980794521",
        "SITE_NAME": "Southeast Chicago Industrial Complex",
        "ADDRESS_TEXT": "2200 E 100th St",
        "CITY_NAME": "Chicago",
        "STATE_CODE": "IL",
        "LATITUDE84": str(lat),
        "LONGITUDE84": str(lon),
        "CURRENT_SITE_STATUS": "Active",
        "NPL_STATUS": "Currently on the Final NPL",
    }])


def _rcra_resp() -> httpx.Response:
    return httpx.Response(200, json=[
        {
            "HANDLER_ID": "ILD000123456",
            "FACILITY_NAME": "Calumet Industries Inc",
            "CITY_NAME": "Chicago",
            "STATE_CODE": "IL",
            "LATITUDE_DECIMAL_DEG": "41.793",
            "LONGITUDE_DECIMAL_DEG": "-87.607",
            "CURRENT_RECORD_ACTIVITY": "Y",
        },
        {
            "HANDLER_ID": "ILD000789012",
            "FACILITY_NAME": "Chicago Drum Service",
            "CITY_NAME": "Chicago",
            "STATE_CODE": "IL",
            "LATITUDE_DECIMAL_DEG": "41.801",
            "LONGITUDE_DECIMAL_DEG": "-87.590",
            "CURRENT_RECORD_ACTIVITY": "N",
        },
    ])


def _tri_resp() -> httpx.Response:
    return httpx.Response(200, json=[{
        "TRI_FACILITY_ID": "60617STLWK",
        "FACILITY_NAME": "Southeast Steel Works",
        "CITY": "Chicago",
        "STATE_ABBR": "IL",
        "LATITUDE82": "41.806",
        "LONGITUDE82": "-87.595",
        "SIC_CODE": "3312",
    }])


def _empty_list_resp() -> httpx.Response:
    return httpx.Response(200, json=[])


def _mock_all(
    *,
    cercla_lat: float = 41.804,
    cercla_lon: float = -87.603,
    frs_n: int = 2,
    echo_violations: bool = True,
):
    respx.get(_FRS_URL).mock(return_value=_frs_resp(frs_n))
    respx.get(_ECHO_URL).mock(return_value=_echo_resp(echo_violations))
    respx.get(re.compile(rf"{re.escape(_SEMS_URL_BASE)}.*")).mock(
        return_value=_cercla_resp(cercla_lat, cercla_lon)
    )
    respx.get(re.compile(rf"{re.escape(_RCRA_URL_BASE)}.*")).mock(
        return_value=_rcra_resp()
    )
    respx.get(re.compile(rf"{re.escape(_TRI_URL_BASE)}.*")).mock(
        return_value=_tri_resp()
    )


# ── _buffer_bbox_miles ────────────────────────────────────────────────────────

def test_buffer_bbox_miles_expands_all_sides():
    bbox = (-87.6, 41.8, -87.5, 41.9)
    r = _buffer_bbox_miles(bbox, 1.0)
    assert r[0] < -87.6
    assert r[1] < 41.8
    assert r[2] > -87.5
    assert r[3] > 41.9


def test_buffer_bbox_miles_one_mile_lat_magnitude():
    """1 mile ≈ 0.0145° latitude at any longitude."""
    bbox = (-87.6, 41.8, -87.5, 41.9)
    r = _buffer_bbox_miles(bbox, 1.0)
    lat_delta = 41.8 - r[1]
    assert 0.013 < lat_delta < 0.016


def test_buffer_bbox_miles_zero_buffer_unchanged():
    bbox = (-87.6, 41.8, -87.5, 41.9)
    r = _buffer_bbox_miles(bbox, 0.0)
    assert r == bbox


def test_buffer_bbox_miles_half_mile():
    bbox = (-87.6, 41.8, -87.5, 41.9)
    full = _buffer_bbox_miles(bbox, 1.0)
    half = _buffer_bbox_miles(bbox, 0.5)
    lat_full = 41.8 - full[1]
    lat_half = 41.8 - half[1]
    assert abs(lat_full / lat_half - 2.0) < 0.01


# ── _haversine_miles ──────────────────────────────────────────────────────────

def test_haversine_miles_same_point_is_zero():
    assert _haversine_miles(41.8, -87.6, 41.8, -87.6) == pytest.approx(0.0, abs=1e-6)


def test_haversine_miles_one_degree_lat():
    """1° latitude ≈ 69 miles."""
    d = _haversine_miles(41.0, -87.6, 42.0, -87.6)
    assert 68.5 < d < 69.5


def test_haversine_miles_commutative():
    d1 = _haversine_miles(41.8, -87.6, 41.804, -87.603)
    d2 = _haversine_miles(41.804, -87.603, 41.8, -87.6)
    assert d1 == pytest.approx(d2, rel=1e-6)


def test_haversine_miles_known_short_distance():
    """≈0.3 miles between two points near Chicago."""
    d = _haversine_miles(41.8, -87.6, 41.804, -87.603)
    assert 0.25 < d < 0.40


# ── _safe_float ───────────────────────────────────────────────────────────────

def test_safe_float_valid_string():
    assert _safe_float("41.8") == pytest.approx(41.8)


def test_safe_float_numeric():
    assert _safe_float(41.8) == pytest.approx(41.8)


def test_safe_float_none():
    assert _safe_float(None) is None


def test_safe_float_empty():
    assert _safe_float("") is None


def test_safe_float_na():
    assert _safe_float("N/A") is None


def test_safe_float_non_numeric():
    assert _safe_float("unknown") is None


# ── _parse_frs_facility ───────────────────────────────────────────────────────

def test_parse_frs_facility_basic():
    raw = {
        "RegistryId": "110001234",
        "FacilityName": "Acme Plant",
        "LocationAddress": "100 Main St",
        "CityName": "Chicago",
        "StateCode": "IL",
        "Latitude83": "41.800",
        "Longitude83": "-87.600",
        "PGMSYSList": [{"PGMSystemAcronym": "CAA"}, {"PGMSystemAcronym": "RCRA"}],
    }
    result = _parse_frs_facility(raw)
    assert result["name"] == "Acme Plant"
    assert result["lat"] == pytest.approx(41.8)
    assert result["programs"] == ["CAA", "RCRA"]
    assert result["category"] == "frs"
    assert result["color"] == _COLOR_FRS


def test_parse_frs_facility_missing_coords():
    raw = {"FacilityName": "Unknown Site"}
    result = _parse_frs_facility(raw)
    assert result["lat"] is None
    assert result["lon"] is None


def test_parse_frs_facility_empty_programs():
    raw = {"FacilityName": "Test", "PGMSYSList": []}
    assert _parse_frs_facility(raw)["programs"] == []


def test_parse_frs_facility_alternate_field_names():
    raw = {
        "RegistryID": "999",
        "PrimaryName": "Alternate Name",
        "latitude83": "41.0",
        "longitude83": "-87.0",
    }
    r = _parse_frs_facility(raw)
    assert r["name"] == "Alternate Name"
    assert r["lat"] == pytest.approx(41.0)


# ── _parse_echo_facility ──────────────────────────────────────────────────────

def test_parse_echo_facility_with_violations():
    raw = {
        "RegistryID": "110001234567",
        "FacilityName": "Republic Industries",
        "Latitude": "41.797",
        "Longitude": "-87.601",
        "CAAStatus": "No Violation Identified",
        "CWAStatus": "No Violation Identified",
        "RCRAStatus": "Significant Violation",
        "TotalViolations": 3,
        "FormalEnforcementActions": 1,
        "InspectionCount": 2,
        "FacilityTypeName": "Waste Handler",
    }
    result = _parse_echo_facility(raw)
    assert result["has_violation"] is True
    assert result["total_violations"] == 3
    assert result["formal_actions"] == 1
    assert result["compliance_status"]["waste"] == "Significant Violation"


def test_parse_echo_facility_no_violations():
    raw = {
        "FacilityName": "Clean Co",
        "TotalViolations": 0,
        "FormalEnforcementActions": 0,
    }
    result = _parse_echo_facility(raw)
    assert result["has_violation"] is False


def test_parse_echo_facility_formal_action_flags_violation():
    raw = {"FacilityName": "Test", "TotalViolations": 0, "FormalEnforcementActions": 1}
    assert _parse_echo_facility(raw)["has_violation"] is True


# ── _parse_cercla_site ────────────────────────────────────────────────────────

def test_parse_cercla_site_computes_distance():
    raw = {
        "SITE_ID": "ILD980794521",
        "SITE_NAME": "Test Superfund",
        "LATITUDE84": "41.804",
        "LONGITUDE84": "-87.603",
    }
    result = _parse_cercla_site(raw, CENTER_LAT, CENTER_LON)
    assert result["distance_miles"] is not None
    assert 0.1 < result["distance_miles"] < 0.5
    assert result["color"] == _COLOR_SUPERFUND
    assert result["category"] == "superfund"


def test_parse_cercla_site_missing_coords_no_distance():
    raw = {"SITE_NAME": "No Location"}
    result = _parse_cercla_site(raw, CENTER_LAT, CENTER_LON)
    assert result["distance_miles"] is None
    assert result["lat"] is None


def test_parse_cercla_site_zero_distance():
    raw = {"SITE_NAME": "On Site", "LATITUDE84": str(CENTER_LAT), "LONGITUDE84": str(CENTER_LON)}
    result = _parse_cercla_site(raw, CENTER_LAT, CENTER_LON)
    assert result["distance_miles"] == pytest.approx(0.0, abs=0.001)


# ── _parse_rcra_handler ───────────────────────────────────────────────────────

def test_parse_rcra_handler_active():
    raw = {
        "HANDLER_ID": "ILD000123456",
        "FACILITY_NAME": "Calumet Industries",
        "CITY_NAME": "Chicago",
        "STATE_CODE": "IL",
        "LATITUDE_DECIMAL_DEG": "41.793",
        "LONGITUDE_DECIMAL_DEG": "-87.607",
        "CURRENT_RECORD_ACTIVITY": "Y",
    }
    result = _parse_rcra_handler(raw)
    assert result["active"] is True
    assert result["color"] == _COLOR_RCRA
    assert result["category"] == "rcra"


def test_parse_rcra_handler_inactive():
    raw = {"FACILITY_NAME": "Old Site", "CURRENT_RECORD_ACTIVITY": "N"}
    assert _parse_rcra_handler(raw)["active"] is False


def test_parse_rcra_handler_missing_activity():
    raw = {"FACILITY_NAME": "Unknown"}
    assert _parse_rcra_handler(raw)["active"] is False


# ── _parse_tri_facility ───────────────────────────────────────────────────────

def test_parse_tri_facility_basic():
    raw = {
        "TRI_FACILITY_ID": "60617STLWK",
        "FACILITY_NAME": "Steel Works",
        "CITY": "Chicago",
        "STATE_ABBR": "IL",
        "LATITUDE82": "41.806",
        "LONGITUDE82": "-87.595",
        "SIC_CODE": "3312",
    }
    result = _parse_tri_facility(raw)
    assert result["name"] == "Steel Works"
    assert result["sic_code"] == "3312"
    assert result["color"] == _COLOR_TRI
    assert result["category"] == "tri"


# ── _build_risk_summary ───────────────────────────────────────────────────────

def _make_superfund(lat: float, lon: float) -> dict:
    return _parse_cercla_site(
        {"SITE_NAME": "Test SF", "LATITUDE84": str(lat), "LONGITUDE84": str(lon)},
        CENTER_LAT, CENTER_LON,
    )


def test_build_risk_summary_superfund_flag_triggered():
    # Site within 0.5 miles
    sf = [_make_superfund(CENTER_LAT + 0.002, CENTER_LON + 0.001)]
    s = _build_risk_summary([], [], sf, [], [])
    assert s["superfund_flag"] is True
    assert s["superfund_near_count"] == 1


def test_build_risk_summary_superfund_flag_not_triggered():
    # Site beyond 0.5 miles (≈ 0.7 miles away)
    sf = [_make_superfund(CENTER_LAT + 0.007, CENTER_LON + 0.005)]
    s = _build_risk_summary([], [], sf, [], [])
    assert s["superfund_flag"] is False
    assert s["superfund_near_count"] == 0


def test_build_risk_summary_exact_flag_threshold():
    """Site exactly at _SUPERFUND_FLAG_MILES should trigger the flag."""
    # 0.5 miles north ≈ 0.00725°
    sf = [_make_superfund(CENTER_LAT + 0.00725, CENTER_LON)]
    dist = sf[0]["distance_miles"]
    s = _build_risk_summary([], [], sf, [], [])
    # Flag depends on whether dist ≤ 0.5
    assert s["superfund_flag"] == (dist is not None and dist <= _SUPERFUND_FLAG_MILES)


def test_build_risk_summary_counts():
    frs  = [{"name": "a"}, {"name": "b"}]
    echo = [{"has_violation": True, "formal_actions": 2},
            {"has_violation": False, "formal_actions": 0}]
    rcra = [{"name": "r"}]
    tri  = [{"name": "t1"}, {"name": "t2"}, {"name": "t3"}]
    s = _build_risk_summary(frs, echo, [], rcra, tri)
    assert s["frs_count"] == 2
    assert s["echo_count"] == 2
    assert s["echo_violations"] == 1
    assert s["formal_actions"] == 2
    assert s["rcra_count"] == 1
    assert s["tri_count"] == 3


def test_build_risk_summary_empty():
    s = _build_risk_summary([], [], [], [], [])
    assert s["superfund_flag"] is False
    assert s["frs_count"] == 0
    assert s["echo_violations"] == 0


def test_build_risk_summary_near_names_capped():
    sf = [
        _make_superfund(CENTER_LAT + 0.001 * i, CENTER_LON)
        for i in range(5)
    ]
    s = _build_risk_summary([], [], sf, [], [])
    assert len(s["near_superfund_names"]) <= 3


# ── query() — mocked ──────────────────────────────────────────────────────────

@respx.mock
async def test_query_full_success():
    _mock_all()
    result = await query(CHICAGO_CTX)

    assert result["source"].startswith("EPA")
    assert len(result["frs_facilities"]) == 2
    assert len(result["echo_facilities"]) == 1
    assert len(result["superfund_sites"]) == 1
    assert len(result["rcra_handlers"]) == 2
    assert len(result["tri_facilities"]) == 1
    assert result["flag"] is True   # Superfund at 41.804/-87.603 ≈ 0.3 mi from center


@respx.mock
async def test_query_no_results():
    respx.get(_FRS_URL).mock(return_value=httpx.Response(200, json={"Results": {"Facilities": []}}))
    respx.get(_ECHO_URL).mock(return_value=httpx.Response(200, json={"Results": {"Facilities": []}}))
    respx.get(re.compile(rf"{re.escape(_SEMS_URL_BASE)}.*")).mock(return_value=_empty_list_resp())
    respx.get(re.compile(rf"{re.escape(_RCRA_URL_BASE)}.*")).mock(return_value=_empty_list_resp())
    respx.get(re.compile(rf"{re.escape(_TRI_URL_BASE)}.*")).mock(return_value=_empty_list_resp())

    result = await query(CHICAGO_CTX)
    assert result["flag"] is False
    assert result["summary"]["superfund_count"] == 0


@respx.mock
async def test_query_frs_failure_nonfatal():
    respx.get(_FRS_URL).mock(side_effect=httpx.ConnectError("timeout"))
    respx.get(_ECHO_URL).mock(return_value=_echo_resp())
    respx.get(re.compile(rf"{re.escape(_SEMS_URL_BASE)}.*")).mock(return_value=_cercla_resp())
    respx.get(re.compile(rf"{re.escape(_RCRA_URL_BASE)}.*")).mock(return_value=_rcra_resp())
    respx.get(re.compile(rf"{re.escape(_TRI_URL_BASE)}.*")).mock(return_value=_tri_resp())

    result = await query(CHICAGO_CTX)
    assert result["frs_facilities"] == []
    assert len(result["echo_facilities"]) == 1   # ECHO still succeeded


@respx.mock
async def test_query_echo_failure_nonfatal():
    respx.get(_FRS_URL).mock(return_value=_frs_resp())
    respx.get(_ECHO_URL).mock(side_effect=httpx.ConnectError("timeout"))
    respx.get(re.compile(rf"{re.escape(_SEMS_URL_BASE)}.*")).mock(return_value=_cercla_resp())
    respx.get(re.compile(rf"{re.escape(_RCRA_URL_BASE)}.*")).mock(return_value=_rcra_resp())
    respx.get(re.compile(rf"{re.escape(_TRI_URL_BASE)}.*")).mock(return_value=_tri_resp())

    result = await query(CHICAGO_CTX)
    assert result["echo_facilities"] == []
    assert len(result["frs_facilities"]) == 2


@respx.mock
async def test_query_cercla_failure_nonfatal():
    respx.get(_FRS_URL).mock(return_value=_frs_resp())
    respx.get(_ECHO_URL).mock(return_value=_echo_resp())
    respx.get(re.compile(rf"{re.escape(_SEMS_URL_BASE)}.*")).mock(
        side_effect=httpx.ConnectError("timeout")
    )
    respx.get(re.compile(rf"{re.escape(_RCRA_URL_BASE)}.*")).mock(return_value=_rcra_resp())
    respx.get(re.compile(rf"{re.escape(_TRI_URL_BASE)}.*")).mock(return_value=_tri_resp())

    result = await query(CHICAGO_CTX)
    assert result["superfund_sites"] == []
    assert result["flag"] is False
    assert len(result["rcra_handlers"]) == 2   # RCRA still returned


@respx.mock
async def test_query_all_envirofacts_fail_nonfatal():
    respx.get(_FRS_URL).mock(return_value=_frs_resp())
    respx.get(_ECHO_URL).mock(return_value=_echo_resp())
    respx.get(re.compile(rf"{re.escape(_SEMS_URL_BASE)}.*")).mock(
        side_effect=httpx.ConnectError("no route")
    )
    respx.get(re.compile(rf"{re.escape(_RCRA_URL_BASE)}.*")).mock(
        side_effect=httpx.ConnectError("no route")
    )
    respx.get(re.compile(rf"{re.escape(_TRI_URL_BASE)}.*")).mock(
        side_effect=httpx.ConnectError("no route")
    )

    result = await query(CHICAGO_CTX)
    assert result["superfund_sites"] == []
    assert result["rcra_handlers"] == []
    assert result["tri_facilities"] == []
    assert len(result["frs_facilities"]) == 2


@respx.mock
async def test_query_superfund_within_half_mile_flags():
    _mock_all(cercla_lat=41.804, cercla_lon=-87.603)   # ≈0.3 mi from center
    result = await query(CHICAGO_CTX)
    assert result["flag"] is True
    assert result["summary"]["superfund_near_count"] == 1


@respx.mock
async def test_query_superfund_beyond_half_mile_no_flag():
    # Place Superfund ≈ 0.8 miles away from center
    _mock_all(cercla_lat=41.812, cercla_lon=-87.590)
    result = await query(CHICAGO_CTX)
    assert result["flag"] is False
    assert result["summary"]["superfund_near_count"] == 0


@respx.mock
async def test_query_http_500_all_sources_nonfatal():
    respx.get(_FRS_URL).mock(return_value=httpx.Response(500, text="error"))
    respx.get(_ECHO_URL).mock(return_value=httpx.Response(500, text="error"))
    respx.get(re.compile(rf"{re.escape(_SEMS_URL_BASE)}.*")).mock(
        return_value=httpx.Response(500, text="error")
    )
    respx.get(re.compile(rf"{re.escape(_RCRA_URL_BASE)}.*")).mock(
        return_value=httpx.Response(500, text="error")
    )
    respx.get(re.compile(rf"{re.escape(_TRI_URL_BASE)}.*")).mock(
        return_value=httpx.Response(500, text="error")
    )

    result = await query(CHICAGO_CTX)
    assert result["frs_facilities"] == []
    assert result["superfund_sites"] == []
    assert result["flag"] is False


@respx.mock
async def test_query_result_structure():
    _mock_all()
    result = await query(CHICAGO_CTX)

    for key in ("source", "flag", "frs_facilities", "echo_facilities",
                "superfund_sites", "rcra_handlers", "tri_facilities",
                "summary", "display"):
        assert key in result, f"Missing key: {key}"

    for key in ("color_superfund", "color_rcra", "color_tri", "buffer_miles"):
        assert key in result["display"], f"Missing display key: {key}"

    for key in ("frs_count", "echo_violations", "superfund_count",
                "rcra_count", "tri_count", "superfund_flag"):
        assert key in result["summary"], f"Missing summary key: {key}"


@respx.mock
async def test_query_frs_facility_fields_present():
    _mock_all()
    result = await query(CHICAGO_CTX)
    fac = result["frs_facilities"][0]
    for field in ("registry_id", "name", "lat", "lon", "programs", "category", "color"):
        assert field in fac


@respx.mock
async def test_query_echo_facility_fields_present():
    _mock_all()
    result = await query(CHICAGO_CTX)
    fac = result["echo_facilities"][0]
    for field in ("name", "lat", "lon", "compliance_status",
                  "total_violations", "formal_actions", "has_violation"):
        assert field in fac


@respx.mock
async def test_query_superfund_distance_populated():
    _mock_all()
    result = await query(CHICAGO_CTX)
    sf = result["superfund_sites"][0]
    assert sf["distance_miles"] is not None
    assert sf["distance_miles"] > 0


# ── Integration (auto-skipped in sandbox) ─────────────────────────────────────

@pytest.mark.integration
async def test_integration_chicago_epa():
    """Live EPA queries near Chicago — requires network."""
    result = await query(CHICAGO_CTX)
    assert isinstance(result["frs_facilities"], list)
    assert result["source"].startswith("EPA")
