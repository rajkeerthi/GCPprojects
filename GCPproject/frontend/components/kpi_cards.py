"""
KPI Cards component for displaying key metrics.

Shows:
- Current Baseline Demand
- Sensed Demand Uplift/Downgrade
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from services.mock_data import get_mock_service


def render_kpi_section(
    product_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: date,
) -> None:
    """
    Renders the KPI metrics section at the top of the Demand Planner tab.
    
    Displays two key metrics:
    1. Current Baseline Demand (from Statistical Baseline Forecast)
    2. Sensed Demand Uplift/Downgrade (% change and absolute units)
    """
    mock_service = get_mock_service()

    # Get forecast data
    forecast = mock_service.get_forecast(
        product_id, customer_id, location_id, as_of_date
    )

    # Calculate values
    baseline = forecast.baseline_forecast
    sensed = forecast.sensed_demand
    boost_pct = forecast.boost_percent

    # Determine if uplift or downgrade
    is_uplift = boost_pct >= 0
    direction_text = "Uplift" if is_uplift else "Downgrade"
    direction_icon = "📈" if is_uplift else "📉"
    direction_color = "#14B8A6" if is_uplift else "#F87171"

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
                border: 1px solid #334155;
                border-radius: 16px;
                padding: 24px;
                height: 140px;
                transition: all 0.2s ease;
            ">
                <div style="
                    color: #94A3B8;
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 12px;
                ">
                    📦 Current Baseline Demand
                </div>
                <div style="
                    color: #F8FAFC;
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 2.8rem;
                    font-weight: 700;
                    line-height: 1;
                ">
                    {baseline:.0f}
                </div>
                <div style="
                    color: #64748B;
                    font-size: 0.85rem;
                    margin-top: 8px;
                ">
                    units • Statistical Forecast
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
                border: 1px solid {direction_color};
                border-radius: 16px;
                padding: 24px;
                height: 140px;
                transition: all 0.2s ease;
                box-shadow: 0 0 20px {direction_color}20;
            ">
                <div style="
                    color: #94A3B8;
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 12px;
                ">
                    {direction_icon} Sensed Demand {direction_text}
                </div>
                <div style="display: flex; align-items: baseline; gap: 12px;">
                    <span style="
                        color: {direction_color};
                        font-family: 'JetBrains Mono', monospace;
                        font-size: 2.8rem;
                        font-weight: 700;
                        line-height: 1;
                    ">
                        {'+' if is_uplift else ''}{boost_pct:.1f}%
                    </span>
                    <span style="
                        color: #F8FAFC;
                        font-size: 1.2rem;
                        font-weight: 600;
                    ">
                        → {sensed:.0f} units
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
