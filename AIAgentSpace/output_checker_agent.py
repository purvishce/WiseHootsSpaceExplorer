from pydantic import BaseModel, Field

from agents import Agent

from AIAgentSpace.model_config import get_ai_model


class OutputSafetyCheck(BaseModel):
    """Decision about whether final output is appropriate for young readers."""

    is_kid_appropriate: bool = Field(
        description="True when the final output is safe, friendly, and suitable for kids."
    )
    reasoning: str = Field(description="Brief explanation of the decision.")
    rejection_message: str = Field(
        description="Friendly message to show when the final output is not appropriate for kids."
    )


def create_output_checker_agent() -> Agent:
    """Create the Output Checker agent that validates final output for kids."""
    return Agent(
        name="Output Checker",
        instructions=(
            "You are the Output Checker for a NASA Space Newsroom agent for kids. "
            "Review the final answer and decide whether it is appropriate for a "
            "young reader. Allow friendly, accurate NASA or space content written "
            "in a safe, age-appropriate way. Reject output that includes graphic "
            "violence, sexual content, hateful or insulting language, unsafe "
            "instructions, frightening exaggeration, unsupported disaster claims, "
            "or wording that is too intense for kids. Also reject output that "
            "encourages panic about asteroids, meteors, radiation, explosions, or "
            "space hazards without calm scientific context. If rejecting, explain "
            "briefly and ask for a safer kid-friendly rewrite."
        ),
        model=get_ai_model(),
        output_type=OutputSafetyCheck,
    )
