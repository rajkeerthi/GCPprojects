"""
Application settings and configuration.

This module centralizes all configuration values for easy management
across development, staging, and production environments.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, timedelta
from functools import lru_cache
from typing import List

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Application configuration settings."""

    # -------------------------------------------------------------------------
    # API Endpoints (Cloud Run Services)
    # -------------------------------------------------------------------------
    demand_planner_api: str = field(
        default_factory=lambda: os.getenv(
            "DEMAND_PLANNER_API_URL", "http://localhost:8001"
        )
    )
    research_agent_api: str = field(
        default_factory=lambda: os.getenv(
            "RESEARCH_AGENT_API_URL", "http://localhost:8002"
        )
    )
    data_science_agent_api: str = field(
        default_factory=lambda: os.getenv(
            "DATA_SCIENCE_AGENT_API_URL", "http://localhost:8003"
        )
    )
    
    # -------------------------------------------------------------------------
    # Vertex AI Agent Engine Configuration
    # -------------------------------------------------------------------------
    agent_engine_id: str = field(
        default_factory=lambda: os.getenv(
            "AGENT_ENGINE_ID", "9197402671718334464"  # Updated with tracing enabled
        )
    )
    gcp_project_id: str = field(
        default_factory=lambda: os.getenv(
            "GCP_PROJECT_ID", "gen-lang-client-0010459436"
        )
    )
    gcp_region: str = field(
        default_factory=lambda: os.getenv(
            "GCP_REGION", "us-central1"
        )
    )
    
    @property
    def agent_engine_url(self) -> str:
        """Vertex AI Agent Engine streamQuery endpoint."""
        return (
            f"https://{self.gcp_region}-aiplatform.googleapis.com/v1/"
            f"projects/{self.gcp_project_id}/locations/{self.gcp_region}/"
            f"reasoningEngines/{self.agent_engine_id}:streamQuery"
        )

    # -------------------------------------------------------------------------
    # Application Metadata
    # -------------------------------------------------------------------------
    app_name: str = "Demand Sensing Hub"
    app_version: str = "0.1.0"
    company_name: str = "Enterprise CPG"

    # -------------------------------------------------------------------------
    # UI Configuration
    # -------------------------------------------------------------------------
    page_title: str = "Demand Sensing Hub"
    page_icon: str = "📊"
    layout: str = "wide"

    # Date constraints: Only next 10 days are selectable
    forecast_horizon_days: int = 10

    # Chat panel width constraints (percentage)
    chat_min_width: int = 20
    chat_max_width: int = 50
    chat_default_width: int = 30

    # -------------------------------------------------------------------------
    # Data Configuration (for prototype/mock)
    # NOTE: In production, these come from BigQuery/Cloud SQL
    # -------------------------------------------------------------------------
    products: List[str] = field(
        default_factory=lambda: [
            "PONDS_SUPER_LIGHT_GEL_100G",
        ]
    )
    customers: List[str] = field(default_factory=lambda: ["BLINKIT"])
    locations: List[str] = field(default_factory=lambda: ["BANGALORE"])

    # -------------------------------------------------------------------------
    # Driver categories for alert detection
    # -------------------------------------------------------------------------
    alert_thresholds: dict = field(
        default_factory=lambda: {
            "Real-Time Sales Velocity": {"high": 15.0, "low": 5.0},
            "Ingredient Trend Velocity": {"high": 0.25, "low": -0.05},
            "Brand Sentiment Score": {"high": 80, "low": 50},
            "Performance Marketing Spend": {"high": 200000, "low": 50000},
            "Competitor Out-of-Stock Status": {"signal": True},
            "Flash Sale Participation": {"signal": True},
        }
    )

    @property
    def min_date(self) -> date:
        """Minimum selectable date (today)."""
        return date.today()

    @property
    def max_date(self) -> date:
        """Maximum selectable date (today + forecast_horizon_days)."""
        return date.today() + timedelta(days=self.forecast_horizon_days)


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached singleton of the Settings object.
    
    Usage:
        from config import get_settings
        settings = get_settings()
    """
    return Settings()

