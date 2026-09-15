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
import os
import re
from zoneinfo import ZoneInfo

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from app.a2ui_utils import a2ui_callback

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.tools import (
    consult_herbal_corpus,
    convert_currency,
    generate_dish_image,
    save_recipe_firestore,
    scale_recipe_nutrition,
    search_recipes_firestore,
)

MODEL = "gemini-3.6-flash"

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are ChefGenie, a personal chef and meal planning AI assistant. "
        "You remember the user's stated dietary preferences, allergies, favorite cuisines, "
        "and household size from previous conversations and use them to personalize recipe "
        "recommendations, weekly meal plans, and nutritional advice."
    ),
    workflow_description=(
        "Analyze the request and return structured UI when appropriate. "
        "When asked about herbal remedies, plant uses, traditional medicinal plants, or Culpeper's Herbal, "
        "always call consult_herbal_corpus to ground your answer on the reference corpus. "
        "When asked to visualize a dish, show a plating presentation, or generate an image for a recipe, "
        "always call generate_dish_image to generate the image. "
        "You also have a safe Python sandbox code execution environment to run calculations. "
        "When asked to scale recipe ingredient quantities or calculate nutritional/calorie/macro math, "
        "always write and execute Python code in the sandbox to ensure 100% correct, precise calculations."
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
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
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

# Determine current Agent Engine resource name dynamically or fallback to deployed resource ID.
app_url = os.environ.get("APP_URL", "")
match = re.search(r"(projects/[a-zA-Z0-9-_]+/locations/[a-zA-Z0-9-_]+/reasoningEngines/\d+)", app_url)
if match:
    agent_engine_resource_name = match.group(1)
else:
    agent_engine_resource_name = "projects/178057287160/locations/us-east1/reasoningEngines/5060788139862261760"

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_resource_name
)



async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


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


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        search_recipes_firestore,
        save_recipe_firestore,
        scale_recipe_nutrition,
        consult_herbal_corpus,
        generate_dish_image,
        get_weather,
        get_current_time,
        convert_currency,
    ],
    code_executor=code_executor,
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

