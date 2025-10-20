"""Wikipedia summary tool for the Movies Buddy agent."""

from __future__ import annotations

import json
import logging
from typing import Annotated

import wikipediaapi
from agents import function_tool

logger = logging.getLogger(__name__)

_USER_AGENT = "MoviesBuddyAgent/1.0 (https://example.com/contact)"


def _fetch_wikipedia_summary(title: str) -> dict[str, str]:
    """
    Retrieve the title and summary for a Wikipedia page.

    Raises:
        LookupError: If the page does not exist or lacks a summary.
    """
    wiki = wikipediaapi.Wikipedia(language="en", user_agent=_USER_AGENT)
    page = wiki.page(title.strip())

    if page.exists() and page.summary:
        return {"title": page.title, "summary": page.summary}

    raise LookupError(f"No Wikipedia summary found for '{title}'.")


@function_tool
def get_series_movies_summary(
    title: Annotated[str, "Exact title of the TV series or movie to summarize."],
) -> Annotated[str, "JSON string with keys: title, summary."]:
    """
    Return a concise Wikipedia summary for a given TV series or movie title.

    Behavior:
    - Fetches the English Wikipedia page for the provided title.
    - Returns a structured JSON string:
      {
        "title": "<Wikipedia page title>",
        "summary": "<introductory paragraph>"
      }

    Notes:
    - If the page is missing or lacks a summary, returns a fallback JSON string with a
      message in the `summary` field.
    - Keeps the input title as-is (no disambiguation variants).
    """
    try:
        result = _fetch_wikipedia_summary(title)
        return json.dumps(result, ensure_ascii=False)
    except LookupError as exc:
        logger.info("No Wikipedia summary found for title=%r", title)
        fallback = {"title": title, "summary": f"No Wikipedia summary found for '{title}'."}
        return json.dumps(fallback, ensure_ascii=False)
    except Exception as exc:
        logger.exception("Failed to retrieve Wikipedia summary for title=%r", title)
        raise RuntimeError(f"Wikipedia summary retrieval failed: {exc}") from exc


__all__ = ["get_series_movies_summary"]
