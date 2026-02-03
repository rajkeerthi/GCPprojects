"""
Custom theme and styling for the Demand Sensing Hub.

Design Philosophy:
- Dark mode friendly with deep slate backgrounds
- Accent colors: Teal (#14B8A6) for positive/uplift, Purple (#A78BFA) for insights
- Enterprise-ready with clean typography and spacing
- Inspired by modern dashboards like Linear, Vercel, Raycast
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class ThemeColors:
    """Color palette for the application."""

    # Background colors
    bg_primary: str = "#0F172A"  # Slate 900
    bg_secondary: str = "#1E293B"  # Slate 800
    bg_tertiary: str = "#334155"  # Slate 700
    bg_card: str = "#1E293B"

    # Text colors
    text_primary: str = "#F8FAFC"  # Slate 50
    text_secondary: str = "#94A3B8"  # Slate 400
    text_muted: str = "#64748B"  # Slate 500

    # Accent colors
    accent_teal: str = "#14B8A6"  # Teal 500
    accent_teal_light: str = "#2DD4BF"  # Teal 400
    accent_purple: str = "#A78BFA"  # Violet 400
    accent_purple_light: str = "#C4B5FD"  # Violet 300

    # Status colors
    success: str = "#22C55E"  # Green 500
    warning: str = "#F59E0B"  # Amber 500
    error: str = "#EF4444"  # Red 500
    info: str = "#3B82F6"  # Blue 500

    # Uplift/Downgrade colors
    uplift: str = "#14B8A6"  # Teal
    downgrade: str = "#F87171"  # Red 400

    # Border colors
    border: str = "#334155"  # Slate 700
    border_light: str = "#475569"  # Slate 600


def get_theme_colors() -> ThemeColors:
    """Returns the theme color palette."""
    return ThemeColors()


def inject_custom_css() -> str:
    """
    Returns custom CSS to inject into the Streamlit app.
    
    This CSS transforms the default Streamlit look into an enterprise-ready
    dark mode dashboard.
    """
    colors = get_theme_colors()

    return f"""
    <style>
    /* =========================================================================
       GLOBAL STYLES & FONTS
       ========================================================================= */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Outfit:wght@300;400;500;600;700&display=swap');
    
    :root {{
        --bg-primary: {colors.bg_primary};
        --bg-secondary: {colors.bg_secondary};
        --bg-tertiary: {colors.bg_tertiary};
        --text-primary: {colors.text_primary};
        --text-secondary: {colors.text_secondary};
        --accent-teal: {colors.accent_teal};
        --accent-purple: {colors.accent_purple};
        --success: {colors.success};
        --warning: {colors.warning};
        --error: {colors.error};
        --border: {colors.border};
    }}

    /* Main app background */
    .stApp {{
        background: linear-gradient(135deg, {colors.bg_primary} 0%, #0C1222 100%);
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* Hide Streamlit branding */
    #MainMenu, footer, header {{
        visibility: hidden;
    }}

    /* =========================================================================
       SIDEBAR STYLES
       ========================================================================= */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {colors.bg_secondary} 0%, {colors.bg_primary} 100%);
        border-right: 1px solid {colors.border};
    }}

    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {{
        color: {colors.text_primary};
        font-weight: 600;
    }}

    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] label {{
        color: {colors.text_secondary};
    }}

    /* =========================================================================
       SELECTBOX / DROPDOWN STYLES
       ========================================================================= */
    [data-testid="stSelectbox"] > div > div {{
        background-color: {colors.bg_tertiary};
        border: 1px solid {colors.border};
        border-radius: 8px;
        color: {colors.text_primary};
    }}

    [data-testid="stSelectbox"] > div > div:hover {{
        border-color: {colors.accent_teal};
    }}

    /* =========================================================================
       DATE INPUT STYLES
       ========================================================================= */
    [data-testid="stDateInput"] > div > div {{
        background-color: {colors.bg_tertiary};
        border: 1px solid {colors.border};
        border-radius: 8px;
    }}

    /* =========================================================================
       TAB STYLES
       ========================================================================= */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {colors.bg_secondary};
        padding: 8px;
        border-radius: 12px;
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        color: {colors.text_secondary};
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
        transition: all 0.2s ease;
    }}

    .stTabs [data-baseweb="tab"]:hover {{
        background-color: {colors.bg_tertiary};
        color: {colors.text_primary};
    }}

    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {colors.accent_teal} 0%, {colors.accent_purple} 100%);
        color: {colors.text_primary} !important;
    }}

    /* =========================================================================
       METRIC / KPI CARD STYLES
       ========================================================================= */
    [data-testid="stMetricValue"] {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem !important;
        font-weight: 600;
        color: {colors.text_primary};
    }}

    [data-testid="stMetricLabel"] {{
        color: {colors.text_secondary};
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.75rem;
    }}

    [data-testid="stMetricDelta"] {{
        font-family: 'JetBrains Mono', monospace;
    }}

    /* =========================================================================
       BUTTON STYLES
       ========================================================================= */
    .stButton > button {{
        background: linear-gradient(135deg, {colors.accent_teal} 0%, {colors.accent_purple} 100%);
        color: {colors.text_primary};
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.2s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(20, 184, 166, 0.3);
    }}

    /* Secondary button style */
    .stButton > button[kind="secondary"] {{
        background: transparent;
        border: 1px solid {colors.border};
        color: {colors.text_secondary};
    }}

    /* =========================================================================
       DATAFRAME / TABLE STYLES
       ========================================================================= */
    [data-testid="stDataFrame"] {{
        background-color: {colors.bg_secondary};
        border-radius: 12px;
        overflow: hidden;
    }}

    [data-testid="stDataFrame"] th {{
        background-color: {colors.bg_tertiary} !important;
        color: {colors.text_secondary} !important;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.5px;
    }}

    [data-testid="stDataFrame"] td {{
        color: {colors.text_primary} !important;
        background-color: {colors.bg_secondary} !important;
    }}

    /* =========================================================================
       EXPANDER / STATUS WIDGET STYLES
       ========================================================================= */
    [data-testid="stExpander"] {{
        background-color: {colors.bg_secondary};
        border: 1px solid {colors.border};
        border-radius: 12px;
    }}

    [data-testid="stExpander"] summary {{
        color: {colors.text_primary};
        font-weight: 500;
    }}

    /* =========================================================================
       CHAT CONTAINER STYLES
       ========================================================================= */
    .chat-container {{
        background: linear-gradient(180deg, {colors.bg_secondary} 0%, {colors.bg_primary} 100%);
        border-left: 1px solid {colors.border};
        border-radius: 16px 0 0 16px;
        height: calc(100vh - 100px);
        display: flex;
        flex-direction: column;
    }}

    .chat-header {{
        padding: 20px;
        border-bottom: 1px solid {colors.border};
        background: {colors.bg_tertiary};
        border-radius: 16px 0 0 0;
    }}

    .chat-messages {{
        flex: 1;
        overflow-y: auto;
        padding: 16px;
    }}

    .chat-input {{
        padding: 16px;
        border-top: 1px solid {colors.border};
    }}

    /* Message bubbles */
    .user-message {{
        background: linear-gradient(135deg, {colors.accent_teal} 0%, {colors.accent_purple} 100%);
        color: {colors.text_primary};
        padding: 12px 16px;
        border-radius: 16px 16px 4px 16px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
    }}

    .assistant-message {{
        background: {colors.bg_tertiary};
        color: {colors.text_primary};
        padding: 12px 16px;
        border-radius: 16px 16px 16px 4px;
        margin: 8px 0;
        max-width: 80%;
    }}

    /* =========================================================================
       ALERT / STATUS INDICATOR STYLES
       ========================================================================= */
    .alert-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }}

    .alert-badge.high {{
        background: rgba(239, 68, 68, 0.2);
        color: {colors.error};
        border: 1px solid {colors.error};
    }}

    .alert-badge.medium {{
        background: rgba(245, 158, 11, 0.2);
        color: {colors.warning};
        border: 1px solid {colors.warning};
    }}

    .alert-badge.low {{
        background: rgba(34, 197, 94, 0.2);
        color: {colors.success};
        border: 1px solid {colors.success};
    }}

    /* =========================================================================
       CUSTOM KPI CARD
       ========================================================================= */
    .kpi-card {{
        background: {colors.bg_secondary};
        border: 1px solid {colors.border};
        border-radius: 16px;
        padding: 24px;
        transition: all 0.2s ease;
    }}

    .kpi-card:hover {{
        border-color: {colors.accent_teal};
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(20, 184, 166, 0.1);
    }}

    .kpi-card .label {{
        color: {colors.text_secondary};
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }}

    .kpi-card .value {{
        color: {colors.text_primary};
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.5rem;
        font-weight: 700;
    }}

    .kpi-card .delta {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        margin-top: 8px;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.875rem;
        font-weight: 600;
    }}

    .kpi-card .delta.positive {{
        background: rgba(20, 184, 166, 0.15);
        color: {colors.uplift};
    }}

    .kpi-card .delta.negative {{
        background: rgba(248, 113, 113, 0.15);
        color: {colors.downgrade};
    }}

    /* =========================================================================
       SCROLLBAR STYLES
       ========================================================================= */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}

    ::-webkit-scrollbar-track {{
        background: {colors.bg_primary};
    }}

    ::-webkit-scrollbar-thumb {{
        background: {colors.bg_tertiary};
        border-radius: 4px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: {colors.border_light};
    }}

    /* =========================================================================
       ANIMATIONS
       ========================================================================= */
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
    }}

    .pulse {{
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }}

    @keyframes slideIn {{
        from {{
            opacity: 0;
            transform: translateY(10px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    .slide-in {{
        animation: slideIn 0.3s ease-out;
    }}

    /* =========================================================================
       UTILITY CLASSES
       ========================================================================= */
    .text-gradient {{
        background: linear-gradient(135deg, {colors.accent_teal} 0%, {colors.accent_purple} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    .border-gradient {{
        border: 2px solid transparent;
        background: linear-gradient({colors.bg_secondary}, {colors.bg_secondary}) padding-box,
                    linear-gradient(135deg, {colors.accent_teal}, {colors.accent_purple}) border-box;
    }}
    </style>
    """

