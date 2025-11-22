import logging
import json
from pathlib import Path
from openai import AzureOpenAI
from core.config import settings
from core.logging_config import setup_logging
from agent.tools.weather_api import get_weather
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

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "weather_prompt.txt"
WEATHER_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------
# Main Function
# ---------------------------------------------------------------------
def run_weather_llm(session_id: str, city: str = None):
    """
    Fetches live weather data and summarizes it using Azure OpenAI.
    Works in two modes:
      1. Direct query (e.g., 'weather in Hyderabad')
      2. Contextual query (uses city from memory if not given)
    """

    try:
        # 1️⃣ Determine target city
        if not city:
            city = memory.get_context(session_id, "city")

        if not city:
            logger.info("[WEATHER LLM] No city provided in query or memory.")
            return {
                "summary": "Could you tell me which city you want the weather for?",
                "error": "missing_city",
            }

        # 2️⃣ Fetch live weather data
        logger.info(f"[WEATHER LLM] Fetching weather for: {city}")
        if city:
            correction_prompt = f"The user entered the city '{city}'. If it's misspelled, suggest the correct spelling of the city name. Otherwise, repeat it unchanged. Respond with only the city name."
            correction = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": correction_prompt}],
                max_tokens=10,
                temperature=0
            )
            city = correction.choices[0].message.content.strip()
        weather_data = get_weather(city)

        if not weather_data or "error" in weather_data:
            logger.warning(f"[WEATHER LLM] Weather data unavailable for {city}")
            return {
                "summary": f"Sorry, I couldn’t find the current weather for {city}.",
                "error": "no_weather_data",
            }

        # 3️⃣ Prepare structured prompt
        prompt = WEATHER_PROMPT.format(
            city=city.title(), weather_data=json.dumps(weather_data, indent=2)
        )

        # 4️⃣ Generate conversational summary with Azure OpenAI
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a friendly, concise meteorologist summarizing real-time "
                        "weather data in a conversational tone."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            top_p=0.1,
            max_tokens=220,
            frequency_penalty=0.1,
            presence_penalty=0.0,
        )

        summary = response.choices[0].message.content.strip()

        # 5️⃣ Persist data in memory for continuity
        memory.set_context(session_id, "city", city)
        memory.set_context(session_id, "weather_raw", weather_data)
        memory.set_context(session_id, "weather_summary", summary)

        logger.info(f"[WEATHER LLM] Summary successfully generated for {city}")
        return {"summary": summary, "city": city, "raw": weather_data}

    except Exception as e:
        logger.exception(f"[WEATHER LLM] Error: {e}")
        return {"error": str(e), "summary": "Something went wrong while fetching the weather."}
