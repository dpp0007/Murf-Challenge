"""
Weather service for Open-Meteo API integration.
Provides real-time and forecast weather data for agricultural use.
"""

import logging
import aiohttp
from typing import Optional, Dict, Any

logger = logging.getLogger("weather_service")


class WeatherService:
    """
    Service to fetch weather data from Open-Meteo API.
    No authentication required.
    """
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    @staticmethod
    async def get_weather(
        latitude: float,
        longitude: float,
        language: str = "hi"
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch current weather and forecast for given coordinates.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            language: Response language (hi for Hindi, en for English)
        
        Returns:
            Dict with weather data or None if fetch fails
        """
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,weather_code,relative_humidity_2m,weather_code,wind_speed_10m,precipitation,rain",
                "hourly": "temperature_2m,precipitation_probability,weather_code",
                "forecast_days": 7,
                "temperature_unit": "celsius",
                "wind_speed_unit": "kmh",
                "timezone": "auto"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(WeatherService.BASE_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Weather data fetched for ({latitude}, {longitude})")
                        return WeatherService._parse_weather(data, language)
                    else:
                        logger.error(f"Weather API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Weather fetch error: {e}")
            return None
    
    @staticmethod
    def _parse_weather(data: Dict, language: str) -> Dict[str, Any]:
        """Parse Open-Meteo response into readable format."""
        try:
            current = data.get("current", {})
            timezone = data.get("timezone", "UTC")
            
            # Weather code interpretation (WMO)
            weather_description = WeatherService._get_weather_description(
                current.get("weather_code", 0),
                language
            )
            
            parsed = {
                "current": {
                    "temperature": current.get("temperature_2m", 0),
                    "weather": weather_description,
                    "humidity": current.get("relative_humidity_2m", 0),
                    "wind_speed": current.get("wind_speed_10m", 0),
                    "precipitation": current.get("precipitation", 0),
                    "rain": current.get("rain", 0),
                },
                "timezone": timezone,
                "hourly": data.get("hourly", {}),
                "daily": data.get("daily", {})
            }
            
            return parsed
        except Exception as e:
            logger.error(f"Weather parse error: {e}")
            return {}
    
    @staticmethod
    def _get_weather_description(code: int, language: str) -> str:
        """Convert WMO weather code to readable description."""
        # WMO Weather interpretation codes
        descriptions_hi = {
            0: "साफ आसमान",
            1: "मुख्यतः साफ",
            2: "आंशिक रूप से बादल",
            3: "अधिकतर बादल",
            45: "धुंध",
            48: "हल्की ठंडी धुंध",
            51: "हल्की बूंदाबारी",
            53: "मध्यम बूंदाबारी",
            55: "घनी बूंदाबारी",
            61: "हल्की बारिश",
            63: "मध्यम बारिश",
            65: "तेज़ बारिश",
            71: "हल्की बर्फानी बारिश",
            73: "मध्यम बर्फानी बारिश",
            75: "तेज़ बर्फानी बारिश",
            80: "हल्की झड़ीदार बारिश",
            81: "मध्यम झड़ीदार बारिश",
            82: "तेज़ झड़ीदार बारिश",
            85: "हल्की बर्फ की झड़ी",
            86: "तेज़ बर्फ की झड़ी",
            95: "तेज़ आंधी-तूफान",
            96: "हल्की ओलावृष्टि के साथ आंधी",
            99: "तेज़ ओलावृष्टि के साथ आंधी",
        }
        
        descriptions_en = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Rime frost fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Heavy drizzle",
            61: "Light rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Light snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Light rain showers",
            81: "Moderate rain showers",
            82: "Heavy rain showers",
            85: "Light snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with light hail",
            99: "Thunderstorm with heavy hail",
        }
        
        descriptions = descriptions_hi if language == "hi" else descriptions_en
        return descriptions.get(code, "Unknown weather" if language == "en" else "अज्ञात मौसम")
