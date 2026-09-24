from agents import Agent

from AIAgentSpace.asteroidexplorer_agenttools import AsteroidExplorerAgentTools
from AIAgentSpace.imageexplorer_agenttools import ImageExplorerAgentTools


def create_science_fact_checker_agent() -> Agent:
    """Create the Science Fact-Checker specialist agent."""
    return Agent(
        name="Science Fact-Checker",
        instructions=(
            "You are the Science Fact-Checker for NASA Space Newsroom. You receive "
            "one selected discovery or story lead and verify it against NASA/JPL "
            "sources. Check title and date, NASA/JPL source, measurements, whether "
            "claims are supported, and whether asteroid language is exaggerated. "
            "Use APOD and NASA media tools for image/story source checks. Use "
            "NeoWs and JPL small-body tools for asteroid measurements, close "
            "approach context, and risk language. Be careful with asteroid wording: "
            "do not call an asteroid dangerous unless the source supports that. "
            "Return exactly these sections: Verified facts, Unsupported claims, "
            "Important context, Confidence level."
        ),
        model="gpt-4o-mini",
        tools=[
            ImageExplorerAgentTools.fetch_nasa_apod,
            ImageExplorerAgentTools.search_nasa_media_library,
            ImageExplorerAgentTools.fetch_nasa_media_asset,
            AsteroidExplorerAgentTools.get_neows_feed,
            AsteroidExplorerAgentTools.get_neows_lookup,
            AsteroidExplorerAgentTools.get_sb_close_approach_data,
            AsteroidExplorerAgentTools.get_sbdb,
            AsteroidExplorerAgentTools.get_sentry,
        ],
    )
