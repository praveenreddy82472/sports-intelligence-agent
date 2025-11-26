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


def format_series_hybrid(series: dict) -> str:
    if not series or "matches" not in series:
        return "<p>No upcoming series found.</p>"

    title = series.get("series", "Upcoming Series")
    matches = series["matches"]

    html = f"<h2>🏏 {title}</h2>"
    html += f"<p><b>Total Matches:</b> {len(matches)}</p><hr>"

    # Group matches by format (TEST, ODI, T20)
    formats = {}
    for m in matches:
        fmt = m.get("format", "Unknown").upper()
        formats.setdefault(fmt, []).append(m)

    for fmt, group in formats.items():
        html += f"<h3>🎯 {fmt} Series</h3>"

        html += """
        <table border="1" cellspacing="0" cellpadding="6" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color:#f2f2f2; font-weight:bold;">
            <th>Match</th>
            <th>Team 1</th>
            <th>Team 2</th>
            <th>Date</th>
            <th>Venue</th>
            <th>City</th>
            <th>Status</th>
        </tr>
        """

        for g in group:
            html += f"""
            <tr>
                <td>{g.get('match_desc', '-')}</td>
                <td>{g.get('team1', '-')}</td>
                <td>{g.get('team2', '-')}</td>
                <td>{g.get('date', '-')}</td>
                <td>{g.get('venue', '-')}</td>
                <td>{g.get('city', '-')}</td>
                <td>{g.get('status', '-')}</td>
            </tr>
            """

        html += "</table><br>"

    # Add a short summary at the end
    html += f"""
    <hr>
    <p><b>🧠 Quick Summary:</b><br>
    Formats included: {list(formats.keys())}<br>
    First match: {matches[0].get('date', '-') if matches else '-'}<br>
    Last match: {matches[-1].get('date', '-') if matches else '-'}
    </p>
    """

    return html


def format_travel_hybrid(travel: dict) -> str:
    # ---------------- ERROR BLOCK ----------------
    if "error" in travel:
        return f"""
        <p style="color:#c0392b;"><b>❌ Error:</b> {travel['error']}</p>
        """

    city = travel.get("city", "-")
    venue = travel.get("venue")
    title = venue if venue else city
    is_venue = venue is not None
    transport = travel.get("transport_options", [])
    maps_link = travel.get("maps_link", "#")

    # ---------------- HEADER ----------------
    html = f"<h2>🚗 Travel & Access Guide</h2>"
    html += f"<p><b>Location:</b> {title}<br><b>City:</b> {city}</p><hr>"

    # ---------------- OVERVIEW SECTION ----------------
    if is_venue:
        html += f"""
        <h3>🏟 Stadium Overview</h3>
        <p>
            <b>{venue}</b> in <b>{city}</b> has access to nearby airports, railway stations, 
            metro lines and road transport. Below is a curated list of the closest transport hubs.
        </p>
        <br>
        """
    else:
        html += f"""
        <h3>🏙 City Transport Overview</h3>
        <p>
            <b>{city}</b> has multiple connectivity options including airports, metros,
            major railway junctions and intercity buses. Here are the closest transport hubs.
        </p>
        <br>
        """

    # ---------------- TABLE HEADER ----------------
    html += """
    <h3>🚌 Nearby Transport Options</h3>
    <table border="1" cellspacing="0" cellpadding="6" 
           style="border-collapse: collapse; width: 100%; font-size:14px;">
        <tr style="background-color:#f2f2f2; font-weight:bold;">
            <th>Type</th>
            <th>Name</th>
            <th>Distance (km)</th>
            <th>Address</th>
        </tr>
    """

    # ---------------- TABLE ROWS ----------------
    if isinstance(transport, list) and transport:
        for spot in transport:
            html += f"""
            <tr>
                <td>{spot.get('type', '-')}</td>
                <td>{spot.get('name', '-')}</td>
                <td style="text-align:center;">{spot.get('distance_km', '-')}</td>
                <td>{spot.get('address', '-')}</td>
            </tr>
            """
    else:
        html += """
        <tr>
            <td colspan="4" style="text-align:center; color:#777;">
                No transport hubs found nearby.
            </td>
        </tr>
        """

    html += "</table><br>"

    # ---------------- MAP BUTTON ----------------
    html += f"""
    <a href="{maps_link}" target="_blank"
       style="background:#0078ff;color:white;padding:10px 16px;
              border-radius:6px;text-decoration:none;font-size:14px;">
        🗺 Open in Maps
    </a>
    <br><br>
    """

    # ---------------- SUMMARY ----------------
    html += f"""
    <hr>
    <p><b>🧠 Quick Summary:</b><br>
       Total transport hubs: {len(transport)}<br>
       Location type: {"Venue" if is_venue else "City"}<br>
       Maps link provided: {"Yes" if maps_link else "No"}
    </p>
    """

    return html

