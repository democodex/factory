"""Plugin configuration for {{cookiecutter.agent_directory}}."""

import os

USE_CLOUD_LOGGING_PLUGIN = True

if USE_CLOUD_LOGGING_PLUGIN:
    from common.plugins import CloudLoggingEventStreamingPlugin as EventPlugin
else:
    from common.plugins import EventStreamingPlugin as EventPlugin

from common.plugins import SlackNotificationPlugin

SLACK_SUCCESS_CHANNEL = os.environ.get("SLACK_SUCCESS_CHANNEL", "feeds-xyborg")
SLACK_ERROR_CHANNEL = os.environ.get("SLACK_ERROR_CHANNEL", "feeds-xyborg")
USE_SLACK_PLUGIN = os.environ.get("ENABLE_SLACK_PLUGIN", "true").lower() == "true"


def get_plugins():
    """Create and return the standard plugin set."""
    plugins = [EventPlugin()]

    if USE_SLACK_PLUGIN:
        plugins.append(
            SlackNotificationPlugin(
                success_channel=SLACK_SUCCESS_CHANNEL,
                error_channel=SLACK_ERROR_CHANNEL,
                notify_agent_names=[],  # Add agent names that should trigger notifications
            ),
        )

    return plugins
