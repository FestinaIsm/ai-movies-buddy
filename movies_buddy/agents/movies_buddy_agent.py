"""Movies Buddy agent definition using the OpenAI Agents SDK."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence, TypedDict

from agents import Agent, RunConfig, Runner
from agents.mcp.server import MCPServerStdio
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from ..prompts import MAIN_INSTRUCTIONS
from ..tools import get_series_movies_summary
from ..utils import load_environment_variables

logger = logging.getLogger(__name__)

# Allow overriding via environment for testing or different gateways.
GEMINI_BASE_URL: str = os.getenv(
    "GEMINI_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta/openai/",
)

# Keep GOOGLE_API_KEY for compatibility; include common misspelling as a legacy alias.
_API_KEY_ENV_VARS: tuple[str, ...] = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMENI_API_KEY")


class ChatMessage(TypedDict, total=False):
    """Typed representation of a chat message for the runner."""

    role: str
    content: Any  # str | list[dict[str, Any]]


Conversation = list[ChatMessage]


class MissingApiKeyError(RuntimeError):
    """Raised when no compatible API key is found."""


def _resolve_api_key(env: Mapping[str, str]) -> str:
    """
    Return the first available Gemini-compatible API key from the provided env mapping
    or the process environment. Prefers explicit mapping, falls back to os.environ.
    """
    for key in _API_KEY_ENV_VARS:
        value = env.get(key) or os.getenv(key, "")
        if value:
            if key == "GEMENI_API_KEY":
                logger.warning(
                    "Environment variable 'GEMENI_API_KEY' is a misspelling. "
                    "Please migrate to 'GEMINI_API_KEY'."
                )
            logger.debug("Using API key from %s", key)
            return value
    raise MissingApiKeyError("Set GEMINI_API_KEY or GOOGLE_API_KEY before running.")


def _create_tvdb_mcp_server(*, cache_tools_list: bool = True) -> MCPServerStdio:
    """
    Instantiate the TVDB MCP server using the local stdio script.
    Fails early with a clear error if the script path is missing.
    """
    server_script = (
        Path(__file__)
        .resolve()
        .parent.parent
        / "tools"
        / "mcp_servers"
        / "tvdb"
        / "server.py"
    )
    if not server_script.is_file():
        raise FileNotFoundError(f"MCP server script not found: {server_script}")
    return MCPServerStdio(
        {
            "command": sys.executable,
            "args": [str(server_script)],
            "cwd": str(server_script.parent),
        },
        cache_tools_list=cache_tools_list,
        name="tvdb-stdio",
    )


def _extract_final_output(conversation: Sequence[ChatMessage], *, fallback: str = "") -> str:
    """
    Return a human-readable final string from the last message, falling back to
    a provided value or empty string.
    """
    if fallback:
        return fallback
    if not conversation:
        return ""
    content = conversation[-1].get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        ]
        return "\n".join(part for part in parts if part)
    return ""


def create_movies_buddy_agent(env: Mapping[str, str]) -> tuple[Agent, RunConfig, MCPServerStdio]:
    """
    Configure the Movies Buddy agent, runtime settings, and TVDB MCP server.

    Returns:
        (Agent, RunConfig, MCPServerStdio)
    """
    api_key = _resolve_api_key(env)
    base_url = env.get("GEMINI_BASE_URL", GEMINI_BASE_URL)

    external_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    model_id = env.get("GEMINI_MODEL", "gemini-2.5-pro")
    model = OpenAIChatCompletionsModel(model=model_id, openai_client=external_client)

    mcp_server = _create_tvdb_mcp_server()

    agent = Agent(
        name="Movies Buddy",
        instructions=MAIN_INSTRUCTIONS,
        model=model,
        tools=[get_series_movies_summary],
        # TODO: activate the MCP server once instructions are added in the system prompt
        # mcp_servers=[mcp_server],
    )

    tracing_disabled = str(env.get("AGENT_TRACING", "true")).lower() in {"1", "true", "yes"}
    config = RunConfig(
        model=model,
        model_provider=external_client,
        tracing_disabled=tracing_disabled,
    )

    logger.info("Created Movies Buddy agent with model %s", model_id)
    return agent, config, mcp_server


async def run_movies_buddy_agent(
    user_input: str,
    *,
    conversation_history: Conversation | None = None,
    timeout_s: float | None = None,
) -> tuple[Conversation, str]:
    """
    Execute the Movies Buddy agent with optional chat history.

    Args:
        user_input: The latest user message.
        conversation_history: Optional list of previous turns (OpenAI chat format).
        timeout_s: Optional timeout for the run (seconds).

    Returns:
        (conversation, final_output)
    """
    env = load_environment_variables()
    agent, config, mcp_server = create_movies_buddy_agent(env)

    messages: Conversation = list(conversation_history or [])
    messages.append({"role": "user", "content": user_input})

    try:
        async with mcp_server:
            coro = Runner.run(agent, messages, run_config=config)
            result = await (asyncio.wait_for(coro, timeout_s) if timeout_s else coro)

        conversation: Conversation = result.to_input_list()
        final_output = _extract_final_output(
            conversation, fallback=getattr(result, "final_output", "") or ""
        )
        logger.info("Movies Buddy agent run completed")
        return conversation, final_output

    except asyncio.TimeoutError:
        logger.warning("Movies Buddy agent run timed out after %s seconds", timeout_s)
        return conversation_history or [], "Request timed out."
    except MissingApiKeyError:
        raise
    except Exception as exc:
        logger.exception("Movies Buddy agent run failed: %s", exc)
        return conversation_history or [], "The agent failed to run."


__all__ = [
    "ChatMessage",
    "Conversation",
    "MissingApiKeyError",
    "create_movies_buddy_agent",
    "run_movies_buddy_agent",
]
