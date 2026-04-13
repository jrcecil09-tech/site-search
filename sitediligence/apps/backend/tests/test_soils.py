"""Tests for services/queries/soils.py"""

from __future__ import annotations

import pytest
import respx
import httpx

from services.queries.soils import (
    _SDA_URL,
    _bbox_to_wkt,
    _parse_sda_table,
    _is_hydric,
    _choose_color,
    _build_map_units,
    _build_summary,
    _HYDRIC_COLOR,
    _DEFAULT_COLOR,
    _DRAINAGE_COLORS,
    query,
)
from services.queries.query_runner import QueryContext

# ── Fixtures ──────────────────────────────────────────────────────────────────

OKLAHOMA_CTX = QueryContext(
    site_id="test-oklahoma",
    bbox=(-97.405, 35.195, -97.395, 35.205),
)

# Minimal SDA table responses used by multiple tests
_COMP_TABLE_HEADERS = [
    "mukey", "musym", "muname", "muacres",
    "cokey", "compname", "comppct_r", "majcompflag",
    "drainagecl", "hydricrating", "farmlndcl",
    "taxclname", "taxorder", "taxsubgrp",
]

_INTERP_TABLE_HEADERS = ["cokey", "mukey", "corr_steel", "corr_concrete", "uscs_class"]


def _make_comp_resp(rows: list[list]) -> dict:
    return {"Table": [_COMP_TABLE_HEADERS] + rows}


def _make_interp_resp(rows: list[list]) -> dict:
    return {"Table": [_INTERP_TABLE_HEADERS] + rows}


def _empty_resp() -> dict:
    return {"Table": []}


# ── _bbox_to_wkt ──────────────────────────────────────────────────────────────

def test_bbox_to_wkt_basic():
    wkt = _bbox_to_wkt((-97.405, 35.195, -97.395, 35.205))
    assert wkt.startswith("POLYGON((")
    assert wkt.endswith("))")


def test_bbox_to_wkt_closes_ring():
    wkt = _bbox_to_wkt((-97.405, 35.195, -97.395, 35.205))
    coords_part = wkt[len("POLYGON(("):-2]
    pairs = [p.strip() for p in coords_part.split(",")]
    assert pairs[0] == pairs[-1], "WKT ring must be closed"


def test_bbox_to_wkt_contains_all_four_corners():
    minlon, minlat, maxlon, maxlat = -97.405, 35.195, -97.395, 35.205
    wkt = _bbox_to_wkt((minlon, minlat, maxlon, maxlat))
    assert str(minlon) in wkt
    assert str(maxlon) in wkt
    assert str(minlat) in wkt
    assert str(maxlat) in wkt


# ── _parse_sda_table ──────────────────────────────────────────────────────────

def test_parse_sda_table_basic():
    data = {"Table": [["mukey", "muname"], ["12345", "Norge loam"]]}
    rows = _parse_sda_table(data)
    assert len(rows) == 1
    assert rows[0]["mukey"] == "12345"
    assert rows[0]["muname"] == "Norge loam"


def test_parse_sda_table_empty_table():
    assert _parse_sda_table({"Table": []}) == []


def test_parse_sda_table_header_only():
    assert _parse_sda_table({"Table": [["col1", "col2"]]}) == []


def test_parse_sda_table_null_table():
    assert _parse_sda_table({"Table": None}) == []


def test_parse_sda_table_missing_key():
    assert _parse_sda_table({}) == []


def test_parse_sda_table_multiple_rows():
    data = {"Table": [["a", "b"], [1, 2], [3, 4]]}
    rows = _parse_sda_table(data)
    assert len(rows) == 2
    assert rows[1]["a"] == 3


def test_parse_sda_table_headers_lowercased():
    data = {"Table": [["MuKey", "MuName"], ["1", "Test"]]}
    rows = _parse_sda_table(data)
    assert "mukey" in rows[0]
    assert "muname" in rows[0]


# ── _is_hydric ────────────────────────────────────────────────────────────────

def test_is_hydric_yes():
    assert _is_hydric("Yes") is True


def test_is_hydric_all():
    assert _is_hydric("All") is True


def test_is_hydric_case_insensitive():
    assert _is_hydric("YES") is True
    assert _is_hydric("yes") is True


def test_is_hydric_no():
    assert _is_hydric("No") is False


def test_is_hydric_unranked():
    assert _is_hydric("Unranked") is False


def test_is_hydric_none():
    assert _is_hydric(None) is False


def test_is_hydric_empty():
    assert _is_hydric("") is False


# ── _choose_color ─────────────────────────────────────────────────────────────

def test_choose_color_hydric_overrides_drainage():
    color = _choose_color("Well drained", is_hydric_soil=True)
    assert color == _HYDRIC_COLOR


def test_choose_color_well_drained():
    color = _choose_color("Well drained", is_hydric_soil=False)
    assert color == _DRAINAGE_COLORS["Well drained"]


def test_choose_color_poorly_drained():
    color = _choose_color("Poorly drained", is_hydric_soil=False)
    assert color == _DRAINAGE_COLORS["Poorly drained"]


def test_choose_color_unknown_drainage():
    color = _choose_color("Unknown class", is_hydric_soil=False)
    assert color == _DEFAULT_COLOR


def test_choose_color_none_drainage():
    color = _choose_color(None, is_hydric_soil=False)
    assert color == _DEFAULT_COLOR


# ── _build_map_units ──────────────────────────────────────────────────────────

def _sample_comp_rows() -> list[dict]:
    return [
        {
            "mukey": "1001", "musym": "No", "muname": "Norge loam", "muacres": 45.0,
            "cokey": "c001", "compname": "Norge", "comppct_r": 80, "majcompflag": "Yes",
            "drainagecl": "Well drained", "hydricrating": "No", "farmlndcl": "Prime farmland",
            "taxclname": "Fine-silty, mixed, superactive, mesic Udic Haplustolls",
            "taxorder": "Mollisols", "taxsubgrp": "Udic Haplustolls",
        },
        {
            "mukey": "1001", "musym": "No", "muname": "Norge loam", "muacres": 45.0,
            "cokey": "c002", "compname": "Bethany", "comppct_r": 15, "majcompflag": "No",
            "drainagecl": "Moderately well drained", "hydricrating": "No", "farmlndcl": None,
            "taxclname": None, "taxorder": None, "taxsubgrp": None,
        },
        {
            "mukey": "1002", "musym": "Gg", "muname": "Gracemont fine sandy loam", "muacres": 12.0,
            "cokey": "c003", "compname": "Gracemont", "comppct_r": 90, "majcompflag": "Yes",
            "drainagecl": "Somewhat poorly drained", "hydricrating": "Yes", "farmlndcl": None,
            "taxclname": "Coarse-loamy, mixed, superactive, nonacid, thermic Oxyaquic Ustifluvents",
            "taxorder": "Entisols", "taxsubgrp": "Oxyaquic Ustifluvents",
        },
    ]


def test_build_map_units_count():
    result = _build_map_units(_sample_comp_rows(), {})
    assert len(result) == 2


def test_build_map_units_hydric_detected():
    result = _build_map_units(_sample_comp_rows(), {})
    gracemont = next(mu for mu in result if mu["mukey"] == "1002")
    assert gracemont["hydric"] is True


def test_build_map_units_non_hydric():
    result = _build_map_units(_sample_comp_rows(), {})
    norge = next(mu for mu in result if mu["mukey"] == "1001")
    assert norge["hydric"] is False


def test_build_map_units_dominant_component():
    result = _build_map_units(_sample_comp_rows(), {})
    norge = next(mu for mu in result if mu["mukey"] == "1001")
    assert norge["dominant_component"] == "Norge"
    assert norge["dominant_pct"] == 80


def test_build_map_units_hydric_color():
    result = _build_map_units(_sample_comp_rows(), {})
    gracemont = next(mu for mu in result if mu["mukey"] == "1002")
    assert gracemont["color"] == _HYDRIC_COLOR


def test_build_map_units_well_drained_color():
    result = _build_map_units(_sample_comp_rows(), {})
    norge = next(mu for mu in result if mu["mukey"] == "1001")
    assert norge["color"] == _DRAINAGE_COLORS["Well drained"]


def test_build_map_units_engineering_interps_merged():
    interp_by_cokey = {
        "c001": {"corr_steel": "Low", "corr_concrete": "High", "uscs_class": "SC-SM"},
    }
    result = _build_map_units(_sample_comp_rows(), interp_by_cokey)
    norge = next(mu for mu in result if mu["mukey"] == "1001")
    assert norge["corr_steel"] == "Low"
    assert norge["corr_concrete"] == "High"
    assert norge["uscs_class"] == "SC-SM"


def test_build_map_units_missing_interps_are_none():
    result = _build_map_units(_sample_comp_rows(), {})
    norge = next(mu for mu in result if mu["mukey"] == "1001")
    assert norge["corr_steel"] is None
    assert norge["corr_concrete"] is None


def test_build_map_units_components_list_present():
    result = _build_map_units(_sample_comp_rows(), {})
    norge = next(mu for mu in result if mu["mukey"] == "1001")
    assert len(norge["components"]) == 2


def test_build_map_units_empty_rows():
    assert _build_map_units([], {}) == []


# ── _build_summary ────────────────────────────────────────────────────────────

def test_build_summary_hydric_count():
    mus = [
        {"hydric": True,  "muname": "Gracemont", "drainage_class": "Somewhat poorly drained"},
        {"hydric": False, "muname": "Norge",      "drainage_class": "Well drained"},
    ]
    s = _build_summary(mus)
    assert s["hydric_unit_count"] == 1
    assert s["hydric_present"] is True


def test_build_summary_no_hydric():
    mus = [{"hydric": False, "muname": "Norge", "drainage_class": "Well drained"}]
    s = _build_summary(mus)
    assert s["hydric_present"] is False
    assert s["hydric_unit_count"] == 0


def test_build_summary_drainage_classes():
    mus = [
        {"hydric": False, "muname": "A", "drainage_class": "Well drained"},
        {"hydric": False, "muname": "B", "drainage_class": "Well drained"},
        {"hydric": True,  "muname": "C", "drainage_class": "Poorly drained"},
    ]
    s = _build_summary(mus)
    assert s["drainage_classes"]["Well drained"] == 2
    assert s["drainage_classes"]["Poorly drained"] == 1


def test_build_summary_hydric_names_capped_at_5():
    mus = [{"hydric": True, "muname": f"Unit {i}", "drainage_class": None} for i in range(10)]
    s = _build_summary(mus)
    assert len(s["hydric_unit_names"]) == 5


# ── query() — mocked ──────────────────────────────────────────────────────────

def _comp_ok_resp() -> httpx.Response:
    return httpx.Response(200, json=_make_comp_resp([
        ["1001", "No", "Norge loam", 45.0,
         "c001", "Norge", 80, "Yes",
         "Well drained", "No", "Prime farmland",
         "Fine-silty, mixed, superactive, mesic Udic Haplustolls",
         "Mollisols", "Udic Haplustolls"],
        ["1002", "Gg", "Gracemont fine sandy loam", 12.0,
         "c003", "Gracemont", 90, "Yes",
         "Somewhat poorly drained", "Yes", None,
         "Coarse-loamy, mixed, superactive, nonacid, thermic Oxyaquic Ustifluvents",
         "Entisols", "Oxyaquic Ustifluvents"],
    ]))


def _interp_ok_resp() -> httpx.Response:
    return httpx.Response(200, json=_make_interp_resp([
        ["c001", "1001", "Low", "High",  "SC-SM"],
        ["c003", "1002", "High", "High", "SM"],
    ]))


@respx.mock
async def test_query_full_success():
    respx.post(_SDA_URL).mock(side_effect=[_comp_ok_resp(), _interp_ok_resp()])

    result = await query(OKLAHOMA_CTX)

    assert result["source"].startswith("NRCS")
    assert result["map_unit_count"] == 2
    assert result["hydric_present"] is True
    assert result["hydric_count"] == 1
    assert result["flag"] is True
    assert len(result["map_units"]) == 2


@respx.mock
async def test_query_no_map_units():
    respx.post(_SDA_URL).mock(side_effect=[
        httpx.Response(200, json=_empty_resp()),
        httpx.Response(200, json=_empty_resp()),
    ])

    result = await query(OKLAHOMA_CTX)
    assert result["map_unit_count"] == 0
    assert result["hydric_present"] is False
    assert result["flag"] is False
    assert result["map_units"] == []


@respx.mock
async def test_query_no_hydric():
    respx.post(_SDA_URL).mock(side_effect=[
        httpx.Response(200, json=_make_comp_resp([
            ["1001", "No", "Norge loam", 45.0,
             "c001", "Norge", 80, "Yes",
             "Well drained", "No", "Prime farmland",
             None, "Mollisols", None],
        ])),
        httpx.Response(200, json=_empty_resp()),
    ])

    result = await query(OKLAHOMA_CTX)
    assert result["hydric_present"] is False
    assert result["flag"] is False


@respx.mock
async def test_query_interp_failure_is_nonfatal():
    """Engineering interps failure should not abort the result."""
    respx.post(_SDA_URL).mock(side_effect=[
        _comp_ok_resp(),
        httpx.ConnectError("timeout"),
    ])

    result = await query(OKLAHOMA_CTX)
    assert result["map_unit_count"] == 2
    # Interp fields should be None but units should be present
    norge = next(mu for mu in result["map_units"] if mu["mukey"] == "1001")
    assert norge["corr_steel"] is None


@respx.mock
async def test_query_comp_failure_raises():
    """Components query failure should propagate."""
    respx.post(_SDA_URL).mock(side_effect=httpx.ConnectError("unreachable"))

    with pytest.raises(httpx.ConnectError):
        await query(OKLAHOMA_CTX)


@respx.mock
async def test_query_http_500_raises():
    respx.post(_SDA_URL).mock(return_value=httpx.Response(500, text="Server Error"))

    with pytest.raises(httpx.HTTPStatusError):
        await query(OKLAHOMA_CTX)


@respx.mock
async def test_query_result_structure():
    respx.post(_SDA_URL).mock(side_effect=[_comp_ok_resp(), _interp_ok_resp()])

    result = await query(OKLAHOMA_CTX)
    assert "summary" in result
    assert "display" in result
    assert "wms_url" in result["display"]
    assert "wms_layer" in result["display"]


@respx.mock
async def test_query_engineering_interps_on_dominant():
    respx.post(_SDA_URL).mock(side_effect=[_comp_ok_resp(), _interp_ok_resp()])

    result = await query(OKLAHOMA_CTX)
    norge = next(mu for mu in result["map_units"] if mu["mukey"] == "1001")
    assert norge["corr_steel"] == "Low"
    assert norge["corr_concrete"] == "High"
    assert norge["uscs_class"] == "SC-SM"


@respx.mock
async def test_query_map_unit_fields_present():
    respx.post(_SDA_URL).mock(side_effect=[_comp_ok_resp(), _interp_ok_resp()])

    result = await query(OKLAHOMA_CTX)
    mu = result["map_units"][0]
    for field in ("mukey", "musym", "muname", "hydric", "drainage_class",
                  "hydric_rating", "farmland_class", "dominant_component",
                  "corr_steel", "corr_concrete", "color", "components"):
        assert field in mu, f"Missing field: {field}"


# ── Integration (auto-skipped in sandbox) ─────────────────────────────────────

@pytest.mark.integration
async def test_integration_oklahoma_soils():
    """Live SDA query near Chickasha, OK — requires network."""
    result = await query(OKLAHOMA_CTX)
    assert isinstance(result["map_units"], list)
    assert result["source"].startswith("NRCS")
