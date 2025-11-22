# agent/llms/city_llm.py
import logging
from typing import Dict, Any, Optional
from openai import AzureOpenAI
from core.config import settings
from core.logging_config import setup_logging
from agent.tools.city_api import get_city_info, get_city_and_venue_info
from agent.state.session_memory import memory
from pathlib import Path


setup_logging()
logger = logging.getLogger(__name__)

client = AzureOpenAI(
    api_key=settings.openai_api_key,
    azure_endpoint=settings.azure_openai_endpoint,
    api_version="2024-12-01-preview",
)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "city_prompt.txt"
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")


def run_city_llm(session_id: str, city: str, venue: Optional[str] = None) -> Dict[str, Any]:
    try:
        city = (city or "").strip()
        if not city:
            return {"error": "Missing city for city guide."}

        # Save memory
        memory.set_context(session_id, "city", city)
        if venue:
            memory.set_context(session_id, "venue", venue)

        # Fetch data
        raw = (
            get_city_and_venue_info(city, venue)
            if venue
            else get_city_info(city)
        )

        if not raw:
            return {"error": f"No city data available for {city}."}

        city_text = raw.get("city_summary") or raw.get("summary") or str(raw)

        user_prompt = f"""
You are a professional travel guide.
Give a friendly, helpful summary for the city **{city}** {f"and the venue **{venue}**" if venue else ""}.

Include:
- cultural or historical highlights
- important places or attractions
- travel tips

DATA:
{city_text}
"""

        res = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,        # more variety & “human” style
            top_p=0.1,
            max_tokens=500,
            frequency_penalty=0.3,  # reduce repetition
            presence_penalty=0.2,
        )

        summary = res.choices[0].message.content.strip()
        return {"summary": summary, "city": city, "venue": venue, "raw": raw}

    except Exception as e:
        logger.exception(f"[CITY LLM] Failure city={city}: {e}")
        return {"error": str(e)}
