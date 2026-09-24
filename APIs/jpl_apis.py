import os
from typing import Any

import requests


JPL_SSD_API_BASE_URL = "https://ssd-api.jpl.nasa.gov"
JPL_HORIZONS_API_BASE_URL = "https://ssd.jpl.nasa.gov/api"
DEFAULT_TIMEOUT = 30
DEFAULT_USER_AGENT = "AgenticAICodeSample/1.0 (JPL API wrapper)"


class JplApiError(Exception):
    """Raised when a JPL API request fails."""


def _user_agent(user_agent: str | None = None) -> str:
    return user_agent or os.getenv("JPL_USER_AGENT") or DEFAULT_USER_AGENT


def _normalize_key(key: str) -> str:
    if key.islower():
        return key.replace("_", "-")
    return key


def _clean_params(params: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in params.items():
        if value is None or value == "":
            continue
        if isinstance(value, bool):
            value = str(value).lower()
        cleaned[_normalize_key(key)] = value
    return cleaned


def _extract_error_message(response: requests.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text

    if isinstance(data, dict):
        for key in ("message", "error", "error_message", "msg"):
            value = data.get(key)
            if value:
                return str(value)

    return str(data)


def _get(
    endpoint: str,
    params: dict[str, Any] | None = None,
    *,
    base_url: str = JPL_SSD_API_BASE_URL,
    timeout: int = DEFAULT_TIMEOUT,
    user_agent: str | None = None,
    expect_json: bool = True,
) -> Any:
    url = f"{base_url}/{endpoint.lstrip('/')}"
    headers = {"User-Agent": _user_agent(user_agent)}

    try:
        response = requests.get(
            url,
            params=_clean_params(params or {}),
            headers=headers,
            timeout=timeout,
        )
        if not response.ok:
            message = _extract_error_message(response)
            raise JplApiError(f"{response.status_code}: {message}")
        if not expect_json:
            return response.text
        return response.json()
    except requests.exceptions.RequestException as exc:
        raise JplApiError(f"Network error: {exc}") from exc
    except ValueError as exc:
        raise JplApiError("JPL returned a non-JSON response.") from exc


def get_sb_close_approach_data(
    des: str | None = None,
    date_min: str | None = None,
    date_max: str | None = None,
    dist_max: str | None = None,
    body: str | None = None,
    sort: str | None = None,
    limit: int | None = None,
    **filters: Any,
) -> dict[str, Any]:
    """Fetch asteroid and comet close approaches from the CAD API."""
    return _get(
        "cad.api",
        {
            "des": des,
            "date_min": date_min,
            "date_max": date_max,
            "dist_max": dist_max,
            "body": body,
            "sort": sort,
            "limit": limit,
            **filters,
        },
    )


def get_sbdb(
    sstr: str | None = None,
    spk: str | int | None = None,
    des: str | None = None,
    **options: Any,
) -> dict[str, Any]:
    """Fetch detailed Small-Body Database data for one asteroid or comet."""
    return _get(
        "sbdb.api",
        {
            "sstr": sstr,
            "spk": spk,
            "des": des,
            **options,
        },
    )


def query_sbdb(
    fields: str | None = None,
    limit: int | None = None,
    **filters: Any,
) -> dict[str, Any]:
    """Search and filter known small bodies using the SBDB Query API."""
    return _get(
        "sbdb_query.api",
        {
            "fields": fields,
            "limit": limit,
            **filters,
        },
    )


def get_sentry(
    des: str | None = None,
    spk: str | int | None = None,
    removed: bool | None = None,
    all: bool | None = None,
    **filters: Any,
) -> dict[str, Any]:
    """Fetch potential Earth-impact risk assessment data from Sentry."""
    return _get(
        "sentry.api",
        {
            "des": des,
            "spk": spk,
            "removed": removed,
            "all": all,
            **filters,
        },
    )


def get_scout(
    tdes: str | None = None,
    eph_start: str | bool | None = None,
    eph_stop: str | None = None,
    eph_step: str | None = None,
    plot: str | None = None,
    orbits: bool | None = None,
    **options: Any,
) -> dict[str, Any]:
    """Fetch Scout early-analysis data for newly discovered NEO candidates."""
    return _get(
        "scout.api",
        {
            "tdes": tdes,
            "eph_start": eph_start,
            "eph_stop": eph_stop,
            "eph_step": eph_step,
            "plot": plot,
            "orbits": orbits,
            **options,
        },
    )


def get_fireball(
    date_min: str | None = None,
    date_max: str | None = None,
    energy_min: str | float | None = None,
    energy_max: str | float | None = None,
    req_loc: bool | None = None,
    req_alt: bool | None = None,
    vel_comp: bool | None = None,
    sort: str | None = None,
    limit: int | None = None,
    **filters: Any,
) -> dict[str, Any]:
    """Fetch atmospheric fireball impact observations."""
    return _get(
        "fireball.api",
        {
            "date_min": date_min,
            "date_max": date_max,
            "energy_min": energy_min,
            "energy_max": energy_max,
            "req_loc": req_loc,
            "req_alt": req_alt,
            "vel_comp": vel_comp,
            "sort": sort,
            "limit": limit,
            **filters,
        },
    )


def get_horizons(
    command: str,
    center: str = "500@399",
    start_time: str | None = None,
    stop_time: str | None = None,
    step_size: str | None = None,
    ephem_type: str = "OBSERVER",
    quantities: str | None = None,
    format: str = "json",
    **settings: Any,
) -> dict[str, Any] | str:
    """Fetch positions and motion data from JPL Horizons."""
    expect_json = format != "text"
    return _get(
        "horizons.api",
        {
            "format": format,
            "COMMAND": command,
            "CENTER": center,
            "START_TIME": start_time,
            "STOP_TIME": stop_time,
            "STEP_SIZE": step_size,
            "EPHEM_TYPE": ephem_type,
            "QUANTITIES": quantities,
            **settings,
        },
        base_url=JPL_HORIZONS_API_BASE_URL,
        expect_json=expect_json,
    )


def lookup_horizons(
    sstr: str,
    group: str | None = None,
    format: str = "json",
) -> dict[str, Any] | str:
    """Look up Horizons object aliases, designations, and SPK IDs."""
    expect_json = format != "text"
    return _get(
        "horizons_lookup.api",
        {
            "sstr": sstr,
            "group": group,
            "format": format,
        },
        base_url=JPL_HORIZONS_API_BASE_URL,
        expect_json=expect_json,
    )


def get_sb_mission_design(
    des: str | None = None,
    year: str | int | None = None,
    limit: int | None = None,
    **constraints: Any,
) -> dict[str, Any]:
    """Fetch small-body spacecraft mission opportunity data."""
    return _get(
        "mdesign.api",
        {
            "des": des,
            "year": year,
            "lim": limit,
            **constraints,
        },
    )


def get_sb_observability(
    mpc_code: str,
    obs_time: str,
    **constraints: Any,
) -> dict[str, Any]:
    """Fetch small bodies observable from an observatory at a given time."""
    return _get(
        "sbwobs.api",
        {
            "mpc_code": mpc_code,
            "obs_time": obs_time,
            **constraints,
        },
    )


def get_nhats(
    des: str | None = None,
    dv: int | None = None,
    dur: int | None = None,
    stay: int | None = None,
    launch: str | None = None,
    h: float | None = None,
    **constraints: Any,
) -> dict[str, Any]:
    """Fetch human-accessible NEO data from NHATS."""
    return _get(
        "nhats.api",
        {
            "des": des,
            "dv": dv,
            "dur": dur,
            "stay": stay,
            "launch": launch,
            "h": h,
            **constraints,
        },
    )


def identify_small_bodies(
    mpc_code: str,
    obs_time: str,
    fov_ra_lim: str,
    fov_dec_lim: str,
    sb_kind: str | None = None,
    **options: Any,
) -> dict[str, Any]:
    """Identify small bodies within a field of view at a specified time."""
    return _get(
        "sb_ident.api",
        {
            "mpc_code": mpc_code,
            "obs_time": obs_time,
            "fov_ra_lim": fov_ra_lim,
            "fov_dec_lim": fov_dec_lim,
            "sb_kind": sb_kind,
            **options,
        },
    )


def convert_jd_date(
    jd: str | float | None = None,
    cd: str | None = None,
    format: str | None = None,
) -> dict[str, Any]:
    """Convert between Julian Day numbers and calendar dates."""
    return _get(
        "jd_cal.api",
        {
            "jd": jd,
            "cd": cd,
            "format": format,
        },
    )


def calendar_to_jd(calendar_date: str, format: str | None = None) -> dict[str, Any]:
    """Convert a calendar date/time string to a Julian Day number."""
    return convert_jd_date(cd=calendar_date, format=format)


def jd_to_calendar(julian_day: str | float, format: str | None = None) -> dict[str, Any]:
    """Convert a Julian Day number to a calendar date/time string."""
    return convert_jd_date(jd=julian_day, format=format)
