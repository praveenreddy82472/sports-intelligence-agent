import textwrap
import datetime

def format_user_query(query: str) -> str:
    """
    Clean and normalize the user's input before sending to the agent or LLM.
    Example: trims spaces, capitalizes, ensures punctuation.
    """
    query = query.strip()
    if not query.endswith("?"):
        query += "?"
    return query[0].upper() + query[1:]


def format_sports_summary(match: dict, weather: dict | None = None, city_info: str | None = None) -> str:
    """
    Combine results from the Sports, Weather, and City APIs into one natural summary string.
    """
    home = match.get("home_team", "Unknown")
    away = match.get("away_team", "Unknown")
    venue = match.get("venue", "Unknown venue")
    city = match.get("city", "Unknown city")
    date = match.get("date", "Unknown date")

    weather_text = ""
    if weather:
        weather_text = f"{weather.get('temp')}°C, {weather.get('desc')}."

    city_brief = textwrap.shorten(city_info or "No city details available.", width=300, placeholder="...")

    summary = f"""
    🏏 **Next Match**
    {home} vs {away}
    📅 Date: {date}
    📍 Venue: {venue}, {city}

    🌦️ **Weather**
    {weather_text}

    🏙️ **City Overview**
    {city_brief}

    ⏱️ Data generated at {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
    """
    return textwrap.dedent(summary).strip()


def clean_api_response(data: dict, keys: list[str]) -> dict:
    """
    Trim large API responses and keep only the required keys.
    """
    return {k: data.get(k) for k in keys if k in data}


def short_text(text: str, limit: int = 200) -> str:
    """
    Truncate long text gracefully for display or LLM input.
    """
    return text if len(text) <= limit else text[:limit].rstrip() + "..."
