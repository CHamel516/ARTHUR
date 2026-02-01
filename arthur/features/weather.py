"""
ARTHUR Weather Feature
Weather information using OpenWeatherMap API (free tier)
"""

import requests
from typing import Optional, Dict
from datetime import datetime


class WeatherService:
    """Handles weather information retrieval"""

    BASE_URL = "http://api.openweathermap.org/data/2.5"

    def __init__(self, api_key: Optional[str] = None, default_city: str = ""):
        """
        Initialize weather service

        Args:
            api_key: OpenWeatherMap API key (free tier available)
            default_city: Default city for weather queries
        """
        self.api_key = api_key
        self.default_city = default_city

    def set_api_key(self, api_key: str):
        """Set the API key"""
        self.api_key = api_key

    def set_default_city(self, city: str):
        """Set the default city"""
        self.default_city = city

    def get_weather(self, city: str = None) -> str:
        """
        Get current weather for a city

        Args:
            city: City name (uses default if not specified)

        Returns:
            Weather description string
        """
        if not self.api_key:
            return "Weather service not configured. Please set an OpenWeatherMap API key."

        city = city or self.default_city
        if not city:
            return "Please specify a city, or set a default city in the configuration."

        try:
            url = f"{self.BASE_URL}/weather"
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'imperial'
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 401:
                return "Weather API key is invalid. Please check your configuration."
            elif response.status_code == 404:
                return f"I couldn't find weather data for '{city}'. Please check the city name."
            elif response.status_code != 200:
                return "I'm having trouble retrieving weather data at the moment."

            data = response.json()
            return self._format_weather(data, city)

        except requests.RequestException as e:
            return "I couldn't connect to the weather service. Please check your internet connection."

    def _format_weather(self, data: Dict, city: str) -> str:
        """Format weather data into a readable string"""
        weather = data['weather'][0]
        main = data['main']

        condition = weather['description']
        temp = round(main['temp'])
        feels_like = round(main['feels_like'])
        humidity = main['humidity']

        response = f"Currently in {city}: {condition}, {temp}°F"

        if abs(temp - feels_like) >= 5:
            response += f" (feels like {feels_like}°F)"

        if humidity > 70:
            response += f". Humidity is {humidity}%"
        elif humidity < 30:
            response += f". It's quite dry at {humidity}% humidity"

        if 'wind' in data:
            wind_speed = round(data['wind']['speed'])
            if wind_speed > 15:
                response += f". Winds at {wind_speed} mph"

        return response + "."

    def get_forecast(self, city: str = None, days: int = 3) -> str:
        """
        Get weather forecast

        Args:
            city: City name
            days: Number of days (max 5 for free tier)

        Returns:
            Forecast description string
        """
        if not self.api_key:
            return "Weather service not configured."

        city = city or self.default_city
        if not city:
            return "Please specify a city."

        try:
            url = f"{self.BASE_URL}/forecast"
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'imperial',
                'cnt': min(days * 8, 40)
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                return "I couldn't retrieve the forecast."

            data = response.json()
            return self._format_forecast(data, city, days)

        except requests.RequestException:
            return "I couldn't connect to the weather service."

    def _format_forecast(self, data: Dict, city: str, days: int) -> str:
        """Format forecast data"""
        lines = [f"Forecast for {city}:"]

        daily_data = {}
        for item in data['list']:
            date = datetime.fromtimestamp(item['dt']).strftime('%A')
            if date not in daily_data:
                daily_data[date] = {
                    'temps': [],
                    'conditions': []
                }
            daily_data[date]['temps'].append(item['main']['temp'])
            daily_data[date]['conditions'].append(item['weather'][0]['description'])

        count = 0
        for day, info in daily_data.items():
            if count >= days:
                break

            avg_temp = round(sum(info['temps']) / len(info['temps']))
            high = round(max(info['temps']))
            low = round(min(info['temps']))

            most_common_condition = max(set(info['conditions']),
                                        key=info['conditions'].count)

            lines.append(f"  {day}: {most_common_condition}, {low}°F - {high}°F")
            count += 1

        return "\n".join(lines)

    def should_bring_umbrella(self, city: str = None) -> str:
        """Quick check if user should bring an umbrella"""
        if not self.api_key:
            return "Weather service not configured."

        city = city or self.default_city
        if not city:
            return "Please specify a city."

        try:
            url = f"{self.BASE_URL}/weather"
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'imperial'
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return "I couldn't check the weather."

            data = response.json()
            weather_id = data['weather'][0]['id']

            if weather_id < 700:
                return "Yes, I'd recommend bringing an umbrella today. Rain is expected."
            elif weather_id < 800:
                return "The sky looks a bit hazy, but no rain expected. You should be fine without an umbrella."
            else:
                return "No umbrella needed today. The weather looks clear."

        except requests.RequestException:
            return "I couldn't check the weather."

    def is_configured(self) -> bool:
        """Check if weather service is properly configured"""
        return bool(self.api_key)
