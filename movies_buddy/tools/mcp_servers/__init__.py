"""MCP server entry points for Movies Buddy tools."""

from .tvdb.server import main, search_tv_series_tvdb

__all__ = [
    "search_tv_series_tvdb",
    "main",
]
