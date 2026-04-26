"""Agent infrastructure wiring for {{cookiecutter.agent_directory}}."""

from common.context.session import before_model_callback, init_agent_session
from common.utils.task_runner import get_background_task_service

from {{cookiecutter.agent_directory}}.plugins import get_plugins

# Awareness events for this agent are declared in awareness_events.py as
# AwarenessEventSpec values. Register them at import time so check_awareness
# (in before_model_callback) and the renderer find them. Pattern:
#
#     from common.context.awareness import register_awareness, validate_awareness_registry
#     from {{cookiecutter.agent_directory}}.awareness_events import ALL_SPECS
#
#     for spec in ALL_SPECS:
#         register_awareness(spec)
#
# Then call validate_awareness_registry(list(ALL_SPECS)) inside bootstrap()
# to assert every spec the agent depends on is actually registered. See
# the docstring in awareness_events.py for the full emit pattern.


def _init_session(callback_context):
    """Session init: common context management."""
    return init_agent_session(callback_context)


def _build_session_service():
    """Build session service: persistent (Cloud SQL) if configured, else in-memory.

    When SESSION_DB_URL is set, uses DatabaseSessionService backed by the
    shared Cloud SQL instance for session persistence across WebSocket
    reconnections. When unset, falls back to InMemorySessionService.
    """
    import os

    session_db_url = os.environ.get("SESSION_DB_URL")
    if session_db_url:
        from google.adk.sessions import DatabaseSessionService

        return DatabaseSessionService(session_db_url)
    from google.adk.sessions import InMemorySessionService

    return InMemorySessionService()


def bootstrap():
    """Initialize agent infrastructure.

    Returns (plugins, before_agent, before_model, session_service_builder).
    """
    plugins = get_plugins()
    get_background_task_service(default_plugins=plugins)
    return plugins, _init_session, before_model_callback, _build_session_service
