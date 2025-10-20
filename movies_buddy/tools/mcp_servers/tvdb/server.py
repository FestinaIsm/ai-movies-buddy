"""TVDB MCP server exposing search capabilities to the Movies Buddy agent."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP

if __package__ in {None, ""}:  # pragma: no cover - runtime safeguard
    current_dir = Path(__file__).resolve().parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from helper import (  # type: ignore
        TVDBClient,
        TVDBSearchTool,
        load_environment_variables,
        load_tvdb_credentials,
    )
else:
    from .helper import (
        TVDBClient,
        TVDBSearchTool,
        load_environment_variables,
        load_tvdb_credentials,
    )

logger = logging.getLogger(__name__)

mcp = FastMCP("tvdb-mcp")


def _build_search_tool() -> TVDBSearchTool:
    """Create a fresh TVDB search tool using credentials from the environment."""
    env = load_environment_variables()
    api_key, pin = load_tvdb_credentials(env)

    client = TVDBClient(api_key=api_key, pin=pin)
    client.authenticate()

    return TVDBSearchTool(client)


@mcp.tool(
    name="search_tv_series_tvdb",
    description="Search The TV Database (TVDB) for TV and movie information.",
)
def search_tv_series_tvdb(
    query: Annotated[str, "Main search term for TV series, movies, or other entertainment content."],
    content_type: Annotated[
        str | None,
        "Optional filter: 'series', 'movie', 'person', or 'company'.",
    ] = None,
    year: Annotated[int | None, "Filter results by release/premiere year."] = None,
    company: Annotated[str | None, "Restrict results to a specific production company or network."] = None,
    limit: Annotated[int, "Maximum number of results (1-20). Defaults to 10."] = 10,
) -> Annotated[
    str,
    "Structured TVDB results with titles, years, genres, networks, and descriptions.",
]:
    """Search The TV Database (TVDB) for entertainment content."""
    tool = _build_search_tool()
    return tool.search(
        query=query,
        content_type=content_type,
        year=year,
        company=company,
        limit=limit,
    )


def main() -> None:
    """Entrypoint for running the MCP server via stdio transport."""
    logging.basicConfig(level=logging.INFO)
    mcp.run()


if __name__ == "__main__":
    main()
