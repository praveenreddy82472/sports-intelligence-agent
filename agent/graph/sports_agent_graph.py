from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict
import uuid

from agent.llms.sports_llm import run_sports_llm, run_schedule_llm
from agent.llms.city_llm import run_city_llm
from agent.llms.weather_llm import run_weather_llm
from agent.llms.travel_llm import run_travel_llm
from agent.llms.complete_llm import run_fusion_llm
from agent.tools.intent_classifier import classify_intent_llm
from agent.state.session_memory import memory
from utils.city_cleaner import extract_city_from_text, correct_city_spelling
from utils.formatters import format_series_hybrid,format_travel_hybrid
from agent.tools.sports_api import (
    get_current_match,
    get_series_schedule_by_team
)


class SportsState(TypedDict):
    user_input: str
    output: str
    session_id: str
    intent: str



def build_graph():

    graph = StateGraph(SportsState)

    # --------------------------------------------------------------------
    # INTENT CLASSIFIER NODE
    # --------------------------------------------------------------------
    def intent_node(state: SportsState):
        intent = classify_intent_llm(state["user_input"])
        print(f"[ROUTER] Detected intent: {intent}")
        return {"intent": intent}

    graph.add_node("IntentClassifier", intent_node)

    # --------------------------------------------------------------------
    # CHIT CHAT NODE
    # --------------------------------------------------------------------
    def chitchat_node(state: SportsState):
        text = state["user_input"].lower()

        if any(w in text for w in ["hi", "hello", "hey", "yo"]):
            return {"output": "Hey! How can I help you today?"}

        if any(w in text for w in ["how are you"]):
            return {"output": "I’m doing great! What’s up?"}

        return {"output": "Hi! Need match info, weather, or travel guidance?"}

    graph.add_node("ChitChatNode", chitchat_node)

    # --------------------------------------------------------------------
    # SPORTS NODE
    # --------------------------------------------------------------------
    def sports_node(state: SportsState):
        user_input = state["user_input"]
        session_id = state["session_id"]
        intent = state["intent"]

        # ---------------- CURRENT MATCH ----------------
        if intent == "current_match":
            result = run_sports_llm(session_id, user_input)
            return {"output": result.get("summary", "No match found.")}

        # ---------------- NEXT SERIES / SCHEDULE ----------------
        if intent in ["schedule_match", "next_series"]:
            raw_schedule = get_series_schedule_by_team(user_input)
            formatted = format_series_hybrid(raw_schedule)
            return {"output": formatted}

        # ---------------- DEFAULT → CURRENT MATCH ----------------
        result = run_sports_llm(session_id, user_input)
        return {"output": result.get("summary", "No match found.")}


    graph.add_node("SportsNode", sports_node)

    # --------------------------------------------------------------------
    # CITY NODE
    # --------------------------------------------------------------------
    def city_node(state: SportsState):
        session_id = state["session_id"]
        user_query = state["user_input"]

        city = extract_city_from_text(user_query)

        if not city:
            city = memory.get_context(session_id, "city")

        if not city:
            return {"output": "Which city do you want to explore?"}

        city = correct_city_spelling(city)
        venue = memory.get_context(session_id, "venue")

        result = run_city_llm(session_id, city, venue)

        memory.set_context(session_id, "city", city)
        return {"output": result.get("summary", str(result))}

    graph.add_node("CityNode", city_node)

    # --------------------------------------------------------------------
    # WEATHER NODE
    # --------------------------------------------------------------------
    def weather_node(state: SportsState):
        session_id = state["session_id"]
        query = state["user_input"]

        import re
        m = re.search(r"weather\s+(?:in|at)?\s*([a-zA-Z\s]+)", query.lower())
        city = m.group(1).strip().title() if m else None

        if not city:
            city = memory.get_context(session_id, "city")

        if not city:
            return {"output": "Tell me the city name to get weather details."}

        result = run_weather_llm(session_id, city)
        return {"output": result.get("summary", str(result))}

    graph.add_node("WeatherNode", weather_node)

    # --------------------------------------------------------------------
    # TRAVEL NODE
    # --------------------------------------------------------------------
    def travel_node(state: SportsState):
        session_id = state["session_id"]
        query = state["user_input"]

        import re
        city = None
        venue = None

        for p in [r"to\s+([a-zA-Z\s]+)", r"in\s+([a-zA-Z\s]+)"]:
            m = re.search(p, query.lower())
            if m:
                city = m.group(1).strip().title()
                break

        for p in [r"at\s+([a-zA-Z\s]+)", r"near\s+([a-zA-Z\s]+)"]:
            m = re.search(p, query.lower())
            if m:
                venue = m.group(1).strip().title()
                break

        if not city:
            city = memory.get_context(session_id, "city")
        if not venue:
            venue = memory.get_context(session_id, "venue")

        if not city:
            return {"output": "I need a city name to lookup travel info."}

        result = run_travel_llm(session_id, city, venue)
        formatted_html = format_travel_hybrid(result)
        return {"output": result.get("summary", str(formatted_html))}

    graph.add_node("TravelNode", travel_node)

    # --------------------------------------------------------------------
    # FUSION SUMMARY NODE
    # --------------------------------------------------------------------
    def fusion_node(state: SportsState):
        session_id = state["session_id"]
        query = state["user_input"]

        result = run_fusion_llm(session_id, query)
        return {"output": result.get("answer", str(result))}

    graph.add_node("FusionNode", fusion_node)

    # --------------------------------------------------------------------
    # ROUTING LOGIC  (FIXED)
    # --------------------------------------------------------------------
    def route(state: SportsState):

        intent = state["intent"]


        if intent == "chitchat":
            return "ChitChatNode"

        if intent in ["current_match", "match_info"]:
            return "SportsNode"

        if intent in ["next_series", "schedule_match"]:
            return "SportsNode"

        if intent == "city_info":
            return "CityNode"

        if intent == "weather_info":
            return "WeatherNode"

        if intent == "travel_info":
            return "TravelNode"
        
        if intent == "match_summary":
            return "FusionNode"

        return "FusionNode"

    graph.set_entry_point("IntentClassifier")
    graph.add_conditional_edges("IntentClassifier", route)

    # END CONNECTIONS
    for node in [
        "ChitChatNode",
        "SportsNode",
        "CityNode",
        "WeatherNode",
        "TravelNode",
        "FusionNode"
    ]:
        graph.add_edge(node, END)

    compiled = graph.compile(checkpointer=MemorySaver())
    return compiled