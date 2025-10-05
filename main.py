from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from typing import List, Optional
from datetime import datetime

app = FastAPI(
    title="Weather API",
    description="Comprehensive weather API with current conditions, forecasts, and historical data",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("OPENWEATHER_API_KEY", "004fbe3f4ad108ff0ac62cec915197ec")
BASE_URL = "https://api.openweathermap.org/data/2.5"

# Enhanced response models
class CurrentWeather(BaseModel):
    city: str
    country: str
    temperature: float
    feels_like: float
    temp_min: float
    temp_max: float
    description: str
    icon: str
    humidity: int
    pressure: int
    wind_speed: float
    wind_deg: int
    clouds: int
    visibility: int
    sunrise: int
    sunset: int
    timezone: int

class ForecastItem(BaseModel):
    dt: int
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    humidity: int
    description: str
    icon: str
    clouds: int
    wind_speed: float
    wind_deg: int
    pop: float  # Probability of precipitation
    rain_3h: Optional[float] = 0

class ForecastResponse(BaseModel):
    city: str
    country: str
    timezone: int
    forecast: List[ForecastItem]

class DailyForecast(BaseModel):
    date: str
    temp_min: float
    temp_max: float
    temp_avg: float
    description: str
    icon: str
    humidity: int
    wind_speed: float
    pop: float

class HourlyChartData(BaseModel):
    labels: List[str]
    temperatures: List[float]
    humidity: List[int]
    wind_speed: List[float]

@app.get("/")
def root():
    return {
        "message": "Comprehensive Weather API",
        "version": "2.0.0",
        "endpoints": {
            "current_weather": "/weather/current/{city}",
            "detailed_forecast": "/weather/forecast/{city}",
            "daily_forecast": "/weather/daily/{city}",
            "hourly_chart_data": "/weather/hourly-chart/{city}",
            "air_quality": "/weather/air-quality/{city}",
            "search_cities": "/weather/search?q={query}",
            "health": "/health"
        }
    }

@app.get("/weather/current/{city}", response_model=CurrentWeather)
def get_current_weather(city: str):
    """Get comprehensive current weather data"""
    url = f"{BASE_URL}/weather?q={city}&appid={API_KEY}&units=metric"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return CurrentWeather(
            city=data["name"],
            country=data["sys"]["country"],
            temperature=data["main"]["temp"],
            feels_like=data["main"]["feels_like"],
            temp_min=data["main"]["temp_min"],
            temp_max=data["main"]["temp_max"],
            description=data["weather"][0]["description"],
            icon=data["weather"][0]["icon"],
            humidity=data["main"]["humidity"],
            pressure=data["main"]["pressure"],
            wind_speed=data["wind"]["speed"],
            wind_deg=data["wind"].get("deg", 0),
            clouds=data["clouds"]["all"],
            visibility=data.get("visibility", 0),
            sunrise=data["sys"]["sunrise"],
            sunset=data["sys"]["sunset"],
            timezone=data["timezone"]
        )
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="City not found")
        raise HTTPException(status_code=response.status_code, detail="Weather service error")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Unable to reach weather service")

@app.get("/weather/forecast/{city}", response_model=ForecastResponse)
def get_detailed_forecast(city: str):
    """Get 5-day forecast with 3-hour intervals (40 data points)"""
    url = f"{BASE_URL}/forecast?q={city}&appid={API_KEY}&units=metric"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        forecast_items = []
        for item in data["list"]:
            forecast_items.append(ForecastItem(
                dt=item["dt"],
                temp=item["main"]["temp"],
                feels_like=item["main"]["feels_like"],
                temp_min=item["main"]["temp_min"],
                temp_max=item["main"]["temp_max"],
                pressure=item["main"]["pressure"],
                humidity=item["main"]["humidity"],
                description=item["weather"][0]["description"],
                icon=item["weather"][0]["icon"],
                clouds=item["clouds"]["all"],
                wind_speed=item["wind"]["speed"],
                wind_deg=item["wind"].get("deg", 0),
                pop=item.get("pop", 0),
                rain_3h=item.get("rain", {}).get("3h", 0)
            ))
        
        return ForecastResponse(
            city=data["city"]["name"],
            country=data["city"]["country"],
            timezone=data["city"]["timezone"],
            forecast=forecast_items
        )
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="City not found")
        raise HTTPException(status_code=response.status_code, detail="Weather service error")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Unable to reach weather service")

@app.get("/weather/daily/{city}")
def get_daily_forecast(city: str):
    """Get simplified daily forecast (aggregated by day)"""
    url = f"{BASE_URL}/forecast?q={city}&appid={API_KEY}&units=metric"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Group by day
        daily_data = {}
        for item in data["list"]:
            date = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
            
            if date not in daily_data:
                daily_data[date] = {
                    "temps": [],
                    "humidity": [],
                    "wind": [],
                    "pop": [],
                    "description": item["weather"][0]["description"],
                    "icon": item["weather"][0]["icon"]
                }
            
            daily_data[date]["temps"].append(item["main"]["temp"])
            daily_data[date]["humidity"].append(item["main"]["humidity"])
            daily_data[date]["wind"].append(item["wind"]["speed"])
            daily_data[date]["pop"].append(item.get("pop", 0))
        
        # Create daily summaries
        daily_forecast = []
        for date, values in list(daily_data.items())[:5]:  # Limit to 5 days
            daily_forecast.append({
                "date": date,
                "day_name": datetime.strptime(date, "%Y-%m-%d").strftime("%A"),
                "temp_min": round(min(values["temps"]), 1),
                "temp_max": round(max(values["temps"]), 1),
                "temp_avg": round(sum(values["temps"]) / len(values["temps"]), 1),
                "description": values["description"],
                "icon": values["icon"],
                "humidity": round(sum(values["humidity"]) / len(values["humidity"])),
                "wind_speed": round(sum(values["wind"]) / len(values["wind"]), 1),
                "pop": round(max(values["pop"]) * 100)  # Max probability as percentage
            })
        
        return {
            "city": data["city"]["name"],
            "country": data["city"]["country"],
            "daily_forecast": daily_forecast
        }
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="City not found")
        raise HTTPException(status_code=response.status_code, detail="Weather service error")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Unable to reach weather service")

@app.get("/weather/hourly-chart/{city}", response_model=HourlyChartData)
def get_hourly_chart_data(city: str, hours: int = 24):
    """Get hourly data formatted for charts (next 24 hours by default)"""
    url = f"{BASE_URL}/forecast?q={city}&appid={API_KEY}&units=metric"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Limit to requested hours (each item is 3 hours)
        items = data["list"][:min(hours // 3, len(data["list"]))]
        
        labels = []
        temperatures = []
        humidity = []
        wind_speed = []
        
        for item in items:
            dt = datetime.fromtimestamp(item["dt"])
            labels.append(dt.strftime("%I:%M %p"))
            temperatures.append(round(item["main"]["temp"], 1))
            humidity.append(item["main"]["humidity"])
            wind_speed.append(round(item["wind"]["speed"], 1))
        
        return HourlyChartData(
            labels=labels,
            temperatures=temperatures,
            humidity=humidity,
            wind_speed=wind_speed
        )
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="City not found")
        raise HTTPException(status_code=response.status_code, detail="Weather service error")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Unable to reach weather service")

@app.get("/weather/air-quality/{city}")
def get_air_quality(city: str):
    """Get air quality data for a city"""
    # First get coordinates
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
    
    try:
        geo_response = requests.get(geo_url, timeout=10)
        geo_response.raise_for_status()
        geo_data = geo_response.json()
        
        if not geo_data:
            raise HTTPException(status_code=404, detail="City not found")
        
        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]
        
        # Get air quality
        aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        aqi_response = requests.get(aqi_url, timeout=10)
        aqi_response.raise_for_status()
        aqi_data = aqi_response.json()
        
        aqi = aqi_data["list"][0]["main"]["aqi"]
        components = aqi_data["list"][0]["components"]
        
        aqi_labels = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
        
        return {
            "city": city,
            "aqi": aqi,
            "aqi_label": aqi_labels.get(aqi, "Unknown"),
            "components": components
        }
    except requests.exceptions.HTTPError:
        raise HTTPException(status_code=404, detail="Air quality data not available")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Unable to reach weather service")

@app.get("/health")
def health_check():
    api_key_configured = API_KEY != "your_openweathermap_api_key"
    return {
        "status": "ok",
        "api_key_configured": api_key_configured,
        "version": "2.0.0"
    }