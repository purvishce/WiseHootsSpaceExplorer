from AIAgentSpace.agenttools import (
    get_fireball,
    get_neows_browse,
    get_neows_feed,
    get_neows_lookup,
    get_nhats,
    get_sb_close_approach_data,
    get_sbdb,
    get_scout,
    get_sentry,
    identify_small_bodies,
    query_sbdb,
    send_pushover,
)


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
