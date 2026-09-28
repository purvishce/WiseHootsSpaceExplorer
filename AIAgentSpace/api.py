import asyncio
import sys
import traceback
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered, Runner, set_tracing_disabled, trace


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from AIAgentSpace.model_config import get_newsroom_timeout_seconds, get_openai_run_config
from AIAgentSpace.newsroom_agent import create_nasa_space_newsroom_agent


NEWSROOM_TIMEOUT_SECONDS = get_newsroom_timeout_seconds()

set_tracing_disabled(True)

app = FastAPI(title="NASA Space Newsroom API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://wisehoots.ai",
        "https://www.wisehoots.ai",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NewsroomRequest(BaseModel):
    message: str = Field(
        min_length=1,
        description="NASA or space-related question for the newsroom agent.",
    )


def _to_jsonable(output: Any) -> Any:
    if hasattr(output, "model_dump"):
        return output.model_dump()
    return output


def _input_guardrail_message(error: InputGuardrailTripwireTriggered) -> str:
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


def _output_guardrail_message(error: OutputGuardrailTripwireTriggered) -> str:
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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/nasa-newsroom")
async def nasa_newsroom(request: NewsroomRequest) -> Any:
    agent = create_nasa_space_newsroom_agent()

    with trace("NASA Space Newsroom API"):
        try:
            result = await asyncio.wait_for(
                Runner.run(
                    agent,
                    request.message,
                    run_config=get_openai_run_config(),
                ),
                timeout=NEWSROOM_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=504,
                content={
                    "error": "timeout",
                    "message": (
                        "NASA Space Newsroom did not finish within "
                        f"{NEWSROOM_TIMEOUT_SECONDS} seconds."
                    ),
                },
            )
        except InputGuardrailTripwireTriggered as guardrail_error:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "out_of_scope",
                    "message": _input_guardrail_message(guardrail_error),
                },
            )
        except OutputGuardrailTripwireTriggered as guardrail_error:
            return JSONResponse(
                status_code=422,
                content={
                    "error": "kid_safety_check_failed",
                    "message": _output_guardrail_message(guardrail_error),
                },
            )
        except Exception as exc:
            traceback.print_exc()
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_error",
                    "message": str(exc),
                    "type": type(exc).__name__,
                },
            )

    return _to_jsonable(result.final_output)
