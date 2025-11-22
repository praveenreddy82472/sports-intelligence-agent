def build_sports_summary_prompt(match_info, city_info, weather_info, travel_info):
    """
    Build the natural-language summarization prompt for Azure OpenAI.
    """
    return f"""
You are an expert AI travel and sports assistant. Using the information below, write a detailed yet natural summary.
Make sure to include:
- Match overview (teams, venue, date)
- City background and highlights
- Stadium overview
- Weather forecast and comfort tips
- Travel accessibility (mention how far the venue is from airports, bus/train/ferry stations)
- Recommended transport (e.g., shuttle, taxi, public transit)
- Close with friendly tourist suggestions.

🏏 MATCH INFO: {match_info}
🏙️ CITY INFO: {city_info.get('city_summary')}
🏟️ VENUE INFO: {city_info.get('venue_summary')}
🌦️ WEATHER INFO: {weather_info}
🧭 TRAVEL INFO: {travel_info.get('transport_options')}
"""


"""
utils/prompts.py
Prompt builders for GPT-powered summaries.
"""

def build_city_context_prompt(city: str, city_info: dict, weather_info: dict, travel_info: dict) -> str:
    """
    Builds a structured Azure OpenAI prompt for city summaries.
    """

    city_summary = city_info.get("summary", "No details available.")
    attractions = city_info.get("places_to_visit", [])
    attractions_str = ", ".join(attractions[:10]) if attractions else "Not available."

    temp = weather_info.get("temperature", "N/A")
    desc = weather_info.get("description", "N/A")
    humidity = weather_info.get("humidity", "N/A")
    wind = weather_info.get("wind_speed", "N/A")

    distance = travel_info.get("distance_km", "N/A")
    duration = travel_info.get("travel_time_min", "N/A")

    prompt = f"""
### 🌆 City Insights: {city}

You are **SPORTSY**, a global sports and travel intelligence assistant.  
Provide an engaging, concise markdown summary for **{city}** with weather, travel, and local highlights.

---

#### 🏙️ City Overview
{city_summary}

#### 🌍 Top Attractions
{attractions_str}

#### 🌦️ Current Weather
- **Temperature:** {temp}°C  
- **Condition:** {desc}  
- **Humidity:** {humidity}%  
- **Wind Speed:** {wind} km/h  

#### ✈️ Travel Information
- **Distance from Origin:** {distance} km  
- **Estimated Travel Time:** {duration} minutes  

#### 💡 Visitor Tips
- Mention clothing suggestions based on weather.
- Include a fun or unique fact about the city.
- End with an encouraging line for travelers or fans.

---

Make the tone friendly, knowledgeable, and visually appealing using emojis like 🏏✈️🌞🎨.
"""
    return prompt.strip()
