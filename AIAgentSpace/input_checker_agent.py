from pydantic import BaseModel, Field

from agents import Agent

from AIAgentSpace.model_config import get_ai_model


class UserInputCheck(BaseModel):
    """Decision about whether a user request belongs in the NASA space agent."""

    is_space_related: bool = Field(
        description="True when the request is related to NASA, space, astronomy, planets, spacecraft, or space science."
    )
    reasoning: str = Field(description="Brief explanation of the decision.")
    rejection_message: str = Field(
        description="Friendly message to show when the request is not appropriate for this NASA space agent."
    )


def create_input_checker_agent() -> Agent:
    """Create the Input Checker agent that validates whether user input is on topic."""
    return Agent(
        name="Input Checker",
        instructions=(
            "You are the Input Checker for a NASA Space Newsroom agent. Decide "
            "whether the user's request is appropriate for this app. Allow requests "
            "about NASA, space, astronomy, planets, moons, stars, galaxies, rockets, "
            "spacecraft, astronauts, space missions, space images, asteroids, "
            "comets, meteors, or space science for kids. Reject requests that are "
            "unrelated, such as homework outside space, cooking, finance, sports, "
            "entertainment, coding questions unrelated to this app's NASA agent "
            "behavior, or general chat. Also reject requests that contain bad "
            "words, profanity, abusive language, insults, political arguments, "
            "political persuasion, political figures, elections, parties, or "
            "government debate. Do not repeat bad words in the rejection message. "
            "If rejecting, explain briefly and invite the user to ask a NASA or "
            "space question instead."
        ),
        model=get_ai_model(),
        output_type=UserInputCheck,
    )
