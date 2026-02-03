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

"""Analytics Agent: generate nl2py and use code interpreter to run the code."""

import os

from google.adk.agents import Agent
from google.adk.code_executors import VertexAiCodeExecutor

from .prompts import return_instructions_analytics

# Lazy initialization for Agent Engine compatibility
_analytics_agent = None


def get_analytics_agent():
    """Lazily initialize and return the analytics agent."""
    global _analytics_agent
    if _analytics_agent is None:
        _analytics_agent = Agent(
            model=os.getenv("ANALYTICS_AGENT_MODEL", ""),
            name="analytics_agent",
            instruction=return_instructions_analytics(),
            code_executor=VertexAiCodeExecutor(
                optimize_data_file=True,
                stateful=True,
            ),
        )
    return _analytics_agent


# For backwards compatibility
analytics_agent = None  # Use get_analytics_agent() instead
