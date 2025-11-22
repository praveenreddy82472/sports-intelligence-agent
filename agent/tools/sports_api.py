import requests
import logging
from core.config import settings
from core.logging_config import setup_logging

# Initialize logger
setup_logging()
logger = logging.getLogger(__name__)

BASE_URL = "https://cricket.sportmonks.com/api/v2.0"
API_KEY = settings.sports_api_key


# ============================================================
# TEAM NORMALIZATION (Fix typos, variations, abbreviations)
# ============================================================
TEAM_ALIASES = {
    "india": ["india", "ind"],
    "australia": ["australia", "aus", "austraila", "austalia"],
    "england": ["england", "eng"],
    "sri lanka": ["sri lanka", "srilanka", "sl", "sri-lanka"],
    "south africa": ["south africa", "sa", "southafrica"],
    "new zealand": ["new zealand", "nz"],
    "pakistan": ["pakistan", "pak"],
    "bangladesh": ["bangladesh", "ban"],
    "west indies": ["west indies", "wi", "windies"],
    "afghanistan": ["afghanistan", "afg"],
    "ireland": ["ireland", "ire"],
}

def normalize_team_name(text: str):
    text = text.lower().strip()

    # remove unwanted words
    for word in ["next", "match", "game", "team"]:
        text = text.replace(word, "").strip()

    for official, aliases in TEAM_ALIASES.items():
        for alias in aliases:
            if alias in text:
                return official

    return None


# ============================================================
# Extract match format (ODI / T20 / Test)
# ============================================================
def extract_format(match):
    league = match.get("league", {})
    stage = match.get("stage", {})

    format_type = (
        league.get("type")
        or stage.get("type")
        or league.get("season_type")
        or "Unknown"
    )

    return format_type


# ============================================================
# Convert raw fixture into clean standardized match object
# ============================================================
def build_match_info(match):
    venue = match.get("venue", {}) or {}
    country = (
        venue.get("country", {}).get("name")
        if isinstance(venue.get("country"), dict)
        else None
    )

    return {
        "home_team": match.get("localteam", {}).get("name"),
        "away_team": match.get("visitorteam", {}).get("name"),
        "date": match.get("starting_at"),
        "status": match.get("status"),
        "venue": venue.get("name"),
        "city": venue.get("city"),
        "country": country,
        "format": extract_format(match)
    }


# ============================================================
# 1️⃣ FETCH NEXT MATCH (LIVE + UPCOMING)
# ============================================================
def get_next_match(team_input: str) -> dict:
    logger.info(f"[SPORTS API] Fetching next match for: {team_input}")

    normalized = normalize_team_name(team_input)
    if not normalized:
        return {"error": f"Unrecognized team name: {team_input}"}

    try:
        # Fetch all fixtures (any status)
        params = {
            "api_token": API_KEY,
            "include": "venue.country,localteam,visitorteam,league,stage",
            "page[limit]": 150,
            "sort": "starting_at",
            "filter[status]": "NS"
        }

        url = f"{BASE_URL}/fixtures"
        response = requests.get(url, params=params, timeout=12)

        if response.status_code != 200:
            logger.error(f"API ERROR: {response.text[:200]}")
            return {"error": f"SportMonks API error {response.status_code}"}

        fixtures = response.json().get("data", [])
        if not fixtures:
            return {"error": "No fixture data returned."}

        matches = []

        # Find matches involving this team
        for match in fixtures:
            local = match.get("localteam", {}).get("name", "").lower()
            visitor = match.get("visitorteam", {}).get("name", "").lower()

            if normalized not in local and normalized not in visitor:
                continue

            matches.append(match)

        if not matches:
            return {"error": f"No matches found for {normalized}"}

        # Sort by upcoming date
        matches.sort(key=lambda m: m.get("starting_at") or "")

        return build_match_info(matches[0])

    except Exception as e:
        logger.exception(f"[SPORTS API] Exception: {e}")
        return {"error": str(e)}


# ============================================================
# 2️⃣ FETCH LIVE MATCH (LIVE / INPLAY / STUMPS)
# ============================================================
def get_live_match(team_input: str) -> dict:
    logger.info(f"[SPORTS API] Fetching live match for: {team_input}")

    normalized = normalize_team_name(team_input)
    if not normalized:
        return {"error": f"Unrecognized team name: {team_input}"}

    LIVE_STATUSES = ["LIVE", "INPLAY", "1st Innings", "2nd Innings", "STUMPS"]

    try:
        params = {
            "api_token": API_KEY,
            "include": "venue.country,localteam,visitorteam,league,stage",
            "page[limit]": 100,
        }

        res = requests.get(f"{BASE_URL}/fixtures", params=params, timeout=12)
        fixtures = res.json().get("data", [])

        for match in fixtures:
            status = match.get("status", "").upper()

            if status not in [s.upper() for s in LIVE_STATUSES]:
                continue

            local = match.get("localteam", {}).get("name", "").lower()
            visitor = match.get("visitorteam", {}).get("name", "").lower()

            if normalized in local or normalized in visitor:
                return build_match_info(match)

        return {"error": f"No live match found for {normalized}"}

    except Exception as e:
        logger.exception(f"[SPORTS API] Error: {e}")
        return {"error": str(e)}


# ============================================================
# 3️⃣ TEAM SCHEDULE (UPCOMING OR PAST)
# ============================================================
def get_team_schedule(team_input: str, limit: int = 3, direction: str = "future") -> list:
    logger.info(f"[SPORTS API] Fetching team schedule for: {team_input}")

    normalized = normalize_team_name(team_input)
    if not normalized:
        return []

    try:
        params = {
            "api_token": API_KEY,
            "include": "venue.country,localteam,visitorteam,league,stage",
            "page[limit]": 200,
            "sort": "starting_at" if direction == "future" else "-starting_at"
        }

        response = requests.get(f"{BASE_URL}/fixtures", params=params, timeout=12)
        fixtures = response.json().get("data", [])

        results = []

        for f in fixtures:
            local = f.get("localteam", {}).get("name", "").lower()
            visitor = f.get("visitorteam", {}).get("name", "").lower()

            if normalized not in local and normalized not in visitor:
                continue

            results.append(build_match_info(f))

        return results[:limit]

    except Exception as e:
        logger.exception(f"[SPORTS API] Error fetching schedule: {e}")
        return []
