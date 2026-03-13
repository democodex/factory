# ruff: noqa
from {{cookiecutter.agent_directory}}.config import DEFAULT_MODEL
from {{cookiecutter.agent_directory}}.plugins import get_plugins
from {{cookiecutter.agent_directory}}.prompts import ROOT_AGENT_INSTRUCTION

from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.models.lite_llm import LiteLlm

# Session & notification callbacks
from common.utils.sessions import init_session_state
from common.utils.notification_callbacks import inject_notification_instructions

# Register domain-specific notification behaviors (customize per agent):
# from common.utils.notification_config import register_behavior, NotificationBehavior
# register_behavior("your_task_type", NotificationBehavior.ANNOUNCED)

# Task tools
from common.tools.tasks import get_task_status, list_active_tasks, call_remote_agent
from common.utils.task_runner import get_background_task_service

plugins = get_plugins()
get_background_task_service(default_plugins=plugins)

root_agent = Agent(
    name="{{cookiecutter.agent_directory}}_root_agent",
    model=LiteLlm(model=DEFAULT_MODEL, num_retries=3),
    description="TODO: Describe your agent.",
    instruction=ROOT_AGENT_INSTRUCTION,
    tools=[get_task_status, list_active_tasks, call_remote_agent],
    before_agent_callback=init_session_state,
    before_model_callback=inject_notification_instructions,
)

app = App(
    root_agent=root_agent,
    name="{{cookiecutter.agent_directory}}",
    plugins=plugins,
)
