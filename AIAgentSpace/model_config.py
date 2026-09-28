import os


DEFAULT_AI_MODEL = "gpt-5.4-nano-2026-03-17"
DEFAULT_NEWSROOM_TIMEOUT_SECONDS = 600


def get_ai_model() -> str:
    """Return the OpenAI model name for all agents."""
    return os.getenv("OPENAI_MODEL", DEFAULT_AI_MODEL).strip() or DEFAULT_AI_MODEL


def get_newsroom_timeout_seconds() -> int:
    """Return the configured newsroom timeout in seconds."""
    raw_timeout = os.getenv("NEWSROOM_TIMEOUT_SECONDS", str(DEFAULT_NEWSROOM_TIMEOUT_SECONDS)).strip()
    try:
        timeout = int(raw_timeout)
    except ValueError:
        return DEFAULT_NEWSROOM_TIMEOUT_SECONDS
    return timeout if timeout > 0 else DEFAULT_NEWSROOM_TIMEOUT_SECONDS


def get_openai_run_config():
    """Return a run config that uses the OpenAI Agents SDK default provider."""
    from agents import RunConfig

    return RunConfig()
