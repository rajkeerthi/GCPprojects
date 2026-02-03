"""
Data Override Table component for HITL approval workflow.

Allows demand planners to:
- View suggested HITL values
- Enter manual override values
- See difference highlighting
- Approve or reject forecasts
"""

from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd
import streamlit as st

from services.mock_data import get_mock_service


def render_data_override_table(
    product_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: date,
) -> None:
    """
    Renders the data override table with HITL approval functionality.
    
    Features:
    - Shows demand driver values with current values
    - Allows planner to enter override value
    - Highlights differences between suggested and override
    - Approve/Reject buttons
    """
    mock_service = get_mock_service()

    # Get forecast data
    forecast = mock_service.get_forecast(
        product_id, customer_id, location_id, as_of_date
    )

    st.markdown("---")
    st.markdown("### ✏️ HITL Override & Approval")

    # Approval status indicator
    status = forecast.approval_status
    status_colors = {
        "pending": ("#F59E0B", "⏳"),
        "approved": ("#22C55E", "✅"),
        "rejected": ("#EF4444", "❌"),
    }
    color, icon = status_colors.get(status, ("#64748B", "•"))

    st.markdown(
        f"""
        <div style="
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: {color}20;
            border: 1px solid {color};
            border-radius: 20px;
            padding: 6px 16px;
            margin-bottom: 16px;
        ">
            <span>{icon}</span>
            <span style="color: {color}; font-weight: 600; text-transform: uppercase; font-size: 0.75rem;">
                {status}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Main override section
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("##### Forecast Summary")

        # Create a summary table
        summary_data = {
            "Metric": [
                "Statistical Baseline",
                "AI Sensed Demand",
                "Change (%)",
                "Planner Override",
            ],
            "Value": [
                f"{forecast.baseline_forecast:.0f} units",
                f"{forecast.sensed_demand:.0f} units",
                f"{'+' if forecast.boost_percent >= 0 else ''}{forecast.boost_percent:.1f}%",
                "—" if forecast.planner_override is None else f"{forecast.planner_override:.0f} units",
            ],
        }

        df_summary = pd.DataFrame(summary_data)
        st.dataframe(
            df_summary,
            hide_index=True,
            use_container_width=True,
        )

    with col2:
        st.markdown("##### Enter Override")

        # Initialize session state for override
        override_key = f"override_{product_id}_{customer_id}_{location_id}_{as_of_date}"
        if override_key not in st.session_state:
            st.session_state[override_key] = None

        # Override input
        override_value = st.number_input(
            "Override Value (units)",
            min_value=0.0,
            max_value=10000.0,
            value=float(forecast.sensed_demand),
            step=1.0,
            key=f"override_input_{override_key}",
            help="Enter your adjusted forecast if different from AI suggestion",
        )

        # Calculate difference
        diff = override_value - forecast.sensed_demand
        diff_pct = (diff / forecast.sensed_demand * 100) if forecast.sensed_demand > 0 else 0

        if abs(diff) > 0.5:
            diff_color = "#F59E0B"
            st.markdown(
                f"""
                <div style="
                    background: {diff_color}20;
                    border: 1px solid {diff_color};
                    border-radius: 8px;
                    padding: 12px;
                    margin-top: 8px;
                ">
                    <span style="color: {diff_color}; font-weight: 600;">
                        ⚠️ Difference: {'+' if diff > 0 else ''}{diff:.0f} units ({'+' if diff_pct > 0 else ''}{diff_pct:.1f}%)
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Reasoning section
    st.markdown("---")
    st.markdown("##### 🤖 AI Reasoning")

    st.markdown(
        f"""
        <div style="
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
            line-height: 1.6;
        ">
            {forecast.reasoning.replace(chr(10), '<br>')}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Approval Buttons
    st.markdown("---")
    st.markdown("##### 🔐 Approval Action")

    col_approve, col_reject, col_spacer = st.columns([1, 1, 2])

    with col_approve:
        if st.button(
            "✅ Approve Forecast",
            type="primary",
            use_container_width=True,
            key=f"approve_{override_key}",
        ):
            try:
                mock_service.update_forecast_approval(
                    sku_id=product_id,
                    customer_id=customer_id,
                    location_id=location_id,
                    as_of_date=as_of_date.strftime("%Y-%m-%d"),
                    status="approved",
                    override_value=override_value if abs(diff) > 0.5 else None,
                )
                st.success("✅ Forecast approved! Data will be written to Final Consensus Demand DB.")
                st.balloons()
            except Exception as e:
                st.error(f"Error: {str(e)}")

    with col_reject:
        if st.button(
            "❌ Reject",
            type="secondary",
            use_container_width=True,
            key=f"reject_{override_key}",
        ):
            try:
                mock_service.update_forecast_approval(
                    sku_id=product_id,
                    customer_id=customer_id,
                    location_id=location_id,
                    as_of_date=as_of_date.strftime("%Y-%m-%d"),
                    status="rejected",
                )
                st.warning("❌ Forecast rejected. Please provide feedback in the chat.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Add note about what happens on approval
    st.caption(
        "💡 On approval, the final consensus demand will be written to `final-consensus-demand-db` (Cloud SQL) "
        "for downstream supply planning systems."
    )
