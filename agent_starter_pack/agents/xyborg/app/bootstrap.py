"""Agent infrastructure wiring for {{cookiecutter.agent_directory}}."""

from {{cookiecutter.agent_directory}}.plugins import get_plugins
from common.utils.sessions import init_session_state
from common.utils.notification_callbacks import inject_notification_instructions
from common.utils.task_runner import get_background_task_service

# Register domain-specific notification behaviors (customize per agent):
# from common.utils.notification_config import register_behavior, NotificationBehavior
# register_behavior("your_task_type", NotificationBehavior.ANNOUNCED)


def bootstrap():
    """Initialize agent infrastructure. Returns (plugins, callbacks) tuple."""
    plugins = get_plugins()
    get_background_task_service(default_plugins=plugins)
    return plugins, init_session_state, inject_notification_instructions
