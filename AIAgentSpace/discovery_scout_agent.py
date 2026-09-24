from agents import Agent

from AIAgentSpace.asteroidexplorer_agenttools import AsteroidExplorerAgentTools
from AIAgentSpace.imageexplorer_agenttools import ImageExplorerAgentTools


def create_discovery_scout_agent() -> Agent:
    """Create the Discovery Scout specialist agent."""
    return Agent(
        name="Discovery Scout",
        handoff_description=(
            "Finds two or three possible NASA space story leads using APOD, "
            "NASA Image and Video Library, and near-Earth asteroid data."
        ),
        instructions=(
            "You are the Discovery Scout for NASA Space Newsroom. Search the "
            "available NASA sources and return two or three possible story ideas. "
            "Use fetch_nasa_apod for APOD, search_nasa_media_library for NASA "
            "Image and Video Library items, and get_neows_feed for near-Earth "
            "asteroid activity. If a NASA media result looks promising, use "
            "fetch_nasa_media_asset to get direct asset URLs. Do not write the "
            "final article, choose a headline style, create a quiz, or decide how "
            "to present the story. Return only concise story leads with: story "
            "idea, source used, why it may interest young readers, and useful "
            "image or data URLs when available."
        ),
        model="gpt-4o-mini",
        tools=[
            ImageExplorerAgentTools.fetch_nasa_apod,
            ImageExplorerAgentTools.search_nasa_media_library,
            ImageExplorerAgentTools.fetch_nasa_media_asset,
            AsteroidExplorerAgentTools.get_neows_feed,
        ],
    )
