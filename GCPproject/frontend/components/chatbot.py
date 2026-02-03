"""
Chatbot component for interactive queries and explanations.

Features:
- Persistent chat interface (right panel)
- Data science query support via Vertex AI Agent Engine
- Rich content display: text, images, markdown, tables
- Demand prediction reasoning display

The chatbot connects to the deployed Data Science Agent on
Vertex AI Agent Engine for real-time responses.
"""

from __future__ import annotations

import base64
from datetime import date, datetime
from typing import Dict, List, Any

import streamlit as st

from services.api_client import AgentEngineClient, AgentResponse
from services.mock_data import get_mock_service


def render_chatbot(
    product_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: date,
) -> None:
    """
    Renders the chatbot interface.
    
    The chatbot handles:
    - Demand forecast generation requests
    - Data science queries (importance, trends, etc.)
    - Rich content display (images, tables, markdown)
    """
    # Initialize chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Initialize session ID for conversation continuity
    if "agent_session_id" not in st.session_state:
        st.session_state.agent_session_id = None

    # Chat header
    st.markdown("### 🤖 Demand Planner Assistant")
    st.caption("Ask about forecasts, predictions & demand drivers")

    # Quick action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎯 Predict POS Sales", use_container_width=True, key="quick_forecast"):
            _handle_quick_action("predict_sales", product_id, customer_id, location_id, as_of_date)

    with col2:
        if st.button("📊 Analyze Drivers", use_container_width=True, key="quick_datascience"):
            _handle_quick_action("analyze_drivers", product_id, customer_id, location_id, as_of_date)

    st.markdown("---")

    # Chat messages container
    chat_container = st.container(height=450)

    with chat_container:
        # Display chat history with rich content
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            elif msg["role"] == "assistant":
                with st.chat_message("assistant"):
                    _render_rich_content(msg)

    # Chat input
    user_input = st.chat_input(
        "Ask about forecasts, predictions, or demand drivers...",
        key="chat_input",
    )

    if user_input:
        _handle_user_message(user_input, product_id, customer_id, location_id, as_of_date)
        st.rerun()

    # Clear chat button
    if st.button("🗑️ Clear Chat", key="clear_chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.agent_session_id = None
        st.rerun()


def _render_rich_content(msg: Dict[str, Any]) -> None:
    """Render rich content from assistant message including text, images, and artifacts."""
    # Render main text content with markdown support
    if msg.get("content"):
        st.markdown(msg["content"])
    
    # Render images if present (charts from analytics agent, etc.)
    if msg.get("images"):
        st.markdown("#### 📊 Generated Charts")
        for idx, img in enumerate(msg["images"]):
            try:
                mime_type = img.get("mime_type", "image/png")
                data = img.get("data", "")
                name = img.get("name", f"Chart {idx + 1}")
                if data:
                    # Ensure data doesn't have data URL prefix
                    if data.startswith("data:"):
                        st.image(data, caption=name)
                    else:
                        st.image(f"data:{mime_type};base64,{data}", caption=name)
            except Exception as e:
                st.warning(f"Could not display image '{name}': {e}")
    
    # Render artifacts (code, files, text output, etc.)
    if msg.get("artifacts"):
        has_displayable = any(
            a.get("name") not in ["code_output"] or 
            (isinstance(a.get("data"), dict) and a["data"].get("type") == "text" and len(a["data"].get("content", "")) > 100)
            for a in msg["artifacts"]
        )
        
        if has_displayable:
            for artifact in msg["artifacts"]:
                name = artifact.get("name", "artifact")
                data = artifact.get("data")
                
                if not data:
                    continue
                
                # Handle executed code artifact
                if name == "executed_code" and isinstance(data, dict):
                    with st.expander("🐍 Python Code Executed", expanded=False):
                        language = data.get("language", "python")
                        code = data.get("code", "")
                        st.code(code, language=language)
                
                # Handle code output (from execution)
                elif name == "code_output" and isinstance(data, dict):
                    content = data.get("content", "")
                    if content and len(content) > 50:
                        with st.expander("📝 Code Output", expanded=False):
                            st.code(content, language="text")
                
                # Handle text artifacts
                elif isinstance(data, dict) and data.get("type") == "text":
                    content = data.get("content", "")
                    if content:
                        with st.expander(f"📄 {name}", expanded=False):
                            st.code(content, language="text")
                
                # Handle file artifacts (GCS URIs, etc.)
                elif isinstance(data, dict) and data.get("type") == "file":
                    uri = data.get("uri", "")
                    mime = data.get("mime_type", "")
                    with st.expander(f"📁 {name}", expanded=False):
                        st.write(f"**Type:** {mime}")
                        st.write(f"**URI:** {uri}")
                
                # Handle dict artifacts with inline_data (missed images)
                elif isinstance(data, dict) and "inline_data" in data:
                    inline = data["inline_data"]
                    if inline.get("mime_type", "").startswith("image/"):
                        st.image(f"data:{inline['mime_type']};base64,{inline.get('data', '')}", caption=name)
                    else:
                        with st.expander(f"📎 {name}", expanded=False):
                            st.json(data)
                
                # Handle dict artifacts with parts (ADK Content format)
                elif isinstance(data, dict) and "parts" in data:
                    for part in data["parts"]:
                        if "inline_data" in part:
                            inline = part["inline_data"]
                            if inline.get("mime_type", "").startswith("image/"):
                                st.image(f"data:{inline['mime_type']};base64,{inline.get('data', '')}", caption=name)
                        elif "text" in part:
                            with st.expander(f"📄 {name}", expanded=False):
                                st.write(part["text"])
                
                # Handle other dict artifacts
                elif isinstance(data, dict):
                    with st.expander(f"📎 {name}", expanded=False):
                        st.json(data)
                
                # Handle string artifacts
                elif isinstance(data, str) and len(data) > 10:
                    with st.expander(f"📎 {name}", expanded=False):
                        st.code(data)
    
    # Show tool calls if present (for transparency)
    if msg.get("tool_calls"):
        with st.expander("🔧 Tools Used", expanded=False):
            for tool in msg["tool_calls"]:
                st.caption(f"• {tool}")


def _handle_user_message(
    message: str,
    product_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: date,
) -> None:
    """Process user message and generate response with rich content."""
    # Add user message
    st.session_state.chat_history.append({
        "role": "user",
        "content": message,
    })

    # Generate rich response
    response = _generate_rich_response(message, product_id, customer_id, location_id, as_of_date)

    # Add assistant response with all content types
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": response.text,
        "images": response.images,
        "artifacts": response.artifacts,
        "tool_calls": response.tool_calls,
    })


def _handle_quick_action(
    action: str,
    product_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: date,
) -> None:
    """Handle quick action button clicks."""
    action_messages = {
        "predict_sales": f"Predict POS sales for {product_id} at {customer_id} in {location_id} for {as_of_date}",
        "analyze_drivers": f"What are the most important demand drivers affecting {product_id} at {customer_id}?",
    }

    message = action_messages.get(action, "Help me understand demand forecasting.")
    _handle_user_message(message, product_id, customer_id, location_id, as_of_date)
    st.rerun()


def _generate_rich_response(
    message: str,
    product_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: date,
) -> AgentResponse:
    """
    Generate a rich response using the Vertex AI Agent Engine.
    
    Returns AgentResponse with text, images, artifacts, and metadata.
    
    Architecture:
    1. Streamlit sends query to Agent Engine (Demand Planner Agent)
    2. Agent queries BigQuery, runs ML predictions, performs analysis
    3. Response includes text, images, and structured data
    """
    # Add context to the message
    context_message = f"""
Context:
- Product: {product_id}
- Customer: {customer_id}
- Location: {location_id}
- Date: {as_of_date}

User Question: {message}
"""
    
    # Use Agent Engine for rich response
    agent_client = AgentEngineClient()
    
    try:
        # Get rich response from Agent Engine
        response = agent_client.query_rich(
            message=context_message,
            user_id=f"streamlit-{customer_id}",
            session_id=st.session_state.get("agent_session_id"),
        )
        
        if response.text and not response.text.startswith("Error"):
            return response
        else:
            # Fallback to mock if Agent Engine fails
            return _fallback_mock_response(message, product_id, customer_id, location_id, as_of_date)
            
    except Exception as e:
        # Fallback to mock data on error
        return _fallback_mock_response(message, product_id, customer_id, location_id, as_of_date)


def _fallback_mock_response(
    message: str,
    product_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: date,
) -> AgentResponse:
    """Fallback to mock data if Agent Engine is unavailable."""
    mock_service = get_mock_service()
    forecast = mock_service.get_forecast(product_id, customer_id, location_id, as_of_date)
    driver_data = mock_service.get_demand_drivers(product_id, customer_id, location_id, as_of_date)

    message_lower = message.lower()

    # FORECAST GENERATION REQUEST
    if any(word in message_lower for word in ["generate", "forecast", "predict"]):
        text = f"""**🎯 Demand Forecast Generated** *(Mock Data - Agent Engine Unavailable)*

**Product:** {mock_service.get_product_display_name(product_id)}
**Customer:** {customer_id} | **Date:** {as_of_date}

| Metric | Value |
|--------|-------|
| Baseline | {forecast.baseline_forecast:.0f} units |
| **Sensed Demand** | **{forecast.sensed_demand:.0f} units** |
| Change | {'+' if forecast.boost_percent >= 0 else ''}{forecast.boost_percent:.1f}% |

**Reasoning:** {forecast.reasoning[:200]}...

📌 *Review in the Demand Planner tab and approve/reject.*"""
        return AgentResponse(text=text)

    # DATA SCIENCE QUERIES
    elif any(word in message_lower for word in ["driver", "important", "affect", "impact"]):
        sorted_drivers = sorted(
            forecast.driver_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True,
        )

        driver_list = "\n".join([
            f"- **{d[0]}**: {'+' if d[1] >= 0 else ''}{d[1]*100:.1f}%"
            for d in sorted_drivers
        ])

        text = f"""**📊 Driver Importance Analysis** *(Mock Data - Agent Engine Unavailable)*

{driver_list}

**Key Insight:** Top driver is **{sorted_drivers[0][0]}** ({'+' if sorted_drivers[0][1] >= 0 else ''}{sorted_drivers[0][1]*100:.1f}%)

💡 *Use Data Scientist tab for detailed charts.*"""
        return AgentResponse(text=text)

    elif any(word in message_lower for word in ["weather", "temperature"]):
        temp = driver_data.drivers.get("Max Temperature Forecast", 25)
        weather_boost = forecast.driver_contributions.get("Weather", 0)

        text = f"""**🌤️ Weather Impact** *(Mock Data - Agent Engine Unavailable)*

Temperature: **{temp}°C**
Weather contribution: **{'+' if weather_boost >= 0 else ''}{weather_boost*100:.1f}%**

{'☀️ Higher temps boost face gel demand.' if temp > 28 else '🌡️ Moderate weather, neutral impact.'}"""
        return AgentResponse(text=text)

    # DEFAULT RESPONSE
    else:
        text = f"""I'm the **Demand Planner Assistant**! I can help you with:

**🎯 POS Sales Predictions:**
- "Predict POS sales for December 25, 2025"

**📊 Demand Driver Analysis:**
- "What are the most important drivers?"
- "How does weather affect demand?"

**📈 Data Queries:**
- "Show me historical sales trends"
- "Compare forecast vs actual"

**Current Mock Forecast:** {forecast.sensed_demand:.0f} units ({'+' if forecast.boost_percent >= 0 else ''}{forecast.boost_percent:.1f}% vs baseline)

⚠️ *Using mock data - Agent Engine connection issue*"""
        return AgentResponse(text=text)
