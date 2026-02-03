"""
Utility helper functions for formatting and display.
"""

from __future__ import annotations

from typing import Union


def format_percent(value: float, decimals: int = 1) -> str:
    """Format a decimal as a percentage string."""
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def format_currency(value: float, currency: str = "₹") -> str:
    """Format a number as currency with K/L/Cr suffixes."""
    if value >= 10000000:  # 1 Crore
        return f"{currency}{value/10000000:.1f}Cr"
    elif value >= 100000:  # 1 Lakh
        return f"{currency}{value/100000:.1f}L"
    elif value >= 1000:
        return f"{currency}{value/1000:.1f}K"
    else:
        return f"{currency}{value:.0f}"


def format_number(value: Union[int, float], decimals: int = 0) -> str:
    """Format a number with thousand separators."""
    if isinstance(value, float) and decimals > 0:
        return f"{value:,.{decimals}f}"
    return f"{int(value):,}"


def get_delta_color(value: float) -> str:
    """Returns CSS color class based on delta value."""
    if value > 0:
        return "positive"
    elif value < 0:
        return "negative"
    return "neutral"


def create_kpi_html(
    label: str,
    value: str,
    delta: float | None = None,
    delta_suffix: str = "%",
    icon: str = "",
) -> str:
    """
    Creates HTML for a custom KPI card.
    
    Args:
        label: KPI label (e.g., "Baseline Demand")
        value: Formatted value string (e.g., "92 units")
        delta: Optional delta value for change indicator
        delta_suffix: Suffix for delta (e.g., "%" or " units")
        icon: Optional emoji/icon for the card
    
    Returns:
        HTML string for the KPI card
    """
    delta_html = ""
    if delta is not None:
        delta_class = get_delta_color(delta)
        arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
        sign = "+" if delta > 0 else ""
        delta_html = f"""
        <div class="delta {delta_class}">
            {arrow} {sign}{delta:.1f}{delta_suffix}
        </div>
        """

    return f"""
    <div class="kpi-card slide-in">
        <div class="label">{icon} {label}</div>
        <div class="value">{value}</div>
        {delta_html}
    </div>
    """


def create_alert_badge_html(severity: str, message: str) -> str:
    """
    Creates HTML for an alert badge.
    
    Args:
        severity: "high", "medium", or "low"
        message: Alert message text
    
    Returns:
        HTML string for the alert badge
    """
    icons = {
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢",
    }
    icon = icons.get(severity, "⚪")

    return f"""
    <div class="alert-badge {severity}">
        {icon} {message}
    </div>
    """


def calculate_forecast_accuracy(predicted: float, actual: float) -> float:
    """Calculate forecast accuracy as a percentage."""
    if actual == 0:
        return 0.0
    error = abs(predicted - actual) / actual
    return max(0.0, (1 - error) * 100)


def format_driver_name(driver_name: str) -> str:
    """Format a driver name for display (shorter form)."""
    abbreviations = {
        "Statistical Baseline Forecast": "Baseline Forecast",
        "Ingredient Trend Velocity": "Trend Velocity",
        "Brand Sentiment Score": "Sentiment",
        "Viral Hashtag Volume": "Hashtag Volume",
        "Influencer Mention Count": "Influencer Mentions",
        "Performance Marketing Spend": "Marketing Spend",
        "Campaign Click-Through-Rate (CTR)": "CTR",
        "Video Completion Rate": "Video Completion",
        "Retargeting Pool Size": "Retargeting Pool",
        "On-Platform Discount Depth": "Discount Depth",
        "Bundle Offer Active Status": "Bundle Active",
        "Flash Sale Participation": "Flash Sale",
        "Cart-Level Offer Conversion": "Cart Conversion",
        "Share of Search (Keyword Rank)": "Search Rank",
        "Product Detail Page (PDP) Views": "PDP Views",
        "Buy Box Win Rate": "Buy Box Rate",
        "Rating & Review Velocity": "Review Velocity",
        "Max Temperature Forecast": "Max Temp",
        "Humidity Index": "Humidity",
        "Air Quality Index (AQI)": "AQI",
        "Competitor Price Gap": "Comp. Price Gap",
        "Competitor Out-of-Stock Status": "Comp. OOS",
        "Competitor Promo Intensity": "Comp. Promo",
        "Competitor New Launch Signal": "Comp. Launch",
        "Real-Time Sales Velocity": "Sales Velocity",
        "Inventory Days on Hand (DOH)": "Days on Hand",
        "Distributor Open Orders": "Open Orders",
    }
    return abbreviations.get(driver_name, driver_name)


def driver_value_formatter(driver_name: str, value) -> str:
    """Format a driver value based on its type."""
    if isinstance(value, bool):
        return "Yes" if value else "No"

    if "Spend" in driver_name:
        return format_currency(value)

    if "Rate" in driver_name or "Depth" in driver_name or "Conversion" in driver_name:
        return f"{value * 100:.1f}%"

    if "Velocity" in driver_name and "Sales" not in driver_name:
        return f"{value * 100:+.0f}%"

    if "Temperature" in driver_name:
        return f"{value:.1f}°C"

    if "Humidity" in driver_name:
        return f"{value * 100:.0f}%"

    if isinstance(value, float):
        if value < 1:
            return f"{value:.2f}"
        return f"{value:.1f}"

    return str(value)

