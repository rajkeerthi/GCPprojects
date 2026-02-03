"""
Sidebar component with compact configuration + chat.

Layout (top to bottom):
1. Logo/Title (compact)
2. Dropdowns (compact) - Product, Customer, Location, Date
3. Live Agent Status (compact)
4. Chat Section - Two buttons + chat history + input
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Tuple

import streamlit as st

from config.settings import get_settings
from services.mock_data import get_mock_service
from components.agent_status import render_agent_status
from components.sidebar_chat import render_sidebar_chat


def render_sidebar() -> Tuple[str, str, str, date]:
    """
    Renders the sidebar with compact config + chat.
    
    Returns:
        Tuple of (selected_product, selected_customer, selected_location, selected_date)
    """
    settings = get_settings()
    mock_service = get_mock_service()

    with st.sidebar:
        # =====================================================================
        # HEADER / LOGO (Compact)
        # =====================================================================
        st.markdown(
            """
            <div style="text-align: center; padding: 10px 0;">
                <h2 style="
                    background: linear-gradient(135deg, #14B8A6 0%, #A78BFA 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-size: 1.4rem;
                    font-weight: 700;
                    margin: 0;
                ">📊 Demand Sensing</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # =====================================================================
        # CONFIGURATION SECTION (Compact)
        # =====================================================================
        st.markdown(
            """<p style="color: #94A3B8; font-size: 0.7rem; text-transform: uppercase; 
            letter-spacing: 1px; margin: 8px 0 4px 0;">⚙️ Configuration</p>""",
            unsafe_allow_html=True,
        )

        # Product Selection (compact)
        products = mock_service.get_products()
        product_display = {p: mock_service.get_product_display_name(p) for p in products}

        selected_product = st.selectbox(
            "Product",
            options=products,
            format_func=lambda x: product_display.get(x, x),
            key="product_select",
            label_visibility="collapsed",
        )

        # Two columns for Customer and Location
        col1, col2 = st.columns(2)
        with col1:
            customers = mock_service.get_customers()
            selected_customer = st.selectbox(
                "Customer",
                options=customers,
                key="customer_select",
                label_visibility="collapsed",
            )
        with col2:
            locations = mock_service.get_locations()
            selected_location = st.selectbox(
                "Location",
                options=locations,
                key="location_select",
                label_visibility="collapsed",
            )

        # Date picker (compact)
        min_date = date.today()
        max_date = date.today() + timedelta(days=settings.forecast_horizon_days)

        selected_date = st.date_input(
            "Date",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key="date_select",
            label_visibility="collapsed",
        )

        st.caption(f"📅 Window: Today → {max_date.strftime('%b %d')}")

        # =====================================================================
        # LIVE AGENT STATUS (Compact)
        # =====================================================================
        render_agent_status(
            selected_product,
            selected_customer,
            selected_location,
            selected_date,
        )

        st.markdown("<hr style='border: none; border-top: 1px solid #334155; margin: 12px 0;'>", unsafe_allow_html=True)

        # =====================================================================
        # CHAT SECTION
        # =====================================================================
        render_sidebar_chat(
            selected_product,
            selected_customer,
            selected_location,
            selected_date,
        )

    return selected_product, selected_customer, selected_location, selected_date
