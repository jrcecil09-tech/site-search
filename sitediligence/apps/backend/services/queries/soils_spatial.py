"""SSURGO Soil polygons and boundaries via NRCS SDMWGS84Geographic WFS.

WFS endpoint: https://sdmdataaccess.nrcs.usda.gov/Spatial/SDMWGS84Geographic.wfs
Protocol: WFS 1.1.0 / GML 3.1.1
Available typenames: MapunitPoly, MapunitLine, MapunitPoint, SurveyAreaBoundary

Geometry handling:
  - WFS 1.1.0 may return either GML (application/xml) or GeoJSON depending on
    the OUTPUTFORMAT param. We request JSON first; fall back to GML parsing.
  - GML 3.1.1 with srsName="urn:ogc:def:crs:EPSG::4326" uses (lat, lon) axis
    order. All returned GeoJSON uses (lon, lat) / [longitude, latitude] order.
"""

from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Any

import httpx

log = logging.getLogger(__name__)

_WFS_URL = "https://sdmdataaccess.nrcs.usda.gov/Spatial/SDMWGS84Geographic.wfs"
_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=5.0)
_WFS_VERSION = "1.1.0"

# XML namespaces used in WFS 1.1.0 / GML 3.1.1 responses
_NS = {
    "wfs": "http://www.opengis.net/wfs",
    "gml": "http://www.opengis.net/gml",
    "ms":  "http://mapserver.gis.umn.edu/mapserver",
    "ogc": "http://www.opengis.net/ogc",
    "ows": "http://www.opengis.net/ows",
}

# Survey areas older than this many years from today are flagged
_SURVEY_AGE_THRESHOLD_YEARS = 20
_TODAY = date(2026, 4, 13)


# ── OGC Filter builder ────────────────────────────────────────────────────────

def _bbox_to_wfs_filter(bbox: tuple[float, float, float, float]) -> str:
    """Build a WFS OGC Filter XML string for a spatial Intersects query.

    bbox = (minlon, minlat, maxlon, maxlat)
    Returns an XML string with an ogc:Intersects element whose bounding polygon
    uses the bbox ring: SW → SE → NE → NW → SW.
    """
    minlon, minlat, maxlon, maxlat = bbox
    pos_list = (
        f"{minlon} {minlat} "
        f"{maxlon} {minlat} "
        f"{maxlon} {maxlat} "
        f"{minlon} {maxlat} "
        f"{minlon} {minlat}"
    )
    return (
        '<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">'
        "<ogc:Intersects>"
        "<ogc:PropertyName>Geometry</ogc:PropertyName>"
        '<gml:Polygon xmlns:gml="http://www.opengis.net/gml" srsName="EPSG:4326">'
        "<gml:exterior><gml:LinearRing>"
        f"<gml:posList>{pos_list}</gml:posList>"
        "</gml:LinearRing></gml:exterior>"
        "</gml:Polygon>"
        "</ogc:Intersects>"
        "</ogc:Filter>"
    )


# ── GML coordinate parsers ────────────────────────────────────────────────────

def _is_lat_lon_first(srs_name: str | None) -> bool:
    """Return True when the CRS spec uses (lat, lon) axis order.

    WFS 1.1.0 with urn:ogc:def:crs:EPSG::4326 uses (lat, lon) order.
    EPSG:4326 (without the urn form) typically means (lon, lat).
    """
    if not srs_name:
        return False
    return "urn:ogc:def:crs" in srs_name.lower()


def _pos_list_to_coords(
    text: str,
    lat_lon_first: bool,
) -> list[list[float]]:
    """Convert a GML posList string to a list of [lon, lat] pairs.

    GML posList packs coordinates as pairs (or triples): x y [z] x y [z] ...
    When lat_lon_first is True the axis order is lat lon, so we swap.
    """
    nums = [float(v) for v in text.split()]
    coords: list[list[float]] = []
    i = 0
    while i + 1 < len(nums):
        a, b = nums[i], nums[i + 1]
        if lat_lon_first:
            coords.append([b, a])   # swap: stored as [lon, lat]
        else:
            coords.append([a, b])
        # skip optional Z ordinate
        i += 2 if len(nums) % 2 == 0 else 3
    return coords


def _linear_ring_coords(
    ring_el: ET.Element,
    lat_lon_first: bool,
) -> list[list[float]]:
    """Extract coordinate list from a gml:LinearRing element."""
    pos_list_el = ring_el.find("gml:posList", _NS)
    if pos_list_el is not None and pos_list_el.text:
        return _pos_list_to_coords(pos_list_el.text.strip(), lat_lon_first)

    # Fallback: gml:pos elements
    pos_els = ring_el.findall("gml:pos", _NS)
    coords: list[list[float]] = []
    for pos_el in pos_els:
        if pos_el.text:
            parts = pos_el.text.split()
            if len(parts) >= 2:
                a, b = float(parts[0]), float(parts[1])
                if lat_lon_first:
                    coords.append([b, a])
                else:
                    coords.append([a, b])
    return coords


def _parse_polygon_el(
    poly_el: ET.Element,
    lat_lon_first: bool,
) -> list[list[list[float]]]:
    """Return polygon ring coordinates from a gml:Polygon element.

    Returns [[exterior_ring], [interior_ring1], ...] in GeoJSON format.
    """
    rings: list[list[list[float]]] = []
    exterior = poly_el.find("gml:exterior/gml:LinearRing", _NS)
    if exterior is not None:
        rings.append(_linear_ring_coords(exterior, lat_lon_first))
    for interior in poly_el.findall("gml:interior/gml:LinearRing", _NS):
        rings.append(_linear_ring_coords(interior, lat_lon_first))
    return rings


def _geom_from_element(geom_el: ET.Element) -> dict[str, Any] | None:
    """Convert a GML geometry element to a GeoJSON geometry dict.

    Handles: gml:Polygon, gml:MultiPolygon, gml:MultiSurface, gml:Surface.
    Returns None when the geometry cannot be parsed.
    """
    tag = geom_el.tag.split("}")[-1] if "}" in geom_el.tag else geom_el.tag
    srs = geom_el.get("srsName")
    lat_lon_first = _is_lat_lon_first(srs)

    if tag == "Polygon":
        rings = _parse_polygon_el(geom_el, lat_lon_first)
        if not rings:
            return None
        return {"type": "Polygon", "coordinates": rings}

    if tag in ("MultiPolygon", "MultiSurface"):
        polys: list[list[list[list[float]]]] = []
        # MultiPolygon uses polygonMember; MultiSurface uses surfaceMember
        for member_tag in ("polygonMember", "surfaceMember"):
            for member in geom_el.findall(f"gml:{member_tag}", _NS):
                poly_el = member.find("gml:Polygon", _NS)
                if poly_el is not None:
                    rings = _parse_polygon_el(poly_el, lat_lon_first)
                    if rings:
                        polys.append(rings)
        if not polys:
            return None
        return {"type": "MultiPolygon", "coordinates": polys}

    if tag == "Surface":
        # gml:Surface / gml:patches / gml:PolygonPatch
        patches = geom_el.findall("gml:patches/gml:PolygonPatch", _NS)
        polys = []
        for patch in patches:
            rings = _parse_polygon_el(patch, lat_lon_first)
            if rings:
                polys.append(rings)
        if len(polys) == 1:
            return {"type": "Polygon", "coordinates": polys[0]}
        if polys:
            return {"type": "MultiPolygon", "coordinates": polys}

    return None


# ── GML response parser ───────────────────────────────────────────────────────

def _parse_wfs_gml(xml_bytes: bytes) -> dict[str, Any]:
    """Parse a WFS 1.1.0 / GML 3.1.1 FeatureCollection response.

    Returns a GeoJSON FeatureCollection dict.  An empty FeatureCollection is
    returned when the response contains no featureMember elements or when the
    XML cannot be parsed.
    """
    empty: dict[str, Any] = {"type": "FeatureCollection", "features": []}

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        log.warning("WFS GML parse error: %s", exc)
        return empty

    features: list[dict[str, Any]] = []

    for member in root.findall(".//wfs:featureMember", _NS):
        # The feature element is the first (and only) child of featureMember
        feature_el = None
        for child in member:
            feature_el = child
            break
        if feature_el is None:
            continue

        def _text(prop: str) -> str | None:
            el = feature_el.find(f"ms:{prop}", _NS)
            return el.text.strip() if el is not None and el.text else None

        props: dict[str, Any] = {
            "areasymbol": _text("AREASYMBOL"),
            "musym":       _text("MUSYM"),
            "mukey":       _text("MUKEY"),
            "spatialver":  _text("SPATIALVER"),
            "layer":       None,  # filled by callers
        }

        # Geometry: look for ms:Shape or ms:Geometry child
        geom: dict[str, Any] | None = None
        for geom_tag in ("Shape", "Geometry"):
            geom_wrapper = feature_el.find(f"ms:{geom_tag}", _NS)
            if geom_wrapper is not None:
                for geom_child in geom_wrapper:
                    geom = _geom_from_element(geom_child)
                    if geom is not None:
                        break
                if geom is not None:
                    break

        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": props,
        })

    return {"type": "FeatureCollection", "features": features}


# ── GeoJSON response parser ───────────────────────────────────────────────────

def _parse_wfs_json(data: dict[str, Any], layer: str) -> dict[str, Any]:
    """Normalize a GeoJSON FeatureCollection from the WFS server.

    Lowercases all property keys and injects the ``layer`` property into each
    feature.  Returns a FeatureCollection dict.
    """
    raw_features = data.get("features") or []
    features: list[dict[str, Any]] = []
    for feat in raw_features:
        raw_props = feat.get("properties") or {}
        props = {k.lower(): v for k, v in raw_props.items()}
        props["layer"] = layer
        features.append({
            "type": "Feature",
            "geometry": feat.get("geometry"),
            "properties": props,
        })
    return {"type": "FeatureCollection", "features": features}


# ── WFS fetch helper ──────────────────────────────────────────────────────────

async def _fetch_layer(
    client: httpx.AsyncClient,
    typename: str,
    bbox: tuple[float, float, float, float],
    filter_xml: str | None = None,
) -> dict[str, Any]:
    """Fetch a single WFS layer and return a GeoJSON FeatureCollection.

    Attempts a JSON-format GetFeature first.  If the server returns XML/GML
    instead (some WFS implementations ignore OUTPUTFORMAT), the GML parser is
    used as a fallback.

    When filter_xml is provided the request is POSTed with the OGC Filter body;
    otherwise a BBOX parameter GET request is made.
    """
    minlon, minlat, maxlon, maxlat = bbox
    layer = typename  # used as the "layer" property value

    base_params: dict[str, str] = {
        "SERVICE":      "WFS",
        "VERSION":      _WFS_VERSION,
        "REQUEST":      "GetFeature",
        "TYPENAME":     typename,
        "OUTPUTFORMAT": "application/json",
    }

    if filter_xml:
        # POST with filter body; BBOX not included (filter replaces it)
        resp = await client.post(
            _WFS_URL,
            params=base_params,
            content=filter_xml.encode(),
            headers={"Content-Type": "application/xml"},
        )
    else:
        params = dict(base_params)
        params["BBOX"] = f"{minlon},{minlat},{maxlon},{maxlat},EPSG:4326"
        resp = await client.get(_WFS_URL, params=params)

    resp.raise_for_status()

    content_type = resp.headers.get("content-type", "").lower()
    if "json" in content_type:
        try:
            fc = _parse_wfs_json(resp.json(), layer)
        except Exception as exc:
            log.warning("WFS JSON parse failed for %s: %s", typename, exc)
            fc = {"type": "FeatureCollection", "features": []}
    else:
        fc = _parse_wfs_gml(resp.content)
        # Inject layer name into GML-parsed features
        for feat in fc.get("features", []):
            props = feat.get("properties") or {}
            props["layer"] = layer
            feat["properties"] = props

    return fc


# ── Public query functions ────────────────────────────────────────────────────

async def get_soil_polygons(ctx: Any) -> dict[str, Any]:
    """Fetch MapunitPoly features for ctx.bbox.

    Returns a GeoJSON FeatureCollection extended with:
      - ``layer``: "MapunitPoly"
      - ``mukeys``: sorted list of unique mukey strings extracted from features
    """
    async with httpx.AsyncClient(
        timeout=_TIMEOUT,
        follow_redirects=True,
        trust_env=False,
    ) as client:
        try:
            fc = await _fetch_layer(client, "MapunitPoly", ctx.bbox)
        except Exception as exc:
            log.warning("MapunitPoly fetch failed (non-fatal): %s", exc)
            return {
                "type": "FeatureCollection",
                "features": [],
                "mukeys": [],
                "layer": "MapunitPoly",
                "error": str(exc),
            }

    mukeys: list[str] = []
    seen: set[str] = set()
    for feat in fc.get("features", []):
        props = feat.get("properties") or {}
        mk = str(props.get("mukey") or "").strip()
        if mk and mk not in seen:
            seen.add(mk)
            mukeys.append(mk)

    fc["mukeys"] = sorted(mukeys)
    fc["layer"] = "MapunitPoly"
    return fc


async def get_survey_areas(ctx: Any) -> list[dict[str, Any]]:
    """Fetch SurveyAreaBoundary features and annotate with staleness flag.

    Each returned dict includes:
      areasymbol, areaname, surveyareaname, saverest (survey date string),
      survey_date_old (True if the survey date is older than 20 years from today).
    """
    async with httpx.AsyncClient(
        timeout=_TIMEOUT,
        follow_redirects=True,
        trust_env=False,
    ) as client:
        try:
            fc = await _fetch_layer(client, "SurveyAreaBoundary", ctx.bbox)
        except Exception as exc:
            log.warning("SurveyAreaBoundary fetch failed (non-fatal): %s", exc)
            return []

    result: list[dict[str, Any]] = []
    for feat in fc.get("features", []):
        props = feat.get("properties") or {}

        areasymbol     = str(props.get("areasymbol")     or props.get("AREASYMBOL")     or "").strip() or None
        areaname       = str(props.get("areaname")       or props.get("AREANAME")       or "").strip() or None
        surveyareaname = str(props.get("surveyareaname") or props.get("SURVEYAREANAME") or "").strip() or None
        saverest_raw   = str(props.get("saverest")       or props.get("SAVEREST")       or "").strip() or None

        # Determine staleness
        survey_date_old = False
        if saverest_raw:
            for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y"):
                try:
                    survey_dt = datetime.strptime(saverest_raw, fmt).date()
                    cutoff = date(
                        _TODAY.year - _SURVEY_AGE_THRESHOLD_YEARS,
                        _TODAY.month,
                        _TODAY.day,
                    )
                    survey_date_old = survey_dt < cutoff
                    break
                except ValueError:
                    continue

        result.append({
            "areasymbol":     areasymbol,
            "areaname":       areaname,
            "surveyareaname": surveyareaname,
            "saverest":       saverest_raw,
            "survey_date_old": survey_date_old,
            "geometry":       feat.get("geometry"),
        })

    return result


async def get_soil_lines(ctx: Any) -> dict[str, Any]:
    """Fetch MapunitLine features for ctx.bbox.

    Returns a GeoJSON FeatureCollection with layer="MapunitLine".
    Non-fatal on error: returns empty FeatureCollection with an error note.
    """
    async with httpx.AsyncClient(
        timeout=_TIMEOUT,
        follow_redirects=True,
        trust_env=False,
    ) as client:
        try:
            fc = await _fetch_layer(client, "MapunitLine", ctx.bbox)
        except Exception as exc:
            log.warning("MapunitLine fetch failed (non-fatal): %s", exc)
            return {
                "type": "FeatureCollection",
                "features": [],
                "layer": "MapunitLine",
                "error": str(exc),
            }

    fc["layer"] = "MapunitLine"
    return fc


async def get_soil_points(ctx: Any) -> dict[str, Any]:
    """Fetch MapunitPoint features for ctx.bbox.

    Returns a GeoJSON FeatureCollection with layer="MapunitPoint".
    Non-fatal on error: returns empty FeatureCollection with an error note.
    """
    async with httpx.AsyncClient(
        timeout=_TIMEOUT,
        follow_redirects=True,
        trust_env=False,
    ) as client:
        try:
            fc = await _fetch_layer(client, "MapunitPoint", ctx.bbox)
        except Exception as exc:
            log.warning("MapunitPoint fetch failed (non-fatal): %s", exc)
            return {
                "type": "FeatureCollection",
                "features": [],
                "layer": "MapunitPoint",
                "error": str(exc),
            }

    fc["layer"] = "MapunitPoint"
    return fc


async def get_soil_lines_and_points(
    ctx: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Fetch MapunitLine and MapunitPoint concurrently.

    Returns (lines_fc, points_fc).  Each uses its own httpx client so the
    requests truly run in parallel via asyncio.gather.
    """
    lines_result, points_result = await asyncio.gather(
        get_soil_lines(ctx),
        get_soil_points(ctx),
        return_exceptions=True,
    )

    _empty_lines: dict[str, Any] = {
        "type": "FeatureCollection",
        "features": [],
        "layer": "MapunitLine",
    }
    _empty_points: dict[str, Any] = {
        "type": "FeatureCollection",
        "features": [],
        "layer": "MapunitPoint",
    }

    if isinstance(lines_result, BaseException):
        log.warning("MapunitLine gather failed: %s", lines_result)
        lines_result = _empty_lines

    if isinstance(points_result, BaseException):
        log.warning("MapunitPoint gather failed: %s", points_result)
        points_result = _empty_points

    return lines_result, points_result  # type: ignore[return-value]
