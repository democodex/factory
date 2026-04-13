"""Agent infrastructure wiring for {{cookiecutter.agent_directory}}."""

from common.context.session import before_model_callback, init_agent_session
from common.utils.task_runner import get_background_task_service

from {{cookiecutter.agent_directory}}.plugins import get_plugins

# Register domain-specific awareness levels (customize per agent):
# from common.context.awareness import register_awareness_level, AwarenessLevel
# register_awareness_level("your_task_type", AwarenessLevel.ANNOUNCED)


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
