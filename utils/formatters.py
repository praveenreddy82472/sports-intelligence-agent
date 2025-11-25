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


def format_travel_info(travel_data: dict) -> str:
    """
    Hybrid HTML formatter for travel info.
    Matches the polished style used in format_series_hybrid.
    """

    # ---------- ERROR BLOCK ----------
    if "error" in travel_data:
        return f"""
<div style="border-left:4px solid #e74c3c;padding:14px;background:#fff3f3;
            border-radius:6px;margin-bottom:12px;">
    <strong style="color:#c0392b;">❌ Error:</strong> {travel_data['error']}
</div>
"""

    city = travel_data.get("city")
    venue = travel_data.get("venue")
    transport = travel_data.get("transport_options", [])
    maps_link = travel_data.get("maps_link")

    title = venue if venue else city
    is_venue = venue is not None

    # ----------------------------------------------------------------
    # HEADER
    # ----------------------------------------------------------------
    html = f"""
<h2 style="margin-bottom:6px;">🚗 Travel & Access Guide</h2>
<p style="color:#555;margin-top:0;">
    Location: <strong>{title}</strong><br>
    City: <strong>{city}</strong>
</p>

<hr style="margin:14px 0;">
"""

    # ----------------------------------------------------------------
    # OVERVIEW CARD
    # ----------------------------------------------------------------
    if is_venue:
        html += f"""
<div style="border:1px solid #e1e1e1;border-radius:8px;padding:16px;background:#fafafa;margin-bottom:18px;">
    <h3 style="margin-top:0;">🏟 Stadium Access Overview</h3>
    <p style="margin-bottom:0;">
        The venue <strong>{venue}</strong> in <strong>{city}</strong> is positioned near multiple transport hubs such as 
        airports, metro and bus stations, and train lines. Below are the closest options to help you plan your arrival.
    </p>
</div>
"""
    else:
        html += f"""
<div style="border:1px solid #e1e1e1;border-radius:8px;padding:16px;background:#fafafa;margin-bottom:18px;">
    <h3 style="margin-top:0;">🏙 City Transport Overview</h3>
    <p style="margin-bottom:0;">
        <strong>{city}</strong> offers multiple modes of transportation including airports, major railway stations,
        intercity buses, and local metro options. Below is a curated list of the nearest transport hubs.
    </p>
</div>
"""

    # ----------------------------------------------------------------
    # TABLE HEADER
    # ----------------------------------------------------------------
    html += """
<h3 style="margin-bottom:8px;">🚌 Nearby Transport Options</h3>

<table style="width:100%;border-collapse:collapse;font-size:14px;margin-top:6px;">
    <thead>
        <tr style="background:#f5f5f5;">
            <th style="padding:10px;border:1px solid #ddd;">Type</th>
            <th style="padding:10px;border:1px solid #ddd;">Name</th>
            <th style="padding:10px;border:1px solid #ddd;text-align:center;">Distance (km)</th>
            <th style="padding:10px;border:1px solid #ddd;">Address</th>
        </tr>
    </thead>
    <tbody>
"""

    # ----------------------------------------------------------------
    # TABLE ROWS
    # ----------------------------------------------------------------
    if isinstance(transport, list) and transport:
        for spot in transport:
            html += f"""
        <tr>
            <td style="padding:8px;border:1px solid #ddd;">{spot.get('type','-')}</td>
            <td style="padding:8px;border:1px solid #ddd;">{spot.get('name','-')}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:center;">{spot.get('distance_km','-')}</td>
            <td style="padding:8px;border:1px solid #ddd;">{spot.get('address','-')}</td>
        </tr>
"""
    else:
        html += """
        <tr>
            <td colspan="4" style="padding:12px;border:1px solid #ddd;text-align:center;color:#777;">
                No transport hubs found nearby.
            </td>
        </tr>
"""

    html += """
    </tbody>
</table>
"""

    # ----------------------------------------------------------------
    # MAP BUTTON
    # ----------------------------------------------------------------
    html += f"""
<div style="margin-top:16px;">
    <a href="{maps_link}" target="_blank"
       style="background:#0078ff;color:white;padding:10px 16px;border-radius:6px;
              text-decoration:none;font-size:14px;">
        🗺 Open in Maps
    </a>
</div>
"""

    return html
