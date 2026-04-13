"""Tests for services/queries/streams.py"""

from __future__ import annotations

import pytest
import respx
import httpx

from services.queries.streams import (
    _BUFFER_M,
    _NHD_BASE,
    _FLOWLINE_LAYER,
    _WATERBODY_LAYER,
    _HIGH_ORDER_THRESHOLD,
    _buffer_bbox,
    _build_summary,
    _parse_flowline,
    _parse_waterbody,
    query,
)
from services.queries.query_runner import QueryContext

# ── Fixtures ──────────────────────────────────────────────────────────────────

NC_CTX = QueryContext(
    site_id="test-nc",
    bbox=(-82.505, 35.495, -82.495, 35.505),
)

_FL_URL = f"{_NHD_BASE}/{_FLOWLINE_LAYER}/query"
_WB_URL = f"{_NHD_BASE}/{_WATERBODY_LAYER}/query"


def _fl_feat(name=None, order=3, ftype=460, length=1.5):
    return {
        "attributes": {
            "GNIS_Name":  name or "",
            "StreamOrde": order,
            "FType":      ftype,
            "FCode":      None,
            "LengthKM":   length,
        }
    }


def _wb_feat(name=None, ftype=390, area=0.5):
    return {
        "attributes": {
            "GNIS_Name": name or "",
            "FType":     ftype,
            "FCode":     None,
            "AreaSqKm":  area,
        }
    }


def _fl_resp(features):
    return {"features": features}


def _wb_resp(features):
    return {"features": features}


# ── _buffer_bbox ──────────────────────────────────────────────────────────────

def test_buffer_bbox_expands_all_sides():
    bbox = (-82.5, 35.5, -82.0, 36.0)
    result = _buffer_bbox(bbox, 1000)
    assert result[0] < -82.5   # minlon shrinks
    assert result[1] < 35.5    # minlat shrinks
    assert result[2] > -82.0   # maxlon grows
    assert result[3] > 36.0    # maxlat grows


def test_buffer_bbox_500ft_magnitude():
    """500 ft ≈ 152.4 m → lat expansion ≈ 0.00137° at mid-latitudes."""
    bbox = (-82.5, 35.5, -82.4, 35.6)
    result = _buffer_bbox(bbox, _BUFFER_M)
    lat_delta = 35.5 - result[1]
    assert 0.001 < lat_delta < 0.002


def test_buffer_bbox_zero_is_identity():
    bbox = (-82.5, 35.5, -82.4, 35.6)
    result = _buffer_bbox(bbox, 0)
    assert result == bbox


def test_buffer_bbox_returns_6_decimal_places():
    bbox = (-82.5, 35.5, -82.4, 35.6)
    result = _buffer_bbox(bbox, 152.4)
    for v in result:
        s = str(v)
        if "." in s:
            assert len(s.split(".")[1]) <= 6


# ── _parse_flowline ───────────────────────────────────────────────────────────

def test_parse_flowline_stream_river():
    attrs = {"GNIS_Name": "French Broad River", "StreamOrde": 7,
             "FType": 460, "LengthKM": 4.8}
    r = _parse_flowline(attrs)
    assert r["name"] == "French Broad River"
    assert r["stream_order"] == 7
    assert r["feature_type"] == "Stream/River"
    assert r["length_km"] == 4.8
    assert r["kind"] == "flowline"
    assert r["color"].startswith("#")


def test_parse_flowline_canal():
    r = _parse_flowline({"GNIS_Name": "", "StreamOrde": 1, "FType": 336, "LengthKM": 0.3})
    assert r["feature_type"] == "Canal/Ditch"
    assert r["name"] is None


def test_parse_flowline_artificial_path():
    r = _parse_flowline({"GNIS_Name": None, "StreamOrde": 2, "FType": 558, "LengthKM": 0.9})
    assert r["feature_type"] == "Artificial Path"


def test_parse_flowline_null_order():
    r = _parse_flowline({"GNIS_Name": None, "StreamOrde": None, "FType": 460, "LengthKM": 0.5})
    assert r["stream_order"] == 0


def test_parse_flowline_missing_fields():
    r = _parse_flowline({})
    assert r["stream_order"] == 0
    assert r["length_km"] == 0.0
    assert r["name"] is None
    assert r["kind"] == "flowline"


# ── _parse_waterbody ──────────────────────────────────────────────────────────

def test_parse_waterbody_reservoir():
    attrs = {"GNIS_Name": "Lake Julian", "FType": 436, "AreaSqKm": 1.23}
    r = _parse_waterbody(attrs)
    assert r["name"] == "Lake Julian"
    assert r["feature_type"] == "Reservoir"
    assert r["area_sqkm"] == 1.23
    assert r["kind"] == "waterbody"


def test_parse_waterbody_lake_pond():
    r = _parse_waterbody({"FType": 390, "AreaSqKm": 0.5})
    assert r["feature_type"] == "Lake/Pond"


def test_parse_waterbody_missing_name_is_none():
    r = _parse_waterbody({"FType": 390, "AreaSqKm": 0.1})
    assert r["name"] is None


def test_parse_waterbody_missing_area_defaults_zero():
    r = _parse_waterbody({"FType": 390})
    assert r["area_sqkm"] == 0.0


# ── _build_summary ─────────────────────────────────────────────────────────────

def test_build_summary_high_order_flag():
    flowlines = [
        _parse_flowline({"GNIS_Name": "French Broad River",
                         "StreamOrde": 7, "FType": 460, "LengthKM": 4.8}),
        _parse_flowline({"GNIS_Name": "Swannanoa River",
                         "StreamOrde": 5, "FType": 460, "LengthKM": 2.1}),
    ]
    s = _build_summary(flowlines, [])
    assert s["high_order_stream"] is True
    assert s["max_stream_order"] == 7
    assert "French Broad River" in s["named_streams"]
    assert 7 in s["stream_orders_present"]
    assert 5 in s["stream_orders_present"]


def test_build_summary_low_order_no_flag():
    flowlines = [_parse_flowline({"GNIS_Name": None, "StreamOrde": 2,
                                   "FType": 460, "LengthKM": 0.4})]
    s = _build_summary(flowlines, [])
    assert s["high_order_stream"] is False
    assert s["max_stream_order"] == 2


def test_build_summary_threshold_exactly_4():
    flowlines = [_parse_flowline({"GNIS_Name": None, "StreamOrde": _HIGH_ORDER_THRESHOLD,
                                   "FType": 460, "LengthKM": 1.0})]
    s = _build_summary(flowlines, [])
    assert s["high_order_stream"] is True


def test_build_summary_empty():
    s = _build_summary([], [])
    assert s["flowline_count"] == 0
    assert s["waterbody_count"] == 0
    assert s["max_stream_order"] == 0
    assert s["total_length_km"] == 0.0
    assert s["high_order_stream"] is False


def test_build_summary_total_length():
    flowlines = [
        _parse_flowline({"GNIS_Name": None, "StreamOrde": 3, "FType": 460, "LengthKM": 1.5}),
        _parse_flowline({"GNIS_Name": None, "StreamOrde": 2, "FType": 460, "LengthKM": 0.7}),
    ]
    s = _build_summary(flowlines, [])
    assert s["total_length_km"] == pytest.approx(2.2)


def test_build_summary_named_waterbodies():
    waterbodies = [_parse_waterbody({"GNIS_Name": "Lake Julian", "FType": 436, "AreaSqKm": 1.2})]
    s = _build_summary([], waterbodies)
    assert "Lake Julian" in s["named_waterbodies"]
    assert s["waterbody_count"] == 1


# ── query() — mocked ──────────────────────────────────────────────────────────

@respx.mock
async def test_query_streams_present_high_order():
    respx.get(_FL_URL).mock(return_value=httpx.Response(200, json=_fl_resp([
        _fl_feat("French Broad River", order=7, ftype=460, length=4.8),
        _fl_feat("Swannanoa River",    order=5, ftype=460, length=2.1),
    ])))
    respx.get(_WB_URL).mock(return_value=httpx.Response(200, json=_wb_resp([
        _wb_feat("Lake Julian", ftype=436, area=1.2),
    ])))

    result = await query(NC_CTX)

    assert result["streams_present"] is True
    assert result["flag"] is True
    assert result["flowline_count"] == 2
    assert result["waterbody_count"] == 1
    assert result["buffer_ft"] == 500
    assert result["summary"]["max_stream_order"] == 7
    assert "display" in result
    assert "wms_url" in result["display"]


@respx.mock
async def test_query_no_streams():
    respx.get(_FL_URL).mock(return_value=httpx.Response(200, json=_fl_resp([])))
    respx.get(_WB_URL).mock(return_value=httpx.Response(200, json=_wb_resp([])))

    result = await query(NC_CTX)
    assert result["streams_present"] is False
    assert result["flag"] is False
    assert result["flowline_count"] == 0


@respx.mock
async def test_query_low_order_no_flag():
    respx.get(_FL_URL).mock(return_value=httpx.Response(200, json=_fl_resp([
        _fl_feat(None, order=2, ftype=460, length=0.4),
        _fl_feat(None, order=1, ftype=460, length=0.2),
    ])))
    respx.get(_WB_URL).mock(return_value=httpx.Response(200, json=_wb_resp([])))

    result = await query(NC_CTX)
    assert result["streams_present"] is True
    assert result["flag"] is False


@respx.mock
async def test_query_waterbody_failure_is_nonfatal():
    """Waterbody HTTP error should not abort the result."""
    respx.get(_FL_URL).mock(return_value=httpx.Response(200, json=_fl_resp([
        _fl_feat("French Broad River", order=7, ftype=460, length=4.8),
    ])))
    respx.get(_WB_URL).mock(side_effect=httpx.ConnectError("timeout"))

    result = await query(NC_CTX)
    assert result["streams_present"] is True
    assert result["flowline_count"] == 1
    assert result["waterbody_count"] == 0  # silently empty


@respx.mock
async def test_query_flowline_failure_raises():
    respx.get(_FL_URL).mock(side_effect=httpx.ConnectError("unreachable"))
    respx.get(_WB_URL).mock(return_value=httpx.Response(200, json=_wb_resp([])))

    with pytest.raises(httpx.ConnectError):
        await query(NC_CTX)


@respx.mock
async def test_query_api_error_in_body():
    respx.get(_FL_URL).mock(return_value=httpx.Response(200, json={
        "error": {"code": 400, "message": "Invalid geometry"}
    }))
    respx.get(_WB_URL).mock(return_value=httpx.Response(200, json=_wb_resp([])))

    with pytest.raises(RuntimeError, match="NHD API error"):
        await query(NC_CTX)


@respx.mock
async def test_query_http_500():
    respx.get(_FL_URL).mock(return_value=httpx.Response(500, text="Internal Server Error"))
    respx.get(_WB_URL).mock(return_value=httpx.Response(200, json=_wb_resp([])))

    with pytest.raises(httpx.HTTPStatusError):
        await query(NC_CTX)


@respx.mock
async def test_query_deduplication():
    """Three identical features should collapse to one."""
    respx.get(_FL_URL).mock(return_value=httpx.Response(200, json=_fl_resp([
        _fl_feat("French Broad River", order=7, ftype=460, length=4.8),
        _fl_feat("French Broad River", order=7, ftype=460, length=4.8),
        _fl_feat("French Broad River", order=7, ftype=460, length=4.8),
    ])))
    respx.get(_WB_URL).mock(return_value=httpx.Response(200, json=_wb_resp([])))

    result = await query(NC_CTX)
    assert result["flowline_count"] == 1


@respx.mock
async def test_query_caps_at_50_flowlines():
    """Result should include at most 50 flowlines."""
    feats = [_fl_feat(f"Stream {i}", order=1, ftype=460, length=0.1) for i in range(80)]
    respx.get(_FL_URL).mock(return_value=httpx.Response(200, json=_fl_resp(feats)))
    respx.get(_WB_URL).mock(return_value=httpx.Response(200, json=_wb_resp([])))

    result = await query(NC_CTX)
    assert len(result["streams"]) <= 50


# ── Integration test (auto-skipped in sandbox) ────────────────────────────────

@pytest.mark.integration
async def test_integration_nc_streams():
    """Live NHD query near Asheville, NC — requires network access."""
    result = await query(NC_CTX)
    assert result["streams_present"] is True
    assert result["flowline_count"] > 0
    assert result["summary"]["max_stream_order"] >= 4
