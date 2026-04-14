"""Configuration and secrets loading for {{cookiecutter.agent_directory}}."""

import os

import config.secrets  # noqa: F401  — auto-loads .env + Google Secret Manager

# ── Model defaults (single source of truth) ──────────────────────────
# setdefault: only sets the value if the env var is NOT already present.
# .env, Secret Manager, and deploy-time vars always take precedence.

# Orchestrator (Live API — native Gemini wrapper, Vertex AI in prod)
os.environ.setdefault("LIVE_MODEL", "gemini-live-2.5-flash-native-audio")

DEFAULT_MODEL = (
    os.environ.get("DEFAULT_MODEL")
    or os.environ.get("MODEL")
    or "gemini/gemini-2.0-flash"
)
