import requests
import logging
from geopy.distance import geodesic
from core.config import settings
from core.logging_config import setup_logging
from utils.formatters import clean_api_response
#from utils.cache_utils import ttl_cache

setup_logging()
logger = logging.getLogger(__name__)
#@ttl_cache()
def get_travel_info(city: str, venue: str) -> dict:
    """
    Fetch nearby transport info (airport, bus, train, ferry) around a sports venue using Azure Maps.
    Calculates distance from the venue and returns up to 5 options per category.
    """
    try:
        logger.info(f"[TRAVEL API] Fetch started for {venue}, {city}")

        base_url = "https://atlas.microsoft.com"
        transport_spots = []

        # Step 1: Get coordinates for the venue
        venue_resp = requests.get(
            f"{base_url}/search/address/json",
            params={
                "api-version": "1.0",
                "subscription-key": settings.azure_maps_key,
                "query": f"{venue}, {city}"
            },
            timeout=10
        )

        if venue_resp.status_code != 200:
            logger.error(f"[TRAVEL API] Failed to get venue coordinates ({venue_resp.status_code})")
            return {"error": "Failed to retrieve venue coordinates"}

        venue_results = venue_resp.json().get("results", [])
        if not venue_results:
            logger.warning(f"[TRAVEL API] No coordinates found for {venue}")
            return {"error": "No venue found"}

        venue_pos = venue_results[0].get("position", {})
        venue_lat, venue_lon = venue_pos.get("lat"), venue_pos.get("lon")

        if not venue_lat or not venue_lon:
            logger.error(f"[TRAVEL API] Invalid coordinates for {venue}")
            return {"error": "Invalid venue coordinates"}

        # Step 2: Fetch nearby transport hubs (within 10 km)
        categories = ["airport", "bus station", "train station", "ferry terminal"]
        seen = set()

        for category in categories:
            params = {
                "api-version": "1.0",
                "subscription-key": settings.azure_maps_key,
                "query": category,
                "lat": venue_lat,
                "lon": venue_lon,
                "limit": 5,
                "radius": 10000,  # 10 km
            }

            resp = requests.get(f"{base_url}/search/poi/category/json", params=params, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"[TRAVEL API] {category} search failed ({resp.status_code})")
                continue

            for r in resp.json().get("results", []):
                name = r.get("poi", {}).get("name")
                if not name or name in seen:
                    continue
                seen.add(name)

                address = r.get("address", {}).get("freeformAddress", "")
                pos = r.get("position", {})
                lat, lon = pos.get("lat"), pos.get("lon")

                distance = None
                if lat and lon:
                    distance = round(geodesic((venue_lat, venue_lon), (lat, lon)).km, 1)

                transport_spots.append({
                    "type": category.title(),
                    "name": name,
                    "address": address,
                    "lat": lat,
                    "lon": lon,
                    "distance_km": distance
                })

        maps_link = f"https://www.bing.com/maps?q={venue}+{city}"

        logger.info(f"[TRAVEL API] Found {len(transport_spots)} transport options near {venue}")
        return clean_api_response({
            "city": city,
            "venue": venue,
            "transport_options": transport_spots or "No transport hubs found nearby.",
            "maps_link": maps_link
        }, ["city", "venue", "transport_options", "maps_link"])

    except Exception as e:
        logger.exception(f"[TRAVEL API] Error fetching travel info for {city}: {e}")
        return {"error": str(e)}
