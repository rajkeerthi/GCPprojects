# Copyright 2025 Google LLC
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

"""Database Agent: get data from database (BigQuery) using NL2SQL."""

import logging
import os

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from . import tools
from .prompts import return_instructions_alloydb

logger = logging.getLogger(__name__)


def setup_before_agent_call(callback_context: CallbackContext) -> None:
    """Setup the agent."""
    logger.debug("setup_before_agent_call")

    if "database_settings" not in callback_context.state:
        callback_context.state["database_settings"] = (
            tools.get_database_settings()
        )


# Lazy initialization for Agent Engine compatibility
_alloydb_agent = None


def get_alloydb_agent():
    """Lazily initialize and return the AlloyDB agent."""
    global _alloydb_agent
    if _alloydb_agent is None:
        _alloydb_agent = LlmAgent(
            model=os.getenv("ALLOYDB_AGENT_MODEL", ""),
            name="alloydb_agent",
            instruction=return_instructions_alloydb(),
            output_key="alloydb_agent_output",
            tools=[
                tools.alloydb_nl2sql,
                tools.run_alloydb_query,
            ],
            generate_content_config=types.GenerateContentConfig(temperature=0.01),
        )
    return _alloydb_agent


# For backwards compatibility
alloydb_agent = None  # Use get_alloydb_agent() instead
