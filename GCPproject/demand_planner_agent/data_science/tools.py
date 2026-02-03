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

"""Tools for the ADK Samples Data Science Agent."""

import logging

from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

# Lazy imports for Agent Engine compatibility
# Sub-agents are imported inside functions to avoid module-level env var access

logger = logging.getLogger(__name__)


async def call_bigquery_agent(
    question: str,
    tool_context: ToolContext,
):
    """Tool to call bigquery database (nl2sql) agent."""
    logger.debug("call_bigquery_agent: %s", question)

    # Lazy import to support Agent Engine deployment
    from .sub_agents.bigquery.agent import get_bigquery_agent
    agent_tool = AgentTool(agent=get_bigquery_agent())

    bigquery_agent_output = await agent_tool.run_async(
        args={"request": question}, tool_context=tool_context
    )
    tool_context.state["bigquery_agent_output"] = bigquery_agent_output
    return bigquery_agent_output


async def call_alloydb_agent(
    question: str,
    tool_context: ToolContext,
):
    """Tool to call alloydb database (nl2sql) agent."""
    logger.debug("call_alloydb_agent: %s", question)

    # Lazy import to support Agent Engine deployment
    from .sub_agents.alloydb.agent import get_alloydb_agent
    agent_tool = AgentTool(agent=get_alloydb_agent())

    alloydb_agent_output = await agent_tool.run_async(
        args={"request": question}, tool_context=tool_context
    )
    tool_context.state["alloydb_agent_output"] = alloydb_agent_output
    return alloydb_agent_output


async def call_analytics_agent(
    question: str,
    tool_context: ToolContext,
):
    """
    This tool can generate Python code to process and analyze a dataset.

    Some of the tasks it can do in Python include:
    * Creating graphics for data visualization;
    * Processing or filtering existing datasets;
    * Combining datasets to create a joined dataset for further analysis.

    The Python modules available to it are:
    * io
    * math
    * re
    * matplotlib.pyplot
    * numpy
    * pandas

    The tool DOES NOT have the ability to retrieve additional data from
    a database. Only the data already retrieved will be analyzed.

    Args:
        question (str): Natural language question or analytics request.
        tool_context (ToolContext): The tool context to use for generating the
            SQL query.

    Returns:
        Response from the analytics agent.

    """
    logger.debug("call_analytics_agent: %s", question)

    # if question == "N/A":
    #    return tool_context.state["db_agent_output"]

    bigquery_data = ""
    alloydb_data = ""

    if "bigquery_query_result" in tool_context.state:
        bigquery_data = tool_context.state["bigquery_query_result"]
    if "alloydb_query_result" in tool_context.state:
        alloydb_data = tool_context.state["alloydb_query_result"]

    question_with_data = f"""
  Question to answer: {question}

  Actual data to analyze this question is available in the following data
  tables:

  <BIGQUERY>
  {bigquery_data}
  </BIGQUERY>

  <ALLOYDB>
  {alloydb_data}
  </ALLOYDB>

  """

    # Lazy import to support Agent Engine deployment
    from .sub_agents.analytics.agent import get_analytics_agent
    agent_tool = AgentTool(agent=get_analytics_agent())

    analytics_agent_output = await agent_tool.run_async(
        args={"request": question_with_data}, tool_context=tool_context
    )
    tool_context.state["analytics_agent_output"] = analytics_agent_output
    return analytics_agent_output


async def call_research_agent(
    request: str,
    tool_context: ToolContext,
):
    """
    Tool to call the Research Agent for INSERTING demand driver data.

    When data is missing for a date, the Research Agent:
    1. Fetches random feature values from existing BigQuery data
    2. Inserts a new row with PONDS/BLINKIT/Bangalore + requested date
    3. Generates a qualitative description of the features

    IMPORTANT: This tool only INSERTS new data - it cannot update existing records.
    Data is always inserted for: PONDS, BLINKIT, Bangalore.

    Args:
        request (str): Natural language request with the target date.
            Example: "Insert demand data for 2025-12-15"
        tool_context (ToolContext): The tool context for state management.

    Returns:
        Response including qualitative description and feature values.
    """
    logger.debug("call_research_agent: %s", request)

    # Lazy import to support Agent Engine deployment
    from .sub_agents.research.agent import research_agent
    agent_tool = AgentTool(agent=research_agent)

    research_agent_output = await agent_tool.run_async(
        args={"request": request}, tool_context=tool_context
    )
    tool_context.state["research_agent_output"] = research_agent_output
    
    # Extract qualitative description for Root Agent to display
    if "qualitative_description" in tool_context.state:
        logger.debug("Qualitative description available for display")
    
    # Extract inserted data features for Root Agent
    if "inserted_demand_data" in tool_context.state:
        logger.debug("Inserted demand data features available")
    
    return research_agent_output


async def call_bqml_agent(
    request: str,
    tool_context: ToolContext,
):
    """
    Tool to call the BQML Agent for predictions and BigQuery ML tasks.

    Use this tool for:
    - Making POS sales predictions using ML.PREDICT
    - Checking available BQML models
    - Training new BQML models
    - Any BigQuery ML related tasks

    The BQML Agent will:
    1. Discover available models using check_bq_models
    2. Generate and execute ML.PREDICT queries
    3. Return prediction results

    Args:
        request (str): Natural language request for BQML task.
            Example: "Predict POS sales for PONDS at BLINKIT Bangalore for Dec 17, 2025"
        tool_context (ToolContext): The tool context for state management.

    Returns:
        Response with prediction results or BQML operation outcome.
    """
    logger.debug("call_bqml_agent: %s", request)

    # Lazy import to support Agent Engine deployment
    from .sub_agents.bqml.agent import get_bqml_agent
    agent_tool = AgentTool(agent=get_bqml_agent())

    bqml_agent_output = await agent_tool.run_async(
        args={"request": request}, tool_context=tool_context
    )
    tool_context.state["bqml_agent_output"] = bqml_agent_output
    return bqml_agent_output
