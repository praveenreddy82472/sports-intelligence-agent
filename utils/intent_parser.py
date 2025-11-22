import re
from difflib import SequenceMatcher

# -------------------------------------------------------------------
# 🔹 GENERIC INTENT DEFINITIONS
# -------------------------------------------------------------------
INTENTS = {
    "smalltalk": [
        "hi", "hello", "hey", "how are you", "good morning", "good evening", "what's up"
    ],
    "get_schedule": [
        "next match", "upcoming match", "fixtures", "schedule", "who will play", "show matches"
    ],
    "get_weather": [
        "weather", "temperature", "forecast", "rain", "climate", "is it hot", "is it cold"
    ],
    "get_travel": [
        "how to reach", "travel", "directions", "route", "distance", "transport"
    ],
    "get_tourist": [
        "tourist", "visit", "places to see", "attractions", "things to do", "city guide", "what to see"
    ],
    "get_format": [
        "format", "odi", "t20", "test", "match type", "what format"
    ],
    "get_city": [
        "city", "venue", "where is", "about the city", "which place", "tell me about"
    ]
}

TEAM_NAMES = [
    "india", "australia", "england", "south africa", "new zealand",
    "pakistan", "west indies", "bangladesh", "sri lanka", "afghanistan"
]


# -------------------------------------------------------------------
# 🔹 HELPER FUNCTIONS
# -------------------------------------------------------------------
def text_similarity(a, b):
    """Rough semantic similarity check."""
    return SequenceMatcher(None, a, b).ratio()


def match_intent(text: str) -> str:
    """Finds best matching intent using fuzzy logic instead of keywords."""
    best_intent, best_score = "fallback", 0.0
    for intent, patterns in INTENTS.items():
        for p in patterns:
            score = text_similarity(p, text)
            if score > best_score:
                best_intent, best_score = intent, score
    return best_intent


# -------------------------------------------------------------------
# 🔹 MAIN PARSER FUNCTION
# -------------------------------------------------------------------
def parse_user_intent(message: str) -> dict:
    """
    Generic NLP-based intent parser.
    Uses fuzzy matching to map message → intent → params.
    """
    text = message.lower().strip()

    # Detect team names
    team = next((t.title() for t in TEAM_NAMES if t in text), None)

    # Extract numeric limit
    limit_match = re.search(r"\b(\d+)\b", text)
    limit = int(limit_match.group(1)) if limit_match else 3

    # Past or future?
    direction = "future"
    if any(x in text for x in ["past", "previous", "last"]):
        direction = "past"

    # Get fuzzy-matched intent
    intent = match_intent(text)

    return {
        "intent": intent,
        "team": team,
        "limit": limit,
        "direction": direction
    }
