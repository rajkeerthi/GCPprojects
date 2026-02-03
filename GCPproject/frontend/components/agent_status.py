"""
Live Agent Status widget component (Compact version).

Displays alerts detected by the Research Agent.
"""

from __future__ import annotations

from datetime import date
from typing import List

import streamlit as st

from services.mock_data import get_mock_service, AlertSignal


def render_agent_status(
    product_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: date,
) -> None:
    """
    Renders a compact Live Agent Status widget.
    """
    mock_service = get_mock_service()

    st.markdown(
        """<p style="color: #94A3B8; font-size: 0.7rem; text-transform: uppercase; 
        letter-spacing: 1px; margin: 12px 0 6px 0;">🤖 Agent Status</p>""",
        unsafe_allow_html=True,
    )

    # Get alerts for the current context
    alerts = mock_service.detect_alerts(
        product_id, customer_id, location_id, as_of_date
    )

    if not alerts:
        # No alerts - show calm status
        st.markdown(
            """
            <div style="
                background: rgba(34, 197, 94, 0.1);
                border: 1px solid #22C55E;
                border-radius: 8px;
                padding: 8px 12px;
                margin-bottom: 8px;
            ">
                <span style="color: #22C55E; font-size: 0.8rem;">✅ All Normal</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Show alert count with expander
        high_count = len([a for a in alerts if a.severity == "high"])
        
        if high_count > 0:
            st.markdown(
                f"""
                <div style="
                    background: rgba(239, 68, 68, 0.1);
                    border: 1px solid #EF4444;
                    border-radius: 8px;
                    padding: 8px 12px;
                    margin-bottom: 8px;
                ">
                    <span style="color: #EF4444; font-size: 0.8rem;">🔴 {high_count} Critical Alert(s)</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="
                    background: rgba(245, 158, 11, 0.1);
                    border: 1px solid #F59E0B;
                    border-radius: 8px;
                    padding: 8px 12px;
                    margin-bottom: 8px;
                ">
                    <span style="color: #F59E0B; font-size: 0.8rem;">🟡 {len(alerts)} Signal(s)</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        # Show alerts in expander
        with st.expander("View Details", expanded=False):
            for alert in alerts[:3]:  # Show max 3
                severity_color = {
                    "high": "#EF4444",
                    "medium": "#F59E0B",
                    "low": "#22C55E",
                }.get(alert.severity, "#64748B")
                
                st.markdown(
                    f"<p style='color: {severity_color}; font-size: 0.75rem; margin: 4px 0;'>{alert.message}</p>",
                    unsafe_allow_html=True,
                )

    # Research agent indicator (compact)
    st.markdown(
        """
        <div style="
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 4px 0;
        ">
            <div style="
                width: 6px;
                height: 6px;
                background: #14B8A6;
                border-radius: 50%;
                animation: pulse 2s infinite;
            "></div>
            <span style="color: #64748B; font-size: 0.7rem;">Research Agent monitoring...</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
