"""Agent infrastructure wiring for {{cookiecutter.agent_directory}}."""

from {{cookiecutter.agent_directory}}.plugins import get_plugins
from common.utils.task_runner import get_background_task_service
from common.context.session import init_agent_session, before_model_callback

# Register domain-specific awareness levels (customize per agent):
# from common.context.awareness import register_awareness_level, AwarenessLevel
# register_awareness_level("your_task_type", AwarenessLevel.ANNOUNCED)


def _init_session(callback_context):
    """Session init: common context management."""
    return init_agent_session(callback_context)


def bootstrap():
    """Initialize agent infrastructure. Returns (plugins, callbacks) tuple."""
    plugins = get_plugins()
    get_background_task_service(default_plugins=plugins)
    return plugins, _init_session, before_model_callback
