import logging
from agent.state.session_memory import memory
from agent.llms import sports_llm, weather_llm, travel_llm, complete_llm
from core.logging_config import setup_logging
from agent.tools.intent_classifier import classify_intent_llm as classify_intent

setup_logging()
logger = logging.getLogger(__name__)

# ───────────────────────────────────────────────
#  INTENT CLASSIFIER
# ───────────────────────────────────────────────
def classify_intent(query: str) -> str:
    """Basic rule-based intent detection. Can be upgraded to an LLM later."""
    q = query.lower()

    if any(word in q for word in ["match", "fixture", "who is playing", "next game"]):
        return "match_info"
    if any(word in q for word in ["weather", "temperature", "rain", "forecast"]):
        return "weather_info"
    if any(word in q for word in ["travel", "airport", "bus", "train", "how far", "distance", "route"]):
        return "travel_info"
    if any(word in q for word in ["summary", "combine", "overview", "recap"]):
        return "fusion_summary"

    # fallback to fusion for generic queries
    return "fusion_summary"

# ───────────────────────────────────────────────
#  CONVERSATIONAL ROUTER
# ───────────────────────────────────────────────
def process_user_query(session_id: str, user_input: str) -> dict:
    """
    Main entry point for handling user messages.
    Dynamically routes to sports, weather, travel, or fusion modules
    based on query intent and available session memory.
    """
    logger.info(f"[ROUTER] Processing user input: {user_input}")

    # Pull current context from memory
    last_answer = memory.get_context(session_id, "last_answer")
    last_city = memory.get_context(session_id, "city")
    last_venue = memory.get_context(session_id, "venue")
    last_team = memory.get_context(session_id, "team")

    # Determine query intent
    intent = classify_intent(user_input)
    logger.info(f"[ROUTER] Detected intent: {intent}")

    try:
        # ─── 1️⃣ Match info ───────────────────────────────
        if intent == "match_info":
            result = sports_llm.run_sports_llm(session_id, user_input)

            # after fetching match info, capture city & venue if available
            if isinstance(result, dict) and "city" in result:
                memory.set_context(session_id, "city", result.get("city"))
            if isinstance(result, dict) and "venue" in result:
                memory.set_context(session_id, "venue", result.get("venue"))
            return result

        # ─── 2️⃣ Weather info ─────────────────────────────
        elif intent == "weather_info":
            if not last_city:
                if last_answer:
                    user_input = f"{last_answer}\nThen user asked: {user_input}"
                return {"error": "No city found yet. Ask about a match first."}
            return weather_llm.run_weather_llm(session_id, last_city)

        # ─── 3️⃣ Travel info ──────────────────────────────
        elif intent == "travel_info":
            if not last_city or not last_venue:
                if last_answer:
                    user_input = f"{last_answer}\nThen user asked: {user_input}"
                return {"error": "No venue or city known yet. Ask about a match first."}
            return travel_llm.run_travel_llm(session_id, last_city, last_venue)

        # ─── 4️⃣ Combined summary ─────────────────────────
        elif intent == "fusion_summary":
            return fusion_llm.run_fusion_llm(session_id, user_input)

        # ─── 5️⃣ Fallback ─────────────────────────────────
        else:
            logger.warning(f"[ROUTER] Unknown intent for query: {user_input}")
            return fusion_llm.run_fusion_llm(session_id, user_input)

    except Exception as e:
        logger.exception(f"[ROUTER] Error handling query: {e}")
        return {"error": str(e)}
