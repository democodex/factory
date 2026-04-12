"""Configuration and secrets loading for {{cookiecutter.agent_directory}}."""

import config.secrets  # noqa: F401  — auto-loads .env + Google Secret Manager

import os

DEFAULT_MODEL = (
    os.environ.get("DEFAULT_MODEL")
    or os.environ.get("MODEL")
    or "gemini/gemini-2.0-flash"
)
