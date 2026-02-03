"""
Mock data service for the prototype.

This service provides realistic mock data for testing the UI without
needing the actual backend services running. In production, this will
be replaced by API calls to the Cloud Run services.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DemandDriverData:
    """Container for demand driver data at a specific context."""

    sku_id: str
    customer_id: str
    location_id: str
    as_of_date: str
    drivers: Dict[str, Any]
    notes: Dict[str, str] = field(default_factory=dict)
    scenario: str = "BASE"


@dataclass
class ForecastResult:
    """Result of a demand forecast prediction."""

    sku_id: str
    customer_id: str
    location_id: str
    as_of_date: str
    baseline_forecast: float
    sensed_demand: float
    boost_percent: float
    confidence_score: float
    reasoning: str
    driver_contributions: Dict[str, float]
    approval_status: str = "pending"  # pending, approved, rejected
    planner_override: Optional[float] = None


@dataclass
class AlertSignal:
    """Alert signal detected from driver data."""

    driver_name: str
    current_value: Any
    threshold_type: str  # "high", "low", "signal"
    severity: str  # "high", "medium", "low"
    message: str


class MockDataService:
    """
    Provides mock data for the demand sensing prototype.
    
    This mimics what would come from BigQuery (demand_drivers_dataset)
    and the Demand Planner Agent's predictions.
    """

    # -------------------------------------------------------------------------
    # Mock demand driver values (matching your DBmock structure)
    # -------------------------------------------------------------------------
    DRIVER_TEMPLATES: Dict[str, Dict[str, Any]] = {
        "base": {
            "Statistical Baseline Forecast": 90,
            "Ingredient Trend Velocity": 0.15,
            "Brand Sentiment Score": 72,
            "Viral Hashtag Volume": 1400,
            "Influencer Mention Count": 24,
            "Performance Marketing Spend": 200000,
            "Campaign Click-Through-Rate (CTR)": 0.020,
            "Video Completion Rate": 0.33,
            "Retargeting Pool Size": 17000,
            "On-Platform Discount Depth": 0.10,
            "Bundle Offer Active Status": False,
            "Flash Sale Participation": False,
            "Cart-Level Offer Conversion": 0.06,
            "Share of Search (Keyword Rank)": 5,
            "Product Detail Page (PDP) Views": 48000,
            "Buy Box Win Rate": 0.95,
            "Rating & Review Velocity": 35,
            "Max Temperature Forecast": 27.0,
            "Humidity Index": 0.60,
            "UV Index": 5.5,
            "Air Quality Index (AQI)": 140,
            "Competitor Price Gap": -10,
            "Competitor Out-of-Stock Status": False,
            "Competitor Promo Intensity": 0.10,
            "Competitor New Launch Signal": False,
            "Real-Time Sales Velocity": 11.0,
            "Inventory Days on Hand (DOH)": 7.0,
            "Distributor Open Orders": 300,
            "Stock-Out Incidents": 0,
        },
        "bullish": {
            "Ingredient Trend Velocity": 0.30,
            "Brand Sentiment Score": 82,
            "Viral Hashtag Volume": 2500,
            "Influencer Mention Count": 40,
            "Performance Marketing Spend": 280000,
            "Campaign Click-Through-Rate (CTR)": 0.028,
            "On-Platform Discount Depth": 0.20,
            "Flash Sale Participation": True,
            "Share of Search (Keyword Rank)": 2,
            "Product Detail Page (PDP) Views": 75000,
            "Buy Box Win Rate": 0.98,
            "Competitor Out-of-Stock Status": True,
            "Real-Time Sales Velocity": 18.0,
        },
        "bearish": {
            "Ingredient Trend Velocity": -0.10,
            "Brand Sentiment Score": 48,
            "Viral Hashtag Volume": 200,
            "Influencer Mention Count": 2,
            "Performance Marketing Spend": 20000,
            "Campaign Click-Through-Rate (CTR)": 0.008,
            "On-Platform Discount Depth": 0.00,
            "Share of Search (Keyword Rank)": 20,
            "Product Detail Page (PDP) Views": 10000,
            "Buy Box Win Rate": 0.70,
            "Competitor Promo Intensity": 0.35,
            "Competitor New Launch Signal": True,
            "Real-Time Sales Velocity": 4.0,
        },
    }

    # Products and their base characteristics
    # NOTE: In production, this comes from BigQuery/Cloud SQL
    PRODUCTS = {
        "PONDS_SUPER_LIGHT_GEL_100G": {
            "display_name": "Pond's Super Light Gel 100g",
            "category": "Face Care",
            "base_demand": 92,
            "weather_sensitivity": 0.8,
            "social_sensitivity": 0.7,
        },
    }

    CUSTOMERS = {
        "BLINKIT": {"display_name": "Blinkit", "channel": "Quick Commerce"},
    }

    LOCATIONS = {
        "BANGALORE": {"display_name": "Bangalore", "region": "South"},
    }

    def __init__(self):
        self._forecast_cache: Dict[Tuple[str, str, str, str], ForecastResult] = {}

    def get_products(self) -> List[str]:
        """Returns list of available product IDs."""
        return list(self.PRODUCTS.keys())

    def get_customers(self) -> List[str]:
        """Returns list of available customer IDs."""
        return list(self.CUSTOMERS.keys())

    def get_locations(self) -> List[str]:
        """Returns list of available location IDs."""
        return list(self.LOCATIONS.keys())

    def get_product_display_name(self, product_id: str) -> str:
        """Returns human-readable product name."""
        return self.PRODUCTS.get(product_id, {}).get("display_name", product_id)

    def get_demand_drivers(
        self,
        sku_id: str,
        customer_id: str,
        location_id: str,
        as_of_date: date,
    ) -> DemandDriverData:
        """
        Fetches demand driver data for a specific context.
        
        In production, this would query BigQuery's demand_drivers_dataset.
        """
        date_str = as_of_date.strftime("%Y-%m-%d")

        # Determine scenario based on date patterns
        day_of_week = as_of_date.weekday()
        day_of_month = as_of_date.day

        if day_of_month % 3 == 0 or day_of_week in [5, 6]:  # Weekends or every 3rd day
            scenario = "bullish"
        elif day_of_month % 5 == 0:
            scenario = "bearish"
        else:
            scenario = "base"

        # Build driver values
        drivers = dict(self.DRIVER_TEMPLATES["base"])
        if scenario != "base":
            drivers.update(self.DRIVER_TEMPLATES[scenario])

        # Add some randomness for realism
        product_info = self.PRODUCTS.get(sku_id, {})
        drivers["Statistical Baseline Forecast"] = product_info.get("base_demand", 85)

        # Vary based on customer
        if customer_id == "ZEPTO":
            drivers["Statistical Baseline Forecast"] *= 0.95
            drivers["Product Detail Page (PDP) Views"] *= 0.85

        return DemandDriverData(
            sku_id=sku_id,
            customer_id=customer_id,
            location_id=location_id,
            as_of_date=date_str,
            drivers=drivers,
            scenario=scenario.upper(),
        )

    def get_forecast(
        self,
        sku_id: str,
        customer_id: str,
        location_id: str,
        as_of_date: date,
    ) -> ForecastResult:
        """
        Gets the demand forecast for a specific context.
        
        In production, this would call the Demand Planner Agent API.
        """
        cache_key = (sku_id, customer_id, location_id, as_of_date.strftime("%Y-%m-%d"))

        if cache_key in self._forecast_cache:
            return self._forecast_cache[cache_key]

        # Get driver data
        driver_data = self.get_demand_drivers(sku_id, customer_id, location_id, as_of_date)
        drivers = driver_data.drivers
        scenario = driver_data.scenario

        # Calculate boost contributions (mimicking heuristic functions)
        contributions = {
            "Social & Trend": self._calc_social_boost(drivers),
            "Marketing Spend": self._calc_marketing_boost(drivers),
            "Trade Promo": self._calc_promo_boost(drivers),
            "Digital Shelf": self._calc_shelf_boost(drivers),
            "Weather": self._calc_weather_boost(drivers, sku_id),
            "Competitor": self._calc_competitor_boost(drivers),
        }

        total_boost = sum(contributions.values())
        baseline = drivers.get("Statistical Baseline Forecast", 85)
        sensed_demand = round(baseline * (1 + total_boost))

        # Generate reasoning
        reasoning = self._generate_reasoning(contributions, scenario, sku_id)

        # Calculate confidence
        confidence = 0.85 if scenario == "BASE" else (0.75 if scenario == "BULLISH" else 0.70)

        result = ForecastResult(
            sku_id=sku_id,
            customer_id=customer_id,
            location_id=location_id,
            as_of_date=as_of_date.strftime("%Y-%m-%d"),
            baseline_forecast=baseline,
            sensed_demand=sensed_demand,
            boost_percent=round(total_boost * 100, 1),
            confidence_score=confidence,
            reasoning=reasoning,
            driver_contributions=contributions,
        )

        self._forecast_cache[cache_key] = result
        return result

    def detect_alerts(
        self,
        sku_id: str,
        customer_id: str,
        location_id: str,
        as_of_date: date,
    ) -> List[AlertSignal]:
        """
        Detects alert signals from driver data.
        
        Returns list of alerts for unusual/outlier values.
        """
        driver_data = self.get_demand_drivers(sku_id, customer_id, location_id, as_of_date)
        drivers = driver_data.drivers
        alerts = []

        # Check for high sales velocity
        velocity = drivers.get("Real-Time Sales Velocity", 0)
        if velocity > 15.0:
            alerts.append(AlertSignal(
                driver_name="Real-Time Sales Velocity",
                current_value=velocity,
                threshold_type="high",
                severity="high",
                message=f"🔥 Sales velocity spike: {velocity:.1f} units/hr (avg: 10)"
            ))

        # Check for social trend spike
        trend = drivers.get("Ingredient Trend Velocity", 0)
        if trend > 0.25:
            alerts.append(AlertSignal(
                driver_name="Ingredient Trend Velocity",
                current_value=trend,
                threshold_type="high",
                severity="medium",
                message=f"📈 Viral trend detected: +{trend*100:.0f}% search velocity"
            ))
        elif trend < -0.05:
            alerts.append(AlertSignal(
                driver_name="Ingredient Trend Velocity",
                current_value=trend,
                threshold_type="low",
                severity="medium",
                message=f"📉 Declining trend: {trend*100:.0f}% search velocity"
            ))

        # Check for competitor OOS
        if drivers.get("Competitor Out-of-Stock Status", False):
            alerts.append(AlertSignal(
                driver_name="Competitor Out-of-Stock Status",
                current_value=True,
                threshold_type="signal",
                severity="high",
                message="🎯 Competitor stock-out detected! Potential demand capture opportunity"
            ))

        # Check for flash sale
        if drivers.get("Flash Sale Participation", False):
            alerts.append(AlertSignal(
                driver_name="Flash Sale Participation",
                current_value=True,
                threshold_type="signal",
                severity="medium",
                message="⚡ Flash sale active - expect demand spike"
            ))

        # Check for low sentiment
        sentiment = drivers.get("Brand Sentiment Score", 70)
        if sentiment < 50:
            alerts.append(AlertSignal(
                driver_name="Brand Sentiment Score",
                current_value=sentiment,
                threshold_type="low",
                severity="high",
                message=f"⚠️ Low brand sentiment: {sentiment}/100 - investigate negative feedback"
            ))

        return alerts

    def update_forecast_approval(
        self,
        sku_id: str,
        customer_id: str,
        location_id: str,
        as_of_date: str,
        status: str,
        override_value: Optional[float] = None,
    ) -> ForecastResult:
        """Updates the approval status and optional override for a forecast."""
        cache_key = (sku_id, customer_id, location_id, as_of_date)

        if cache_key in self._forecast_cache:
            result = self._forecast_cache[cache_key]
            result.approval_status = status
            if override_value is not None:
                result.planner_override = override_value
            return result

        raise ValueError(f"Forecast not found for {cache_key}")

    # -------------------------------------------------------------------------
    # Private helper methods for boost calculations
    # -------------------------------------------------------------------------

    def _calc_social_boost(self, drivers: Dict[str, Any]) -> float:
        """Calculate social/trend boost."""
        trend = drivers.get("Ingredient Trend Velocity", 0)
        sentiment = drivers.get("Brand Sentiment Score", 70) / 100
        hashtags = min(drivers.get("Viral Hashtag Volume", 0) / 3000, 1.0)

        return round(0.4 * trend + 0.3 * (sentiment - 0.7) + 0.3 * hashtags * 0.3, 3)

    def _calc_marketing_boost(self, drivers: Dict[str, Any]) -> float:
        """Calculate marketing spend boost."""
        spend = drivers.get("Performance Marketing Spend", 0)
        ctr = drivers.get("Campaign Click-Through-Rate (CTR)", 0)

        spend_factor = min(spend / 300000, 1.0) * 0.15
        ctr_factor = ctr * 2

        return round(spend_factor + ctr_factor, 3)

    def _calc_promo_boost(self, drivers: Dict[str, Any]) -> float:
        """Calculate promotional boost."""
        discount = drivers.get("On-Platform Discount Depth", 0)
        bundle = 0.05 if drivers.get("Bundle Offer Active Status", False) else 0
        flash = 0.10 if drivers.get("Flash Sale Participation", False) else 0

        return round(discount * 0.8 + bundle + flash, 3)

    def _calc_shelf_boost(self, drivers: Dict[str, Any]) -> float:
        """Calculate digital shelf boost."""
        rank = drivers.get("Share of Search (Keyword Rank)", 10)
        rank_factor = max(0, (10 - rank) / 10) * 0.10

        buy_box = drivers.get("Buy Box Win Rate", 0.9)
        bb_factor = (buy_box - 0.9) * 0.5

        return round(rank_factor + bb_factor, 3)

    def _calc_weather_boost(self, drivers: Dict[str, Any], sku_id: str) -> float:
        """Calculate weather-related boost."""
        temp = drivers.get("Max Temperature Forecast", 25)
        uv = drivers.get("UV Index", 5)

        product_info = self.PRODUCTS.get(sku_id, {})
        sensitivity = product_info.get("weather_sensitivity", 0.5)

        # Higher temp/UV boosts face care products
        if "POND" in sku_id:
            temp_factor = max(0, (temp - 25) / 10) * 0.15 * sensitivity
            uv_factor = max(0, (uv - 5) / 5) * 0.10 * sensitivity
            return round(temp_factor + uv_factor, 3)

        return 0.0

    def _calc_competitor_boost(self, drivers: Dict[str, Any]) -> float:
        """Calculate competitor-related boost."""
        price_gap = drivers.get("Competitor Price Gap", 0)
        oos = 0.15 if drivers.get("Competitor Out-of-Stock Status", False) else 0
        promo = -drivers.get("Competitor Promo Intensity", 0) * 0.5

        price_factor = -price_gap / 100 * 0.10

        return round(price_factor + oos + promo, 3)

    def _generate_reasoning(
        self, contributions: Dict[str, float], scenario: str, sku_id: str
    ) -> str:
        """Generate human-readable reasoning for the forecast."""
        sorted_drivers = sorted(
            contributions.items(), key=lambda x: abs(x[1]), reverse=True
        )

        top_positive = [(k, v) for k, v in sorted_drivers if v > 0.02][:3]
        top_negative = [(k, v) for k, v in sorted_drivers if v < -0.02][:2]

        product_name = self.PRODUCTS.get(sku_id, {}).get("display_name", sku_id)

        lines = [f"**Demand Sensing Analysis for {product_name}**\n"]

        if scenario == "BULLISH":
            lines.append("📈 **Scenario: Bullish** - Multiple positive signals detected.\n")
        elif scenario == "BEARISH":
            lines.append("📉 **Scenario: Bearish** - Headwinds present across drivers.\n")
        else:
            lines.append("➡️ **Scenario: Baseline** - Normal operating conditions.\n")

        if top_positive:
            lines.append("**Key Uplift Drivers:**")
            for driver, value in top_positive:
                lines.append(f"- {driver}: +{value*100:.1f}%")

        if top_negative:
            lines.append("\n**Key Headwinds:**")
            for driver, value in top_negative:
                lines.append(f"- {driver}: {value*100:.1f}%")

        return "\n".join(lines)


@lru_cache()
def get_mock_service() -> MockDataService:
    """Returns a cached singleton of the MockDataService."""
    return MockDataService()

