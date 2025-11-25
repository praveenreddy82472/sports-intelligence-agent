import logging
import re
from openai import AzureOpenAI
from core.config import settings
from core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=settings.openai_api_key,
    azure_endpoint=settings.azure_openai_endpoint,
    api_version="2024-12-01-preview"
)

SYSTEM_PROMPT = """
You are a friendly sports conversation assistant that classifies user intent.
Your job is to understand what the user *means*, even if they speak casually.

Available intents:
1. match_info — questions about matches, teams, players, dates, or venues.
2. city_info — questions about the city, local attractions, or nearby places.
3. weather_info — questions about temperature, rain, or match-day weather.
4. travel_info — questions about transport, distance, or how to reach a venue.
5. fusion_summary — when user asks for a full report, summary, or combined view.
6. chitchat — greetings, jokes, or casual talk unrelated to sports.

Output Rules:
- Respond with **only one** of these exact intents.
- Never explain or add text — just output the intent keyword.
- Handle natural phrases like "hey", "what's up", or "tell me about tomorrow's match".
"""

def classify_intent_llm(query: str) -> str:
    """Classify user query into one of the defined intents, with natural fallback handling."""
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query.strip()}
            ],
            temperature=0.2,
            max_tokens=15
        )

        intent = response.choices[0].message.content.strip().lower()
        intent = re.sub(r'[^a-z_]', '', intent)  # clean up stray chars

        # ---------------------------------------------
        # 🔥 ADD CUSTOM SPORTS SUB-INTENTS HERE
        # ---------------------------------------------
        q = query.lower()

        # LIVE or current match
        if any(w in q for w in ["live", "current", "right now", "playing now", "today match"]):
            return "current_match"

        # NEXT SERIES (not next match)
        if any(w in q for w in ["next", "upcoming", "future", "fixtures", "schedule"]):
            return "next_series"

        # ---------------------------------------------
        # ADD NEW VALID INTENTS BELOW
        # ---------------------------------------------
        VALID_INTENTS = {
            "match_info",
            "city_info",
            "weather_info",
            "travel_info",
            "fusion_summary",
            "chitchat",
            "live_match",
            "next_match",
            "schedule_match",
        }

        # If LLM returned a valid intent directly
        if intent in VALID_INTENTS:
            return intent

        # -----------------------------------------
        # 🧠 Fallback keyword detection
        # -----------------------------------------
        # LIVE or current match
        if any(w in q for w in ["live", "current", "right now", "playing now", "today match"]):
            return "current_match"

        # NEXT SERIES (not next match)
        if any(w in q for w in ["next", "upcoming", "future", "fixtures", "schedule"]):
            return "next_series"

        if any(word in q for word in ["match", "team", "play", "score"]):
            return "match_info"

        if any(word in q for word in ["weather", "rain", "temp", "forecast"]):
            return "weather_info"

        if any(word in q for word in ["travel", "bus", "airport", "train", "distance"]):
            return "travel_info"

        if any(word in q for word in ["city", "place", "things to do", "restaurant"]):
            return "city_info"

        if any(w in q for w in ["match summary", "summary of", "summarize match", "full summary"]):
            return "match_summary"


        if any(word in q for word in ["hi", "hello", "hey", "how are you", "yo"]):
            return "chitchat"

        logger.warning(f"[INTENT] Unknown query, defaulting to fusion_summary")
        return "fusion_summary"

    except Exception as e:
        logger.error(f"[INTENT] LLM classification failed: {e}")
        return "fusion_summary"
