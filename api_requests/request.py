import requests

from settings import api_weather
from settings.get_token import load_env


def get_city_coord(city: str) -> str:
    """get geo data of city"""

    payload: dict = {
        "geocode": city,
        "apikey": load_env("GEO_KEY"),
        "format": "json",
        }
    url: str = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(url=url, params=payload)
    geo_data: dict = response.json()
    return geo_data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"]


def get_weather(city: str) -> dict:
    """get weather data of city"""

    coordinates: list = get_city_coord(city).split()
    payload: dict = {"lat": coordinates[1], "lon": coordinates[0], "lang": "ru_RU"}
    url: str = "https://api.weather.yandex.ru/v2/forecast/"
    response = requests.get(url=url, params=payload, headers=api_weather.WEATHER_API)
    weather_data: dict = response.json()
    return weather_data["fact"]
