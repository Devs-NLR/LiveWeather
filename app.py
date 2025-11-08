from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

API_KEY = "d4cbf798420ef5b27990b8ea272670f2"

def get_coordinates(country, state, district, village):
    query = f"{village}, {district}, {state}, {country}"
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}"
    res = requests.get(url, headers={"User-Agent": "GeoWeatherApp/4.0"}, timeout=10)
    data = res.json()
    if data:
        return float(data[0]["lat"]), float(data[0]["lon"])
    return None, None

@app.route("/get_weather", methods=["POST"])
def get_weather():
    data = request.json
    country = data.get("country")
    state = data.get("state")
    district = data.get("district")
    village = data.get("village")

    lat, lon = get_coordinates(country, state, district, village)
    if not lat:
        return jsonify({"error": "Invalid location"}), 404

    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    res = requests.get(url, timeout=10)
    if res.status_code != 200:
        return jsonify({"error": "Failed to fetch weather"}), 500

    data = res.json()
    daily_data = {}
    for item in data["list"]:
        date = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
        temp = item["main"]["temp"]
        desc = item["weather"][0]["description"].capitalize()
        humidity = item["main"]["humidity"]
        wind = item["wind"]["speed"]
        rain_prob = item.get("pop", 0) * 100  # Probability of precipitation (0–100%)

        if date not in daily_data:
            daily_data[date] = {
                "temps": [temp],
                "humidity": [humidity],
                "wind": [wind],
                "conditions": [desc],
                "rain_probs": [rain_prob],
            }
        else:
            daily_data[date]["temps"].append(temp)
            daily_data[date]["humidity"].append(humidity)
            daily_data[date]["wind"].append(wind)
            daily_data[date]["conditions"].append(desc)
            daily_data[date]["rain_probs"].append(rain_prob)

    forecast_summary = {}
    for date, d in daily_data.items():
        avg_temp = round(sum(d["temps"]) / len(d["temps"]), 1)
        max_temp = round(max(d["temps"]), 1)
        min_temp = round(min(d["temps"]), 1)
        humidity = round(sum(d["humidity"]) / len(d["humidity"]), 1)
        wind = round(sum(d["wind"]) / len(d["wind"]), 1)
        rain_chance = round(sum(d["rain_probs"]) / len(d["rain_probs"]), 1)
        condition = max(set(d["conditions"]), key=d["conditions"].count)
        forecast_summary[date] = {
            "avg_temp": avg_temp,
            "max_temp": max_temp,
            "min_temp": min_temp,
            "humidity": humidity,
            "wind_speed": wind,
            "rain_chance": rain_chance,
            "condition": condition
        }

    return jsonify({"forecast": forecast_summary})

if __name__ == "__main__":
    app.run(debug=True)
