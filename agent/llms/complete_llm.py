import logging
import asyncio
import time
from pathlib import Path
from typing import Dict, Any
from openai import AzureOpenAI

from core.config import settings
from core.logging_config import setup_logging
from agent.state.session_memory import memory

# Domain LLMs & APIs
from agent.llms.sports_llm import run_sports_llm
from agent.llms.weather_llm import run_weather_llm
from agent.llms.city_llm import run_city_llm
from agent.llms.travel_llm import run_travel_llm
from agent.tools.sports_api import get_next_match
#from utils.cache_utils import ttl_cache

setup_logging()
logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "fusion_prompt.txt"
FUSION_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")

client = AzureOpenAI(
    api_key=settings.openai_api_key,
    azure_endpoint=settings.azure_openai_endpoint,
    api_version="2024-12-01-preview",
)

# --------------------------------------------------------------------
# Helper: Detect team dynamically from query
# --------------------------------------------------------------------
def detect_team_from_query(query: str) -> str | None:
    if not query:
        return None
    query = query.lower()
    teams = [
        "india", "england", "australia", "pakistan", "south africa",
        "new zealand", "bangladesh", "sri lanka", "afghanistan", "ireland",
        "west indies", "zimbabwe", "netherlands", "nepal", "uae"
    ]
    for team in teams:
        if team in query:
            return team.title()
    return None


# --------------------------------------------------------------------
# Main orchestration function
# --------------------------------------------------------------------
async def run_fusion_llm_async(session_id: str, user_query: str) -> Dict[str, Any]:
    try:
        # --- Load any stored memory context ---
        context_data = memory.get_all(session_id)
        logger.info(f"[FUSION LLM] Loaded memory context: {list(context_data.keys())}")

        # --- Detect team from query or fallback to memory ---
        team = detect_team_from_query(user_query)
        if not team:
            team = context_data.get("team")
            if team:
                logger.info(f"[FUSION LLM] Using team from memory: {team}")
            else:
                logger.warning("[FUSION LLM] No team found in query or memory.")
                return {"error": "No team detected. Try asking about a specific team, e.g., 'next match for Bangladesh'."}

        # --- Fetch match info fresh from API ---
        match_info = get_next_match(team)
        if not match_info or "city" not in match_info:
            raise ValueError(f"No match info found for {team}")

        city = match_info.get("city")
        venue = match_info.get("venue")
        logger.info(f"[FUSION LLM] Upcoming match: {match_info.get('home_team')} vs {match_info.get('away_team')} at {venue}, {city}")

        # --- Decide mode ---
        use_memory = bool(context_data)
        mode = "CONTEXT" if use_memory else "FRESH"
        logger.info(f"[FUSION LLM] Running domain LLMs in {mode} mode...")

        # --- Run domain LLMs concurrently ---
        async def run_all():
            return await asyncio.gather(
                asyncio.to_thread(run_sports_llm, session_id, team),
                asyncio.to_thread(run_weather_llm, session_id, city),
                asyncio.to_thread(run_city_llm, session_id, city, venue),
                asyncio.to_thread(run_travel_llm, session_id, city, venue),
            )


        sports_summary, weather_summary, city_summary, travel_summary = await run_all()

        # --- Update memory only in context mode ---
        if use_memory:
            memory.set_context(session_id, "team", team)
            memory.set_context(session_id, "city", city)
            memory.set_context(session_id, "venue", venue)
            logger.info("[FUSION LLM] Updated memory context for continuity.")
        else:
            logger.info("[FUSION LLM] Skipped memory update (fresh query).")

        # --- Build combined context for summary ---
        context_data = memory.get_all(session_id)
        context_str = "\n\n".join(
            [f"### {k.upper()} CONTEXT\n{v}" for k, v in context_data.items() if v]
        )

        user_prompt = f"""
{FUSION_PROMPT}

Below is all the relevant context and user query.

CONTEXT:
{context_str}

USER QUESTION:
{user_query}

INSTRUCTION:
Follow the exact structure and formatting rules given in the system prompt.
Always produce well-formatted sections and tables.
Keep the answer clean, concise, and readable.\
and more make it correct and give the correct results
"""

        # --- Generate final summary ---
        res = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": FUSION_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=800,
        )

        final_summary = res.choices[0].message.content.strip()

        # --- Save last interaction ---
        memory.set_context(session_id, "last_answer", final_summary)
        memory.set_context(session_id, "last_question", user_query)

        logger.info(f"[FUSION LLM] Final summary generated for {team} ({mode} mode).")
        return {
            "answer": final_summary,
            "team": team,
            "match_info": match_info,
            "context_used": list(context_data.keys()),
        }

    except Exception as e:
        logger.exception(f"[FUSION LLM] Error: {e}")
        return {"error": str(e)}


# --------------------------------------------------------------------
# Sync wrapper for backward compatibility
# --------------------------------------------------------------------
# --------------------------------------------------------------------
# SYNC WRAPPER (SAFE)
# --------------------------------------------------------------------
import concurrent.futures
import asyncio


def run_fusion_llm(session_id: str, user_query: str):
    """
    Safe sync wrapper for LangGraph & FastAPI.
    Executes the async fusion function in a separate thread.
    """
    try:
        loop = asyncio.get_event_loop()

        # If already inside running event loop — LangGraph case
        if loop.is_running():
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    lambda: asyncio.run(run_fusion_llm_async(session_id, user_query))
                )
                return future.result()

        # No running loop — normal case
        return loop.run_until_complete(
            run_fusion_llm_async(session_id, user_query)
        )

    except RuntimeError:
        # No loop exists — create new loop
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        return new_loop.run_until_complete(
            run_fusion_llm_async(session_id, user_query)
        )




