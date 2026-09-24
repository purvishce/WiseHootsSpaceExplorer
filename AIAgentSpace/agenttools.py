import json
import os
import sys
from pathlib import Path
from typing import Any

import requests
from agents import function_tool


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from APIs.nasa_apis import (
    NasaApiError,
    build_epic_image_url,
    get_earth_imagery,
    get_epic_images,
    get_nasa_media_asset,
    get_nasa_media_metadata_location,
    get_nasa_apod,
    get_neows_browse as nasa_get_neows_browse,
    get_neows_feed as nasa_get_neows_feed,
    get_neows_lookup as nasa_get_neows_lookup,
    search_nasa_image_library,
)
from APIs.jpl_apis import (
    JplApiError,
    get_fireball as jpl_get_fireball,
    get_nhats as jpl_get_nhats,
    get_sb_close_approach_data as jpl_get_sb_close_approach_data,
    get_sbdb as jpl_get_sbdb,
    get_scout as jpl_get_scout,
    get_sentry as jpl_get_sentry,
    identify_small_bodies as jpl_identify_small_bodies,
    query_sbdb as jpl_query_sbdb,
)


def _parse_extra_filters(extra_filters_json: str | None) -> dict[str, Any]:
    if not extra_filters_json:
        return {}
    try:
        parsed = json.loads(extra_filters_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"extra_filters_json must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("extra_filters_json must be a JSON object.")
    return parsed


def _compact_json(data: Any, max_chars: int = 3500) -> str:
    text = json.dumps(data, indent=2, default=str)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... truncated ..."


@function_tool
def send_pushover(message: str, title: str = "NASA APOD Agent") -> str:
    """Send a Pushover notification."""
    user_key = os.getenv("PUSHOVER_USER")
    app_token = os.getenv("PUSHOVER_TOKEN")

    if not user_key or not app_token:
        return "Pushover is not configured. Set PUSHOVER_USER and PUSHOVER_TOKEN in .env."

    response = requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": app_token,
            "user": user_key,
            "title": title,
            "message": message,
        },
        timeout=10,
    )

    if response.ok:
        return "Pushover notification sent."

    return f"Pushover notification failed: {response.status_code} {response.text}"


@function_tool
def fetch_nasa_apod(date: str | None = None, hd: bool = False) -> str:
    """
    Fetch NASA's Astronomy Picture of the Day.

    Args:
        date: Optional APOD date in YYYY-MM-DD format. Leave empty for today.
        hd: Whether to prefer the high-definition image URL when available.
    """
    title, image_url, explanation = get_nasa_apod(date=date, hd=hd)

    if image_url:
        return f"Title: {title}\nImage URL: {image_url}\nExplanation: {explanation}"

    return f"Title: {title}\nExplanation: {explanation}"


@function_tool
def fetch_epic_images(
    collection: str = "natural",
    date: str | None = None,
    image_type: str = "jpg",
    max_results: int = 5,
) -> str:
    """
    Fetch NASA EPIC Earth image metadata.

    Args:
        collection: EPIC collection, usually natural or enhanced.
        date: Optional EPIC date in YYYY-MM-DD format. Leave empty for latest images.
        image_type: Image file type to build URLs for, usually jpg or png.
        max_results: Maximum number of images to include in the response.
    """
    try:
        images = get_epic_images(collection=collection, date=date)
    except NasaApiError as exc:
        return f"Error fetching EPIC images: {exc}"

    if not images:
        search_date = date or "the latest available date"
        return f"No EPIC {collection} images found for {search_date}."

    image_lines: list[str] = []
    for image in images[:max_results]:
        image_name = image.get("image")
        image_date = image.get("date", "")
        caption = image.get("caption", "No caption available.")
        centroid = image.get("centroid_coordinates", {})

        details = [
            f"{image_name or 'Unknown image'}",
            f"date: {image_date or 'unknown'}",
            f"caption: {caption}",
        ]

        if image_name and image_date:
            details.append(f"url: {build_epic_image_url(image_name, image_date, collection, image_type)}")
        if centroid:
            lat = centroid.get("lat")
            lon = centroid.get("lon")
            details.append(f"centroid: lat {lat}, lon {lon}")

        image_lines.append("- " + "; ".join(details))

    header = f"Found {len(images)} EPIC {collection} image(s)"
    if len(image_lines) < len(images):
        header += f"; showing {len(image_lines)}"

    return header + ":\n" + "\n".join(image_lines)


@function_tool
def create_epic_image_url(
    image_name: str,
    image_date: str,
    collection: str = "natural",
    image_type: str = "jpg",
) -> str:
    """
    Build a public NASA EPIC image URL from EPIC image metadata.

    Args:
        image_name: EPIC image name, such as epic_1b_20260920010437.
        image_date: EPIC image date or timestamp, such as 2026-09-20 or 2026-09-20 01:04:37.
        collection: EPIC collection, usually natural or enhanced.
        image_type: Image file type, usually jpg or png.
    """
    try:
        return build_epic_image_url(image_name, image_date, collection, image_type)
    except ValueError as exc:
        return f"Error building EPIC image URL: {exc}"


@function_tool
def fetch_earth_imagery(
    lat: float,
    lon: float,
    date: str | None = None,
    dim: float | None = 0.1,
) -> str:
    """
    Fetch NASA Earth imagery metadata for a latitude and longitude.

    Args:
        lat: Latitude of the location.
        lon: Longitude of the location.
        date: Optional image date in YYYY-MM-DD format.
        dim: Width and height of the image in degrees.
    """
    try:
        data = get_earth_imagery(lat=lat, lon=lon, date=date, dim=dim)
    except NasaApiError as exc:
        return f"Error fetching Earth imagery: {exc}"

    url = data.get("url")
    imagery_date = data.get("date") or date or "unknown"
    resource = data.get("resource", {})
    dataset = resource.get("dataset")
    planet = resource.get("planet")

    details = [
        f"Latitude: {lat}",
        f"Longitude: {lon}",
        f"Date: {imagery_date}",
    ]
    if dataset:
        details.append(f"Dataset: {dataset}")
    if planet:
        details.append(f"Planet: {planet}")
    if url:
        details.append(f"Image URL: {url}")

    return "\n".join(details)


@function_tool
def search_nasa_media_library(
    query: str,
    media_type: str | None = None,
    year_start: int | None = None,
    year_end: int | None = None,
    page_size: int = 5,
) -> str:
    """
    Search NASA's Image and Video Library.

    Args:
        query: Search text, such as Apollo 11, Mars, or Hubble.
        media_type: Optional media type, such as image, video, or audio.
        year_start: Optional earliest year to search.
        year_end: Optional latest year to search.
        page_size: Maximum number of results to request and show.
    """
    try:
        data = search_nasa_image_library(
            q=query,
            media_type=media_type,
            year_start=year_start,
            year_end=year_end,
            page_size=page_size,
        )
    except NasaApiError as exc:
        return f"Error searching NASA media library: {exc}"

    collection = data.get("collection", {})
    items = collection.get("items", [])
    total_hits = collection.get("metadata", {}).get("total_hits", len(items))
    if not items:
        return f"No NASA media library results found for {query}."

    result_lines: list[str] = []
    for item in items[:page_size]:
        item_data = (item.get("data") or [{}])[0]
        links = item.get("links") or []
        preview_url = links[0].get("href") if links else None

        details = [
            f"{item_data.get('title', 'Untitled')}",
            f"NASA ID: {item_data.get('nasa_id', 'unknown')}",
            f"media type: {item_data.get('media_type', 'unknown')}",
            f"date: {item_data.get('date_created', 'unknown')}",
        ]
        if preview_url:
            details.append(f"preview: {preview_url}")

        result_lines.append("- " + "; ".join(details))

    header = f"Found {total_hits} NASA media result(s)"
    if len(result_lines) < total_hits:
        header += f"; showing {len(result_lines)}"

    return header + ":\n" + "\n".join(result_lines)


@function_tool
def fetch_nasa_media_asset(nasa_id: str, max_results: int = 10) -> str:
    """
    Fetch an asset manifest from NASA's Image and Video Library.

    Args:
        nasa_id: NASA media ID returned by search_nasa_media_library.
        max_results: Maximum asset URLs to include.
    """
    try:
        data = get_nasa_media_asset(nasa_id)
    except NasaApiError as exc:
        return f"Error fetching NASA media asset: {exc}"

    collection = data.get("collection", {})
    items = collection.get("items", [])
    if not items:
        return f"No asset files found for NASA ID {nasa_id}."

    asset_lines = []
    for item in items[:max_results]:
        href = item.get("href")
        if href:
            asset_lines.append(f"- {href}")

    header = f"Found {len(items)} asset file(s) for NASA ID {nasa_id}"
    if len(asset_lines) < len(items):
        header += f"; showing {len(asset_lines)}"

    return header + ":\n" + "\n".join(asset_lines)


@function_tool
def get_neows_feed(
    start_date: str | None = None,
    end_date: str | None = None,
    max_results: int = 10,
) -> str:
    """
    Fetch NASA NeoWs near-Earth asteroid feed for a date range.

    Args:
        start_date: Optional start date in YYYY-MM-DD format.
        end_date: Optional end date in YYYY-MM-DD format.
        max_results: Maximum asteroid summaries to return.
    """
    try:
        data = nasa_get_neows_feed(start_date=start_date, end_date=end_date)
    except NasaApiError as exc:
        return f"Error fetching NeoWs feed: {exc}"

    near_earth_objects = data.get("near_earth_objects", {})
    if not near_earth_objects:
        return "No near-Earth asteroids found for that date range."

    asteroid_lines: list[str] = []
    for date, asteroids in sorted(near_earth_objects.items()):
        for asteroid in asteroids:
            if len(asteroid_lines) >= max_results:
                break
            approach = (asteroid.get("close_approach_data") or [{}])[0]
            miss_distance = approach.get("miss_distance", {})
            velocity = approach.get("relative_velocity", {})
            diameter = asteroid.get("estimated_diameter", {}).get("meters", {})
            details = [
                f"{asteroid.get('name', 'Unknown asteroid')} on {date}",
                f"id: {asteroid.get('id', 'unknown')}",
                "potentially hazardous"
                if asteroid.get("is_potentially_hazardous_asteroid")
                else "not potentially hazardous",
            ]
            if miss_distance.get("lunar"):
                details.append(f"{float(miss_distance['lunar']):.2f} lunar distances away")
            if velocity.get("kilometers_per_hour"):
                details.append(f"{float(velocity['kilometers_per_hour']):,.0f} km/h")
            if diameter.get("estimated_diameter_min") is not None and diameter.get("estimated_diameter_max") is not None:
                details.append(
                    f"{diameter['estimated_diameter_min']:.1f}-{diameter['estimated_diameter_max']:.1f} m wide"
                )
            asteroid_lines.append("- " + "; ".join(details))
        if len(asteroid_lines) >= max_results:
            break

    total = data.get("element_count", len(asteroid_lines))
    header = f"Found {total} near-Earth asteroid(s)"
    if len(asteroid_lines) < total:
        header += f"; showing {len(asteroid_lines)}"
    return header + ":\n" + "\n".join(asteroid_lines)


@function_tool
def get_neows_lookup(asteroid_id: str) -> str:
    """
    Fetch one NASA NeoWs asteroid by asteroid ID.

    Args:
        asteroid_id: NASA NeoWs asteroid ID.
    """
    try:
        data = nasa_get_neows_lookup(asteroid_id)
    except NasaApiError as exc:
        return f"Error fetching NeoWs asteroid lookup: {exc}"

    diameter = data.get("estimated_diameter", {}).get("meters", {})
    details = [
        f"Name: {data.get('name', 'unknown')}",
        f"ID: {data.get('id', asteroid_id)}",
        f"NASA JPL URL: {data.get('nasa_jpl_url', 'unavailable')}",
        "Potentially hazardous: "
        + ("yes" if data.get("is_potentially_hazardous_asteroid") else "no"),
    ]
    if diameter.get("estimated_diameter_min") is not None and diameter.get("estimated_diameter_max") is not None:
        details.append(f"Estimated diameter: {diameter['estimated_diameter_min']:.1f}-{diameter['estimated_diameter_max']:.1f} m")
    if data.get("close_approach_data"):
        details.append(f"Close approach records: {len(data['close_approach_data'])}")
    return "\n".join(details)


@function_tool
def get_neows_browse(page: int = 0, size: int = 20) -> str:
    """
    Browse NASA NeoWs near-Earth asteroid records.

    Args:
        page: Result page number.
        size: Number of asteroid records per page.
    """
    try:
        data = nasa_get_neows_browse(page=page, size=size)
    except NasaApiError as exc:
        return f"Error browsing NeoWs asteroids: {exc}"

    objects = data.get("near_earth_objects", [])
    if not objects:
        return "No NeoWs asteroid records found."

    lines = []
    for asteroid in objects[:size]:
        lines.append(
            "- "
            + "; ".join(
                [
                    asteroid.get("name", "Unknown asteroid"),
                    f"id: {asteroid.get('id', 'unknown')}",
                    "potentially hazardous"
                    if asteroid.get("is_potentially_hazardous_asteroid")
                    else "not potentially hazardous",
                ]
            )
        )
    page_info = data.get("page", {})
    return f"NeoWs page {page_info.get('number', page)} of asteroid records:\n" + "\n".join(lines)


@function_tool
def get_sb_close_approach_data(
    des: str | None = None,
    date_min: str | None = None,
    date_max: str | None = None,
    dist_max: str | None = None,
    body: str | None = None,
    sort: str | None = None,
    limit: int | None = 10,
    extra_filters_json: str | None = None,
) -> str:
    """
    Fetch asteroid and comet close approaches from JPL CAD.

    Args:
        des: Object designation.
        date_min: Minimum close-approach date.
        date_max: Maximum close-approach date.
        dist_max: Maximum distance filter, such as 0.05 for AU.
        body: Close-approach body, such as Earth.
        sort: Sort field.
        limit: Maximum rows to return.
        extra_filters_json: Optional JSON object of extra JPL CAD filters.
    """
    try:
        filters = _parse_extra_filters(extra_filters_json)
        data = jpl_get_sb_close_approach_data(
            des=des,
            date_min=date_min,
            date_max=date_max,
            dist_max=dist_max,
            body=body,
            sort=sort,
            limit=limit,
            **filters,
        )
    except (JplApiError, ValueError) as exc:
        return f"Error fetching JPL close-approach data: {exc}"
    return _compact_json(data)


@function_tool
def get_sbdb(sstr: str | None = None, spk: int | None = None, des: str | None = None) -> str:
    """
    Fetch detailed JPL Small-Body Database data for one asteroid or comet.

    Args:
        sstr: Search string, such as an asteroid name or designation.
        spk: SPK object ID.
        des: Object designation.
    """
    try:
        data = jpl_get_sbdb(sstr=sstr, spk=spk, des=des)
    except JplApiError as exc:
        return f"Error fetching JPL SBDB object: {exc}"
    return _compact_json(data)


@function_tool
def query_sbdb(fields: str | None = None, limit: int | None = 10, extra_filters_json: str | None = None) -> str:
    """
    Search and filter known small bodies using the JPL SBDB Query API.

    Args:
        fields: Comma-separated fields to return.
        limit: Maximum rows to return.
        extra_filters_json: Optional JSON object of SBDB query filters.
    """
    try:
        filters = _parse_extra_filters(extra_filters_json)
        data = jpl_query_sbdb(fields=fields, limit=limit, **filters)
    except (JplApiError, ValueError) as exc:
        return f"Error querying JPL SBDB: {exc}"
    return _compact_json(data)


@function_tool
def get_sentry(
    des: str | None = None,
    spk: int | None = None,
    removed: bool | None = None,
    include_all: bool | None = None,
    extra_filters_json: str | None = None,
) -> str:
    """
    Fetch potential Earth-impact risk assessment data from JPL Sentry.

    Args:
        des: Object designation.
        spk: SPK object ID.
        removed: Whether to include removed objects.
        include_all: Whether to request all Sentry records.
        extra_filters_json: Optional JSON object of extra Sentry filters.
    """
    try:
        filters = _parse_extra_filters(extra_filters_json)
        data = jpl_get_sentry(des=des, spk=spk, removed=removed, all=include_all, **filters)
    except (JplApiError, ValueError) as exc:
        return f"Error fetching JPL Sentry data: {exc}"
    return _compact_json(data)


@function_tool
def get_scout(
    tdes: str | None = None,
    eph_start: str | None = None,
    eph_stop: str | None = None,
    eph_step: str | None = None,
    plot: str | None = None,
    orbits: bool | None = None,
    extra_options_json: str | None = None,
) -> str:
    """
    Fetch JPL Scout early-analysis data for newly discovered NEO candidates.

    Args:
        tdes: Temporary designation.
        eph_start: Ephemeris start time.
        eph_stop: Ephemeris stop time.
        eph_step: Ephemeris step size.
        plot: Plot option.
        orbits: Whether to include orbit data.
        extra_options_json: Optional JSON object of extra Scout options.
    """
    try:
        options = _parse_extra_filters(extra_options_json)
        data = jpl_get_scout(
            tdes=tdes,
            eph_start=eph_start,
            eph_stop=eph_stop,
            eph_step=eph_step,
            plot=plot,
            orbits=orbits,
            **options,
        )
    except (JplApiError, ValueError) as exc:
        return f"Error fetching JPL Scout data: {exc}"
    return _compact_json(data)


@function_tool
def get_fireball(
    date_min: str | None = None,
    date_max: str | None = None,
    energy_min: float | None = None,
    energy_max: float | None = None,
    req_loc: bool | None = None,
    req_alt: bool | None = None,
    vel_comp: bool | None = None,
    sort: str | None = None,
    limit: int | None = 10,
    extra_filters_json: str | None = None,
) -> str:
    """
    Fetch atmospheric fireball impact observations from JPL.

    Args:
        date_min: Minimum event date.
        date_max: Maximum event date.
        energy_min: Minimum impact energy.
        energy_max: Maximum impact energy.
        req_loc: Require location data.
        req_alt: Require altitude data.
        vel_comp: Include velocity components.
        sort: Sort field.
        limit: Maximum rows to return.
        extra_filters_json: Optional JSON object of extra Fireball filters.
    """
    try:
        filters = _parse_extra_filters(extra_filters_json)
        data = jpl_get_fireball(
            date_min=date_min,
            date_max=date_max,
            energy_min=energy_min,
            energy_max=energy_max,
            req_loc=req_loc,
            req_alt=req_alt,
            vel_comp=vel_comp,
            sort=sort,
            limit=limit,
            **filters,
        )
    except (JplApiError, ValueError) as exc:
        return f"Error fetching JPL Fireball data: {exc}"
    return _compact_json(data)


@function_tool
def get_nhats(
    des: str | None = None,
    dv: int | None = None,
    dur: int | None = None,
    stay: int | None = None,
    launch: str | None = None,
    h: float | None = None,
    extra_constraints_json: str | None = None,
) -> str:
    """
    Fetch JPL NHATS human-accessible near-Earth object data.

    Args:
        des: Object designation.
        dv: Delta-v constraint.
        dur: Mission duration constraint.
        stay: Stay duration constraint.
        launch: Launch window constraint.
        h: Absolute magnitude constraint.
        extra_constraints_json: Optional JSON object of extra NHATS constraints.
    """
    try:
        constraints = _parse_extra_filters(extra_constraints_json)
        data = jpl_get_nhats(des=des, dv=dv, dur=dur, stay=stay, launch=launch, h=h, **constraints)
    except (JplApiError, ValueError) as exc:
        return f"Error fetching JPL NHATS data: {exc}"
    return _compact_json(data)


@function_tool
def identify_small_bodies(
    mpc_code: str,
    obs_time: str,
    fov_ra_lim: str,
    fov_dec_lim: str,
    sb_kind: str | None = None,
    extra_options_json: str | None = None,
) -> str:
    """
    Identify small bodies within an observation field of view.

    Args:
        mpc_code: Observatory MPC code.
        obs_time: Observation time.
        fov_ra_lim: Field-of-view right ascension limits.
        fov_dec_lim: Field-of-view declination limits.
        sb_kind: Optional small-body kind filter.
        extra_options_json: Optional JSON object of extra identification options.
    """
    try:
        options = _parse_extra_filters(extra_options_json)
        data = jpl_identify_small_bodies(
            mpc_code=mpc_code,
            obs_time=obs_time,
            fov_ra_lim=fov_ra_lim,
            fov_dec_lim=fov_dec_lim,
            sb_kind=sb_kind,
            **options,
        )
    except (JplApiError, ValueError) as exc:
        return f"Error identifying small bodies: {exc}"
    return _compact_json(data)



class ImageExplorerAgentTools:
    """OpenAI Agents SDK tools for finding NASA image URLs."""

    send_pushover = send_pushover
    fetch_nasa_apod = fetch_nasa_apod
    fetch_epic_images = fetch_epic_images
    create_epic_image_url = create_epic_image_url
    fetch_earth_imagery = fetch_earth_imagery
    search_nasa_media_library = search_nasa_media_library
    fetch_nasa_media_asset = fetch_nasa_media_asset


class AsteroidExplorerAgentTools:
    """OpenAI Agents SDK tools for NASA/JPL asteroid and small-body data."""

    send_pushover = send_pushover
    get_neows_feed = get_neows_feed
    get_neows_lookup = get_neows_lookup
    get_neows_browse = get_neows_browse
    get_sb_close_approach_data = get_sb_close_approach_data
    get_sbdb = get_sbdb
    query_sbdb = query_sbdb
    get_sentry = get_sentry
    get_scout = get_scout
    get_fireball = get_fireball
    get_nhats = get_nhats
    identify_small_bodies = identify_small_bodies


class AgentTools:
    """Compatibility namespace containing all available OpenAI Agents SDK tools."""

    send_pushover = send_pushover
    fetch_nasa_apod = fetch_nasa_apod
    fetch_epic_images = fetch_epic_images
    create_epic_image_url = create_epic_image_url
    fetch_earth_imagery = fetch_earth_imagery
    search_nasa_media_library = search_nasa_media_library
    fetch_nasa_media_asset = fetch_nasa_media_asset
    get_neows_feed = get_neows_feed
    get_neows_lookup = get_neows_lookup
    get_neows_browse = get_neows_browse
    get_sb_close_approach_data = get_sb_close_approach_data
    get_sbdb = get_sbdb
    query_sbdb = query_sbdb
    get_sentry = get_sentry
    get_scout = get_scout
    get_fireball = get_fireball
    get_nhats = get_nhats
    identify_small_bodies = identify_small_bodies
