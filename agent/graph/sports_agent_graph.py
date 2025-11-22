from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict
import uuid
import asyncio

from agent.llms.sports_llm import run_sports_llm,run_live_match_llm,run_schedule_llm
from agent.llms.city_llm import run_city_llm
from agent.llms.weather_llm import run_weather_llm
from agent.llms.travel_llm import run_travel_llm
from agent.llms.complete_llm import run_fusion_llm
from agent.tools.intent_classifier import classify_intent_llm
from agent.state.session_memory import memory
from utils.city_cleaner import extract_city_from_text, correct_city_spelling
from agent.tools.sports_api import get_team_schedule


class SportsState(TypedDict):
    user_input: str
    output: str
    session_id: str
    intent: str


def build_graph():
    graph = StateGraph(SportsState)

    # --- Intent Node ---
    def intent_node(state: SportsState):
        intent = classify_intent_llm(state["user_input"])
        print(f"[ROUTER] Detected intent: {intent}")
        return {"intent": intent}
    graph.add_node("IntentClassifier", intent_node)

    # --- Chitchat Node ---
    def chitchat_node(state: SportsState):
        """Respond casually for greetings or small talk."""
        user_text = state["user_input"].lower()
        if any(word in user_text for word in ["hi", "hello", "hey", "yo", "what’s up"]):
            reply = "Hey there! How’s it going?"
        elif any(word in user_text for word in ["how are you", "doing", "you good"]):
            reply = "I’m doing great — just keeping up with the sports world! How about you?"
        else:
            reply = "Hi! What can I help you with today — match details, weather, or travel info?"
        return {"output": reply}
    graph.add_node("ChitChatNode", chitchat_node)

    # --- Sports Node ---
    def sports_node(state: SportsState):
        session_id = state["session_id"]
        user_input = state["user_input"]
        intent = state["intent"]

        # Next match
        if intent == "next_match":
            result = run_sports_llm(session_id, user_input)
            return {"output": result.get("summary", str(result))}

        # Live match
        if intent == "live_match":
            result = run_live_match_llm(session_id, user_input)
            return {"output": result.get("summary", str(result))}

        # Schedule
        if intent == "schedule_match":
            schedule = get_team_schedule(user_input)
            result = run_schedule_llm(schedule, user_input)

            return {"output": result}

        # Default fallback → next match
        result = run_sports_llm(session_id, user_input)
        return {"output": result.get("summary", str(result))}
    graph.add_node("SportsNode", sports_node)

    # --- City Node ---
    """    def city_node(state: SportsState):
        session_id = state["session_id"]
        user_query = state.get("user_input", "")

        import re
        # Try to extract city from user query (e.g., “tell me about Mumbai city”)
        match = re.search(r"(?:city\s*(?:of|in)?\s*)?([a-zA-Z\s]{3,})", user_query.lower())
        city = match.group(1).strip().title() if match else None

        # Fallback: use memory if city not found
        if not city:
            city = memory.get_context(session_id, "city")

        # Call LLM
        result = run_city_llm(city)
        return {"output": result.get("summary", str(result))}
    graph.add_node("CityNode", city_node)"""
    def city_node(state: SportsState):
        session_id = state["session_id"]
        query = state["user_input"]

        # 1) Try extracting city directly from query
        city = extract_city_from_text(query)

        # 2) If STILL not found → fallback to memory
        if not city:
            city = memory.get_context(session_id, "city")

        # 3) If nothing available at all → ask user for city
        if not city:
            return {"output": "Which city would you like to explore?"}

        # 4) Fix spelling (Hyderbad → Hyderabad)
        city = correct_city_spelling(city)

        # 5) Get venue from memory (optional)
        venue = memory.get_context(session_id, "venue")

        # 6) Run the LLM
        result = run_city_llm(session_id, city, venue)

        # 7) Store updated memory
        memory.set_context(session_id, "city", city)

        return {"output": result.get("summary", str(result))}
    graph.add_node("CityNode", city_node)
    
    # --- Weather Node ---
    def weather_node(state: SportsState):
        session_id = state["session_id"]
        user_query = state.get("user_input", "")

        import re
        # 🧠 Try to extract city from user query (e.g., "weather in Delhi")
        match = re.search(r"weather\s+(?:in|at|of)?\s*([a-zA-Z\s]+)", user_query.lower())
        city = match.group(1).strip().title() if match else None

        # 🗂️ Fallback: use memory if no city found in query
        if not city:
            city = memory.get_context(session_id, "city")
        
        if not city:
            return {"output": "Tell me the city name to fetch weather information."}

        result = run_weather_llm(session_id, city)
        return {"output": result.get("summary", str(result))}
    graph.add_node("WeatherNode", weather_node)


    # --- Travel Node ---
    """def travel_node(state: SportsState):
        session_id = state["session_id"]
        user_query = state.get("user_input", "")

        import re
        # Extract city and venue from query if present
        city_match = re.search(r"(?:in|to)\s+([a-zA-Z\s]+)", user_query.lower())
        city = city_match.group(1).strip().title() if city_match else None

        venue_match = re.search(r"(?:at|around|near)\s+([a-zA-Z\s]+)", user_query.lower())
        venue = venue_match.group(1).strip().title() if venue_match else None

        # Fallbacks to memory
        if not city:
            city = memory.get_context(session_id, "city")
        if not venue:
            venue = memory.get_context(session_id, "venue")

        result = run_travel_llm(session_id, city, venue)
        return {"output": result.get("summary", str(result))}
    graph.add_node("TravelNode", travel_node)"""
    def travel_node(state: SportsState):
        session_id = state["session_id"]
        user_query = state.get("user_input", "")

        import re
        city = None
        venue = None

        # extract city
        city_patterns = [
            r"travel\s+(?:in|to)\s+([a-zA-Z\s]+)",
            r"in\s+([a-zA-Z\s]+)",
            r"to\s+([a-zA-Z\s]+)",
        ]

        for p in city_patterns:
            m = re.search(p, user_query.lower())
            if m:
                city = m.group(1).strip().title()
                break

        # extract venue
        venue_patterns = [
            r"at\s+([a-zA-Z\s]+)",
            r"near\s+([a-zA-Z\s]+)",
            r"around\s+([a-zA-Z\s]+)",
        ]

        for p in venue_patterns:
            m = re.search(p, user_query.lower())
            if m:
                venue = m.group(1).strip().title()
                break

        # fallbacks to memory
        if not city:
            city = memory.get_context(session_id, "city")
        if not venue:
            venue = memory.get_context(session_id, "venue")

        if not city:
            return {"output": "I don’t know the city yet. Ask about a match or specify the city."}

        result = run_travel_llm(session_id, city, venue)
        return {"output": result.get("summary", str(result))}
    graph.add_node("TravelNode", travel_node)


    # --- Fusion Node ---
    def fusion_node(state):
        session_id = state["session_id"]
        user_query = state["user_input"]

        result = run_fusion_llm(session_id, user_query)  
        return {"output": result.get("answer", str(result))}
    graph.add_node("FusionNode", fusion_node)

    # --- Routing Logic ---
    def route(state: SportsState):
        intent = state.get("intent") or classify_intent_llm(state["user_input"])
        if intent == "chitchat":
            return "ChitChatNode"
        elif intent == "match_info":
            return "SportsNode"
        elif intent == "city_info":
            return "CityNode"
        elif intent == "weather_info":
            return "WeatherNode"
        elif intent == "travel_info":
            return "TravelNode"
        else:
            return "FusionNode"

    graph.set_entry_point("IntentClassifier")
    graph.add_conditional_edges("IntentClassifier", route)

    # Connect all processing nodes to END
    for node in ["ChitChatNode", "SportsNode", "CityNode", "WeatherNode", "TravelNode", "FusionNode"]:
        graph.add_edge(node, END)

    memory_saver = MemorySaver()
    compiled = graph.compile(checkpointer=memory_saver)
    return compiled


if __name__ == "__main__":
    sports_agent_graph = build_graph()
    print("🏏 Sports Intelligence Agent (LangGraph Edition) ready! Type 'exit' to quit.\n")

    # Auto-generate new session each run
    session_id = f"user_{uuid.uuid4().hex[:8]}"
    print(f"[SESSION] Started new session: {session_id}\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("👋 Goodbye!")
            break

        result = sports_agent_graph.invoke(
            {"user_input": user_input, "session_id": session_id},
            config={"configurable": {"thread_id": session_id}}
        )

        print("\nAssistant:", result["output"], "\n")
