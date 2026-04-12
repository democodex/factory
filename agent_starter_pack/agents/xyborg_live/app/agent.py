# ruff: noqa
import os

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini

from {{cookiecutter.agent_directory}}.bootstrap import bootstrap
from {{cookiecutter.agent_directory}}.prompts import ROOT_AGENT_INSTRUCTION

from common.tools.tasks import get_task_status, list_active_tasks, call_remote_agent

plugins, before_agent, before_model = bootstrap()

LIVE_MODEL = os.environ.get("LIVE_MODEL", "gemini-live-2.5-flash-native-audio")

root_agent = Agent(
    name="{{cookiecutter.agent_directory}}_root_agent",
    model=Gemini(model=LIVE_MODEL),
    description="TODO: Describe your agent.",
    instruction=ROOT_AGENT_INSTRUCTION,
    tools=[get_task_status, list_active_tasks, call_remote_agent],
    before_agent_callback=before_agent,
    before_model_callback=before_model,
)

app = App(
    root_agent=root_agent,
    name="{{cookiecutter.agent_directory}}",
    plugins=plugins,
)
