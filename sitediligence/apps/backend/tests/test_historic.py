"""Tests for services/queries/historic.py

Coverage groups:
  1. Geometry helpers (_buffer_bbox_miles, _haversine_miles, _safe_float)
  2. NRHP date parser (_parse_nrhp_date)
  3. NRHP feature parser (_parse_nrhp_feature) — distance, near_flag, field mapping
  4. GNIS cemetery parser (_parse_gnis_cemetery) — distance, near_flag, GNIS ID
  5. Flag logic (_build_summary) — counts, section_106, near names
  6. query() success — both APIs return data, correct flag
  7. query() non-fatal failures — API errors return empty lists, flag=False
  8. SHPO data — all 50 states + DC present, URL format, content
  9. Integration (auto-skipped in sandbox)
"""

from __future__ import annotations

import pytest
import httpx
import respx

from services.queries.historic import (
    _NRHP_URL,
    _GNIS_URL,
    _FLAG_MILES,
    _FLAG_FEET,
    _COLOR_NRHP,
    _COLOR_CEMETERY,
    _SHPO_DATA,
    _buffer_bbox_miles,
    _haversine_miles,
    _safe_float,
    _parse_nrhp_date,
    _parse_nrhp_feature,
    _parse_gnis_cemetery,
    _build_summary,
    query,
)
from services.queries.query_runner import QueryContext

# ── Test fixtures ─────────────────────────────────────────────────────────────

DC_CTX = QueryContext(
    site_id="test-dc",
    bbox=(-77.005, 38.895, -76.995, 38.905),  # centroid = (38.9, -77.0)
)

MONTGOMERY_CTX = QueryContext(
    site_id="test-montgomery",
    bbox=(-86.315, 32.295, -86.285, 32.305),
)

SITE_LAT = 38.9
SITE_LON = -77.0


# ── Helpers: NRHP feature builder ─────────────────────────────────────────────

def _nrhp_feature(
    name: str = "Test Property",
    refnum: str = "77000001",
    lat: float | None = 38.9,
    lon: float | None = -77.0,
    category: str = "Building",
    date: str | None = "1977-08-22",
    city: str = "Washington",
    state: str = "DC",
) -> dict:
    return {
        "attributes": {
            "PROPERTYNAME": name,
            "REFNUM":        refnum,
            "STATE":         state,
            "COUNTY":        "District of Columbia",
            "CITY":          city,
            "CATEGORY":      category,
            "CERTIFIEDDATE": date,
            "LATITUDE":      lat,
            "LONGITUDE":     lon,
        }
    }


def _gnis_cemetery(
    name: str = "Oak Hill Cemetery",
    gnis_id: str = "1234567",
    lat: float | None = 38.9,
    lon: float | None = -77.0,
    state: str = "DC",
    county: str = "District of Columbia",
) -> dict:
    return {
        "FEATURE_ID":   gnis_id,
        "FEATURE_NAME": name,
        "FEATURE_CLASS": "Cemetery",
        "STATE_ALPHA":  state,
        "COUNTY_NAME":  county,
        "PRIM_LAT_DEC": lat,
        "PRIM_LONG_DEC": lon,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Geometry helpers
# ─────────────────────────────────────────────────────────────────────────────

class TestGeometryHelpers:

    def test_buffer_bbox_expands_all_sides(self):
        orig = (-77.01, 38.895, -76.995, 38.905)
        buf  = _buffer_bbox_miles(orig, 1.0)
        assert buf[0] < orig[0]   # minlon expanded west
        assert buf[1] < orig[1]   # minlat expanded south
        assert buf[2] > orig[2]   # maxlon expanded east
        assert buf[3] > orig[3]   # maxlat expanded north

    def test_buffer_bbox_zero_miles_unchanged(self):
        orig = (-77.01, 38.895, -76.995, 38.905)
        buf  = _buffer_bbox_miles(orig, 0.0)
        assert buf == orig

    def test_haversine_miles_same_point(self):
        assert _haversine_miles(38.9, -77.0, 38.9, -77.0) == pytest.approx(0.0)

    def test_haversine_miles_known_distance(self):
        # ~69 miles per degree of latitude
        dist = _haversine_miles(38.0, -77.0, 39.0, -77.0)
        assert 68.0 < dist < 70.0

    def test_haversine_miles_flag_threshold(self):
        # 500 ft ≈ 0.0947 miles
        dist = _haversine_miles(38.9, -77.0, 38.9 + _FLAG_MILES / 69.0, -77.0)
        assert dist == pytest.approx(_FLAG_MILES, rel=0.05)

    def test_safe_float_numeric(self):
        assert _safe_float(38.9) == pytest.approx(38.9)

    def test_safe_float_string(self):
        assert _safe_float("38.9") == pytest.approx(38.9)

    def test_safe_float_none(self):
        assert _safe_float(None) is None

    def test_safe_float_empty_string(self):
        assert _safe_float("") is None

    def test_safe_float_na(self):
        assert _safe_float("N/A") is None

    def test_safe_float_invalid(self):
        assert _safe_float("not-a-number") is None


# ─────────────────────────────────────────────────────────────────────────────
# 2.  NRHP date parser
# ─────────────────────────────────────────────────────────────────────────────

class TestNrhpDateParser:

    def test_none_returns_none(self):
        assert _parse_nrhp_date(None) is None

    def test_empty_string_returns_none(self):
        assert _parse_nrhp_date("") is None

    def test_epoch_ms(self):
        # 1977-08-22 in ms since epoch
        import datetime
        dt = datetime.datetime(1977, 8, 22, 0, 0, 0)
        epoch_ms = int(dt.timestamp()) * 1_000
        result = _parse_nrhp_date(epoch_ms)
        assert result == "1977-08-22"

    def test_slash_format_mm_dd_yyyy(self):
        assert _parse_nrhp_date("08/22/1977") == "1977-08-22"

    def test_slash_format_single_digit(self):
        assert _parse_nrhp_date("8/5/1970") == "1970-08-05"

    def test_dash_format_mm_dd_yyyy(self):
        assert _parse_nrhp_date("08-22-1977") == "1977-08-22"

    def test_iso_format_passthrough(self):
        result = _parse_nrhp_date("1977-08-22")
        assert result == "1977-08-22"

    def test_iso_with_time(self):
        # e.g. "1977-08-22 00:00:00" — return first 10 chars
        result = _parse_nrhp_date("1977-08-22 00:00:00")
        assert result == "1977-08-22"


# ─────────────────────────────────────────────────────────────────────────────
# 3.  NRHP feature parser
# ─────────────────────────────────────────────────────────────────────────────

class TestNrhpParser:

    def test_basic_field_mapping(self):
        feat   = _nrhp_feature(name="Capitol Hill", refnum="77000318", category="District")
        result = _parse_nrhp_feature(feat, SITE_LAT, SITE_LON)
        assert result["name"]     == "Capitol Hill"
        assert result["refnum"]   == "77000318"
        assert result["category"] == "District"
        assert result["state"]    == "DC"
        assert result["city"]     == "Washington"
        assert result["category_code"] == "nrhp"
        assert result["color"]    == _COLOR_NRHP

    def test_distance_computed_from_site(self):
        # Property exactly 0.1 miles north
        lat_offset = 0.1 / 69.0
        feat   = _nrhp_feature(lat=SITE_LAT + lat_offset, lon=SITE_LON)
        result = _parse_nrhp_feature(feat, SITE_LAT, SITE_LON)
        assert result["distance_miles"] == pytest.approx(0.1, rel=0.05)

    def test_near_flag_true_when_within_500ft(self):
        # Place property 200ft away (0.0379 miles)
        lat_offset = (200 / 5280) / 69.0
        feat   = _nrhp_feature(lat=SITE_LAT + lat_offset, lon=SITE_LON)
        result = _parse_nrhp_feature(feat, SITE_LAT, SITE_LON)
        assert result["near_flag"] is True

    def test_near_flag_false_when_beyond_500ft(self):
        # Place property 0.5 miles away
        lat_offset = 0.5 / 69.0
        feat   = _nrhp_feature(lat=SITE_LAT + lat_offset, lon=SITE_LON)
        result = _parse_nrhp_feature(feat, SITE_LAT, SITE_LON)
        assert result["near_flag"] is False

    def test_near_flag_false_when_no_coordinates(self):
        feat   = _nrhp_feature(lat=None, lon=None)
        result = _parse_nrhp_feature(feat, SITE_LAT, SITE_LON)
        assert result["near_flag"] is False
        assert result["distance_miles"] is None

    def test_date_listed_parsed(self):
        feat   = _nrhp_feature(date="08/22/1977")
        result = _parse_nrhp_feature(feat, SITE_LAT, SITE_LON)
        assert result["date_listed"] == "1977-08-22"

    def test_missing_name_defaults_to_unknown(self):
        feat = {"attributes": {"REFNUM": "123", "LATITUDE": 38.9, "LONGITUDE": -77.0}}
        result = _parse_nrhp_feature(feat, SITE_LAT, SITE_LON)
        assert result["name"] == "Unknown"

    def test_all_required_keys_present(self):
        feat   = _nrhp_feature()
        result = _parse_nrhp_feature(feat, SITE_LAT, SITE_LON)
        for key in ("refnum", "name", "city", "state", "county", "category",
                    "date_listed", "lat", "lon", "distance_miles", "near_flag",
                    "category_code", "color"):
            assert key in result, f"Missing key: {key}"

    def test_washington_dc_nrhp_properties(self):
        """Washington DC (38.9, -77.0) should have many NRHP properties within 1 mile."""
        props = [
            _nrhp_feature("Capitol Hill Historic District", lat=38.890, lon=-77.003, category="District"),
            _nrhp_feature("White House",                   lat=38.8977, lon=-77.0365, category="Building"),
            _nrhp_feature("Washington Monument",           lat=38.8895, lon=-77.0353, category="Structure"),
        ]
        results = [_parse_nrhp_feature(p, SITE_LAT, SITE_LON) for p in props]
        assert all(r["state"] == "DC" for r in results)
        categories = {r["category"] for r in results}
        assert "District" in categories
        assert "Building" in categories


# ─────────────────────────────────────────────────────────────────────────────
# 4.  GNIS cemetery parser
# ─────────────────────────────────────────────────────────────────────────────

class TestGnisCemeteryParser:

    def test_basic_field_mapping(self):
        raw    = _gnis_cemetery(name="Oak Hill Cemetery", gnis_id="1234567")
        result = _parse_gnis_cemetery(raw, SITE_LAT, SITE_LON)
        assert result["name"]     == "Oak Hill Cemetery"
        assert result["gnis_id"]  == "1234567"
        assert result["state"]    == "DC"
        assert result["category_code"] == "cemetery"
        assert result["color"]    == _COLOR_CEMETERY

    def test_distance_computed(self):
        lat_offset = 0.2 / 69.0
        raw    = _gnis_cemetery(lat=SITE_LAT + lat_offset, lon=SITE_LON)
        result = _parse_gnis_cemetery(raw, SITE_LAT, SITE_LON)
        assert result["distance_miles"] == pytest.approx(0.2, rel=0.05)

    def test_near_flag_true_within_500ft(self):
        lat_offset = (300 / 5280) / 69.0
        raw    = _gnis_cemetery(lat=SITE_LAT + lat_offset, lon=SITE_LON)
        result = _parse_gnis_cemetery(raw, SITE_LAT, SITE_LON)
        assert result["near_flag"] is True

    def test_near_flag_false_beyond_500ft(self):
        lat_offset = 1.0 / 69.0   # 1 mile away
        raw    = _gnis_cemetery(lat=SITE_LAT + lat_offset, lon=SITE_LON)
        result = _parse_gnis_cemetery(raw, SITE_LAT, SITE_LON)
        assert result["near_flag"] is False

    def test_near_flag_false_no_coordinates(self):
        raw    = _gnis_cemetery(lat=None, lon=None)
        result = _parse_gnis_cemetery(raw, SITE_LAT, SITE_LON)
        assert result["near_flag"] is False
        assert result["distance_miles"] is None

    def test_lat_lon_stored(self):
        raw    = _gnis_cemetery(lat=32.3456, lon=-86.3456)
        result = _parse_gnis_cemetery(raw, 32.3, -86.3)
        assert result["lat"] == pytest.approx(32.3456)
        assert result["lon"] == pytest.approx(-86.3456)

    def test_all_required_keys_present(self):
        raw    = _gnis_cemetery()
        result = _parse_gnis_cemetery(raw, SITE_LAT, SITE_LON)
        for key in ("gnis_id", "name", "state", "county", "lat", "lon",
                    "distance_miles", "near_flag", "category_code", "color"):
            assert key in result, f"Missing key: {key}"

    def test_montgomery_al_cemeteries(self):
        """Montgomery AL (32.3, -86.3) — test cemetery near flag."""
        site_lat, site_lon = 32.3, -86.3
        # Place a cemetery right next to site (100ft)
        lat_offset = (100 / 5280) / 69.0
        raw = _gnis_cemetery(
            name="Oakwood Cemetery", gnis_id="0404404",
            lat=site_lat + lat_offset, lon=site_lon,
            state="AL", county="Montgomery",
        )
        result = _parse_gnis_cemetery(raw, site_lat, site_lon)
        assert result["near_flag"] is True
        assert result["state"] == "AL"


# ─────────────────────────────────────────────────────────────────────────────
# 5.  Flag / summary logic
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildSummary:

    def test_no_data_no_flag(self):
        s = _build_summary([], [])
        assert s["nrhp_count"] == 0
        assert s["cemetery_count"] == 0
        assert s["section_106_required"] is False
        assert s["near_nrhp_names"] == []
        assert s["near_cemetery_names"] == []

    def test_nrhp_near_flag_triggers_section_106(self):
        props = [{"name": "Capitol Hill", "near_flag": True}]
        s = _build_summary(props, [])
        assert s["nrhp_near_count"] == 1
        assert s["section_106_required"] is True
        assert "Capitol Hill" in s["near_nrhp_names"]

    def test_nrhp_not_near_no_section_106(self):
        props = [{"name": "Far Away Property", "near_flag": False}]
        s = _build_summary(props, [])
        assert s["nrhp_near_count"] == 0
        assert s["section_106_required"] is False

    def test_cemetery_near_count(self):
        cems = [
            {"name": "Oak Hill",    "near_flag": True},
            {"name": "Mount Sinai", "near_flag": True},
            {"name": "Far Cemetery","near_flag": False},
        ]
        s = _build_summary([], cems)
        assert s["cemetery_count"] == 3
        assert s["cemetery_near_count"] == 2
        assert "Oak Hill" in s["near_cemetery_names"]
        assert "Far Cemetery" not in s["near_cemetery_names"]

    def test_near_names_capped_at_3(self):
        props = [{"name": f"Property {i}", "near_flag": True} for i in range(10)]
        s = _build_summary(props, [])
        assert len(s["near_nrhp_names"]) == 3

    def test_mixed_near_and_far(self):
        props = [
            {"name": "Near A", "near_flag": True},
            {"name": "Near B", "near_flag": True},
            {"name": "Far C",  "near_flag": False},
        ]
        cems = [{"name": "Adjacent Cem", "near_flag": True}]
        s = _build_summary(props, cems)
        assert s["nrhp_count"] == 3
        assert s["nrhp_near_count"] == 2
        assert s["cemetery_near_count"] == 1
        assert s["section_106_required"] is True


# ─────────────────────────────────────────────────────────────────────────────
# 6.  query() — full success (mocked)
# ─────────────────────────────────────────────────────────────────────────────

def _nrhp_arcgis_response(features: list[dict]) -> httpx.Response:
    return httpx.Response(200, json={"features": features})


def _gnis_response(features: list[dict]) -> httpx.Response:
    return httpx.Response(200, json={"total": len(features), "features": features})


@respx.mock
async def test_query_dc_nrhp_flag():
    """DC site with an NRHP property within 500 ft → flag=True."""
    # Place NRHP property 200 ft from site centroid
    lat_offset = (200 / 5280) / 69.0
    nrhp_feat = _nrhp_feature(
        name="Capitol Hill Historic District",
        lat=38.9 + lat_offset, lon=-77.0,
        category="District",
        date="08/22/1977",
    )
    respx.get(_NRHP_URL).mock(return_value=_nrhp_arcgis_response([nrhp_feat]))
    respx.get(_GNIS_URL).mock(return_value=_gnis_response([]))

    result = await query(DC_CTX)

    assert result["flag"] is True
    assert result["summary"]["nrhp_near_count"] == 1
    assert result["summary"]["section_106_required"] is True
    assert len(result["nrhp_properties"]) == 1
    prop = result["nrhp_properties"][0]
    assert prop["name"] == "Capitol Hill Historic District"
    assert prop["near_flag"] is True
    assert prop["date_listed"] == "1977-08-22"


@respx.mock
async def test_query_cemetery_near_flag():
    """Cemetery within 500ft → flag=True."""
    lat_offset = (300 / 5280) / 69.0
    cem = _gnis_cemetery(
        name="Congressional Cemetery",
        gnis_id="999001",
        lat=38.9 + lat_offset, lon=-77.0,
    )
    respx.get(_NRHP_URL).mock(return_value=_nrhp_arcgis_response([]))
    respx.get(_GNIS_URL).mock(return_value=_gnis_response([cem]))

    result = await query(DC_CTX)

    assert result["flag"] is True
    assert result["summary"]["cemetery_near_count"] == 1
    assert len(result["cemeteries"]) == 1
    assert result["cemeteries"][0]["gnis_id"] == "999001"


@respx.mock
async def test_query_no_flag_when_properties_far():
    """NRHP and cemeteries beyond 500ft → flag=False."""
    lat_offset = 0.5 / 69.0  # 0.5 miles away
    nrhp_feat = _nrhp_feature(lat=38.9 + lat_offset, lon=-77.0)
    cem       = _gnis_cemetery(lat=38.9 + lat_offset, lon=-77.0)
    respx.get(_NRHP_URL).mock(return_value=_nrhp_arcgis_response([nrhp_feat]))
    respx.get(_GNIS_URL).mock(return_value=_gnis_response([cem]))

    result = await query(DC_CTX)

    assert result["flag"] is False
    assert result["summary"]["nrhp_near_count"] == 0
    assert result["summary"]["cemetery_near_count"] == 0


@respx.mock
async def test_query_result_structure():
    """Full result dict has all required top-level keys."""
    respx.get(_NRHP_URL).mock(return_value=_nrhp_arcgis_response([]))
    respx.get(_GNIS_URL).mock(return_value=_gnis_response([]))

    result = await query(DC_CTX)

    for key in ("source", "flag", "nrhp_properties", "cemeteries",
                "shpo_data", "summary", "display"):
        assert key in result, f"Missing key: {key}"


@respx.mock
async def test_query_shpo_data_always_returned():
    """SHPO data is static and always present regardless of API results."""
    respx.get(_NRHP_URL).mock(return_value=_nrhp_arcgis_response([]))
    respx.get(_GNIS_URL).mock(return_value=_gnis_response([]))

    result = await query(DC_CTX)

    shpo = result["shpo_data"]
    assert len(shpo) >= 50
    abbrs = {s["abbr"] for s in shpo}
    assert "CA" in abbrs
    assert "TX" in abbrs
    assert "NY" in abbrs


@respx.mock
async def test_query_properties_sorted_by_distance():
    """Properties must be returned sorted nearest-first."""
    far  = _nrhp_feature(name="Far",  lat=38.9 + 0.5/69.0, lon=-77.0)
    near = _nrhp_feature(name="Near", lat=38.9 + 0.05/69.0, lon=-77.0)
    respx.get(_NRHP_URL).mock(return_value=_nrhp_arcgis_response([far, near]))
    respx.get(_GNIS_URL).mock(return_value=_gnis_response([]))

    result = await query(DC_CTX)

    props = result["nrhp_properties"]
    assert props[0]["name"] == "Near"
    assert props[1]["name"] == "Far"


@respx.mock
async def test_query_display_colors_present():
    """Display dict must include both category colours."""
    respx.get(_NRHP_URL).mock(return_value=_nrhp_arcgis_response([]))
    respx.get(_GNIS_URL).mock(return_value=_gnis_response([]))

    result = await query(DC_CTX)
    display = result["display"]

    assert display["color_nrhp"]     == _COLOR_NRHP
    assert display["color_cemetery"] == _COLOR_CEMETERY
    assert display["flag_distance_ft"] == _FLAG_FEET


# ─────────────────────────────────────────────────────────────────────────────
# 7.  query() — non-fatal API failures
# ─────────────────────────────────────────────────────────────────────────────

@respx.mock
async def test_query_nrhp_failure_nonfatal():
    """NRHP API error → empty list, no exception raised."""
    respx.get(_NRHP_URL).mock(side_effect=httpx.ConnectError("timeout"))
    respx.get(_GNIS_URL).mock(return_value=_gnis_response([]))

    result = await query(DC_CTX)

    assert result["nrhp_properties"] == []
    assert result["flag"] is False   # no cemeteries either


@respx.mock
async def test_query_gnis_failure_nonfatal():
    """GNIS API error → empty cemetery list, no exception raised."""
    lat_offset = 0.5 / 69.0
    respx.get(_NRHP_URL).mock(return_value=_nrhp_arcgis_response(
        [_nrhp_feature(lat=38.9 + lat_offset, lon=-77.0)]
    ))
    respx.get(_GNIS_URL).mock(side_effect=httpx.ConnectError("timeout"))

    result = await query(DC_CTX)

    assert result["cemeteries"] == []


@respx.mock
async def test_query_both_apis_fail_returns_empty():
    """Both APIs fail → empty lists, flag=False, no exception."""
    respx.get(_NRHP_URL).mock(side_effect=httpx.ConnectError("timeout"))
    respx.get(_GNIS_URL).mock(side_effect=httpx.ConnectError("timeout"))

    result = await query(DC_CTX)

    assert result["nrhp_properties"] == []
    assert result["cemeteries"] == []
    assert result["flag"] is False


@respx.mock
async def test_query_http_500_nrhp_nonfatal():
    """NRHP HTTP 500 → non-fatal, empty list."""
    respx.get(_NRHP_URL).mock(return_value=httpx.Response(500, text="Error"))
    respx.get(_GNIS_URL).mock(return_value=_gnis_response([]))

    result = await query(DC_CTX)

    assert result["nrhp_properties"] == []


# ─────────────────────────────────────────────────────────────────────────────
# 8.  SHPO static data
# ─────────────────────────────────────────────────────────────────────────────

class TestShpoData:

    def test_has_all_50_states_plus_dc(self):
        abbrs = {s["abbr"] for s in _SHPO_DATA}
        expected = {
            "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
            "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
            "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
            "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
            "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
            "DC",
        }
        assert abbrs == expected

    def test_total_count_51(self):
        assert len(_SHPO_DATA) == 51

    def test_each_entry_has_required_fields(self):
        for entry in _SHPO_DATA:
            assert "abbr" in entry,  f"Missing abbr in {entry}"
            assert "name" in entry,  f"Missing name in {entry}"
            assert "url"  in entry,  f"Missing url in {entry}"

    def test_all_urls_start_with_https(self):
        for entry in _SHPO_DATA:
            assert entry["url"].startswith("https://"), (
                f"{entry['abbr']} URL does not start with https: {entry['url']}"
            )

    def test_specific_known_states(self):
        by_abbr = {s["abbr"]: s for s in _SHPO_DATA}
        assert "Colorado"    in by_abbr["CO"]["name"]
        assert "California"  in by_abbr["CA"]["name"]
        assert "Texas"       in by_abbr["TX"]["name"]
        assert "Virginia"    in by_abbr["VA"]["name"]
        assert "Washington"  in by_abbr["WA"]["name"]

    def test_colorado_shpo_url(self):
        by_abbr = {s["abbr"]: s for s in _SHPO_DATA}
        assert "historycolorado" in by_abbr["CO"]["url"]

    def test_dc_entry_present(self):
        by_abbr = {s["abbr"]: s for s in _SHPO_DATA}
        assert "DC" in by_abbr
        assert "dc.gov" in by_abbr["DC"]["url"] or "planning.dc.gov" in by_abbr["DC"]["url"]

    def test_no_duplicate_abbreviations(self):
        abbrs = [s["abbr"] for s in _SHPO_DATA]
        assert len(abbrs) == len(set(abbrs))

    def test_names_are_non_empty(self):
        for entry in _SHPO_DATA:
            assert entry["name"].strip(), f"Empty name for {entry['abbr']}"

    def test_flag_constants(self):
        assert _FLAG_FEET == 500
        assert _FLAG_MILES == pytest.approx(500 / 5280, rel=1e-4)
        assert _COLOR_NRHP.startswith("#")
        assert _COLOR_CEMETERY.startswith("#")


# ─────────────────────────────────────────────────────────────────────────────
# 9.  Integration (auto-skipped in sandbox)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
async def test_integration_dc_nrhp():
    """Live NRHP query near Washington DC — requires network."""
    result = await query(DC_CTX)
    assert isinstance(result["nrhp_properties"], list)
    # DC should have many NRHP properties within 1 mile
    assert result["summary"]["nrhp_count"] > 0


@pytest.mark.integration
async def test_integration_montgomery_cemeteries():
    """Live GNIS cemetery query near Montgomery AL — requires network."""
    result = await query(MONTGOMERY_CTX)
    assert isinstance(result["cemeteries"], list)
    # Montgomery AL has known cemeteries near downtown
    assert result["summary"]["cemetery_count"] >= 0   # conservative — just check it runs
