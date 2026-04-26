"""Agent infrastructure wiring for {{cookiecutter.agent_directory}}."""

from {{cookiecutter.agent_directory}}.plugins import get_plugins
from common.utils.task_runner import get_background_task_service
from common.context.session import init_agent_session, before_model_callback

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


def bootstrap():
    """Initialize agent infrastructure. Returns (plugins, callbacks) tuple."""
    plugins = get_plugins()
    get_background_task_service(default_plugins=plugins)
    return plugins, _init_session, before_model_callback
