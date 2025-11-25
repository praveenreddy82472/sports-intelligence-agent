import requests
import logging
import re
from datetime import datetime
from core.config import settings

# --------------------------------------------------------
# Logging
# --------------------------------------------------------
logger = logging.getLogger(__name__)

# --------------------------------------------------------
# RapidAPI Config
# --------------------------------------------------------
RAPIDAPI_HOST = "unofficial-cricbuzz.p.rapidapi.com"

print("Rapid API Key Loaded:", settings.rapid_api_key)

HEADERS = {
    "x-rapidapi-key": settings.rapid_api_key,
    "x-rapidapi-host": RAPIDAPI_HOST
}

CURRENT_MATCHES_URL = "https://unofficial-cricbuzz.p.rapidapi.com/matches/get-schedules"
SERIES_MATCHES_URL = "https://unofficial-cricbuzz.p.rapidapi.com/series/get-matches"


# --------------------------------------------------------
# TEAM NORMALIZATION
# --------------------------------------------------------
TEAM_MAP = {
    "aus": "australia", "australia": "australia",
    "ind": "india", "india": "india",
    "pak": "pakistan", "pakistan": "pakistan",
    "eng": "england", "england": "england",
    "sa": "south africa", "south africa": "south africa",
    "nz": "new zealand", "new zealand": "new zealand",
    "sl": "sri lanka", "sri lanka": "sri lanka",
    "wi": "west indies", "west indies": "west indies"
}

def normalize_team(text: str):
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # token match
    for w in text.split():
        if w in TEAM_MAP:
            return TEAM_MAP[w]

    # substring fallback
    for _, v in TEAM_MAP.items():
        if v in text:
            return v

    return None


# ============================================================
# 1️⃣ CURRENT MATCHES (LIVE / ONGOING)
# ============================================================
def get_current_match(team_input: str):
    logger.info(f"[CRICBUZZ] Checking CURRENT match for: {team_input}")

    team = normalize_team(team_input)
    if not team:
        return {"error": f"Team not recognized: {team_input}"}

    params = {"matchType": "international"}

    try:
        res = requests.get(CURRENT_MATCHES_URL, headers=HEADERS, params=params, timeout=10)
        data = res.json()

        LIVE_KEYS = ["live", "day", "session", "innings", "stumps"]

        for day in data.get("scheduleAdWrapper", []):
            block = day.get("matchScheduleMap", {})
            matches = block.get("matchScheduleList", [])

            for bucket in matches:
                for match in bucket.get("matchInfo", []):

                    t1 = match["team1"]["teamName"].lower()
                    t2 = match["team2"]["teamName"].lower()
                    if team not in t1 and team not in t2:
                        continue

                    desc = match.get("matchDesc", "").lower()
                    if any(k in desc for k in LIVE_KEYS):
                        ts = int(match["startDate"]) / 1000
                        venue = match.get("venueInfo", {})

                        return {
                            "team1": match["team1"]["teamName"],
                            "team2": match["team2"]["teamName"],
                            "status": match.get("matchDesc"),
                            "format": match.get("matchFormat"),
                            "date": datetime.fromtimestamp(ts).isoformat(),
                            "venue": venue.get("ground"),
                            "city": venue.get("city"),
                            "country": venue.get("country")
                        }

        return {"message": f"No current match right now for {team}."}

    except Exception as e:
        logger.exception(e)
        return {"error": str(e)}


# ============================================================
# 2️⃣ DETECT SERIES FOR TEAM (using CURRENT MATCHES API)
# ============================================================
def detect_series_for_team(team: str):
    """Find the series name + seriesId for a team from schedule API"""

    params = {"matchType": "international"}

    try:
        res = requests.get(CURRENT_MATCHES_URL, headers=HEADERS, params=params, timeout=10)
        data = res.json()

        for day in data.get("scheduleAdWrapper", []):
            block = day.get("matchScheduleMap", {})
            matches = block.get("matchScheduleList", [])

            for bucket in matches:
                series_name = bucket.get("seriesName")
                series_id = bucket.get("seriesId")

                for match in bucket.get("matchInfo", []):
                    t1 = match["team1"]["teamName"].lower()
                    t2 = match["team2"]["teamName"].lower()

                    if team in t1 or team in t2:
                        return series_name, series_id

        return None, None

    except Exception as e:
        logger.exception(e)
        return None, None


# ============================================================
# 3️⃣ SERIES SCHEDULE BASED ON TEAM NAME
# ============================================================
def get_series_schedule_by_team(team_input: str):
    team = normalize_team(team_input)
    if not team:
        return {"error": f"Team not recognized: {team_input}"}

    logger.info(f"[CRICBUZZ] Getting SERIES for team: {team}")

    # STEP 1: Find series linked to the team
    series_name, series_id = detect_series_for_team(team)

    if not series_id:
        return {"error": f"No active or upcoming series found for {team}"}

    # STEP 2: Fetch full series schedule
    try:
        params = {"seriesId": series_id}
        res = requests.get(SERIES_MATCHES_URL, headers=HEADERS, params=params, timeout=15)
        data = res.json()

        matches = []

        for block in data.get("adWrapper", []):
            matchDetails = block.get("matchDetails", {})
            for match in matchDetails.get("matches", []):
                match_info = match.get("matchInfo")
                if not match_info:
                    continue

                ts = int(match_info["startDate"]) / 1000
                dt = datetime.fromtimestamp(ts)

                venue = match_info.get("venueInfo", {})

                matches.append({
                    "team1": match_info["team1"]["teamName"],
                    "team2": match_info["team2"]["teamName"],
                    "match_desc": match_info.get("matchDesc"),
                    "format": match_info.get("matchFormat"),
                    "date": dt.isoformat(),
                    "venue": venue.get("ground"),
                    "city": venue.get("city"),
                    "country": venue.get("country"),
                    "status": match_info.get("status")
                })

        return {
            "team": team,
            "series": series_name,
            "seriesId": series_id,
            "matches": matches
        }

    except Exception as e:
        logger.exception(e)
        return {"error": str(e)}
    
    