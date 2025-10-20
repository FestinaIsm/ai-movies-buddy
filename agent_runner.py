#!/usr/bin/env python3
"""Convenience script to execute the Movies Buddy workshop agent."""

from __future__ import annotations

import asyncio
import logging
from typing import Final

from movies_buddy import (
    Conversation,
    MissingApiKeyError,
    run_movies_buddy_agent,
)

logging.basicConfig(level=logging.INFO)

RUN_TIMEOUT_SECONDS: Final[float] = 30.0


async def _run_agent(user_query: str) -> None:
    """Execute the Movies Buddy agent with the configured user query."""
    try:
        conversation, final_output = await run_movies_buddy_agent(
            user_query,
            timeout_s=RUN_TIMEOUT_SECONDS,
        )
    except MissingApiKeyError as exc:
        logging.error("Configuration error: %s", exc)
        print("Set GEMINI_API_KEY and TVDB credentials in your .env before running the agent.")
        return
    except Exception as exc:
        logging.exception("Movies Buddy agent run failed: %s", exc)
        print("The agent failed to run.")
        return

    _print_results(conversation, final_output)


def _print_results(conversation: Conversation, final_output: str) -> None:
    """Display the final output, falling back to a friendly message if missing."""
    if final_output:
        print("\n" + "="*50)
        print("AGENT RESPONSE:")
        print("="*50)
        print(final_output)
        print("="*50 + "\n")
        return

    logging.warning("Conversation produced no final output: %r", conversation[-1] if conversation else None)
    print("No agent response captured.")


def main() -> None:
    """Program entry point."""
    print("\n🎬 Movies Buddy Agent 🎬")
    print("="*50)
    user_query = input("Enter your question about movies or TV series: ").strip()
    
    if not user_query:
        print("No query provided. Exiting.")
        return
    
    print(f"\nProcessing: {user_query}\n")
    asyncio.run(_run_agent(user_query))


if __name__ == "__main__":
    main()