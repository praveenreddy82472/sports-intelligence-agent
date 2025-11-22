from agent.llms.complete_llm import run_fusion_llm
from agent.llms.sports_llm import run_sports_llm,run_live_match_llm,run_schedule_llm
from agent.llms.weather_llm import run_weather_llm
from agent.llms.city_llm import run_city_llm
from agent.llms.travel_llm import run_travel_llm

from agent.state.session_memory import memory

session_id = "travel_28"

team = 'England'
city = "Chittagong"


print(run_sports_llm(session_id,team))
print(run_live_match_llm(session_id,team))
print(run_schedule_llm(session_id,team))
#print(run_weather_llm(session_id=session_id,city=city))
#print(run_city_llm(city=city))
#print(run_travel_llm(session_id=session_id,city=city))
