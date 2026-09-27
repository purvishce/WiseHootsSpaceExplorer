import os


DEFAULT_AI_MODEL = "gemini/gemini-3.5-flash-lite"
DEFAULT_NEWSROOM_TIMEOUT_SECONDS = 600


def configure_google_api_environment() -> None:
    """Prepare environment variables expected by the Gemini LiteLLM provider."""
    google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if google_api_key and not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = google_api_key


def get_ai_model() -> str:
    """Return the Google Gemini model name for all agents."""
    model = os.getenv("GOOGLE_MODEL", DEFAULT_AI_MODEL).strip()

    if not model or model.startswith("gpt-") or model.startswith("openai/"):
        return DEFAULT_AI_MODEL
    if model.startswith("gemini/"):
        return model
    return f"gemini/{model}"


def get_newsroom_timeout_seconds() -> int:
    """Return the configured newsroom timeout in seconds."""
    raw_timeout = os.getenv("NEWSROOM_TIMEOUT_SECONDS", str(DEFAULT_NEWSROOM_TIMEOUT_SECONDS)).strip()
    try:
        timeout = int(raw_timeout)
    except ValueError:
        return DEFAULT_NEWSROOM_TIMEOUT_SECONDS
    return timeout if timeout > 0 else DEFAULT_NEWSROOM_TIMEOUT_SECONDS


def get_google_run_config():
    """Return a run config that routes model calls through Google Gemini via LiteLLM."""
    from agents import RunConfig
    from agents.extensions.models.litellm_provider import LitellmProvider

    configure_google_api_environment()
    return RunConfig(model_provider=LitellmProvider())
