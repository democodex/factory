# ruff: noqa
from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.models.lite_llm import LiteLlm

from {{cookiecutter.agent_directory}}.bootstrap import bootstrap
from {{cookiecutter.agent_directory}}.settings import DEFAULT_MODEL
from {{cookiecutter.agent_directory}}.prompts import ROOT_AGENT_INSTRUCTION

from common.tools.tasks import get_task_status, list_active_tasks, call_remote_agent

plugins, before_agent, before_model = bootstrap()

root_agent = Agent(
    name="{{cookiecutter.agent_directory}}_root_agent",
    model=LiteLlm(model=DEFAULT_MODEL, num_retries=3),
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
