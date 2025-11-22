import logging
import json
from pathlib import Path
from openai import AzureOpenAI
from core.config import settings
from core.logging_config import setup_logging
from agent.tools.travel_api import get_travel_info
from agent.state.session_memory import memory

# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------
setup_logging()
logger = logging.getLogger(__name__)

client = AzureOpenAI(
    api_key=settings.openai_api_key,
    azure_endpoint=settings.azure_openai_endpoint,
    api_version="2024-05-01-preview",
)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "travel_prompt.txt"
TRAVEL_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")

# ---------------------------------------------------------------------
# Main Function
# ---------------------------------------------------------------------
def run_travel_llm(session_id: str, city: str = None, venue: str = None):
    """
    Fetches travel and transportation info for a given city or venue.
    Works in two modes:
      1. Direct mode: user asks “show travel routes for Delhi”
      2. Context mode: uses stored city/venue from match memory
    """

    try:
        # 1️⃣ Determine context
        if not city:
            city = memory.get_context(session_id, "city")
        if not venue:
            venue = memory.get_context(session_id, "venue")

        # 2️⃣ Gracefully handle missing info
        if not city and not venue:
            logger.info("[TRAVEL LLM] Missing both city and venue.")
            return {
                "summary": "Could you tell me which city or stadium you want travel information for?",
                "error": "missing_location",
            }

        logger.info(f"[TRAVEL LLM] Processing travel info for {venue or 'N/A'}, {city or 'N/A'}")

        # 3️⃣ Fetch travel info from API
        travel_data = get_travel_info(city, venue)
        if not travel_data or "error" in travel_data:
            logger.warning(f"[TRAVEL LLM] No transport data found for {venue}, {city}")
            travel_data = {
                "city": city,
                "venue": venue,
                "transport_options": "No nearby transport hubs or detailed map data available.",
                "maps_link": f"https://www.bing.com/maps?q={venue or city}",
            }

        # 4️⃣ Build prompt dynamically
        prompt = TRAVEL_PROMPT.format(
            city=city or "Unknown City",
            venue=venue or "Unknown Venue",
            travel_data=json.dumps(travel_data, indent=2),
        )

        # 5️⃣ Generate response via Azure OpenAI
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful travel assistant. Summarize transport data clearly "
                        "in markdown format with concise tables when possible."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,        # keep it deterministic for tables
            top_p=0.1,
            max_tokens=350,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        summary = response.choices[0].message.content.strip()

        # 6️⃣ Store results for continuity
        memory.set_context(session_id, "city", city)
        memory.set_context(session_id, "venue", venue)
        memory.set_context(session_id, "travel_summary", summary)

        logger.info(f"[TRAVEL LLM] Summary generated successfully for {venue or city}")
        return {"summary": summary, "city": city, "venue": venue, "raw": travel_data}

    except Exception as e:
        logger.exception(f"[TRAVEL LLM] Error: {e}")
        return {
            "error": str(e),
            "summary": "Something went wrong while fetching travel information.",
        }
