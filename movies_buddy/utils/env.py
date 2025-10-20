"""Environment loading utilities."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def load_environment_variables() -> dict[str, str]:
    """
    Load environment variables, including values from a project-level `.env` file.

    Returns:
        Dictionary containing the current environment variables.
    """
    repo_root = Path(__file__).resolve().parents[2]
    dotenv_path = repo_root / ".env"
    load_dotenv(dotenv_path=dotenv_path, override=False)
    return dict(os.environ)
