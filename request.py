import requests
import config


def get_city(city: str) -> requests:
    payload: dict = {
        "geocode": city,
        "apikey": config.geo_key,
        "format": "json",
        }
    url: str = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(url=url, params=payload)
    geo_data = response.json()
    return geo_data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']


print(get_city("Moscow"))
