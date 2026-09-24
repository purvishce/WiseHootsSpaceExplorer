from agents import Agent

from AIAgentSpace.discovery_scout_agent import create_discovery_scout_agent
from AIAgentSpace.science_fact_checker_agent import create_science_fact_checker_agent
from AIAgentSpace.space_quiz_agent import create_space_quiz_agent
from AIAgentSpace.young_explorer_writer_agent import create_young_explorer_writer_agent


def create_nasa_space_newsroom_agent() -> Agent:
    """Create the NASA Space Newsroom editor agent."""
    discovery_scout = create_discovery_scout_agent()
    science_fact_checker = create_science_fact_checker_agent()
    young_explorer_writer = create_young_explorer_writer_agent()
    space_quiz_agent = create_space_quiz_agent()

    return Agent(
        name="NASA Space Newsroom",
        instructions=(
            "You are the Space News Editor for NASA Space Newsroom. Your job is "
            "to coordinate specialist newsroom agents by calling them as tools. "
            "For the default story workflow, call discovery_scout first, then "
            "science_fact_checker on the selected discovery, then "
            "young_explorer_writer to create the kid-friendly story. Use "
            "space_quiz_agent only when the user explicitly asks for a quiz, "
            "questions, classroom activity, or comprehension check. Do not call "
            "space_quiz_agent for an ordinary story request. Keep editorial "
            "control: specialists return research, writing drafts, or quiz drafts, "
            "and you decide how to pass the result back to the user. Do not invent "
            "NASA/JPL facts that the specialist tools did not support."
        ),
        model="gpt-4o-mini",
        tools=[
            discovery_scout.as_tool(
                tool_name="discovery_scout",
                tool_description=(
                    "Find two or three possible NASA space story leads using APOD, "
                    "NASA Image and Video Library, and near-Earth asteroid data."
                ),
            ),
            science_fact_checker.as_tool(
                tool_name="science_fact_checker",
                tool_description=(
                    "Verify a selected NASA space discovery or story lead for facts, "
                    "sources, measurements, unsupported claims, context, and confidence."
                ),
            ),
            young_explorer_writer.as_tool(
                tool_name="young_explorer_writer",
                tool_description=(
                    "Turn verified NASA space information into a 100-word story for "
                    "a 9-year-old, with a Wow fact and follow-up question."
                ),
            ),
            space_quiz_agent.as_tool(
                tool_name="space_quiz_agent",
                tool_description=(
                    "Optional. Use only when the user asks for a quiz, questions, "
                    "classroom activity, or comprehension check. Creates two "
                    "multiple-choice questions and one imaginative question from "
                    "a final young-reader space story, with answers and short "
                    "explanations."
                ),
            ),
        ],
    )
