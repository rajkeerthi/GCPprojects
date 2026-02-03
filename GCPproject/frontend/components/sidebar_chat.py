"""
Sidebar Chat component.

Features:
- Two trigger buttons: Generate Demand, Data Science Query
- Chat history display
- Input box for custom queries
- Conversational flow for gathering context
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List

import streamlit as st

from services.mock_data import get_mock_service


def render_sidebar_chat(
    product_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: date,
) -> None:
    """
    Renders the chat interface in the sidebar.
    
    Two main flows:
    1. Generate Demand - Agent asks questions, then generates forecast
    2. Data Science Query - Agent asks what analysis user wants
    """
    # Initialize chat state
    if "sidebar_chat_history" not in st.session_state:
        st.session_state.sidebar_chat_history = []
    
    if "chat_mode" not in st.session_state:
        st.session_state.chat_mode = None  # None, "demand", "datascience"

    # Header
    st.markdown(
        """<p style="color: #94A3B8; font-size: 0.7rem; text-transform: uppercase; 
        letter-spacing: 1px; margin: 0 0 8px 0;">💬 Assistant</p>""",
        unsafe_allow_html=True,
    )

    # Two trigger buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎯 Demand", use_container_width=True, key="btn_demand"):
            _start_demand_flow(product_id, customer_id, location_id, as_of_date)
            st.rerun()

    with col2:
        if st.button("📊 Analysis", use_container_width=True, key="btn_analysis"):
            _start_datascience_flow()
            st.rerun()

    # Chat history container
    chat_container = st.container(height=280)
    
    with chat_container:
        if not st.session_state.sidebar_chat_history:
            st.markdown(
                """
                <div style="
                    color: #64748B;
                    font-size: 0.8rem;
                    text-align: center;
                    padding: 20px 10px;
                ">
                    Click <b>🎯 Demand</b> to generate forecast<br>
                    or <b>📊 Analysis</b> for data science queries
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for msg in st.session_state.sidebar_chat_history:
                if msg["role"] == "assistant":
                    st.chat_message("assistant", avatar="🤖").write(msg["content"])
                elif msg["role"] == "user":
                    st.chat_message("user", avatar="👤").write(msg["content"])

    # Input box
    user_input = st.chat_input("Type your message...", key="sidebar_chat_input")
    
    if user_input:
        _handle_user_input(user_input, product_id, customer_id, location_id, as_of_date)
        st.rerun()

    # Clear button
    if st.session_state.sidebar_chat_history:
        if st.button("🗑️ Clear", use_container_width=True, key="btn_clear_chat"):
            st.session_state.sidebar_chat_history = []
            st.session_state.chat_mode = None
            st.rerun()


def _start_demand_flow(product_id: str, customer_id: str, location_id: str, as_of_date: date) -> None:
    """Start the demand generation conversation flow."""
    st.session_state.chat_mode = "demand"
    st.session_state.sidebar_chat_history = []
    
    mock_service = get_mock_service()
    product_name = mock_service.get_product_display_name(product_id)
    
    # Agent initiates conversation
    st.session_state.sidebar_chat_history.append({
        "role": "assistant",
        "content": f"""**🎯 Demand Forecast Generation**

I'll generate a forecast using the current context:

• **Product:** {product_name}
• **Customer:** {customer_id}
• **Location:** {location_id}
• **Date:** {as_of_date}

Type **"generate"** to proceed, or tell me if you want to change anything."""
    })


def _start_datascience_flow() -> None:
    """Start the data science query conversation flow."""
    st.session_state.chat_mode = "datascience"
    st.session_state.sidebar_chat_history = []
    
    # Agent initiates conversation
    st.session_state.sidebar_chat_history.append({
        "role": "assistant",
        "content": """**📊 Data Science Query**

What would you like to analyze?

1️⃣ **Driver importance** - Which factors affect demand most?
2️⃣ **Trend analysis** - How are drivers changing over time?
3️⃣ **Correlation** - How do drivers relate to each other?
4️⃣ **Weather impact** - How does weather affect this product?

Type a number (1-4) or ask your own question."""
    })


def _handle_user_input(
    user_input: str,
    product_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: date,
) -> None:
    """Process user input and generate response."""
    # Add user message
    st.session_state.sidebar_chat_history.append({
        "role": "user",
        "content": user_input,
    })
    
    # Generate response based on mode and input
    response = _generate_response(
        user_input,
        product_id,
        customer_id,
        location_id,
        as_of_date,
    )
    
    st.session_state.sidebar_chat_history.append({
        "role": "assistant",
        "content": response,
    })


def _generate_response(
    user_input: str,
    product_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: date,
) -> str:
    """Generate a response based on user input and current mode."""
    mock_service = get_mock_service()
    input_lower = user_input.lower().strip()
    mode = st.session_state.chat_mode
    
    # =========================================================================
    # DEMAND GENERATION MODE
    # =========================================================================
    if mode == "demand":
        if "generate" in input_lower or "yes" in input_lower or "proceed" in input_lower:
            forecast = mock_service.get_forecast(product_id, customer_id, location_id, as_of_date)
            
            return f"""**✅ Forecast Generated!**

| Metric | Value |
|--------|-------|
| Baseline | {forecast.baseline_forecast:.0f} units |
| **Sensed Demand** | **{forecast.sensed_demand:.0f} units** |
| Change | {'+' if forecast.boost_percent >= 0 else ''}{forecast.boost_percent:.1f}% |

**Top Drivers:**
{_format_top_drivers(forecast.driver_contributions)}

📌 **Go to Demand Planner tab** to review details and approve/reject."""
        else:
            return "Please type **'generate'** to create the forecast, or click the **🎯 Demand** button again to restart."
    
    # =========================================================================
    # DATA SCIENCE MODE
    # =========================================================================
    elif mode == "datascience":
        forecast = mock_service.get_forecast(product_id, customer_id, location_id, as_of_date)
        driver_data = mock_service.get_demand_drivers(product_id, customer_id, location_id, as_of_date)
        
        # Option 1: Driver importance
        if input_lower in ["1", "driver", "importance", "drivers"]:
            return f"""**📊 Driver Importance Analysis**

{_format_all_drivers(forecast.driver_contributions)}

**Insight:** Top driver is **{max(forecast.driver_contributions.items(), key=lambda x: abs(x[1]))[0]}**

📈 *View chart in Data Scientist tab → Driver Importance*"""
        
        # Option 2: Trend analysis
        elif input_lower in ["2", "trend", "trends"]:
            return """**📈 Trend Analysis**

To see detailed trend charts:
1. Go to **Data Scientist tab**
2. Select **"Time Series Trend"** from dropdown
3. Choose which drivers to compare

The chart will show 30-day trends for selected drivers."""
        
        # Option 3: Correlation
        elif input_lower in ["3", "correlation", "correlate"]:
            return """**🔗 Correlation Analysis**

To see driver correlations:
1. Go to **Data Scientist tab**
2. Select **"Driver Correlation Heatmap"**

This shows how drivers relate to each other (positive/negative correlations)."""
        
        # Option 4: Weather
        elif input_lower in ["4", "weather"]:
            temp = driver_data.drivers.get("Max Temperature Forecast", 25)
            uv = driver_data.drivers.get("UV Index", 5)
            weather_contrib = forecast.driver_contributions.get("Weather", 0)
            
            return f"""**🌤️ Weather Impact Analysis**

**Current Conditions:**
• Temperature: {temp}°C
• UV Index: {uv}

**Impact on Demand:**
Weather contributes **{'+' if weather_contrib >= 0 else ''}{weather_contrib*100:.1f}%** to forecast.

{'☀️ High temps boost face care product demand.' if temp > 28 else '🌡️ Moderate weather has neutral impact.'}"""
        
        # Custom question
        else:
            return _handle_custom_query(input_lower, forecast, driver_data)
    
    # =========================================================================
    # NO MODE - General response
    # =========================================================================
    else:
        if any(word in input_lower for word in ["forecast", "demand", "generate", "predict"]):
            _start_demand_flow(product_id, customer_id, location_id, as_of_date)
            return st.session_state.sidebar_chat_history[-1]["content"]
        elif any(word in input_lower for word in ["driver", "analysis", "chart", "trend", "data"]):
            _start_datascience_flow()
            return st.session_state.sidebar_chat_history[-1]["content"]
        else:
            return """I can help you with:

**🎯 Demand Generation** - Click the button or type "forecast"
**📊 Data Science** - Click the button or type "analysis"

What would you like to do?"""


def _handle_custom_query(query: str, forecast, driver_data) -> str:
    """Handle custom/free-form queries."""
    if "marketing" in query or "spend" in query:
        contrib = forecast.driver_contributions.get("Marketing Spend", 0)
        spend = driver_data.drivers.get("Performance Marketing Spend", 0)
        return f"""**📢 Marketing Impact**

Current spend: ₹{spend:,.0f}
Contribution: **{'+' if contrib >= 0 else ''}{contrib*100:.1f}%**

Marketing is {'a significant uplift driver' if contrib > 0.05 else 'having moderate impact'}."""
    
    elif "competitor" in query:
        contrib = forecast.driver_contributions.get("Competitor", 0)
        oos = driver_data.drivers.get("Competitor Out-of-Stock Status", False)
        return f"""**🎯 Competitor Analysis**

Competitor OOS: {'Yes ✅ (opportunity!)' if oos else 'No'}
Impact: **{'+' if contrib >= 0 else ''}{contrib*100:.1f}%**

{'Competitor stock-out is creating demand capture opportunity!' if oos else 'No significant competitor headwinds.'}"""
    
    elif "social" in query or "trend" in query:
        contrib = forecast.driver_contributions.get("Social & Trend", 0)
        return f"""**📱 Social & Trend Impact**

Contribution: **{'+' if contrib >= 0 else ''}{contrib*100:.1f}%**

{'Social signals are driving uplift!' if contrib > 0.05 else 'Social signals are neutral.'}"""
    
    else:
        return """I didn't understand that query. Try asking about:
• **Marketing** - "How is marketing spend affecting demand?"
• **Competitors** - "What's the competitor impact?"
• **Social trends** - "How are social signals?"

Or select a numbered option (1-4)."""


def _format_top_drivers(contributions: Dict[str, float]) -> str:
    """Format top 3 drivers as bullet points."""
    sorted_drivers = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
    return "\n".join([
        f"• **{d[0]}**: {'+' if d[1] >= 0 else ''}{d[1]*100:.1f}%"
        for d in sorted_drivers
    ])


def _format_all_drivers(contributions: Dict[str, float]) -> str:
    """Format all drivers as a list."""
    sorted_drivers = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
    return "\n".join([
        f"• **{d[0]}**: {'+' if d[1] >= 0 else ''}{d[1]*100:.1f}%"
        for d in sorted_drivers
    ])









