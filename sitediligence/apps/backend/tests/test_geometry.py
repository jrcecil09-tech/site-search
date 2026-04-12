"""Tests for geometry and coordinate utilities."""

import pytest

from utils.geometry import bbox_to_polygon, compute_area_m2
from utils.validators import is_valid_bbox, is_valid_coordinate, sanitize_filename


def test_bbox_to_polygon_type():
    result = bbox_to_polygon((-77.1, 38.8, -76.9, 39.0))
    assert result["type"] == "Polygon"
    assert len(result["coordinates"][0]) == 5  # 4 corners + closing point


def test_is_valid_bbox_pass():
    assert is_valid_bbox((-180, -90, 180, 90)) is True
    assert is_valid_bbox((-77.1, 38.8, -76.9, 39.0)) is True


def test_is_valid_bbox_fail():
    assert is_valid_bbox((10, 20, 5, 30)) is False   # minLon > maxLon
    assert is_valid_bbox((-181, 0, 0, 0)) is False   # out of range


def test_is_valid_coordinate():
    assert is_valid_coordinate(-77.0, 38.9) is True
    assert is_valid_coordinate(200, 38.9) is False
    assert is_valid_coordinate(-77.0, 91) is False


def test_sanitize_filename():
    assert sanitize_filename("../etc/passwd") == "etc_passwd"
    assert sanitize_filename("site report 2024.pdf") == "site report 2024.pdf"
    assert sanitize_filename("file<>name.txt") == "file__name.txt"


def test_compute_area_m2():
    # Small bbox around DC — area should be roughly ~270 km²
    polygon = bbox_to_polygon((-77.12, 38.79, -76.91, 38.99))
    area = compute_area_m2(polygon)
    assert area > 100_000_000   # > 100 km² in m²
    assert area < 500_000_000   # < 500 km²
