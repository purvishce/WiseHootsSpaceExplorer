import os
from typing import Any
from urllib.parse import quote
import requests
import asyncio
from pathlib import Path
import requests
from agents import Agent, Runner, function_tool, trace
from openai.types.responses import ResponseTextDeltaEvent
from dotenv import load_dotenv
NASA_API_BASE_URL = "https://api.nasa.gov"
NASA_IMAGES_API_BASE_URL = "https://images-api.nasa.gov"
MARS_ROVER_FALLBACK_BASE_URL = "https://rovers.nebulum.one/api/v1"
EPIC_BASE_URL = "https://epic.gsfc.nasa.gov"
EONET_BASE_URL = "https://eonet.gsfc.nasa.gov/api/v3"
DEFAULT_TIMEOUT = 20


class NasaApiError(Exception):
    """Raised when a NASA API request fails."""


def _api_key(api_key: str | None = None) -> str:
    return api_key or os.getenv("NASA_API_KEY") or "DEMO_KEY"


def _clean_params(params: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in params.items() if value is not None and value != ""}


def _extract_error_message(response: requests.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text

    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict):
            return error.get("message") or str(error)
        if error:
            return str(error)
        if data.get("msg"):
            return str(data["msg"])

    return str(data)


def _get_json(
    url: str,
    params: dict[str, Any] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Any:
    try:
        response = requests.get(url, params=_clean_params(params or {}), timeout=timeout)
        if not response.ok:
            message = _extract_error_message(response)
            raise NasaApiError(f"{response.status_code}: {message}")
        return response.json()
    except requests.exceptions.RequestException as exc:
        raise NasaApiError(f"Network error: {exc}") from exc
    except ValueError as exc:
        raise NasaApiError("NASA returned a non-JSON response.") from exc


def get_nasa_apod(date: str | None = None, hd: bool = False, api_key: str | None = None):
    """
    Fetch APOD and return (title, image_url, explanation).
    Handles errors and non-image media types gracefully for the Gradio UI.
    """
    try:
        data = _get_json(
            f"{NASA_API_BASE_URL}/planetary/apod",
            {
                "api_key": _api_key(api_key),
                "date": date,
                "hd": hd,
            },
        )
    except NasaApiError as exc:
        return ("Error fetching APOD", None, str(exc))

    if isinstance(data, dict) and "error" in data:
        error = data.get("error", {})
        message = error.get("message", "Unknown API error") if isinstance(error, dict) else str(error)
        return ("API error", None, message)

    title = data.get("title", "Astronomy Picture of the Day")
    explanation = data.get("explanation", "")
    media_type = data.get("media_type", "image")

    if media_type == "image":
        image_url = data.get("hdurl") if hd and data.get("hdurl") else data.get("url")
        return (title, image_url, explanation)

    media_url = data.get("url")
    note = f"This APOD is a {media_type}. Open in browser: {media_url}\n\n{explanation}"
    return (title, None, note)


def get_neows_feed(
    start_date: str | None = None,
    end_date: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Fetch near-earth objects within a date range."""
    return _get_json(
        f"{NASA_API_BASE_URL}/neo/rest/v1/feed",
        {
            "api_key": _api_key(api_key),
            "start_date": start_date,
            "end_date": end_date,
        },
    )


def get_neows_lookup(asteroid_id: str, api_key: str | None = None) -> dict[str, Any]:
    """Fetch a specific near-earth object by asteroid id."""
    return _get_json(
        f"{NASA_API_BASE_URL}/neo/rest/v1/neo/{asteroid_id}",
        {"api_key": _api_key(api_key)},
    )


def get_neows_browse(
    page: int = 0,
    size: int = 20,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Browse the near-earth object data set."""
    return _get_json(
        f"{NASA_API_BASE_URL}/neo/rest/v1/neo/browse",
        {
            "api_key": _api_key(api_key),
            "page": page,
            "size": size,
        },
    )




def get_epic_images(
    collection: str = "natural",
    date: str | None = None,
    api_key: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch EPIC image metadata for the latest available date or a specific date."""
    path = f"{collection}/date/{date}" if date else collection
    return _get_json(
        f"{NASA_API_BASE_URL}/EPIC/api/{path}",
        {"api_key": _api_key(api_key)},
    )

#Comment
def build_epic_image_url(
    image_name: str,
    image_date: str,
    collection: str = "natural",
    image_type: str = "jpg",
) -> str:
    """Build the public EPIC image URL from EPIC metadata."""
    year, month, day = image_date[:10].split("-")
    extension = "png" if image_type == "png" else "jpg"
    return (
        f"{EPIC_BASE_URL}/archive/{collection}/{year}/{month}/{day}/"
        f"{image_type}/{image_name}.{extension}"
    )


def get_earth_imagery(
    lat: float,
    lon: float,
    date: str | None = None,
    dim: float | None = 0.1,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Fetch Landsat imagery metadata for a latitude and longitude."""
    return _get_json(
        f"{NASA_API_BASE_URL}/planetary/earth/imagery",
        {
            "api_key": _api_key(api_key),
            "lat": lat,
            "lon": lon,
            "date": date,
            "dim": dim,
        },
    )


def get_earth_assets(
    lat: float,
    lon: float,
    date: str | None = None,
    dim: float | None = 0.1,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Fetch available Landsat asset dates for a latitude and longitude."""
    return _get_json(
        f"{NASA_API_BASE_URL}/planetary/earth/assets",
        {
            "api_key": _api_key(api_key),
            "lat": lat,
            "lon": lon,
            "date": date,
            "dim": dim,
        },
    )


def search_nasa_image_library(
    q: str | None = None,
    center: str | None = None,
    description: str | None = None,
    description_508: str | None = None,
    keywords: str | None = None,
    location: str | None = None,
    media_type: str | None = None,
    nasa_id: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
    photographer: str | None = None,
    secondary_creator: str | None = None,
    title: str | None = None,
    year_start: str | int | None = None,
    year_end: str | int | None = None,
) -> dict[str, Any]:
    """Search NASA's Image and Video Library."""
    params = {
        "q": q,
        "center": center,
        "description": description,
        "description_508": description_508,
        "keywords": keywords,
        "location": location,
        "media_type": media_type,
        "nasa_id": nasa_id,
        "page": page,
        "page_size": page_size,
        "photographer": photographer,
        "secondary_creator": secondary_creator,
        "title": title,
        "year_start": year_start,
        "year_end": year_end,
    }
    if not _clean_params(params):
        raise NasaApiError("At least one search parameter is required.")

    return _get_json(f"{NASA_IMAGES_API_BASE_URL}/search", params)


def get_nasa_media_asset(nasa_id: str) -> dict[str, Any]:
    """Fetch an asset manifest from NASA's Image and Video Library."""
    encoded_id = quote(nasa_id, safe="")
    return _get_json(f"{NASA_IMAGES_API_BASE_URL}/asset/{encoded_id}")


def get_nasa_media_metadata_location(nasa_id: str) -> dict[str, Any]:
    """Fetch the metadata JSON location for a NASA Image and Video Library asset."""
    encoded_id = quote(nasa_id, safe="")
    return _get_json(f"{NASA_IMAGES_API_BASE_URL}/metadata/{encoded_id}")


def get_nasa_media_captions_location(nasa_id: str) -> dict[str, Any]:
    """Fetch the captions location for a NASA Image and Video Library video asset."""
    encoded_id = quote(nasa_id, safe="")
    return _get_json(f"{NASA_IMAGES_API_BASE_URL}/captions/{encoded_id}")


def get_nasa_media_album(
    album_name: str,
    page: int | None = None,
) -> dict[str, Any]:
    """Fetch a NASA Image and Video Library album's contents."""
    encoded_album = quote(album_name, safe="")
    return _get_json(
        f"{NASA_IMAGES_API_BASE_URL}/album/{encoded_album}",
        {"page": page},
    )


def get_eonet_events(
    source: str | None = None,
    category: str | None = None,
    status: str | None = None,
    limit: int | None = None,
    days: int | None = None,
    start: str | None = None,
    end: str | None = None,
    bbox: str | None = None,
    geojson: bool = False,
) -> dict[str, Any]:
    """Fetch EONET v3 natural events."""
    endpoint = "events/geojson" if geojson else "events"
    return _get_json(
        f"{EONET_BASE_URL}/{endpoint}",
        {
            "source": source,
            "category": category,
            "status": status,
            "limit": limit,
            "days": days,
            "start": start,
            "end": end,
            "bbox": bbox,
        },
    )


def get_eonet_categories(category: str | None = None) -> dict[str, Any]:
    """Fetch EONET v3 categories."""
    url = f"{EONET_BASE_URL}/categories"
    if category:
        url = f"{url}/{category}"
    return _get_json(url)


def get_eonet_sources() -> dict[str, Any]:
    """Fetch EONET v3 sources."""
    return _get_json(f"{EONET_BASE_URL}/sources")


def get_eonet_layers(category: str | None = None) -> dict[str, Any]:
    """Fetch EONET v3 imagery layers."""
    url = f"{EONET_BASE_URL}/layers"
    if category:
        url = f"{url}/{category}"
    return _get_json(url)
