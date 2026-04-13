"""Tests for services/queries/elevation.py"""

from __future__ import annotations

import math

import numpy as np
import pytest
import respx
import httpx

from services.queries.elevation import (
    _GRID_N,
    _FT_TO_M,
    _build_grid,
    _compute_stats,
    _generate_contours,
    _marching_squares_segments,
    _SAMPLES_URL,
    _TNM_PRODUCTS,
    query,
)
from services.queries.query_runner import QueryContext

# ── Fixtures ──────────────────────────────────────────────────────────────────

DENVER_CTX = QueryContext(
    site_id="test-denver",
    bbox=(-104.905, 39.695, -104.895, 39.705),
)

# A simple flat 11×11 grid all at 5280 ft (Denver "mile high")
_FLAT_SAMPLES = [5280.0] * (_GRID_N * _GRID_N)

# A sloped 11×11 grid: rises 10ft across the x-axis
_SLOPED_SAMPLES = [
    5280.0 + (i % _GRID_N) * 1.0
    for i in range(_GRID_N * _GRID_N)
]

def _samples_resp(values: list[float]) -> dict:
    return {
        "samples": [
            {"attributes": {"Pixel Value": str(v)}}
            for v in values
        ]
    }

def _tnm_resp(n: int = 2) -> dict:
    return {
        "items": [
            {
                "title": f"USGS 1/3 Arc Second DEM Tile {i+1}",
                "downloadURL": f"https://prd-tnm.s3.amazonaws.com/tile{i+1}.zip",
                "sizeInBytes": 15_728_640,
                "publicationDate": "2020-01-01",
            }
            for i in range(n)
        ]
    }


# ── _build_grid ────────────────────────────────────────────────────────────────

def test_build_grid_count():
    pts = _build_grid(DENVER_CTX.bbox, 11)
    assert len(pts) == 121


def test_build_grid_corners_within_bbox():
    minlon, minlat, maxlon, maxlat = DENVER_CTX.bbox
    pts = _build_grid(DENVER_CTX.bbox, 11)
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    assert min(lons) >= minlon
    assert max(lons) <= maxlon
    assert min(lats) >= minlat
    assert max(lats) <= maxlat


def test_build_grid_includes_center():
    pts = _build_grid(DENVER_CTX.bbox, 11)
    center_idx = 60  # middle of 11×11
    lon, lat = pts[center_idx]
    cx = (DENVER_CTX.bbox[0] + DENVER_CTX.bbox[2]) / 2
    cy = (DENVER_CTX.bbox[1] + DENVER_CTX.bbox[3]) / 2
    assert abs(lon - cx) < 0.001
    assert abs(lat - cy) < 0.001


def test_build_grid_custom_n():
    pts = _build_grid(DENVER_CTX.bbox, 5)
    assert len(pts) == 25


# ── _compute_stats ─────────────────────────────────────────────────────────────

def test_compute_stats_flat_grid():
    stats = _compute_stats([5280.0] * 121, 11, DENVER_CTX.bbox)
    assert stats["min_ft"] == 5280.0
    assert stats["max_ft"] == 5280.0
    assert stats["mean_ft"] == 5280.0
    assert stats["relief_ft"] == 0.0
    assert stats["slope_max_deg"] == pytest.approx(0.0, abs=0.1)


def test_compute_stats_converts_to_meters():
    stats = _compute_stats([5280.0] * 121, 11, DENVER_CTX.bbox)
    assert stats["min_m"] == pytest.approx(5280.0 * _FT_TO_M, rel=1e-3)
    assert stats["max_m"] == pytest.approx(5280.0 * _FT_TO_M, rel=1e-3)
    assert stats["mean_m"] == pytest.approx(5280.0 * _FT_TO_M, rel=1e-3)


def test_compute_stats_relief():
    values = [5280.0 if i < 60 else 5290.0 for i in range(121)]
    stats = _compute_stats(values, 11, DENVER_CTX.bbox)
    assert stats["relief_ft"] == pytest.approx(10.0)


def test_compute_stats_slope_detected():
    """A sloped grid should have non-zero slope."""
    stats = _compute_stats(_SLOPED_SAMPLES, 11, DENVER_CTX.bbox)
    assert stats["slope_max_deg"] > 0.0


def test_compute_stats_empty():
    stats = _compute_stats([], 11, DENVER_CTX.bbox)
    assert stats["min_ft"] is None
    assert stats["max_ft"] is None
    assert stats["slope_min_deg"] is None


# ── _marching_squares_segments ────────────────────────────────────────────────

def test_marching_squares_flat_returns_empty():
    grid = np.full((10, 10), 5280.0)
    lons = np.linspace(-105.0, -104.9, 10)
    lats = np.linspace(39.6, 39.7, 10)
    segs = _marching_squares_segments(grid, 5285.0, lons, lats)
    assert segs == []


def test_marching_squares_step_produces_segments():
    """Grid that steps from 5280 to 5290 should yield segments at 5285."""
    grid = np.zeros((10, 10))
    grid[:, :5] = 5280.0
    grid[:, 5:] = 5290.0
    lons = np.linspace(-105.0, -104.9, 10)
    lats = np.linspace(39.6, 39.7, 10)
    segs = _marching_squares_segments(grid, 5285.0, lons, lats)
    assert len(segs) > 0
    # Each segment should have exactly 2 coordinate pairs
    for seg in segs:
        assert len(seg) == 2


def test_marching_squares_segment_coordinates_in_bbox():
    grid = np.zeros((10, 10))
    grid[:, :5] = 5280.0
    grid[:, 5:] = 5290.0
    lons = np.linspace(-105.0, -104.9, 10)
    lats = np.linspace(39.6, 39.7, 10)
    segs = _marching_squares_segments(grid, 5285.0, lons, lats)
    for seg in segs:
        for pt in seg:
            lon, lat = pt
            assert -105.0 <= lon <= -104.9
            assert 39.6 <= lat <= 39.7


# ── _generate_contours ─────────────────────────────────────────────────────────

def test_generate_contours_returns_three_intervals():
    pts = _build_grid(DENVER_CTX.bbox, 11)
    contours = _generate_contours(pts, _SLOPED_SAMPLES, DENVER_CTX.bbox)
    assert len(contours) == 3
    intervals = {c["interval_ft"] for c in contours}
    assert intervals == {1, 2, 5}


def test_generate_contours_flat_no_features():
    """Flat terrain → no elevation change → no contour features."""
    pts = _build_grid(DENVER_CTX.bbox, 11)
    contours = _generate_contours(pts, _FLAT_SAMPLES, DENVER_CTX.bbox)
    for c in contours:
        assert c["features"] == []


def test_generate_contours_too_few_points_returns_empty():
    pts = [(0.0, 0.0), (1.0, 1.0)]
    contours = _generate_contours(pts, [100.0, 110.0], DENVER_CTX.bbox)
    assert contours == []


def test_generate_contours_have_color_and_dash():
    pts = _build_grid(DENVER_CTX.bbox, 11)
    contours = _generate_contours(pts, _SLOPED_SAMPLES, DENVER_CTX.bbox)
    for c in contours:
        assert "color" in c
        assert "dash" in c
        assert c["color"].startswith("#")


# ── query() — mocked ──────────────────────────────────────────────────────────

@respx.mock
async def test_query_full_success():
    respx.post(_SAMPLES_URL).mock(return_value=httpx.Response(
        200, json=_samples_resp(_SLOPED_SAMPLES)
    ))
    respx.get(_TNM_PRODUCTS).mock(return_value=httpx.Response(
        200, json=_tnm_resp(2)
    ))

    result = await query(DENVER_CTX)

    assert result["source"].startswith("USGS 3DEP")
    assert result["sample_count"] == 121
    assert result["stats"]["min_ft"] is not None
    assert result["stats"]["max_ft"] >= result["stats"]["min_ft"]
    assert result["stats"]["mean_m"] > 0
    assert result["stats"]["slope_max_deg"] >= 0
    assert len(result["contours"]) == 3
    assert len(result["dem_downloads"]) == 2
    assert result["dem_downloads"][0]["download_url"].startswith("https://")
    assert result["flag"] is False


@respx.mock
async def test_query_flat_terrain():
    respx.post(_SAMPLES_URL).mock(return_value=httpx.Response(
        200, json=_samples_resp(_FLAT_SAMPLES)
    ))
    respx.get(_TNM_PRODUCTS).mock(return_value=httpx.Response(
        200, json=_tnm_resp(0)
    ))

    result = await query(DENVER_CTX)
    assert result["stats"]["relief_ft"] == 0.0
    assert result["stats"]["slope_max_deg"] == pytest.approx(0.0, abs=0.1)
    assert result["dem_downloads"] == []


@respx.mock
async def test_query_tnm_failure_is_nonfatal():
    """TNM products error should not abort the result."""
    respx.post(_SAMPLES_URL).mock(return_value=httpx.Response(
        200, json=_samples_resp(_SLOPED_SAMPLES)
    ))
    respx.get(_TNM_PRODUCTS).mock(side_effect=httpx.ConnectError("timeout"))

    result = await query(DENVER_CTX)
    assert result["stats"]["min_ft"] is not None
    assert result["dem_downloads"] == []


@respx.mock
async def test_query_samples_failure_raises():
    respx.post(_SAMPLES_URL).mock(side_effect=httpx.ConnectError("unreachable"))
    respx.get(_TNM_PRODUCTS).mock(return_value=httpx.Response(200, json=_tnm_resp()))

    with pytest.raises(httpx.ConnectError):
        await query(DENVER_CTX)


@respx.mock
async def test_query_api_error_in_body():
    respx.post(_SAMPLES_URL).mock(return_value=httpx.Response(200, json={
        "error": {"code": 400, "message": "Bad geometry"}
    }))
    respx.get(_TNM_PRODUCTS).mock(return_value=httpx.Response(200, json=_tnm_resp()))

    with pytest.raises(RuntimeError, match="3DEP ImageServer error"):
        await query(DENVER_CTX)


@respx.mock
async def test_query_http_500():
    respx.post(_SAMPLES_URL).mock(return_value=httpx.Response(500, text="Server Error"))
    respx.get(_TNM_PRODUCTS).mock(return_value=httpx.Response(200, json=_tnm_resp()))

    with pytest.raises(httpx.HTTPStatusError):
        await query(DENVER_CTX)


@respx.mock
async def test_query_centroid_elevation_present():
    respx.post(_SAMPLES_URL).mock(return_value=httpx.Response(
        200, json=_samples_resp(_FLAT_SAMPLES)
    ))
    respx.get(_TNM_PRODUCTS).mock(return_value=httpx.Response(200, json=_tnm_resp()))

    result = await query(DENVER_CTX)
    assert result["centroid_elevation_ft"] == pytest.approx(5280.0)
    assert result["centroid_elevation_m"] == pytest.approx(5280.0 * _FT_TO_M, rel=1e-3)


@respx.mock
async def test_query_nodata_samples_handled():
    """NoData pixels should be filtered, not crash the stats."""
    mixed = _FLAT_SAMPLES[:60] + [None] * 61
    respx.post(_SAMPLES_URL).mock(return_value=httpx.Response(200, json={
        "samples": [
            {"attributes": {"Pixel Value": str(v) if v is not None else "NoData"}}
            for v in mixed
        ]
    }))
    respx.get(_TNM_PRODUCTS).mock(return_value=httpx.Response(200, json=_tnm_resp()))

    result = await query(DENVER_CTX)
    assert result["stats"]["min_ft"] == pytest.approx(5280.0)


# ── Integration (auto-skipped in sandbox) ─────────────────────────────────────

@pytest.mark.integration
async def test_integration_denver_elevation():
    """Live 3DEP query near Denver — requires network."""
    result = await query(DENVER_CTX)
    assert result["centroid_elevation_ft"] is not None
    # Denver is ~5280 ft / ~1609 m — allow ±500 ft for local variation
    assert 4800 < result["centroid_elevation_ft"] < 5800
    assert result["stats"]["min_ft"] is not None
