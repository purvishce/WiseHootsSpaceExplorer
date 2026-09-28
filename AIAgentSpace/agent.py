import asyncio
import json
import sys
from pathlib import Path

from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered, Runner, set_tracing_disabled, trace
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from AIAgentSpace.model_config import get_newsroom_timeout_seconds, get_openai_run_config
from AIAgentSpace.newsroom_agent import create_nasa_space_newsroom_agent


NEWSROOM_TIMEOUT_SECONDS = get_newsroom_timeout_seconds()

set_tracing_disabled(True)


def _guardrail_rejection_message(error: InputGuardrailTripwireTriggered) -> str:
    default_message = (
        "This NASA Space Newsroom agent can only help with NASA, space, "
        "astronomy, planets, spacecraft, asteroids, or space science questions."
    )

    run_data = getattr(error, "run_data", None)
    results = getattr(run_data, "input_guardrail_results", None) if run_data else None
    if not results:
        return default_message

    output_info = getattr(results[-1].output, "output_info", None)
    return getattr(output_info, "rejection_message", None) or default_message


def _output_guardrail_rejection_message(error: OutputGuardrailTripwireTriggered) -> str:
    default_message = (
        "The NASA Space Newsroom response was blocked because it was not "
        "appropriate for young readers."
    )

    run_data = getattr(error, "run_data", None)
    results = getattr(run_data, "output_guardrail_results", None) if run_data else None
    if not results:
        return default_message

    output_info = getattr(results[-1].output, "output_info", None)
    return getattr(output_info, "rejection_message", None) or default_message


async def main():
    agent = create_nasa_space_newsroom_agent()

    with trace("NASA Space Newsroom"):
        try:
            result = await asyncio.wait_for(
                Runner.run(
                    agent,
                    "Can you find two or three cool NASA space story ideas for kids?",
                    run_config=get_openai_run_config(),
                ),
                timeout=NEWSROOM_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            print(
                json.dumps(
                    {
                        "error": "timeout",
                        "message": (
                            "NASA Space Newsroom did not finish within "
                            f"{NEWSROOM_TIMEOUT_SECONDS} seconds."
                        ),
                    },
                    indent=2,
                )
            )
            return
        except InputGuardrailTripwireTriggered as guardrail_error:
            print(
                json.dumps(
                    {
                        "error": "out_of_scope",
                        "message": _guardrail_rejection_message(guardrail_error),
                    },
                    indent=2,
                )
            )
            return
        except OutputGuardrailTripwireTriggered as guardrail_error:
            print(
                json.dumps(
                    {
                        "error": "kid_safety_check_failed",
                        "message": _output_guardrail_rejection_message(guardrail_error),
                    },
                    indent=2,
                )
            )
            return

        final_output = result.final_output
        if hasattr(final_output, "model_dump"):
            print(final_output.model_dump_json(indent=2))
        else:
            print(json.dumps(final_output, indent=2))

        #final_text = "".join(chunks)
        #print()
        #print(send_pushover(final_text, "Study Buddy Summary"))
           
    
if __name__ == "__main__":
    asyncio.run(main())
    
