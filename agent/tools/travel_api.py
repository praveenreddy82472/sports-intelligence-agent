import requests
import logging
from geopy.distance import geodesic
from core.config import settings
from utils.formatters import clean_api_response

logger = logging.getLogger("TRAVEL_API")


def _geocode(query: str):
    """Geocode any text globally using Azure Maps."""
    url = "https://atlas.microsoft.com/search/address/json"
    params = {
        "api-version": "1.0",
        "subscription-key": settings.azure_maps_key,
        "query": query
    }

    resp = requests.get(url, params=params, timeout=10)

    if resp.status_code != 200:
        return None

    results = resp.json().get("results", [])
    if not results:
        return None

    pos = results[0].get("position")
    if not pos:
        return None

    lat, lon = pos.get("lat"), pos.get("lon")
    return lat, lon, results[0]


def _reverse_geocode(lat, lon):
    """Reverse lookup country & city for validation."""
    url = "https://atlas.microsoft.com/search/address/reverse/json"
    params = {
        "api-version": "1.0",
        "subscription-key": settings.azure_maps_key,
        "query": f"{lat},{lon}"
    }

    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code != 200:
        return None

    results = resp.json().get("addresses", [])
    if not results:
        return None

    addr = results[0].get("address", {})
    return {
        "country": addr.get("country"),
        "state": addr.get("countrySubdivision"),
        "city": addr.get("municipality"),
    }


def _is_far(lat, lon, city_lat=None, city_lon=None):
    """Check if venue coords are too far from city coords (over 200 km)."""
    if not city_lat or not city_lon:
        return False
    try:
        dist = geodesic((lat, lon), (city_lat, city_lon)).km
        return dist > 200
    except:
        return False


def get_travel_info(city: str, venue: str = None) -> dict:
    """GLOBAL SAFE travel lookup with fallback chain."""
    try:
        # ---------------------------------------------------------
        # 1. Try different search queries: venue, venue+city, city
        # ---------------------------------------------------------
        logger.info(f"[TRAVEL] Searching coordinates for: {venue or city}")

        queries = []
        if venue:
            queries.append(venue)
            queries.append(f"{venue}, {city}")

        queries.append(city)

        venue_lat = venue_lon = None
        city_lat = city_lon = None

        for q in queries:
            geo = _geocode(q)
            if not geo:
                continue

            lat, lon, meta = geo

            # Assign city coords when matching city-only lookup
            if q.lower() == city.lower():
                city_lat, city_lon = lat, lon

            # Reverse-geocode validation
            rev = _reverse_geocode(lat, lon)
            if rev:
                detected_city = (rev.get("city") or "").lower()
                if city.lower() not in detected_city and venue:
                    # Venue but city mismatch → consider suspicious
                    logger.warning(f"[TRAVEL] '{q}' resolves far from expected city → skipping")
                    continue

            # If too far from city center (>200 km), reject unless it is city lookup
            if venue and _is_far(lat, lon, city_lat, city_lon):
                logger.warning(f"[TRAVEL] '{q}' is too far from city → skipping")
                continue

            venue_lat, venue_lon = lat, lon
            logger.info(f"[TRAVEL] VALID coordinates for '{q}' → {lat}, {lon}")
            break

        if not venue_lat:
            return {"error": f"Could not find valid coordinates for '{venue or city}'"}

        # ---------------------------------------------------------
        # 2. Search transport hubs near the validated coordinates
        # ---------------------------------------------------------
        categories = ["airport", "bus station", "train station", "ferry terminal"]
        results = []
        seen = set()

        base_url = "https://atlas.microsoft.com/search/poi/category/json"

        for cat in categories:
            logger.info(f"[TRAVEL] Fetching nearby {cat}")

            params = {
                "api-version": "1.0",
                "subscription-key": settings.azure_maps_key,
                "query": cat,
                "lat": venue_lat,
                "lon": venue_lon,
                "radius": 15000,
                "limit": 5,
            }

            resp = requests.get(base_url, params=params, timeout=10)
            if resp.status_code != 200:
                continue

            for item in resp.json().get("results", []):
                name = item.get("poi", {}).get("name")
                if not name or name in seen:
                    continue
                seen.add(name)

                address = item.get("address", {}).get("freeformAddress")
                lat2 = item.get("position", {}).get("lat")
                lon2 = item.get("position", {}).get("lon")

                # Compute accurate distance
                dist = round(geodesic((venue_lat, venue_lon), (lat2, lon2)).km, 1) if (lat2 and lon2) else None

                results.append({
                    "type": cat.title(),
                    "name": name,
                    "address": address,
                    "distance_km": dist,
                })

        return clean_api_response({
            "city": city,
            "venue": venue,
            "transport_options": results or "No nearby transport hubs found.",
            "maps_link": f"https://www.bing.com/maps?q={(venue or city).replace(' ', '+')}"
        }, ["city", "venue", "transport_options", "maps_link"])

    except Exception as e:
        logger.exception(f"[TRAVEL] ERROR: {e}")
        return {"error": str(e)}