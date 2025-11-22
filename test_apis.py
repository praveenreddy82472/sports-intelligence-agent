from agent.tools.city_api import get_city_info,get_city_and_venue_info
from agent.tools.sports_api import get_next_match,get_live_match
from agent.tools.travel_api import get_travel_info
from agent.tools.weather_api import get_weather

team = 'England'
city = "tell me about hyderbad city"
venue = 'Cricket'

print(get_next_match(team))
print(get_live_match(team))
#print(get_weather(city=city))
#print(get_city_info(city_name=city))
#print(get_travel_info(city=city,venue=venue))

