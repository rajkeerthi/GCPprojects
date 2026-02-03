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

"""Research Agent for collecting and inserting demand driver data."""

import os
from datetime import date

from google.adk.agents import LlmAgent
from google.genai import types

from .prompts import return_instructions_research
from .tools import fetch_and_insert_demand_data, store_qualitative_description


research_agent = LlmAgent(
    model=os.getenv("RESEARCH_AGENT_MODEL", "gemini-2.5-flash"),
    name="research_agent",
    instruction=return_instructions_research(),
    global_instruction=f"""
        Today's date is {date.today().isoformat()}.
        You can only insert data for dates on or before today, NOT future dates.
        Always use: product_id=PONDS, customer_id=BLINKIT, location_id=Bangalore.
    """,
    tools=[
        fetch_and_insert_demand_data,
        store_qualitative_description,
    ],
    generate_content_config=types.GenerateContentConfig(temperature=0.3),
)
