import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://marine-api.open-meteo.com/v1/marine"
params = {
	"latitude": -23.9608,
	"longitude": -46.3336,
	"current": ["wave_height", "wave_direction", "wave_period", "wave_peak_period"],
	"forecast_days": 7,
}
responses = openmeteo.weather_api(url, params = params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation: {response.Elevation()} m asl")
print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

# Process current data. The order of variables needs to be the same as requested.
current = response.Current()
current_wave_height = current.Variables(0).Value()
current_wave_direction = current.Variables(1).Value()
current_wave_period = current.Variables(2).Value()
current_wave_peak_period = current.Variables(3).Value()

print(f"\nCurrent time: {current.Time()}")
print(f"Current wave_height: {current_wave_height}")
print(f"Current wave_direction: {current_wave_direction}")
print(f"Current wave_period: {current_wave_period}")
print(f"Current wave_peak_period: {current_wave_peak_period}")
