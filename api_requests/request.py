import requests
from settings import api_config


def get_city_coord(city: str) -> str:
    # get geo data of city
    payload: dict = {
        "geocode": city,
        "apikey": api_config.geo_key,
        "format": "json",
        }
    url: str = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(url=url, params=payload)
    geo_data: dict = response.json()
    return geo_data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"]


def get_weather(city: str) -> dict:
    # get weather data of city
    coordinates: list = get_city_coord(city).split()
    payload: dict = {"lat": coordinates[1], "lon": coordinates[0], "lang": "ru_RU"}
    url: str = "https://api.weather.yandex.ru/v2/forecast"
    response = requests.get(url=url, params=payload, headers=api_config.weather_key)
    weather: dict = response.json()
    return weather
