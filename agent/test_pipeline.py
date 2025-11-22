import logging
from core.logging_config import setup_logging
from agent.tools.sports_api import get_next_match
from agent.tools.city_api import get_city_and_venue_info
from agent.tools.weather_api import get_weather
from agent.tools.travel_api import get_travel_info

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

def main():
    team_name = "India"
    print(f"🔍 Fetching match details for {team_name}...")

    # 1️⃣ Get match info
    match = get_next_match(team_name)
    if "error" in match:
        print("❌ Failed to fetch match details:", match)
        return
    print(f"\n📍 Match Location: {match['venue']}, {match['city']}")

    # 2️⃣ Get city + venue info
    city_info = get_city_and_venue_info(match["city"], match["venue"])

    # 3️⃣ Get weather info
    weather = get_weather(match["city"])
    
     # 4 Get weather info
    travel_info = get_travel_info(match["city"], match["venue"])

    # 5 Final Combined Output
    print("\n✅ Final Combined Result:\n")

    print("🏏 MATCH_INFO:")
    print(match)

    print("\n🏙️ CITY_INFO:")
    print(city_info.get("city_summary", "No city data found."))

    print("\n🏟️ VENUE_INFO:")
    print(city_info.get("venue_summary", "No venue data found."))

    print("\n🌦️ WEATHER_INFO:")
    if "error" in weather:
        print("Weather data not available.")
    else:
        print(weather)
    
    print("\n Transportation")
    print(travel_info)

    print("\n🧭 TOURIST_HIGHLIGHTS:")
    print(city_info.get("tourist_info", "No tourist data found."))

if __name__ == "__main__":
    main()
