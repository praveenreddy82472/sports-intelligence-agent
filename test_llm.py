import requests
import logging
from datetime import datetime

API_KEY = "6yma91GOhw57QQIjJeByiOvRg7cx2X8fNKefwiSmrRxKFt1CnW5CAJRBC9zY"
BASE_URL = "https://cricket.sportmonks.com/api/v2.0"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("TEAM-FIXTURES")

# ==============================================
# TEAM ALIAS MAPPING
# ==============================================
TEAM_ALIASES = {
    "india": ["india", "ind"],
    "australia": ["australia", "aus"],
    "england": ["england", "eng"],
    "pakistan": ["pakistan", "pak"],
    "south africa": ["south africa", "sa"],
    "new zealand": ["new zealand", "nz"],
    "bangladesh": ["bangladesh", "ban"],
    "west indies": ["west indies", "wi", "windies"],
    "afghanistan": ["afghanistan", "afg"],
    "ireland": ["ireland", "ire"],
    "sri lanka": ["sri lanka", "sl"]
}

def normalize_team_name(name: str):
    name = name.lower().strip()
    for official, aliases in TEAM_ALIASES.items():
        if name in aliases:
            return official
    return None


# ==============================================
# GET TEAM LIST (One-Time API Call)
# ==============================================
def get_all_teams():
    url = f"{BASE_URL}/teams?api_token={API_KEY}"
    res = requests.get(url)
    if res.status_code != 200:
        log.error(res.text)
        return []
    return res.json().get("data", [])


# ==============================================
# GET TEAM ID FROM NAME
# ==============================================
def get_team_id(team_name: str):
    team_name = normalize_team_name(team_name)
    teams = get_all_teams()

    for t in teams:
        if t["name"].lower() == team_name:
            return t["id"]
        if team_name in t["name"].lower():
            return t["id"]

    return None


# ==============================================
# BUILD MATCH OBJECT
# ==============================================
def build_match_info(f):
    return {
        "match": f"{f['localteam_id']} vs {f['visitorteam_id']}",
        "type": f.get("type"),
        "status": f.get("status"),
        "date": f.get("starting_at"),
        "venue_id": f.get("venue_id"),
        "league_id": f.get("league_id")
    }


# ==============================================
# GET UPCOMING MATCHES FOR A TEAM
# ==============================================
def get_upcoming_matches(team_name: str, limit=5):
    team_id = get_team_id(team_name)
    if not team_id:
        return {"error": "Team not found"}

    log.info(f"[API] Fetching fixtures for Team ID: {team_id}")

    url = f"{BASE_URL}/teams/{team_id}?api_token={API_KEY}&include=fixtures"
    res = requests.get(url)

    if res.status_code != 200:
        return {"error": res.text}

    data = res.json().get("data", {})
    fixtures = data.get("fixtures", [])

    upcoming = []

    for f in fixtures:
        # Only future matches
        if f["status"] != "NS":
            continue

        # Only international matches (Types: T20I, ODI, Test)
        if f.get("type") not in ["T20I", "ODI", "TEST"]:
            continue

        upcoming.append(build_match_info(f))

    # Sort by date
    upcoming.sort(key=lambda x: x["date"])

    return upcoming[:limit]


# ==============================================
# MAIN TEST
# ==============================================
if __name__ == "__main__":
    team = "Australia"

    print("\n========== NEXT MATCH ==========")
    print(get_upcoming_matches(team, limit=1))

    print("\n========== NEXT 5 MATCHES ==========")
    print(get_upcoming_matches(team, limit=5))
