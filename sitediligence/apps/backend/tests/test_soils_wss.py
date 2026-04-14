"""Tests for the comprehensive NRCS Web Soil Survey (WSS) module.

Coverage groups:
  1. Spatial helpers  — _bbox_to_wfs_filter, _is_lat_lon_first,
                        _pos_list_to_coords, _parse_wfs_gml, get_soil_polygons
  2. Tabular helpers  — _fmt_mukeys, _parse_sda, get_all_tabular fatal/non-fatal
  3. Hydric flag      — hydricrating detection, apply_flags, process_all
  4. Restrictive layer detection — shallow (<24 in) FLAG, moderate (24–60 in) REVIEW
  5. File downloads   — save_geojson, save_csv, create_shapefile_zip
  6. Flag rule engine — lep_r, organic soils (PT/OH/OL), flood, corr, bearing, slope, survey
  7. CAD export       — export_soils_to_dxf layer names and entity presence
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import httpx
import pytest
import respx

import services.queries.soils_downloader as dl
from services.exporters.cad import export_soils_to_dxf
from services.queries.query_runner import QueryContext
from services.queries.soils_downloader import (
    create_shapefile_zip,
    save_csv,
    save_geojson,
)
from services.queries.soils_spatial import (
    _WFS_URL,
    _bbox_to_wfs_filter,
    _is_lat_lon_first,
    _parse_wfs_gml,
    _pos_list_to_coords,
    get_soil_polygons,
)
from services.queries.soils_tabular import (
    _SDA_URL,
    _fmt_mukeys,
    _parse_sda,
    get_all_tabular,
)
from utils.soils_parser import (
    FLAG_FLAG,
    FLAG_INFO,
    FLAG_PASS,
    FLAG_REVIEW,
    apply_flags,
    build_summary_row,
    process_all,
)


# ── Common fixtures ────────────────────────────────────────────────────────────

OKLAHOMA_CTX = QueryContext(
    site_id="test-oklahoma-wss",
    bbox=(-97.405, 35.195, -97.395, 35.205),
)

# Minimal GeoJSON FeatureCollection with one polygon
_SIMPLE_FC: dict = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-97.405, 35.195],
                        [-97.395, 35.195],
                        [-97.395, 35.205],
                        [-97.405, 35.205],
                        [-97.405, 35.195],
                    ]
                ],
            },
            "properties": {"mukey": "490709", "musym": "NoA", "areasymbol": "OK001"},
        }
    ],
}

# Minimal WFS GML (EPSG:4326 short form — lon/lat axis order)
_GML_RESPONSE = b"""<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs" xmlns:gml="http://www.opengis.net/gml" xmlns:ms="http://mapserver.gis.umn.edu/mapserver">
  <wfs:featureMember>
    <ms:MapunitPoly>
      <ms:AREASYMBOL>OK001</ms:AREASYMBOL>
      <ms:MUSYM>NoA</ms:MUSYM>
      <ms:MUKEY>490709</ms:MUKEY>
      <ms:SPATIALVER>3</ms:SPATIALVER>
      <ms:Shape>
        <gml:Polygon srsName="EPSG:4326">
          <gml:exterior>
            <gml:LinearRing>
              <gml:posList>-97.405 35.195 -97.395 35.195 -97.395 35.205 -97.405 35.205 -97.405 35.195</gml:posList>
            </gml:LinearRing>
          </gml:exterior>
        </gml:Polygon>
      </ms:Shape>
    </ms:MapunitPoly>
  </wfs:featureMember>
</wfs:FeatureCollection>"""

# WFS GML with URN srsName (lat-first axis order)
_GML_URN_RESPONSE = b"""<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs" xmlns:gml="http://www.opengis.net/gml" xmlns:ms="http://mapserver.gis.umn.edu/mapserver">
  <wfs:featureMember>
    <ms:MapunitPoly>
      <ms:MUSYM>NoA</ms:MUSYM>
      <ms:MUKEY>490710</ms:MUKEY>
      <ms:Shape>
        <gml:Polygon srsName="urn:ogc:def:crs:EPSG::4326">
          <gml:exterior>
            <gml:LinearRing>
              <gml:posList>35.195 -97.405 35.195 -97.395 35.205 -97.395 35.205 -97.405 35.195 -97.405</gml:posList>
            </gml:LinearRing>
          </gml:exterior>
        </gml:Polygon>
      </ms:Shape>
    </ms:MapunitPoly>
  </wfs:featureMember>
</wfs:FeatureCollection>"""


def _base_flags_row(**overrides) -> dict:
    """Return a minimal row dict suitable for apply_flags testing."""
    row: dict = {
        "hydric":               False,
        "flood_freq":           None,
        "depth_to_restrict":    None,
        "restrict_type":        None,
        "bearing_capacity_label": None,
        "corr_steel":           None,
        "corr_concrete":        None,
        "lep_r":                None,
        "unified_class":        None,
        "slope_r":              None,
        "farmland_class":       None,
        "ksat_r":               None,
        "tax_order":            None,
        "survey_old":           False,
    }
    row.update(overrides)
    return row


def _empty_sda_resp() -> httpx.Response:
    return httpx.Response(200, json={"Table": []})


# ═══════════════════════════════════════════════════════════════════════════════
# Group 1 — Spatial helpers (soils_spatial.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSpatialHelpers:

    def test_bbox_to_wfs_filter_contains_ogc_filter(self):
        xml = _bbox_to_wfs_filter((-97.405, 35.195, -97.395, 35.205))
        assert "<ogc:Filter" in xml
        assert "ogc:Intersects" in xml

    def test_bbox_to_wfs_filter_contains_bbox_coords(self):
        xml = _bbox_to_wfs_filter((-97.405, 35.195, -97.395, 35.205))
        assert "-97.405" in xml
        assert "35.195" in xml
        assert "-97.395" in xml
        assert "35.205" in xml

    def test_bbox_to_wfs_filter_has_polygon_element(self):
        xml = _bbox_to_wfs_filter((-97.405, 35.195, -97.395, 35.205))
        assert "gml:Polygon" in xml
        assert "gml:posList" in xml

    def test_is_lat_lon_first_urn(self):
        assert _is_lat_lon_first("urn:ogc:def:crs:EPSG::4326") is True

    def test_is_lat_lon_first_epsg_short_form(self):
        assert _is_lat_lon_first("EPSG:4326") is False

    def test_is_lat_lon_first_none(self):
        assert _is_lat_lon_first(None) is False

    def test_is_lat_lon_first_empty_string(self):
        assert _is_lat_lon_first("") is False

    def test_pos_list_to_coords_basic_lon_lat(self):
        # lat_lon_first=False: raw values are [lon, lat]
        coords = _pos_list_to_coords("-97.405 35.195 -97.395 35.205", lat_lon_first=False)
        assert len(coords) == 2
        assert abs(coords[0][0] - (-97.405)) < 1e-6
        assert abs(coords[0][1] - 35.195) < 1e-6

    def test_pos_list_to_coords_lat_first_swapped(self):
        # lat_lon_first=True: raw values are [lat, lon] → stored as [lon, lat]
        coords = _pos_list_to_coords("35.195 -97.405 35.205 -97.395", lat_lon_first=True)
        assert len(coords) == 2
        assert abs(coords[0][0] - (-97.405)) < 1e-6   # lon
        assert abs(coords[0][1] - 35.195) < 1e-6      # lat

    def test_parse_wfs_gml_returns_feature_collection(self):
        fc = _parse_wfs_gml(_GML_RESPONSE)
        assert fc["type"] == "FeatureCollection"
        assert isinstance(fc["features"], list)
        assert len(fc["features"]) == 1

    def test_parse_wfs_gml_extracts_properties(self):
        fc = _parse_wfs_gml(_GML_RESPONSE)
        props = fc["features"][0]["properties"]
        assert props["musym"] == "NoA"
        assert props["mukey"] == "490709"
        assert props["areasymbol"] == "OK001"

    def test_parse_wfs_gml_extracts_polygon_geometry(self):
        fc = _parse_wfs_gml(_GML_RESPONSE)
        geom = fc["features"][0]["geometry"]
        assert geom is not None
        assert geom["type"] == "Polygon"
        # EPSG:4326 (not URN) → lat_lon_first=False → posList is lon lat
        first_coord = geom["coordinates"][0][0]
        assert abs(first_coord[0] - (-97.405)) < 1e-6
        assert abs(first_coord[1] - 35.195) < 1e-6

    def test_parse_wfs_gml_urn_swaps_axis_order(self):
        fc = _parse_wfs_gml(_GML_URN_RESPONSE)
        geom = fc["features"][0]["geometry"]
        assert geom is not None
        # URN srs: posList is lat lon → stored as [lon, lat]
        first_coord = geom["coordinates"][0][0]
        assert abs(first_coord[0] - (-97.405)) < 1e-6   # lon
        assert abs(first_coord[1] - 35.195) < 1e-6      # lat

    def test_parse_wfs_gml_malformed_xml_returns_empty(self):
        fc = _parse_wfs_gml(b"not valid xml <><>>")
        assert fc["type"] == "FeatureCollection"
        assert fc["features"] == []

    @respx.mock
    async def test_get_soil_polygons_json_response(self):
        respx.get(_WFS_URL).mock(return_value=httpx.Response(
            200,
            json={
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [-97.405, 35.195], [-97.395, 35.195],
                            [-97.395, 35.205], [-97.405, 35.195],
                        ]],
                    },
                    "properties": {"MUKEY": "490709", "MUSYM": "NoA"},
                }],
            },
            headers={"content-type": "application/json"},
        ))
        result = await get_soil_polygons(OKLAHOMA_CTX)
        assert result["type"] == "FeatureCollection"
        assert len(result["features"]) == 1
        assert "490709" in result["mukeys"]
        assert result["layer"] == "MapunitPoly"

    @respx.mock
    async def test_get_soil_polygons_gml_fallback(self):
        respx.get(_WFS_URL).mock(return_value=httpx.Response(
            200,
            content=_GML_RESPONSE,
            headers={"content-type": "application/xml"},
        ))
        result = await get_soil_polygons(OKLAHOMA_CTX)
        assert result["type"] == "FeatureCollection"
        assert "490709" in result["mukeys"]

    @respx.mock
    async def test_get_soil_polygons_timeout_returns_empty(self):
        respx.get(_WFS_URL).mock(side_effect=httpx.TimeoutException("timeout"))
        result = await get_soil_polygons(OKLAHOMA_CTX)
        assert result["type"] == "FeatureCollection"
        assert result["features"] == []
        assert result["mukeys"] == []
        assert "error" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Group 2 — Tabular helpers (soils_tabular.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestTabularHelpers:

    def test_fmt_mukeys_single(self):
        assert _fmt_mukeys(["12345"]) == "'12345'"

    def test_fmt_mukeys_multiple(self):
        assert _fmt_mukeys(["12345", "67890"]) == "'12345','67890'"

    def test_fmt_mukeys_empty(self):
        assert _fmt_mukeys([]) == ""

    def test_parse_sda_basic(self):
        data = {"Table": [["mukey", "muname"], ["12345", "Norge loam"]]}
        rows = _parse_sda(data)
        assert len(rows) == 1
        assert rows[0]["mukey"] == "12345"
        assert rows[0]["muname"] == "Norge loam"

    def test_parse_sda_lowercases_headers(self):
        data = {"Table": [["MUKEY", "MUNAME"], ["1", "Test"]]}
        rows = _parse_sda(data)
        assert "mukey" in rows[0]
        assert "muname" in rows[0]

    def test_parse_sda_empty_table(self):
        assert _parse_sda({"Table": []}) == []

    def test_parse_sda_header_only(self):
        assert _parse_sda({"Table": [["mukey"]]}) == []

    def test_parse_sda_missing_key(self):
        assert _parse_sda({}) == []

    def test_parse_sda_multiple_rows(self):
        data = {"Table": [["a", "b"], [1, 2], [3, 4]]}
        rows = _parse_sda(data)
        assert len(rows) == 2
        assert rows[1]["a"] == 3

    @respx.mock
    async def test_get_all_tabular_happy_path_returns_all_keys(self):
        """All 9 groups return empty-but-valid JSON → function returns all keys."""
        respx.post(_SDA_URL).mock(return_value=_empty_sda_resp())
        result = await get_all_tabular(["490709"])
        for key in (
            "mapunit", "components", "restrictions", "engineering",
            "flooding", "hydric", "corrosivity", "bearing", "interpretations"
        ):
            assert key in result
            assert isinstance(result[key], list)

    @respx.mock
    async def test_get_all_tabular_group_a_fatal_raises(self):
        """If all groups fail (including A), the exception propagates."""
        respx.post(_SDA_URL).mock(side_effect=httpx.ConnectError("refused"))
        with pytest.raises(Exception):
            await get_all_tabular(["490709"])

    def test_process_all_empty_groups_does_not_raise(self):
        """process_all with all-empty tabular groups (non-fatal failures) is stable."""
        tabular = {k: [] for k in (
            "mapunit", "components", "restrictions", "engineering",
            "flooding", "hydric", "corrosivity", "bearing", "interpretations"
        )}
        result = process_all(["490709"], tabular, [])
        assert "map_units" in result
        assert "hydric_present" in result
        assert "flags_summary" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Group 3 — Hydric flag (utils/soils_parser.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestHydricFlag:

    def test_apply_flags_hydric_true_is_flag_level(self):
        level, _ = apply_flags(_base_flags_row(hydric=True))
        assert level == FLAG_FLAG

    def test_apply_flags_hydric_code_present(self):
        _, flags = apply_flags(_base_flags_row(hydric=True))
        assert any(f["code"] == "hydric" for f in flags)

    def test_apply_flags_no_hydric_no_hydric_code(self):
        _, flags = apply_flags(_base_flags_row(hydric=False))
        assert all(f["code"] != "hydric" for f in flags)

    def test_build_summary_row_hydricrating_yes(self):
        row = build_summary_row(
            mukey="1", group_a=None, dominant_comp=None,
            engineering_rows=[], restriction_rows=[], flooding_rows=[],
            hydric_row={"hydricrating": "Yes", "hydric_criterion": None},
            bearing_rows=[], corr_rows=[], survey_old=False,
        )
        assert row["hydric"] is True

    def test_build_summary_row_hydricrating_all(self):
        row = build_summary_row(
            mukey="1", group_a=None, dominant_comp=None,
            engineering_rows=[], restriction_rows=[], flooding_rows=[],
            hydric_row={"hydricrating": "All", "hydric_criterion": None},
            bearing_rows=[], corr_rows=[], survey_old=False,
        )
        assert row["hydric"] is True

    def test_build_summary_row_hydricrating_no(self):
        row = build_summary_row(
            mukey="1", group_a=None, dominant_comp=None,
            engineering_rows=[], restriction_rows=[], flooding_rows=[],
            hydric_row={"hydricrating": "No", "hydric_criterion": None},
            bearing_rows=[], corr_rows=[], survey_old=False,
        )
        assert row["hydric"] is False

    def test_process_all_hydric_present_true(self):
        tabular = {k: [] for k in (
            "mapunit", "components", "restrictions", "engineering",
            "flooding", "corrosivity", "bearing", "interpretations"
        )}
        tabular["hydric"] = [
            {"mukey": "490709", "hydricrating": "Yes", "hydgrp": "D", "hydric_criterion": None}
        ]
        result = process_all(["490709"], tabular, [])
        assert result["hydric_present"] is True
        assert result["hydric_count"] >= 1

    def test_process_all_hydric_absent(self):
        tabular = {k: [] for k in (
            "mapunit", "components", "restrictions", "engineering",
            "flooding", "hydric", "corrosivity", "bearing", "interpretations"
        )}
        result = process_all(["490709"], tabular, [])
        assert result["hydric_present"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# Group 4 — Restrictive layer detection
# ═══════════════════════════════════════════════════════════════════════════════

class TestRestrictiveLayer:

    def test_shallow_restriction_under_24in_is_flag(self):
        level, flags = apply_flags(_base_flags_row(
            depth_to_restrict=18.0, restrict_type="Caliche"
        ))
        assert level == FLAG_FLAG
        assert any(f["code"] == "shallow_restrict" for f in flags)

    def test_shallow_restrict_message_includes_type(self):
        _, flags = apply_flags(_base_flags_row(
            depth_to_restrict=12.0, restrict_type="Duripan"
        ))
        flag = next(f for f in flags if f["code"] == "shallow_restrict")
        assert "Duripan" in flag["message"]

    def test_moderate_restriction_24_to_60in_is_review(self):
        _, flags = apply_flags(_base_flags_row(
            depth_to_restrict=36.0, restrict_type="Fragipan"
        ))
        assert any(f["code"] == "restrict_moderate" for f in flags)
        rev_flag = next(f for f in flags if f["code"] == "restrict_moderate")
        assert rev_flag["level"] == FLAG_REVIEW

    def test_deep_restriction_over_60in_no_flag(self):
        _, flags = apply_flags(_base_flags_row(depth_to_restrict=72.0))
        restrict_codes = [f["code"] for f in flags if "restrict" in f["code"]]
        assert restrict_codes == []

    def test_no_restriction_data_no_flag(self):
        _, flags = apply_flags(_base_flags_row())
        assert not any("restrict" in f["code"] for f in flags)

    def test_build_summary_row_shallowest_restriction_wins(self):
        restrictions = [
            {"resdept_r": 36, "reskind": "Fragipan", "reshard": "Soft", "resdepb_r": 50, "resthk_r": 14},
            {"resdept_r": 12, "reskind": "Caliche",  "reshard": "Hard", "resdepb_r": 20, "resthk_r": 8},
        ]
        row = build_summary_row(
            mukey="1", group_a=None, dominant_comp=None,
            engineering_rows=[], restriction_rows=restrictions, flooding_rows=[],
            hydric_row=None, bearing_rows=[], corr_rows=[], survey_old=False,
        )
        assert row["restrict_type"] == "Caliche"
        assert row["depth_to_restrict"] == 12.0

    def test_process_all_has_restrictions_true(self):
        tabular = {k: [] for k in (
            "mapunit", "components", "engineering", "flooding",
            "hydric", "corrosivity", "bearing", "interpretations"
        )}
        tabular["restrictions"] = [
            {
                "mukey": "490709", "cokey": "c1", "compname": "Test",
                "reskind": "Caliche", "reshard": "Hard",
                "resdept_r": 18, "resdepb_r": 24, "resthk_r": 6,
            }
        ]
        result = process_all(["490709"], tabular, [])
        assert result["has_restrictions"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# Group 5 — File downloads (soils_downloader.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFileDownloads:

    def test_save_geojson_creates_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dl, "_EXPORTS_BASE", tmp_path / "soils")
        path = save_geojson("proj1", "soil_polygons.geojson", _SIMPLE_FC)
        assert path.exists()

    def test_save_geojson_valid_json_content(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dl, "_EXPORTS_BASE", tmp_path / "soils")
        path = save_geojson("proj1", "soil_polygons.geojson", _SIMPLE_FC)
        loaded = json.loads(path.read_text())
        assert loaded["type"] == "FeatureCollection"
        assert len(loaded["features"]) == 1

    def test_save_geojson_nested_path_creates_subdirectory(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dl, "_EXPORTS_BASE", tmp_path / "soils")
        path = save_geojson("proj1", "tabular/mapunit.json", {"rows": []})
        assert path.exists()
        assert path.parent.name == "tabular"

    def test_save_csv_creates_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dl, "_EXPORTS_BASE", tmp_path / "soils")
        rows = [{"mukey": "490709", "musym": "NoA", "muname": "Norge loam"}]
        path = save_csv("proj1", "mapunit.csv", rows)
        assert path is not None
        assert path.exists()

    def test_save_csv_has_correct_headers(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dl, "_EXPORTS_BASE", tmp_path / "soils")
        rows = [{"mukey": "490709", "musym": "NoA"}]
        path = save_csv("proj1", "mapunit.csv", rows)
        assert path is not None
        text = path.read_text()
        assert "mukey" in text
        assert "musym" in text

    def test_save_csv_has_data_row(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dl, "_EXPORTS_BASE", tmp_path / "soils")
        rows = [{"mukey": "490709", "musym": "NoA"}]
        path = save_csv("proj1", "mapunit.csv", rows)
        assert path is not None
        assert "490709" in path.read_text()

    def test_save_csv_empty_rows_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dl, "_EXPORTS_BASE", tmp_path / "soils")
        assert save_csv("proj1", "empty.csv", []) is None

    def test_create_shapefile_zip_returns_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dl, "_EXPORTS_BASE", tmp_path / "soils")
        path = create_shapefile_zip("proj1", _SIMPLE_FC, "soil_mapunits")
        assert path is not None
        assert path.suffix == ".zip"
        assert path.exists()

    def test_create_shapefile_zip_contains_required_extensions(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dl, "_EXPORTS_BASE", tmp_path / "soils")
        path = create_shapefile_zip("proj1", _SIMPLE_FC, "soil_mapunits")
        assert path is not None
        with zipfile.ZipFile(path) as zf:
            exts = {Path(n).suffix for n in zf.namelist()}
        assert ".shp" in exts
        assert ".dbf" in exts
        assert ".shx" in exts
        assert ".prj" in exts

    def test_create_shapefile_zip_no_features_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dl, "_EXPORTS_BASE", tmp_path / "soils")
        empty_fc = {"type": "FeatureCollection", "features": []}
        assert create_shapefile_zip("proj1", empty_fc, "empty") is None


# ═══════════════════════════════════════════════════════════════════════════════
# Group 6 — Flag rule engine (utils/soils_parser.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFlagRuleEngine:

    def test_lep_above_6_shrink_swell_flag(self):
        level, flags = apply_flags(_base_flags_row(lep_r=8.0))
        assert level == FLAG_FLAG
        assert any(f["code"] == "shrink_swell" for f in flags)

    def test_lep_below_6_no_shrink_swell_flag(self):
        _, flags = apply_flags(_base_flags_row(lep_r=4.0))
        assert all(f["code"] != "shrink_swell" for f in flags)

    def test_organic_soils_pt_flag(self):
        level, flags = apply_flags(_base_flags_row(unified_class="PT"))
        assert level == FLAG_FLAG
        assert any(f["code"] == "organic_soils" for f in flags)

    def test_organic_soils_oh_flag(self):
        _, flags = apply_flags(_base_flags_row(unified_class="OH"))
        assert any(f["code"] == "organic_soils" for f in flags)

    def test_organic_soils_ol_flag(self):
        _, flags = apply_flags(_base_flags_row(unified_class="OL"))
        assert any(f["code"] == "organic_soils" for f in flags)

    def test_flood_frequent_flag(self):
        level, flags = apply_flags(_base_flags_row(flood_freq="Frequent"))
        assert level == FLAG_FLAG
        assert any(f["code"] == "flood_risk" for f in flags)

    def test_flood_occasional_flag(self):
        _, flags = apply_flags(_base_flags_row(flood_freq="Occasional"))
        assert any(f["code"] == "flood_risk" for f in flags)

    def test_flood_rare_review(self):
        _, flags = apply_flags(_base_flags_row(flood_freq="Rare"))
        flag = next((f for f in flags if f["code"] == "flood_rare"), None)
        assert flag is not None
        assert flag["level"] == FLAG_REVIEW

    def test_corr_steel_high_flag(self):
        level, flags = apply_flags(_base_flags_row(corr_steel="High"))
        assert level == FLAG_FLAG
        assert any(f["code"] == "corr_steel" for f in flags)

    def test_bearing_very_low_flag(self):
        level, flags = apply_flags(_base_flags_row(bearing_capacity_label="Very low"))
        assert level == FLAG_FLAG
        assert any(f["code"] == "bearing_low" for f in flags)

    def test_bearing_low_review(self):
        _, flags = apply_flags(_base_flags_row(bearing_capacity_label="Low"))
        flag = next((f for f in flags if f["code"] == "bearing_moderate"), None)
        assert flag is not None
        assert flag["level"] == FLAG_REVIEW

    def test_steep_slope_review(self):
        _, flags = apply_flags(_base_flags_row(slope_r=20.0))
        assert any(f["code"] == "steep_slope" for f in flags)

    def test_survey_old_info_level(self):
        level, flags = apply_flags(_base_flags_row(survey_old=True))
        assert level == FLAG_INFO
        assert any(f["code"] == "old_survey" for f in flags)

    def test_flag_level_precedence_flag_overrides_review(self):
        level, _ = apply_flags(_base_flags_row(
            hydric=True,     # FLAG_FLAG
            slope_r=20.0,    # FLAG_REVIEW
        ))
        assert level == FLAG_FLAG

    def test_clean_row_pass_level_no_flags(self):
        level, flags = apply_flags(_base_flags_row())
        assert level == FLAG_PASS
        assert flags == []


# ═══════════════════════════════════════════════════════════════════════════════
# Group 7 — CAD export (services/exporters/cad.py)
# ═══════════════════════════════════════════════════════════════════════════════

_SUMMARY_FLAGGED = {
    "mukey":      "490709",
    "musym":      "NoA",
    "muname":     "Norge loam",
    "flags":      [{"level": "flag", "code": "hydric", "message": "Hydric soils present"}],
    "flag_level": "flag",
}

_SUMMARY_CLEAN = {
    "mukey":      "490709",
    "musym":      "NoA",
    "muname":     "Norge loam",
    "flags":      [],
    "flag_level": "pass",
}


class TestCadExport:

    def _text(self, data: bytes) -> str:
        return data.decode("latin-1")

    def test_export_returns_non_empty_bytes(self):
        result = export_soils_to_dxf(_SIMPLE_FC, [_SUMMARY_CLEAN])
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_export_empty_fc_returns_valid_bytes(self):
        empty_fc: dict = {"type": "FeatureCollection", "features": []}
        result = export_soils_to_dxf(empty_fc, [])
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_has_soils_boundary_layer(self):
        text = self._text(export_soils_to_dxf(_SIMPLE_FC, [_SUMMARY_CLEAN]))
        assert "SOILS-BOUNDARY" in text

    def test_has_soils_labels_layer(self):
        text = self._text(export_soils_to_dxf(_SIMPLE_FC, [_SUMMARY_CLEAN]))
        assert "SOILS-LABELS" in text

    def test_has_soils_flags_layer(self):
        text = self._text(export_soils_to_dxf(_SIMPLE_FC, [_SUMMARY_CLEAN]))
        assert "SOILS-FLAGS" in text

    def test_has_per_musym_layer(self):
        text = self._text(export_soils_to_dxf(_SIMPLE_FC, [_SUMMARY_CLEAN]))
        assert "SOILS-NoA" in text

    def test_flag_annotation_appears_for_flagged_unit(self):
        text = self._text(export_soils_to_dxf(_SIMPLE_FC, [_SUMMARY_FLAGGED]))
        assert "HYDRIC" in text.upper()

    def test_multipolygon_geometry_handled(self):
        multi_fc: dict = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [[[-97.405, 35.195], [-97.400, 35.195],
                          [-97.400, 35.200], [-97.405, 35.195]]],
                        [[[-97.400, 35.200], [-97.395, 35.200],
                          [-97.395, 35.205], [-97.400, 35.200]]],
                    ],
                },
                "properties": {"mukey": "490709", "musym": "NoA"},
            }],
        }
        result = export_soils_to_dxf(multi_fc, [_SUMMARY_CLEAN])
        text = self._text(result)
        assert "SOILS-BOUNDARY" in text
        assert "SOILS-NoA" in text


# ═══════════════════════════════════════════════════════════════════════════════
# Integration (auto-skipped in sandbox)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
async def test_integration_oklahoma_soil_polygons():
    """Live WFS query near Chickasha, OK — requires network."""
    result = await get_soil_polygons(OKLAHOMA_CTX)
    assert result["type"] == "FeatureCollection"
    assert len(result["mukeys"]) > 0


@pytest.mark.integration
async def test_integration_oklahoma_tabular():
    """Live SDA tabular query — requires network."""
    result = await get_all_tabular(["490709"])
    assert "mapunit" in result
    assert len(result["mapunit"]) > 0
