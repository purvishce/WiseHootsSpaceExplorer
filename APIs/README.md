# NASA Space Newsroom APIs

This folder contains reusable NASA and JPL API wrappers for the NASA Space Newsroom agent project.

## NASA APIs

Implemented in `nasa_apis.py`:

```text
get_nasa_apod
get_neows_feed
get_neows_lookup
get_neows_browse
get_epic_images
build_epic_image_url
get_earth_imagery
get_earth_assets
search_nasa_image_library
get_nasa_media_asset
get_nasa_media_metadata_location
get_nasa_media_captions_location
get_nasa_media_album
```

## JPL APIs

Implemented in `jpl_apis.py`:

```text
get_sb_close_approach_data
get_sbdb
query_sbdb
get_sentry
get_scout
get_fireball
get_nhats
identify_small_bodies
```

## Environment

Use a project-root `.env` file:

```bash
NASA_API_KEY=your_nasa_key
OPENAI_API_KEY=your_openai_key
```

`NASA_API_KEY` falls back to `DEMO_KEY`, but a real key is recommended because `DEMO_KEY` is rate-limited.

## Used By

The wrappers are used by tools in:

```text
AIAgentSpace/agenttools.py
AIAgentSpace/imageexplorer_agenttools.py
AIAgentSpace/asteroidexplorer_agenttools.py
```
