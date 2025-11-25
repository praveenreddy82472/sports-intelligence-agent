import logging
import json
from openai import AzureOpenAI
from pathlib import Path
from core.config import settings
from core.logging_config import setup_logging

# Updated sports API (your new module)
from agent.tools.sports_api import (
    get_current_match,
    get_series_schedule_by_team,
    normalize_team
)

from agent.state.session_memory import memory

setup_logging()
logger = logging.getLogger(__name__)

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=settings.openai_api_key,
    azure_endpoint=settings.azure_openai_endpoint,
    api_version="2024-05-01-preview",
)

# Load master prompt
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "sports_prompt.txt"
SPORTS_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")


# -------------------------------------------------------
# 1️⃣ Clean team extraction
# -------------------------------------------------------
def extract_team_name(query: str) -> str:
    """Returns official normalized team name or None."""
    team = normalize_team(query)
    return team


# -------------------------------------------------------
# 2️⃣ MAIN ORCHESTRATOR (Next Match + LLM Summary)
# -------------------------------------------------------
def run_sports_llm(session_id: str, user_team_query: str):
    """
    1. Extract team name (handles typos/aliases)
    2. Call sports API (next match)
    3. Format structured JSON
    4. Ask LLM to generate a summary
    5. Store context for future queries
    """
    try:
        clean_team = extract_team_name(user_team_query)

        if not clean_team:
            return {"error": "Team not recognized. Try India, Australia, England, Pakistan, etc."}

        logger.info(f"[SPORTS LLM] Processing sports query for: {clean_team}")

        # -------------------------
        # STEP 1: Fetch next match
        # -------------------------
        match_data = get_current_match(clean_team)

        if match_data.get("error"):
            logger.warning(f"[SPORTS LLM] No match data found -> {match_data['error']}")
            return {"error": match_data["error"]}

        # -------------------------
        # STEP 2: JSON encode match data
        # -------------------------
        match_json_str = json.dumps(match_data, indent=2)

        # -------------------------
        # STEP 3: Build final prompt
        # -------------------------
        prompt = SPORTS_PROMPT.format(
            team=clean_team,
            match_data=match_json_str
        )

        # -------------------------
        # STEP 4: LLM SUMMARY
        # -------------------------
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the Global Sports Intelligence Agent.\n"
                        "You MUST NOT fabricate dates, teams, venues, formats, or match info.\n"
                        "Use ONLY the JSON provided. If any field is missing, state 'Not available'."
                    )
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,       # strict factual mode
            top_p=0.3,
            max_tokens=300,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        summary = response.choices[0].message.content.strip()

        # -------------------------
        # STEP 5: Update memory
        # -------------------------
        memory.set_context(session_id, "team", clean_team)
        memory.set_context(session_id, "city", match_data.get("city", ""))
        memory.set_context(session_id, "venue", match_data.get("venue", ""))
        memory.set_context(session_id, "sports_summary", summary)

        logger.info(f"[SPORTS LLM] Final summary ready for {clean_team}")

        return {
            "summary": summary,
            "raw": match_data
        }

    except Exception as e:
        logger.error(f"[SPORTS LLM] Exception: {e}")
        return {"error": str(e)}



# -------------------------------------------------------
# 4️⃣ TEAM SCHEDULE (Upcoming fixtures)
# -------------------------------------------------------

def run_schedule_llm(session_id: str, user_team_query: str):
    """
    Fetch a team's upcoming schedule and summarize using LLM.
    """
    try:
        clean_team = extract_team_name(user_team_query)
        if not clean_team:
            return {"error": "Team not recognized. Try India, Australia, England, Pakistan, etc."}

        logger.info(f"[SPORTS LLM] Processing schedule for: {clean_team}")

        schedule = get_series_schedule_by_team(clean_team)

        if not schedule:
            return {"error": f"No schedule found for {clean_team}."}

        schedule_json = json.dumps(schedule, indent=2)

        prompt = (
            f"Team: {clean_team}\n\n"
            f"Here is the upcoming schedule in JSON:\n\n"
            f"{schedule_json}\n\n"
            "Write a clear, short human summary. "
            "Use ONLY the JSON provided. "
            "No extra facts."
        )

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You summarize cricket schedules factually."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            top_p=0.3,
            max_tokens=300,
        )

        summary = response.choices[0].message.content.strip()

        memory.set_context(session_id, "schedule_summary", summary)

        return {"summary": summary, "raw": schedule}

    except Exception as e:
        logger.error(f"[SPORTS LLM] Schedule Error: {e}")
        return {"error": str(e)}
