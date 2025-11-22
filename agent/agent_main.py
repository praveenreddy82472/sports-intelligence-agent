import logging
from core.logging_config import setup_logging
from agent.tools.intent_classifier import classify_intent_llm as classify_intent
from agent.llms.sports_llm import run_sports_llm
from agent.llms.city_llm import run_city_llm
from agent.llms.weather_llm import run_weather_llm
from agent.llms.travel_llm import run_travel_llm
from agent.llms.complete_llm import run_fusion_llm
from agent.state.session_memory import memory

setup_logging()
logger = logging.getLogger(__name__)

def run_sports_conversation():
    """
    Interactive conversational sports agent.
    - Detects intent dynamically.
    - Calls only the required LLM.
    - Keeps memory context across turns.
    """
    session_id = "user125"
    print("🏏  Sports Intelligence Agent ready! Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break
        if user_input.lower() in ["clear", "reset", "new chat", "clear chat"]:
            memory.clear(session_id)
            print("👍 Chat cleared. You can start fresh!")
            continue


        # Detect intent
        intent = classify_intent(user_input)
        logger.info(f"[AGENT] Detected intent: {intent}")

        try:
            # ─────────────────────────────────────────────
            # 1️⃣ MATCH-RELATED QUERIES
            # ─────────────────────────────────────────────
            if intent == "match_info":
                result = run_sports_llm(session_id, user_input)
                if "error" in result:
                    print(f"❌ {result['error']}")
                    continue

                city = result.get("city")
                venue = result.get("venue")
                if city: memory.set_context(session_id, "city", city)
                if venue: memory.set_context(session_id, "venue", venue)

                print(result["summary"])

            # ─────────────────────────────────────────────
            # 2️⃣ CITY / VENUE INFO
            # ─────────────────────────────────────────────
            elif intent == "city_info":
                city = memory.get_context(session_id, "city")
                venue = memory.get_context(session_id, "venue")
                if not city or not venue:
                    print("⚠️ Ask about a match first so I know the location.")
                    continue

                result = run_city_llm(session_id, city)
                print(result["summary"])

            # ─────────────────────────────────────────────
            # 3️⃣ WEATHER INFO
            # ─────────────────────────────────────────────
            elif intent == "weather_info":
                city = memory.get_context(session_id, "city")
                if not city:
                    print("⚠️ I don’t know the city yet. Ask about a match first.")
                    continue

                result = run_weather_llm(session_id, city)
                print(result["summary"])

            # ─────────────────────────────────────────────
            # 4️⃣ TRAVEL INFO
            # ─────────────────────────────────────────────
            elif intent == "travel_info":
                city = memory.get_context(session_id, "city")
                venue = memory.get_context(session_id, "venue")
                if not city or not venue:
                    print("⚠️ Ask about a match first so I know the venue.")
                    continue

                result = run_travel_llm(session_id, city, venue)
                print(result["summary"])

            # ─────────────────────────────────────────────
            # 5️⃣ FUSION / SUMMARY REQUEST
            # ─────────────────────────────────────────────
            elif intent == "fusion_summary":
                result = run_fusion_llm(session_id, user_input)
                print(result["answer"])
                
            elif intent == "chitchat":
                print("👋 Hey there! I’m your Sports Intelligence Assistant. Ask me about upcoming matches or travel details.")
                continue

            # ─────────────────────────────────────────────
            # 6️⃣ DEFAULT
            # ─────────────────────────────────────────────
            else:
                result = run_fusion_llm(session_id, user_input)
                print(result["answer"])

        except Exception as e:
            logger.exception(f"[AGENT] Error: {e}")
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    run_sports_conversation()
