"""Services module for data fetching and API communication."""

# Only import what's needed - api_client is for future production use
from services.mock_data import MockDataService, get_mock_service

__all__ = ["MockDataService", "get_mock_service"]

