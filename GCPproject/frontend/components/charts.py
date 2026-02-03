"""
Chart components for the Data Scientist tab.

Provides visualization capabilities for:
- Driver importance analysis
- Trend charts
- Correlation plots
- Custom data analysis requests

Architecture Note:
- All chart data requests go through Demand Planner Agent
- Demand Planner routes data science queries to Data Science Agent
- Data Science Agent queries BigQuery and returns chart data
- Demand Planner passes the response back to Streamlit
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.mock_data import get_mock_service


def render_chart_section(
    product_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: date,
) -> None:
    """
    Renders the chart section for the Data Scientist tab.
    
    Includes:
    - Driver importance chart
    - Historical trend simulation
    - Interactive chart builder
    """
    mock_service = get_mock_service()

    st.markdown("### 📊 Analytics Dashboard")

    # Chart type selector
    chart_type = st.selectbox(
        "Select Analysis Type",
        options=[
            "Driver Importance",
            "Forecast vs Actuals (Simulated)",
            "Driver Correlation Heatmap",
            "Time Series Trend",
        ],
        key="chart_type_select",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if chart_type == "Driver Importance":
        _render_driver_importance_chart(product_id, customer_id, location_id, as_of_date)
    elif chart_type == "Forecast vs Actuals (Simulated)":
        _render_forecast_vs_actuals(product_id, customer_id)
    elif chart_type == "Driver Correlation Heatmap":
        _render_correlation_heatmap(product_id, customer_id, location_id, as_of_date)
    elif chart_type == "Time Series Trend":
        _render_time_series_trend(product_id, customer_id, location_id)


def _render_driver_importance_chart(
    product_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: date,
) -> None:
    """Renders a horizontal bar chart showing driver importance/contribution."""
    mock_service = get_mock_service()
    forecast = mock_service.get_forecast(product_id, customer_id, location_id, as_of_date)

    contributions = forecast.driver_contributions
    df = pd.DataFrame([
        {"Driver": k, "Contribution (%)": v * 100}
        for k, v in sorted(contributions.items(), key=lambda x: x[1], reverse=True)
    ])

    # Color based on positive/negative
    df["Color"] = df["Contribution (%)"].apply(lambda x: "#14B8A6" if x >= 0 else "#F87171")

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df["Driver"],
        x=df["Contribution (%)"],
        orientation="h",
        marker=dict(
            color=df["Color"],
            line=dict(color="#1E293B", width=1),
        ),
        text=df["Contribution (%)"].apply(lambda x: f"{x:+.1f}%"),
        textposition="outside",
        textfont=dict(color="#F8FAFC", size=12),
    ))

    fig.update_layout(
        title=dict(
            text="Driver Contribution to Demand Uplift/Downgrade",
            font=dict(color="#F8FAFC", size=16),
        ),
        xaxis=dict(
            title=dict(text="Contribution (%)", font=dict(color="#94A3B8")),
            tickfont=dict(color="#94A3B8"),
            gridcolor="#334155",
            zeroline=True,
            zerolinecolor="#475569",
        ),
        yaxis=dict(
            title=dict(text="", font=dict(color="#F8FAFC")),
            tickfont=dict(color="#F8FAFC"),
        ),
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        height=400,
        margin=dict(l=20, r=100, t=60, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Insight box
    top_driver = max(contributions.items(), key=lambda x: abs(x[1]))
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #14B8A620 0%, #A78BFA20 100%);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 16px;
            margin-top: 16px;
        ">
            <span style="color: #A78BFA; font-weight: 600;">💡 Key Insight:</span>
            <span style="color: #F8FAFC;">
                The strongest driver is <strong>{top_driver[0]}</strong> with 
                {'+' if top_driver[1] >= 0 else ''}{top_driver[1]*100:.1f}% contribution.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_forecast_vs_actuals(product_id: str, customer_id: str) -> None:
    """Renders a line chart comparing forecasted vs actual sales (simulated historical data)."""
    # Simulated historical data
    dates = pd.date_range(end=date.today(), periods=30, freq="D")

    import numpy as np
    np.random.seed(42)

    base = 85 if "POND" in product_id else 75
    forecast_values = base + np.random.normal(0, 10, 30).cumsum() * 0.3
    actual_values = forecast_values + np.random.normal(0, 8, 30)

    df = pd.DataFrame({
        "Date": dates,
        "Forecast": forecast_values,
        "Actual": actual_values,
    })

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df["Forecast"],
        name="Forecast",
        mode="lines+markers",
        line=dict(color="#A78BFA", width=2),
        marker=dict(size=6),
    ))

    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df["Actual"],
        name="Actual",
        mode="lines+markers",
        line=dict(color="#14B8A6", width=2),
        marker=dict(size=6),
    ))

    # Add shaded area for forecast error
    fig.add_trace(go.Scatter(
        x=df["Date"].tolist() + df["Date"].tolist()[::-1],
        y=(df["Forecast"] + 10).tolist() + (df["Forecast"] - 10).tolist()[::-1],
        fill="toself",
        fillcolor="rgba(167, 139, 250, 0.1)",
        line=dict(color="rgba(255,255,255,0)"),
        name="Confidence Band",
        showlegend=True,
    ))

    fig.update_layout(
        title=dict(
            text="Forecast vs Actual Sales (Last 30 Days)",
            font=dict(color="#F8FAFC", size=16),
        ),
        xaxis=dict(
            title=dict(text="Date", font=dict(color="#94A3B8")),
            tickfont=dict(color="#94A3B8"),
            gridcolor="#334155",
        ),
        yaxis=dict(
            title=dict(text="Units", font=dict(color="#94A3B8")),
            tickfont=dict(color="#94A3B8"),
            gridcolor="#334155",
        ),
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#F8FAFC"),
        ),
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Calculate MAPE
    mape = np.mean(np.abs((df["Actual"] - df["Forecast"]) / df["Actual"])) * 100
    accuracy = 100 - mape

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Forecast Accuracy", f"{accuracy:.1f}%")
    with col2:
        st.metric("MAPE", f"{mape:.1f}%")
    with col3:
        bias = np.mean(df["Forecast"] - df["Actual"])
        st.metric("Bias", f"{bias:+.1f} units")


def _render_correlation_heatmap(
    product_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: date,
) -> None:
    """Renders a correlation heatmap between demand drivers."""
    mock_service = get_mock_service()
    driver_data = mock_service.get_demand_drivers(
        product_id, customer_id, location_id, as_of_date
    )

    # Select numeric drivers for correlation
    numeric_drivers = {
        k: v for k, v in driver_data.drivers.items()
        if isinstance(v, (int, float)) and not isinstance(v, bool)
    }

    # Simulated correlation matrix (in production, this would come from BigQuery analysis)
    import numpy as np
    np.random.seed(42)

    driver_names = list(numeric_drivers.keys())[:8]  # Limit for readability
    n = len(driver_names)

    # Generate a semi-realistic correlation matrix
    corr_matrix = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            corr = np.random.uniform(-0.5, 0.8)
            corr_matrix[i, j] = corr
            corr_matrix[j, i] = corr

    # Shorten names for display
    short_names = [name[:15] + "..." if len(name) > 18 else name for name in driver_names]

    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix,
        x=short_names,
        y=short_names,
        colorscale=[
            [0, "#F87171"],
            [0.5, "#0F172A"],
            [1, "#14B8A6"],
        ],
        zmid=0,
        text=np.round(corr_matrix, 2),
        texttemplate="%{text}",
        textfont=dict(size=10, color="#F8FAFC"),
        hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.2f}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text="Driver Correlation Matrix",
            font=dict(color="#F8FAFC", size=16),
        ),
        xaxis=dict(
            tickfont=dict(color="#94A3B8", size=10),
            tickangle=45,
        ),
        yaxis=dict(
            tickfont=dict(color="#94A3B8", size=10),
        ),
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        height=500,
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_time_series_trend(
    product_id: str,
    customer_id: str,
    location_id: str,
) -> None:
    """Renders a multi-driver time series trend chart."""
    mock_service = get_mock_service()

    # Let user select drivers to plot
    available_drivers = [
        "Sales Velocity",
        "PDP Views",
        "Marketing Spend",
        "Sentiment Score",
        "Discount Depth",
    ]

    selected_drivers = st.multiselect(
        "Select drivers to plot",
        options=available_drivers,
        default=["Sales Velocity", "PDP Views"],
        key="trend_drivers_select",
    )

    if not selected_drivers:
        st.info("Please select at least one driver to display.")
        return

    # Simulated time series data
    import numpy as np
    np.random.seed(42)

    dates = pd.date_range(end=date.today(), periods=30, freq="D")

    data = {"Date": dates}
    for driver in selected_drivers:
        base = np.random.uniform(50, 100)
        trend = np.random.uniform(-0.5, 0.5)
        noise = np.random.normal(0, 5, 30)
        values = base + np.arange(30) * trend + noise
        data[driver] = values

    df = pd.DataFrame(data)

    fig = go.Figure()

    colors = ["#14B8A6", "#A78BFA", "#F59E0B", "#EF4444", "#3B82F6"]
    for idx, driver in enumerate(selected_drivers):
        fig.add_trace(go.Scatter(
            x=df["Date"],
            y=df[driver],
            name=driver,
            mode="lines+markers",
            line=dict(color=colors[idx % len(colors)], width=2),
            marker=dict(size=5),
        ))

    fig.update_layout(
        title=dict(
            text="Driver Trends Over Time",
            font=dict(color="#F8FAFC", size=16),
        ),
        xaxis=dict(
            title=dict(text="Date", font=dict(color="#94A3B8")),
            tickfont=dict(color="#94A3B8"),
            gridcolor="#334155",
        ),
        yaxis=dict(
            title=dict(text="Value (Normalized)", font=dict(color="#94A3B8")),
            tickfont=dict(color="#94A3B8"),
            gridcolor="#334155",
        ),
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#F8FAFC"),
        ),
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)
