import requests
import logging
import time
from urllib.parse import quote
from core.logging_config import setup_logging
from utils.formatters import short_text
#from utils.cache_utils import ttl_cache

setup_logging()
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "GlobalSportsAgent/1.0 (contact: team@example.com)",
    "Accept": "application/json",
}

def _fetch_wikipedia_summary(query: str) -> str:
    """Fetch a Wikipedia summary with retries and required headers."""
    if not query:
        return "No topic provided."

    encoded = quote(query.strip())
    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"

    for attempt in range(2):
        try:
            resp = requests.get(summary_url, headers=HEADERS, timeout=10)
            if resp.status_code == 200 and "application/json" in resp.headers.get("Content-Type", ""):
                data = resp.json()
                text = data.get("extract")
                if text:
                    return short_text(text, 600)
            elif resp.status_code in (403, 429):
                logger.warning(f"[CITY API] Wikipedia rate-limit or header block for {query}, retrying...")
                time.sleep(1.5)
                continue
            else:
                logger.warning(f"[CITY API] No summary found for {query} (status {resp.status_code})")
                break
        except Exception as e:
            logger.error(f"[CITY API] Wikipedia error for {query}: {e}")
            break

    # 🔄 Fallback: use search API
    try:
        search_url = (
            f"https://en.wikipedia.org/w/api.php?"
            f"action=query&list=search&srsearch={encoded}&utf8=&format=json"
        )
        resp = requests.get(search_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200 and "application/json" in resp.headers.get("Content-Type", ""):
            results = resp.json().get("query", {}).get("search", [])
            if results:
                title = results[0]["title"]
                logger.info(f"[CITY API] Fallback search found: {title}")
                return _fetch_wikipedia_summary(title)
    except Exception as e:
        logger.error(f"[CITY API] Wikipedia fallback error for {query}: {e}")

    return f"No detailed Wikipedia data available for {query}."




def _fetch_tourist_highlights(city: str) -> str:
    """
    Return a detailed tourist guide section by combining Wikipedia summaries
    for tourism and attractions pages.
    """
    import urllib.parse
    headers = {
        "User-Agent": "GlobalSportsAgent/1.0 (contact: team@example.com)",
        "Accept": "application/json",
    }
    queries = [
        f"Tourism_in_{urllib.parse.quote(city)}",
        f"List_of_tourist_attractions_in_{urllib.parse.quote(city)}",
        f"Landmarks_in_{urllib.parse.quote(city)}",
    ]

    snippets = []
    for q in queries:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{q}"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200 and "application/json" in resp.headers.get("Content-Type", ""):
            data = resp.json()
            text = data.get("extract", "")
            if text and "may refer to" not in text.lower():
                snippets.append(short_text(text, 400))

    if snippets:
        return " ".join(snippets)

    return (
        f"Visitors to {city} can enjoy its cultural attractions, museums, parks, "
        f"shopping districts, and local food experiences."
    )




def get_city_and_venue_info(city_name: str, venue_name: str | None = None) -> dict:
    logger.info(f"[CITY API] Fetch started for city={city_name}, venue={venue_name}")

    city_summary = _fetch_wikipedia_summary(city_name)
    venue_summary = _fetch_wikipedia_summary(venue_name) if venue_name else None
    tourist_info = _fetch_tourist_highlights(city_name)

    # ✨ Conversational assistant tone
    combined_summary = (
        f"🏙️ **{city_name} Travel & Match Guide**\n\n"
        f"{city_summary}\n\n"
        f"{tourist_info}\n\n"
        f"🏟️ **About {venue_name}:** {venue_summary or 'Venue details unavailable.'}\n\n"
        f"If you're heading to {city_name} for the game, explore nearby landmarks, "
        f"local cuisine, and attractions to make the most of your trip!"
    )

    logger.info(f"[CITY API] Completed info fetch for {city_name} and {venue_name}")
    return {
        "city": city_name,
        "venue": venue_name,
        "city_summary": city_summary,
        "venue_summary": venue_summary,
        "tourist_info": tourist_info,
        "combined_summary": combined_summary,
    }


#@ttl_cache
def get_city_info(city_name: str) -> dict:
    """
    Wrapper around get_city_and_venue_info() for simpler calls.
    Used for city-only queries (like user follow-ups or landmarks).
    """

    # Basic input validation
    if not city_name or not city_name.strip():
        logger.warning("[CITY API] get_city_info called with empty city name.")
        return {
            "city": None,
            "summary": "⚠️ No city provided.",
            "tourist_info": "",
            "combined_summary": "No valid city name provided."
        }

    try:
        # Reuse main Wikipedia fetch logic
        result = get_city_and_venue_info(city_name, venue_name=None)

        # Gracefully extract minimal structure
        return {
            "city": result.get("city", city_name),
            "summary": result.get("city_summary", "No details found."),
            "tourist_info": result.get("tourist_info", ""),
            "combined_summary": result.get("combined_summary", ""),
        }

    except Exception as e:
        logger.error(f"[CITY API] Error in get_city_info for {city_name}: {e}")
        return {
            "city": city_name,
            "summary": f"⚠️ Unable to fetch city details: {e}",
            "tourist_info": "",
            "combined_summary": ""
        }
