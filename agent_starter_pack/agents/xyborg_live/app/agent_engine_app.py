# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""XybOrg Live agent engine app with session persistence.

Extends the standard ADK AgentEngineApp with a bidi_stream_query override
that resolves session_id before delegating to the parent. This enables
session persistence across WebSocket reconnections — the frontend sends
a session_id from a prior connection, and the backend resumes that session
from the configured session service (DatabaseSessionService or InMemory).

Session service configuration is wired from bootstrap.py via agent.py —
this file receives it as an import, keeping deployment infrastructure
free of domain logic.
"""

import asyncio
import logging
import os
from collections.abc import AsyncIterable
from typing import Any

import vertexai
from dotenv import load_dotenv
from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService
from google.cloud import logging as google_cloud_logging
from vertexai.agent_engines.templates.adk import AdkApp
from vertexai.preview.reasoning_engines import AdkApp as PreviewAdkApp

from {{cookiecutter.agent_directory}}.agent import app as adk_app
from {{cookiecutter.agent_directory}}.agent import session_service_builder
from {{cookiecutter.agent_directory}}.app_utils.telemetry import setup_telemetry
from {{cookiecutter.agent_directory}}.app_utils.typing import Feedback

# Load environment variables from .env file at runtime
load_dotenv()


class AgentEngineApp(AdkApp):
    def set_up(self) -> None:
        """Initialize the agent engine app with logging and telemetry."""
        vertexai.init()
        setup_telemetry()
        super().set_up()
        logging.basicConfig(level=logging.INFO)
        logging_client = google_cloud_logging.Client()
        self.logger = logging_client.logger(__name__)
        if gemini_location:
            os.environ["GOOGLE_CLOUD_LOCATION"] = gemini_location

    def register_feedback(self, feedback: dict[str, Any]) -> None:
        """Collect and log feedback."""
        feedback_obj = Feedback.model_validate(feedback)
        self.logger.log_struct(feedback_obj.model_dump(), severity="INFO")

    def register_operations(self) -> dict[str, list[str]]:
        """Registers the operations of the Agent."""
        operations = super().register_operations()
        operations[""] = operations.get("", []) + ["register_feedback"]
        # Add bidi_stream_query for adk_live
        operations["bidi_stream"] = ["bidi_stream_query"]
        return operations

    async def bidi_stream_query(
        self,
        request_queue: Any,
    ) -> AsyncIterable[Any]:
        """Bidi streaming with session persistence across WebSocket reconnections.

        Wraps the preview ADK's bidi_stream_query to intercept session
        creation. Peeks at the first request to resolve the session_id
        (existing or newly created), then yields a synthetic sessionInfo
        event before delegating to the parent implementation. This ensures
        the WebSocket adapter can send session_id to the frontend in
        setupComplete — even on the very first connection.

        If the frontend sends a session_id from a prior connection and that
        session has expired or been deleted, this gracefully falls back to
        creating a new session rather than crashing the WebSocket.
        """
        if not isinstance(request_queue, asyncio.Queue):
            raise TypeError("request_queue must be an asyncio.Queue instance.")

        first_request = await request_queue.get()
        user_id = first_request.get("user_id")
        if not user_id:
            raise ValueError("The first request must have a user_id.")

        session_id = first_request.get("session_id")
        run_config = first_request.get("run_config")
        first_live_request = first_request.get("live_request")

        if not self._tmpl_attrs.get("runner"):
            self.set_up()

        # Resolve session: resume existing or create new
        if not session_id:
            state = first_request.get("state")
            session = await self.async_create_session(user_id=user_id, state=state)
            session_id = session.id
        else:
            # Graceful fallback: if the session_id is invalid/expired,
            # create a new one rather than crashing the WebSocket.
            try:
                session = await self.async_get_session(
                    user_id=user_id, session_id=session_id,
                )
            except Exception:
                logging.warning(
                    f"Session {session_id} not found or expired — creating new session"
                )
                session = await self.async_create_session(user_id=user_id)
                session_id = session.id

        # Yield synthetic event so the adapter can capture session_id
        # before any agent output arrives
        yield {"sessionInfo": {"session_id": session_id}}

        # Reconstruct the request queue with session_id resolved
        resolved_queue: asyncio.Queue[dict] = asyncio.Queue()
        resolved_first = {
            "user_id": user_id,
            "session_id": session_id,
        }
        if run_config:
            resolved_first["run_config"] = run_config
        if first_live_request:
            resolved_first["live_request"] = first_live_request
        await resolved_queue.put(resolved_first)

        # Forward remaining requests from original queue to resolved queue
        async def _bridge_queues():
            while True:
                item = await request_queue.get()
                await resolved_queue.put(item)

        bridge_task = asyncio.create_task(_bridge_queues())

        try:
            # Delegate to parent implementation with session_id resolved
            async for event in PreviewAdkApp.bidi_stream_query(self, resolved_queue):
                yield event
        finally:
            bridge_task.cancel()
            try:
                await bridge_task
            except asyncio.CancelledError:
                pass


gemini_location = os.environ.get("GEMINI_LOCATION")
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")
agent_engine = AgentEngineApp(
    app=adk_app,
    session_service_builder=session_service_builder,
    artifact_service_builder=lambda: (
        GcsArtifactService(bucket_name=logs_bucket_name)
        if logs_bucket_name
        else InMemoryArtifactService()
    ),
)
