from AIAgentSpace.agenttools import (
    create_epic_image_url,
    fetch_earth_imagery,
    fetch_epic_images,
    fetch_nasa_apod,
    fetch_nasa_media_asset,
    search_nasa_media_library,
    send_pushover,
)


class ImageExplorerAgentTools:
    """OpenAI Agents SDK tools for finding NASA image URLs."""

    send_pushover = send_pushover
    fetch_nasa_apod = fetch_nasa_apod
    fetch_epic_images = fetch_epic_images
    create_epic_image_url = create_epic_image_url
    fetch_earth_imagery = fetch_earth_imagery
    search_nasa_media_library = search_nasa_media_library
    fetch_nasa_media_asset = fetch_nasa_media_asset
