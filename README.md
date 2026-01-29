Weather Dashboard API
A comprehensive weather API built with FastAPI and OpenWeatherMap, featuring current conditions, forecasts, air quality monitoring, and interactive charts.
Features

🌡️ Current weather with detailed metrics
📅 5-day weather forecast
💨 Air quality index (AQI) with pollutant breakdown
📊 Hourly temperature and humidity charts
🌅 Sunrise/sunset times
🌍 Global city coverage

API Endpoints
GET /weather/current/{city}          - Current weather conditions
GET /weather/daily/{city}            - 5-day daily forecast
GET /weather/hourly-chart/{city}     - Hourly data for charts
GET /weather/air-quality/{city}      - Air quality index and pollutants
GET /health                          - API health check
Setup
1. Clone the repository
bashgit clone https://github.com/yourusername/weather-dashboard-api.git
cd weather-dashboard-api
2. Install dependencies
bashpip install -r requirements.txt
3. Set your API key
Get a free API key from OpenWeatherMap
bashexport OPENWEATHER_API_KEY="your_api_key_here"
4. Run locally
bashuvicorn main:app --reload
Visit http://localhost:8000/docs for interactive API documentation.
Deployment
Deploy to Render.com

Push code to GitHub
Create new Web Service on Render
Connect your repository
Add environment variable: OPENWEATHER_API_KEY
Deploy with these settings:

Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT



Environment Variables
VariableDescriptionRequiredOPENWEATHER_API_KEYYour OpenWeatherMap API keyYes
Technologies

FastAPI - Modern Python web framework
OpenWeatherMap API - Weather data provider
Uvicorn - ASGI server
Pydantic - Data validation

Project Structure
weather-dashboard-api/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── .gitignore          # Git ignore rules
└── README.md           # This file
License
MIT
Author
Your Name - GitHub
Acknowledgments

Weather data provided by OpenWeatherMap
Built with FastAPI
