# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


import json
from pathlib import Path
from google.adk.code_executors import AgentEngineSandboxCodeExecutor

# Load agent engine resource name from deployment_metadata.json if available
deployment_metadata_path = Path(__file__).parent.parent / "deployment_metadata.json"
agent_engine_id = None
if deployment_metadata_path.exists():
    try:
        with open(deployment_metadata_path) as f:
            metadata = json.load(f)
            agent_engine_id = metadata.get("remote_agent_runtime_id")
    except Exception:
        pass

code_executor = (
    AgentEngineSandboxCodeExecutor(agent_engine_resource_name=agent_engine_id)
    if agent_engine_id
    else AgentEngineSandboxCodeExecutor()
)

from app.tools import (
    add_venue,
    calculate_trip_budget,
    generate_destination_image,
    generate_destination_preview,
    generate_destination_video,
    get_city_details,
    search_venues,
)

from google.adk.agents.callback_context import CallbackContext
from google.adk.memory import VertexAiMemoryBankService
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from app.a2ui_utils import a2ui_callback


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are a helpful City & Weekend Gateway Concierge AI assistant. "
        "You must pay close attention to and remember all user travels (including cities visited, past trips, upcoming travel plans, itineraries, favorite destinations, and travel styles), "
        "as well as any user allergies (e.g. peanuts, gluten, dairy, shellfish), dietary restrictions, and personal preferences mentioned across conversations. "
        "Always recall these stated travels and allergies from memory, explicitly acknowledge them, "
        "and personalize all venue, dining, and weekend getaway recommendations based on their travel history and dietary needs."
    ),
    workflow_description=(
        "Use your tools to search venues in the database, add new venues, calculate trip budgets, "
        "fetch city details and coordinates, generate destination preview postcard images, "
        "generate AI images for destinations using gemini-3.1-flash-lite-image, "
        "generate short cinematic videos for getaway spots using gemini-omni-flash-preview, "
        "look up weather, and check local time. When asked to perform Python computations or data analysis, use your code_executor sandbox. "
        "Analyze the request and return structured UI when appropriate."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


async def generate_memories_callback(callback_context: CallbackContext):
    try:
        await callback_context.add_session_to_memory()
    except Exception:
        pass
    return None


def memory_bank_service_builder():
    return VertexAiMemoryBankService(
        project="qwiklabs-gcp-02-77ad6185964c",
        location="us-east1",
        agent_engine_id="2103873718307520512",
    )


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=code_executor,
    tools=[
        PreloadMemoryTool(),
        get_weather,
        get_current_time,
        search_venues,
        add_venue,
        generate_destination_preview,
        calculate_trip_budget,
        get_city_details,
        generate_destination_image,
        generate_destination_video,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)


app = App(
    root_agent=root_agent,
    name="app",
)


