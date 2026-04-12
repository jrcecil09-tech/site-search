"""Shared pytest fixtures and skip logic for integration tests."""

from __future__ import annotations

import asyncio
import pytest
import httpx


def _can_reach_federal_apis() -> bool:
    """Return True if a lightweight probe to a federal ArcGIS endpoint succeeds."""
    probe_url = (
        "https://fwspublicservices.wim.usgs.gov"
        "/wetlandsmapservice/rest/services/Wetlands/MapServer?f=json"
    )
    try:
        r = httpx.get(probe_url, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


# Evaluate once per session
_FEDERAL_APIS_REACHABLE = _can_reach_federal_apis()


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: tests that call real external federal GIS APIs",
    )


def pytest_collection_modifyitems(config, items):
    """Auto-skip integration tests when federal APIs are unreachable."""
    if _FEDERAL_APIS_REACHABLE:
        return
    skip = pytest.mark.skip(
        reason="federal API endpoints unreachable from this environment "
               "(sandbox/CI proxy blocks government ArcGIS services)"
    )
    for item in items:
        if item.get_closest_marker("integration"):
            item.add_marker(skip)
