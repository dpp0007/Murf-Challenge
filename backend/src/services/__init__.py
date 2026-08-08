"""
Services module for Kisan Mitra - handles external API integrations.

Available services:
- WeatherService: Open-Meteo weather API
- MandiService: Indian agricultural market prices API
"""

from .weather_service import WeatherService
from .mandi_service import MandiService, get_mandi_service

__all__ = [
    "WeatherService",
    "MandiService",
    "get_mandi_service",
]
