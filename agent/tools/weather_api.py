import requests
import logging
from core.config import settings
from core.logging_config import setup_logging
from utils.formatters import clean_api_response
#from utils.cache_utils import ttl_cache

setup_logging()
logger = logging.getLogger(__name__)

#@ttl_cache
def get_weather(city: str) -> dict:
    """
    Fetch current weather data for a given city using OpenWeatherMap API.
    """
    try:
        logger.info(f"[WEATHER API] Fetch started for city: {city}")

        base_url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": settings.weather_api_key,
            "units": "metric"
        }

        response = requests.get(base_url, params=params, timeout=10)
        if response.status_code != 200:
            logger.error(f"[WEATHER API] API returned {response.status_code}: {response.text}")
            return {"error": f"OpenWeatherMap API error {response.status_code}"}

        data = response.json()

        # Extract relevant info
        weather_info = {
            "city": city,
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "condition": data["weather"][0]["description"].capitalize(),
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
        }

        logger.info(f"[WEATHER API] Weather data fetched for {city}: {weather_info}")

        return clean_api_response(
            weather_info,
            ["city", "temperature", "condition", "humidity", "wind_speed", "feels_like"]
        )

    except Exception as e:
        logger.error(f"[WEATHER API] Error fetching weather for {city}: {e}")
        return {"error": str(e)}
