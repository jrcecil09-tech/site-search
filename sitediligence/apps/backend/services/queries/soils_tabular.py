"""SSURGO tabular attribute queries via NRCS Soil Data Access (SDA).

Endpoint: https://sdmdataaccess.nrcs.usda.gov/tabular/post.rest
Protocol: HTTP POST, application/x-www-form-urlencoded
Body:      query=<T-SQL>&format=JSON+PLUS
Response:  {"Table": [["col1","col2",...], [row1_val1, row1_val2,...], ...]}

Nine attribute groups (A–I) are queried in parallel against the SDA tabular
endpoint.  Group A (map unit overview) and Group B (component data) are fatal
if they fail; Groups C–I are non-fatal and return empty lists on failure.

Spatial mukey discovery uses the SDA built-in T-SQL function:
    SDA_Get_Mukey_from_intersection_with_WktWgs84('{wkt}')
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)

_SDA_URL = "https://sdmdataaccess.nrcs.usda.gov/tabular/post.rest"
_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=5.0)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _fmt_mukeys(mukeys: list[str]) -> str:
    """Format mukey list for SQL IN clause: '490709','490712'"""
    return ",".join(f"'{k}'" for k in mukeys)


def _parse_sda(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse SDA JSON+PLUS response to list of row dicts."""
    table = data.get("Table") or []
    if len(table) < 2:
        return []
    headers = [str(h).strip().lower() for h in table[0]]
    return [dict(zip(headers, row)) for row in table[1:]]


async def _sda_post(client: httpx.AsyncClient, sql: str) -> list[dict[str, Any]]:
    """POST SQL to SDA, return parsed rows."""
    resp = await client.post(
        _SDA_URL,
        data={"query": sql, "format": "JSON+PLUS"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp.raise_for_status()
    return _parse_sda(resp.json())


# ── Group query functions ─────────────────────────────────────────────────────

async def get_group_a_mapunit(
    client: httpx.AsyncClient,
    mukeys: list[str],
) -> list[dict[str, Any]]:
    """GROUP A Map Unit Overview."""
    sql = f"""
SELECT mu.mukey, mu.musym, mu.muname, mu.mukind,
       mu.farmlndcl, mu.muacres, mu.niccdcd, mu.niccdcd_r, mu.urbrecgr
FROM mapunit mu
WHERE mu.mukey IN ({_fmt_mukeys(mukeys)})
""".strip()
    return await _sda_post(client, sql)


async def get_group_b_components(
    client: httpx.AsyncClient,
    mukeys: list[str],
) -> list[dict[str, Any]]:
    """GROUP B Component Data."""
    sql = f"""
SELECT co.mukey, co.compname, co.comppct_r, co.compkind, co.majcompflag,
       co.slope_r, co.slope_l, co.slope_h, co.elev_r, co.aspectrep,
       co.map_r, co.airtempa_r, co.ffd_r, co.tfact, co.wei, co.weg,
       co.erocl, co.earthcovkind1, co.hydrgrp, co.hydgrp,
       co.drainagecl, co.taxorder, co.taxsuborder, co.taxgrtgroup,
       co.taxsubgrp, co.taxpartsize, co.taxreaction, co.taxtempcl, co.cokey
FROM component co
WHERE co.mukey IN ({_fmt_mukeys(mukeys)})
AND co.majcompflag = 'Yes'
ORDER BY co.mukey, co.comppct_r DESC
""".strip()
    return await _sda_post(client, sql)


async def get_group_c_restrictions(
    client: httpx.AsyncClient,
    mukeys: list[str],
) -> list[dict[str, Any]]:
    """GROUP C Soil Restrictions."""
    sql = f"""
SELECT co.mukey, co.cokey, co.compname,
       cr.reskind, cr.reshard, cr.resdept_r, cr.resdepb_r, cr.resthk_r
FROM component co
INNER JOIN corestrictions cr ON cr.cokey = co.cokey
WHERE co.mukey IN ({_fmt_mukeys(mukeys)})
AND co.majcompflag = 'Yes'
ORDER BY co.mukey, cr.resdept_r
""".strip()
    return await _sda_post(client, sql)


async def get_group_d_engineering(
    client: httpx.AsyncClient,
    mukeys: list[str],
) -> list[dict[str, Any]]:
    """GROUP D Engineering Properties."""
    sql = f"""
SELECT co.mukey, co.cokey, co.compname,
       ch.hzname, ch.hzdept_r, ch.hzdepb_r,
       ch.sandtotal_r, ch.silttotal_r, ch.claytotal_r,
       ch.om_r, ch.dbmoist_r, ch.ksat_r, ch.awc_r,
       ch.wtenthbar_r, ch.wthirdbar_r, ch.wfifteenbar_r,
       ch.lep_r, ch.LL_r, ch.pi_r,
       ch.fraggt10_r, ch.frag3to10_r, ch.kwfact, ch.kffact,
       chia_u.chiavalue AS unified_class,
       chia_a.chiavalue AS aashto_class
FROM component co
INNER JOIN chorizon ch ON ch.cokey = co.cokey
LEFT JOIN chia AS chia_u ON chia_u.chkey = ch.chkey
    AND chia_u.chiakind = 'Unified soil classification'
LEFT JOIN chia AS chia_a ON chia_a.chkey = ch.chkey
    AND chia_a.chiakind = 'AASHTO group classification'
WHERE co.mukey IN ({_fmt_mukeys(mukeys)})
AND co.majcompflag = 'Yes'
ORDER BY co.mukey, ch.hzdept_r
""".strip()
    return await _sda_post(client, sql)


async def get_group_e_flooding(
    client: httpx.AsyncClient,
    mukeys: list[str],
) -> list[dict[str, Any]]:
    """GROUP E Flooding and Ponding."""
    sql = f"""
SELECT co.mukey, co.cokey, co.compname,
       cf.flodfreqcl, cf.floddurcl, cf.floddept_r,
       cp.pondfreqcl, cp.ponddurcl, cp.ponddept_r
FROM component co
LEFT JOIN coflood cf ON cf.cokey = co.cokey
LEFT JOIN copontd cp ON cp.cokey = co.cokey
WHERE co.mukey IN ({_fmt_mukeys(mukeys)})
AND co.majcompflag = 'Yes'
""".strip()
    return await _sda_post(client, sql)


async def get_group_f_hydric(
    client: httpx.AsyncClient,
    mukeys: list[str],
) -> list[dict[str, Any]]:
    """GROUP F Hydric Soils."""
    sql = f"""
SELECT co.mukey, co.cokey, co.compname,
       co.hydricrating, co.hydgrp,
       cc.cocrname AS hydric_criterion
FROM component co
LEFT JOIN cocrittom cc ON cc.cokey = co.cokey
    AND cc.cocrflag = 'Yes'
WHERE co.mukey IN ({_fmt_mukeys(mukeys)})
AND co.majcompflag = 'Yes'
""".strip()
    return await _sda_post(client, sql)


async def get_group_g_corrosivity(
    client: httpx.AsyncClient,
    mukeys: list[str],
) -> list[dict[str, Any]]:
    """GROUP G Corrosivity."""
    sql = f"""
SELECT co.mukey, co.cokey, co.compname,
       ch.hzname, ch.hzdept_r, ch.hzdepb_r, ch.ph1to1h2o_r,
       cor_steel.chiavalue AS corr_steel,
       cor_conc.chiavalue AS corr_concrete
FROM component co
INNER JOIN chorizon ch ON ch.cokey = co.cokey
LEFT JOIN chia AS cor_steel ON cor_steel.chkey = ch.chkey
    AND cor_steel.chiakind = 'Corrosion of steel'
LEFT JOIN chia AS cor_conc ON cor_conc.chkey = ch.chkey
    AND cor_conc.chiakind = 'Corrosion of concrete'
WHERE co.mukey IN ({_fmt_mukeys(mukeys)})
AND co.majcompflag = 'Yes'
ORDER BY co.mukey, ch.hzdept_r
""".strip()
    return await _sda_post(client, sql)


async def get_group_h_bearing(
    client: httpx.AsyncClient,
    mukeys: list[str],
) -> list[dict[str, Any]]:
    """GROUP H Bearing Capacity."""
    sql = f"""
SELECT co.mukey, co.cokey, co.compname,
       ch.hzname, ch.hzdept_r,
       bc.chiavalue AS bearing_capacity,
       sett.chiavalue AS settlement_potential
FROM component co
INNER JOIN chorizon ch ON ch.cokey = co.cokey
LEFT JOIN chia AS bc ON bc.chkey = ch.chkey
    AND bc.chiakind = 'Soil bearing capacity'
LEFT JOIN chia AS sett ON sett.chkey = ch.chkey
    AND sett.chiakind = 'Settlement potential'
WHERE co.mukey IN ({_fmt_mukeys(mukeys)})
AND co.majcompflag = 'Yes'
ORDER BY co.mukey, ch.hzdept_r
""".strip()
    return await _sda_post(client, sql)


async def get_group_i_interpretations(
    client: httpx.AsyncClient,
    mukeys: list[str],
) -> list[dict[str, Any]]:
    """GROUP I Septic/Suitability Interpretations."""
    sql = f"""
SELECT co.mukey, co.compname, si.interphr, si.interphrc, si.mrulename
FROM component co
INNER JOIN cointerp si ON si.cokey = co.cokey
WHERE co.mukey IN ({_fmt_mukeys(mukeys)})
AND co.majcompflag = 'Yes'
AND si.mrulename IN (
  'SEE - Septic Tank Absorption Fields',
  'DHS - Drainage - Lawns and Landscaping',
  'ENG - Construction Materials - Embankments',
  'ENG - Construction Materials - Road Fill',
  'ENG - Dwellings Without Basements',
  'ENG - Dwellings With Basements',
  'ENG - Local Roads and Streets',
  'ENG - Small Commercial Buildings',
  'ENG - Shallow Excavations',
  'ENG - Trench Sanitary Landfill',
  'AGR - Irrigated Capability Class',
  'FOR - Woodland Suitability - Timber Production',
  'REC - Paths and Trails'
)
ORDER BY co.mukey, si.mrulename
""".strip()
    return await _sda_post(client, sql)


# ── Top-level aggregator ──────────────────────────────────────────────────────

async def get_all_tabular(mukeys: list[str]) -> dict[str, list[dict[str, Any]]]:
    """Run all 9 tabular query groups concurrently against SDA.

    Groups A and B are fatal on failure (exception propagates).
    Groups C–I are non-fatal: a warning is logged and an empty list is returned.

    Returns a dict with keys:
        mapunit, components, restrictions, engineering, flooding,
        hydric, corrosivity, bearing, interpretations
    """
    async with httpx.AsyncClient(
        timeout=_TIMEOUT,
        follow_redirects=True,
        trust_env=False,
    ) as client:
        results = await asyncio.gather(
            get_group_a_mapunit(client, mukeys),        # 0 — fatal
            get_group_b_components(client, mukeys),     # 1 — fatal
            get_group_c_restrictions(client, mukeys),   # 2 — non-fatal
            get_group_d_engineering(client, mukeys),    # 3 — non-fatal
            get_group_e_flooding(client, mukeys),       # 4 — non-fatal
            get_group_f_hydric(client, mukeys),         # 5 — non-fatal
            get_group_g_corrosivity(client, mukeys),    # 6 — non-fatal
            get_group_h_bearing(client, mukeys),        # 7 — non-fatal
            get_group_i_interpretations(client, mukeys),# 8 — non-fatal
            return_exceptions=True,
        )

    _group_names = (
        "mapunit",
        "components",
        "restrictions",
        "engineering",
        "flooding",
        "hydric",
        "corrosivity",
        "bearing",
        "interpretations",
    )

    # Groups A (index 0) and B (index 1) are fatal
    for fatal_idx in (0, 1):
        if isinstance(results[fatal_idx], BaseException):
            log.error(
                "SDA group %s query failed (fatal): %s",
                _group_names[fatal_idx],
                results[fatal_idx],
            )
            raise results[fatal_idx]  # type: ignore[misc]

    output: dict[str, list[dict[str, Any]]] = {}
    for idx, name in enumerate(_group_names):
        res = results[idx]
        if isinstance(res, BaseException):
            log.warning(
                "SDA group %s query failed (non-fatal): %s",
                name,
                res,
            )
            output[name] = []
        else:
            output[name] = res  # type: ignore[assignment]

    return output


# ── Spatial mukey discovery ───────────────────────────────────────────────────

async def discover_mukeys_by_bbox(
    bbox: tuple[float, float, float, float],
) -> list[str]:
    """Use SDA_Get_Mukey_from_intersection_with_WktWgs84 to get mukeys.

    bbox = (minlon, minlat, maxlon, maxlat)
    Returns a list of mukey strings; empty list if none found or on error.
    """
    minlon, minlat, maxlon, maxlat = bbox
    wkt = (
        f"POLYGON(({minlon} {minlat},{maxlon} {minlat},"
        f"{maxlon} {maxlat},{minlon} {maxlat},{minlon} {minlat}))"
    )
    sql = f"SELECT * FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('{wkt}')"

    async with httpx.AsyncClient(
        timeout=_TIMEOUT,
        follow_redirects=True,
        trust_env=False,
    ) as client:
        try:
            rows = await _sda_post(client, sql)
        except Exception as exc:
            log.warning("SDA mukey discovery failed: %s", exc)
            return []

    # The function returns a single-column table; the column name varies
    # (typically "mukey").  Extract whatever the first column value is.
    mukeys: list[str] = []
    for row in rows:
        # row is a dict; grab first value regardless of key name
        for val in row.values():
            mk = str(val).strip() if val is not None else ""
            if mk:
                mukeys.append(mk)
            break  # only the first column matters

    return mukeys
