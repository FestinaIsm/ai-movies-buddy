"""TVDB helper utilities for Movies Buddy MCP servers."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

TVDB_BASE_URL = "https://api4.thetvdb.com/v4"


class TVDBAuthenticationError(RuntimeError):
    """Raised when authentication with the TVDB API fails."""


class TVDBRequestError(RuntimeError):
    """Raised when a TVDB API request fails."""


@dataclass
class TVDBClient:
    """Client for interacting with the TVDB API."""

    api_key: str
    pin: str
    session: requests.Session | None = None
    _token: str | None = None

    def __post_init__(self) -> None:
        if not self.session:
            self.session = requests.Session()

    @property
    def base_url(self) -> str:
        """Return the base URL for the TVDB API."""
        return TVDB_BASE_URL

    def authenticate(self) -> None:
        """Authenticate with the TVDB API and cache the bearer token."""
        login_url = f"{self.base_url}/login"
        payload = {"apikey": self.api_key, "pin": self.pin}
        headers = {"Content-Type": "application/json"}

        try:
            response = self.session.post(login_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            msg = f"TVDB authentication failed: {exc}"
            logger.error(msg)
            raise TVDBAuthenticationError(msg) from exc

        data = response.json()
        token = data.get("data", {}).get("token")
        if not token:
            msg = "TVDB authentication failed: token missing in response."
            logger.error(msg)
            raise TVDBAuthenticationError(msg)

        self._token = token
        logger.info("TVDB authentication successful")

    def _headers(self) -> dict[str, str]:
        if not self._token:
            raise TVDBAuthenticationError("Client is not authenticated. Call authenticate() first.")
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def search(self, **params: Any) -> dict[str, Any]:
        """Search the TVDB API using flexible parameters."""
        url = f"{self.base_url}/search"
        clean_params = {key: value for key, value in params.items() if value is not None}

        try:
            response = self.session.get(url, params=clean_params, headers=self._headers(), timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            msg = f"TVDB search failed: {exc}"
            logger.error(msg)
            raise TVDBRequestError(msg) from exc

        return response.json()


def load_environment_variables() -> dict[str, str]:
    """
    Load environment variables, including values from a project-level `.env` file.

    This local implementation mirrors the project utility to avoid circular imports
    when the MCP server is executed as a standalone script.
    """
    repo_root = Path(__file__).resolve().parents[4]
    dotenv_path = repo_root / ".env"
    load_dotenv(dotenv_path=dotenv_path, override=False)
    return dict(os.environ)


def load_tvdb_credentials(env: dict[str, str] | None = None) -> tuple[str, str]:
    """Load TVDB API credentials from the environment mapping or os.environ."""
    mapping = env or load_environment_variables()
    api_key = mapping.get("TVDB_API_KEY", "").strip()
    pin = mapping.get("TVDB_PIN", "").strip()

    if not api_key or not pin:
        raise ValueError("TVDB_API_KEY and TVDB_PIN environment variables are required.")

    return api_key, pin


def format_search_results(results: dict[str, Any]) -> str:
    """Format TVDB search results into a structured text response."""
    data = results.get("data") if results else None
    if not data:
        return "No results found for the search query."

    lines: list[str] = [f"Found {len(data)} results:\n"]
    for index, item in enumerate(data, start=1):
        lines.extend(_format_item(index, item))

    return "\n".join(lines)


def _format_item(index: int, item: dict[str, Any]) -> Iterable[str]:
    name = item.get("name", "N/A")
    item_type = item.get("type", "N/A").title()
    year = item.get("year", "N/A")
    tvdb_id = item.get("tvdb_id") or item.get("id", "N/A")

    yield f"{index}. **{name}** ({item_type}, {year})"
    yield f"   - TVDB ID: {tvdb_id}"

    overview = item.get("overview") or ""
    if overview:
        truncated = f"{overview[:200]}..." if len(overview) > 200 else overview
        yield f"   - Overview: {truncated}"

    if companies := item.get("companies"):
        names = ", ".join(
            company.get("name", "N/A") if isinstance(company, dict) else str(company)
            for company in companies[:3]
        )
        yield f"   - Networks/Companies: {names}"

    if genres := item.get("genres"):
        genre_names = ", ".join(
            genre.get("name", "N/A") if isinstance(genre, dict) else str(genre)
            for genre in genres[:5]
        )
        yield f"   - Genres: {genre_names}"


class TVDBSearchTool:
    """High-level helper that wraps TVDB search operations."""

    def __init__(self, client: TVDBClient) -> None:
        self._client = client

    def search(
        self,
        *,
        query: str,
        content_type: str | None = None,
        year: int | None = None,
        company: str | None = None,
        limit: int = 10,
    ) -> str:
        """Search the TVDB API and return formatted results."""
        query = query.strip()
        if not query:
            raise ValueError("query is required and cannot be empty.")

        if limit < 1 or limit > 20:
            raise ValueError("limit must be between 1 and 20.")

        params: dict[str, Any] = {"query": query, "limit": limit}

        if content_type:
            normalized_type = content_type.lower()
            valid_types = {"series", "movie", "person", "company"}
            if normalized_type not in valid_types:
                logger.warning("Invalid content_type '%s', proceeding anyway.", content_type)
            params["type"] = normalized_type

        if year is not None:
            params["year"] = year

        if company:
            params["company"] = company.strip()

        logger.info("Searching TVDB with parameters: %s", params)
        results = self._client.search(**params)
        logger.debug("TVDB raw search response: %s", json.dumps(results))
        formatted = format_search_results(results)
        logger.debug("TVDB formatted search output:\n%s", formatted)
        logger.info("TVDB search completed successfully for query: '%s'", query)
        return formatted


__all__ = [
    "TVDBAuthenticationError",
    "TVDBRequestError",
    "TVDBClient",
    "TVDBSearchTool",
    "load_environment_variables",
    "load_tvdb_credentials",
    "format_search_results",
]
