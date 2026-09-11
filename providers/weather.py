import os
import re
import json
import time
import urllib.request
import urllib.parse
import threading
from datetime import datetime, timezone
import math
from pathlib import Path
from .base import BaseProvider, SearchResult
from i18n import t, get_current_language

try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gdk
except (ValueError, ImportError):
    pass

CACHE_DIR = Path(os.path.expanduser('~/.cache/echo_search'))
CACHE_FILE = CACHE_DIR / 'weather.json'
ICONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons', 'weather'))

MAJOR_CITIES = {
    'нью-йорк': {'name_ru': 'Нью-Йорк', 'name_en': 'New York', 'lat': 40.7128, 'lon': -74.0060, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['ny', 'new york', 'нью йорк']},
    'новокузнецк': {'name_ru': 'Новокузнецк', 'name_en': 'Novokuznetsk', 'lat': 53.7557, 'lon': 87.1099, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': ['кузня', 'nvkz']},
    'москва': {'name_ru': 'Москва', 'name_en': 'Moscow', 'lat': 55.7520, 'lon': 37.6178, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': ['мск', 'moscow']},
    'санкт-петербург': {'name_ru': 'Санкт-Петербург', 'name_en': 'Saint Petersburg', 'lat': 59.9386, 'lon': 30.3141, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': ['питер', 'спб']},
    'новосибирск': {'name_ru': 'Новосибирск', 'name_en': 'Novosibirsk', 'lat': 55.0415, 'lon': 82.9346, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': ['нск', 'сиб']},
    'екатеринбург': {'name_ru': 'Екатеринбург', 'name_en': 'Yekaterinburg', 'lat': 56.8389, 'lon': 60.6057, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': ['екб']},
    'казань': {'name_ru': 'Казань', 'name_en': 'Kazan', 'lat': 55.7887, 'lon': 49.1221, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': ['kzn']},
    'нижний новгород': {'name_ru': 'Нижний Новгород', 'name_en': 'Nizhny Novgorod', 'lat': 56.3269, 'lon': 44.0059, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': ['нн']},
    'челябинск': {'name_ru': 'Челябинск', 'name_en': 'Chelyabinsk', 'lat': 55.1644, 'lon': 61.4368, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': ['члб']},
    'самара': {'name_ru': 'Самара', 'name_en': 'Samara', 'lat': 53.2001, 'lon': 50.1500, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'омск': {'name_ru': 'Омск', 'name_en': 'Omsk', 'lat': 54.9885, 'lon': 73.3242, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'ростов-на-дону': {'name_ru': 'Ростов-на-Дону', 'name_en': 'Rostov-on-Don', 'lat': 47.2357, 'lon': 39.7015, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': ['ростов']},
    'уфа': {'name_ru': 'Уфа', 'name_en': 'Ufa', 'lat': 54.7388, 'lon': 55.9721, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'красноярск': {'name_ru': 'Красноярск', 'name_en': 'Krasnoyarsk', 'lat': 56.0153, 'lon': 92.8932, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': ['крск']},
    'воронеж': {'name_ru': 'Воронеж', 'name_en': 'Voronezh', 'lat': 51.6720, 'lon': 39.1843, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'пермь': {'name_ru': 'Пермь', 'name_en': 'Perm', 'lat': 58.0105, 'lon': 56.2502, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'волгоград': {'name_ru': 'Волгоград', 'name_en': 'Volgograd', 'lat': 48.7080, 'lon': 44.5133, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'краснодар': {'name_ru': 'Краснодар', 'name_en': 'Krasnodar', 'lat': 45.0355, 'lon': 38.9753, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': ['крд']},
    'саратов': {'name_ru': 'Саратов', 'name_en': 'Saratov', 'lat': 51.5406, 'lon': 46.0086, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'тюмень': {'name_ru': 'Тюмень', 'name_en': 'Tyumen', 'lat': 57.1522, 'lon': 65.5272, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'тольятти': {'name_ru': 'Тольятти', 'name_en': 'Tolyatti', 'lat': 53.5303, 'lon': 49.3461, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'барнаул': {'name_ru': 'Барнаул', 'name_en': 'Barnaul', 'lat': 53.3606, 'lon': 83.7636, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'ижевск': {'name_ru': 'Ижевск', 'name_en': 'Izhevsk', 'lat': 56.8498, 'lon': 53.2045, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'ульяновск': {'name_ru': 'Ульяновск', 'name_en': 'Ulyanovsk', 'lat': 54.3282, 'lon': 48.3866, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'иркутск': {'name_ru': 'Иркутск', 'name_en': 'Irkutsk', 'lat': 52.2978, 'lon': 104.2964, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'хабаровск': {'name_ru': 'Хабаровск', 'name_en': 'Khabarovsk', 'lat': 48.4827, 'lon': 135.0838, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'ярославль': {'name_ru': 'Ярославль', 'name_en': 'Yaroslavl', 'lat': 57.6261, 'lon': 39.8845, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'владивосток': {'name_ru': 'Владивосток', 'name_en': 'Vladivostok', 'lat': 43.1155, 'lon': 131.8855, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': ['вдк']},
    'томск': {'name_ru': 'Томск', 'name_en': 'Tomsk', 'lat': 56.4977, 'lon': 84.9744, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'кемерово': {'name_ru': 'Кемерово', 'name_en': 'Kemerovo', 'lat': 55.3333, 'lon': 86.0833, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'сочи': {'name_ru': 'Сочи', 'name_en': 'Sochi', 'lat': 43.6028, 'lon': 39.7342, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': []},
    'калининград': {'name_ru': 'Калининград', 'name_en': 'Kaliningrad', 'lat': 54.7104, 'lon': 20.4522, 'country_ru': 'Россия', 'country_en': 'Russia', 'keywords': ['клд']},
    'лондон': {'name_ru': 'Лондон', 'name_en': 'London', 'lat': 51.5074, 'lon': -0.1278, 'country_ru': 'Великобритания', 'country_en': 'UK', 'keywords': ['london']},
    'париж': {'name_ru': 'Париж', 'name_en': 'Paris', 'lat': 48.8566, 'lon': 2.3522, 'country_ru': 'Франция', 'country_en': 'France', 'keywords': ['paris']},
    'токио': {'name_ru': 'Токио', 'name_en': 'Tokyo', 'lat': 35.6762, 'lon': 139.6503, 'country_ru': 'Япония', 'country_en': 'Japan', 'keywords': ['tokyo']},
    'берлин': {'name_ru': 'Берлин', 'name_en': 'Berlin', 'lat': 52.5200, 'lon': 13.4050, 'country_ru': 'Германия', 'country_en': 'Germany', 'keywords': ['berlin']},
    'рим': {'name_ru': 'Рим', 'name_en': 'Rome', 'lat': 41.9028, 'lon': 12.4964, 'country_ru': 'Италия', 'country_en': 'Italy', 'keywords': ['rome']},
    'дубай': {'name_ru': 'Дубай', 'name_en': 'Dubai', 'lat': 25.2048, 'lon': 55.2708, 'country_ru': 'ОАЭ', 'country_en': 'UAE', 'keywords': ['dubai']},
    'минск': {'name_ru': 'Минск', 'name_en': 'Minsk', 'lat': 53.9045, 'lon': 27.5615, 'country_ru': 'Беларусь', 'country_en': 'Belarus', 'keywords': ['minsk']},
    'алматы': {'name_ru': 'Алматы', 'name_en': 'Almaty', 'lat': 43.2220, 'lon': 76.8512, 'country_ru': 'Казахстан', 'country_en': 'Kazakhstan', 'keywords': ['almaty', 'алмата']},
    'астана': {'name_ru': 'Астана', 'name_en': 'Astana', 'lat': 51.1694, 'lon': 71.4491, 'country_ru': 'Казахстан', 'country_en': 'Kazakhstan', 'keywords': ['astana']},
    'ташкент': {'name_ru': 'Ташкент', 'name_en': 'Tashkent', 'lat': 41.2995, 'lon': 69.2401, 'country_ru': 'Узбекистан', 'country_en': 'Uzbekistan', 'keywords': ['tashkent']},
    'тбилиси': {'name_ru': 'Тбилиси', 'name_en': 'Tbilisi', 'lat': 41.7151, 'lon': 44.8271, 'country_ru': 'Грузия', 'country_en': 'Georgia', 'keywords': ['tbilisi']},
    'ереван': {'name_ru': 'Ереван', 'name_en': 'Yerevan', 'lat': 40.1792, 'lon': 44.4991, 'country_ru': 'Армения', 'country_en': 'Armenia', 'keywords': ['yerevan']},
    'стамбул': {'name_ru': 'Стамбул', 'name_en': 'Istanbul', 'lat': 41.0082, 'lon': 28.9784, 'country_ru': 'Турция', 'country_en': 'Turkey', 'keywords': ['istanbul']},
    'пекин': {'name_ru': 'Пекин', 'name_en': 'Beijing', 'lat': 39.9042, 'lon': 116.4074, 'country_ru': 'Китай', 'country_en': 'China', 'keywords': ['beijing']},
    'сеул': {'name_ru': 'Сеул', 'name_en': 'Seoul', 'lat': 37.5665, 'lon': 126.9780, 'country_ru': 'Южная Корея', 'country_en': 'South Korea', 'keywords': ['seoul']},
    'бангкок': {'name_ru': 'Бангкок', 'name_en': 'Bangkok', 'lat': 13.7563, 'lon': 100.5018, 'country_ru': 'Таиланд', 'country_en': 'Thailand', 'keywords': ['bangkok']},
    'пхукет': {'name_ru': 'Пхукет', 'name_en': 'Phuket', 'lat': 7.8804, 'lon': 98.3923, 'country_ru': 'Таиланд', 'country_en': 'Thailand', 'keywords': ['phuket']},
    'лос-анджелес': {'name_ru': 'Лос-Анджелес', 'name_en': 'Los Angeles', 'lat': 34.0522, 'lon': -118.2437, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['la', 'los angeles']},
    'вашингтон': {'name_ru': 'Вашингтон', 'name_en': 'Washington D.C.', 'lat': 38.8951, 'lon': -77.0364, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['washington', 'dc', 'd.c.', 'вашингтон']},
    'чикаго': {'name_ru': 'Чикаго', 'name_en': 'Chicago', 'lat': 41.8781, 'lon': -87.6298, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['chicago', 'чикаго']},
    'майами': {'name_ru': 'Майами', 'name_en': 'Miami', 'lat': 25.7617, 'lon': -80.1918, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['miami', 'майами']},
    'сан-франциско': {'name_ru': 'Сан-Франциско', 'name_en': 'San Francisco', 'lat': 37.7749, 'lon': -122.4194, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['sf', 'san francisco', 'сан франциско']},
    'бостон': {'name_ru': 'Бостон', 'name_en': 'Boston', 'lat': 42.3601, 'lon': -71.0589, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['boston', 'бостон']},
    'сиэтл': {'name_ru': 'Сиэтл', 'name_en': 'Seattle', 'lat': 47.6062, 'lon': -122.3321, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['seattle', 'сиэтл']},
    'лас-вегас': {'name_ru': 'Лас-Вегас', 'name_en': 'Las Vegas', 'lat': 36.1716, 'lon': -115.1391, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['vegas', 'las vegas', 'вегас', 'лас вегас']},
    'хьюстон': {'name_ru': 'Хьюстон', 'name_en': 'Houston', 'lat': 29.7604, 'lon': -95.3698, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['houston', 'хьюстон']},
    'даллас': {'name_ru': 'Даллас', 'name_en': 'Dallas', 'lat': 32.7767, 'lon': -96.7970, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['dallas', 'даллас']},
    'атланта': {'name_ru': 'Атланта', 'name_en': 'Atlanta', 'lat': 33.7490, 'lon': -84.3880, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['atlanta', 'атланта']},
    'филадельфия': {'name_ru': 'Филадельфия', 'name_en': 'Philadelphia', 'lat': 39.9526, 'lon': -75.1652, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['philly', 'philadelphia', 'филадельфия']},
    'сан-диего': {'name_ru': 'Сан-Диего', 'name_en': 'San Diego', 'lat': 32.7157, 'lon': -117.1611, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['san diego', 'сан диего']},
    'денвер': {'name_ru': 'Денвер', 'name_en': 'Denver', 'lat': 39.7392, 'lon': -104.9903, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['denver', 'денвер']},
    'остин': {'name_ru': 'Остин', 'name_en': 'Austin', 'lat': 30.2672, 'lon': -97.7431, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['austin', 'остин']},
    'финикс': {'name_ru': 'Финикс', 'name_en': 'Phoenix', 'lat': 33.4484, 'lon': -112.0740, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['phoenix', 'финикс']},
    'орландо': {'name_ru': 'Орландо', 'name_en': 'Orlando', 'lat': 28.5383, 'lon': -81.3792, 'country_ru': 'США', 'country_en': 'USA', 'keywords': ['orlando', 'орландо']},
    'торонто': {'name_ru': 'Торонто', 'name_en': 'Toronto', 'lat': 43.6532, 'lon': -79.3832, 'country_ru': 'Канада', 'country_en': 'Canada', 'keywords': ['toronto', 'торонто']},
    'ванкувер': {'name_ru': 'Ванкувер', 'name_en': 'Vancouver', 'lat': 49.2827, 'lon': -123.1207, 'country_ru': 'Канада', 'country_en': 'Canada', 'keywords': ['vancouver', 'ванкувер']},
    'монреаль': {'name_ru': 'Монреаль', 'name_en': 'Montreal', 'lat': 45.5017, 'lon': -73.5673, 'country_ru': 'Канада', 'country_en': 'Canada', 'keywords': ['montreal', 'монреаль']},
    'сидней': {'name_ru': 'Сидней', 'name_en': 'Sydney', 'lat': -33.8688, 'lon': 151.2093, 'country_ru': 'Австралия', 'country_en': 'Australia', 'keywords': ['sydney', 'сидней']},
    'мельбурн': {'name_ru': 'Мельбурн', 'name_en': 'Melbourne', 'lat': -37.8136, 'lon': 144.9631, 'country_ru': 'Австралия', 'country_en': 'Australia', 'keywords': ['melbourne', 'мельбурн']},
    'мадрид': {'name_ru': 'Мадрид', 'name_en': 'Madrid', 'lat': 40.4168, 'lon': -3.7038, 'country_ru': 'Испания', 'country_en': 'Spain', 'keywords': ['madrid', 'мадрид']},
    'барселона': {'name_ru': 'Барселона', 'name_en': 'Barcelona', 'lat': 41.3879, 'lon': 2.1699, 'country_ru': 'Испания', 'country_en': 'Spain', 'keywords': ['barcelona', 'барселона']},
    'амстердам': {'name_ru': 'Амстердам', 'name_en': 'Amsterdam', 'lat': 52.3676, 'lon': 4.9041, 'country_ru': 'Нидерланды', 'country_en': 'Netherlands', 'keywords': ['amsterdam', 'амстердам']},
    'вена': {'name_ru': 'Вена', 'name_en': 'Vienna', 'lat': 48.2082, 'lon': 16.3738, 'country_ru': 'Австрия', 'country_en': 'Austria', 'keywords': ['vienna', 'вена']},
    'прага': {'name_ru': 'Прага', 'name_en': 'Prague', 'lat': 50.0755, 'lon': 14.4378, 'country_ru': 'Чехия', 'country_en': 'Czech Republic', 'keywords': ['prague', 'прага']},
    'варшава': {'name_ru': 'Варшава', 'name_en': 'Warsaw', 'lat': 52.2297, 'lon': 21.0122, 'country_ru': 'Польша', 'country_en': 'Poland', 'keywords': ['warsaw', 'варшава']},
    'лиссабон': {'name_ru': 'Лиссабон', 'name_en': 'Lisbon', 'lat': 38.7223, 'lon': -9.1393, 'country_ru': 'Португалия', 'country_en': 'Portugal', 'keywords': ['lisbon', 'лиссабон', 'lissabon']}
}

WMO_INFO = {
    0: {'ru': 'Солнечно', 'en': 'Clear', 'icon_day': 'clear-day.svg', 'icon_night': 'clear-night.svg', 'grad': 'clear'},
    1: {'ru': 'Преимущественно ясно', 'en': 'Mainly clear', 'icon_day': 'clear-day.svg', 'icon_night': 'clear-night.svg', 'grad': 'clear'},
    2: {'ru': 'Переменная облачность', 'en': 'Partly cloudy', 'icon_day': 'partly-cloudy-day.svg', 'icon_night': 'partly-cloudy-night.svg', 'grad': 'clouds'},
    3: {'ru': 'Пасмурно', 'en': 'Overcast', 'icon_day': 'cloudy.svg', 'icon_night': 'cloudy.svg', 'grad': 'clouds'},
    45: {'ru': 'Туман', 'en': 'Fog', 'icon_day': 'fog.svg', 'icon_night': 'fog.svg', 'grad': 'fog'},
    48: {'ru': 'Туман с изморозью', 'en': 'Rime fog', 'icon_day': 'fog.svg', 'icon_night': 'fog.svg', 'grad': 'fog'},
    51: {'ru': 'Легкая морось', 'en': 'Light drizzle', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'rain'},
    53: {'ru': 'Умеренная морось', 'en': 'Moderate drizzle', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'rain'},
    55: {'ru': 'Плотная морось', 'en': 'Dense drizzle', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'rain'},
    56: {'ru': 'Ледяная морось', 'en': 'Freezing drizzle', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'rain'},
    57: {'ru': 'Плотная ледяная морось', 'en': 'Freezing drizzle', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'rain'},
    61: {'ru': 'Небольшой дождь', 'en': 'Slight rain', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'rain'},
    63: {'ru': 'Дождь', 'en': 'Rain', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'rain'},
    65: {'ru': 'Сильный дождь', 'en': 'Heavy rain', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'rain'},
    66: {'ru': 'Ледяной дождь', 'en': 'Freezing rain', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'rain'},
    67: {'ru': 'Сильный ледяной дождь', 'en': 'Freezing rain', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'rain'},
    71: {'ru': 'Небольшой снег', 'en': 'Slight snow', 'icon_day': 'snow.svg', 'icon_night': 'snow.svg', 'grad': 'snow'},
    73: {'ru': 'Снегопад', 'en': 'Snow fall', 'icon_day': 'snow.svg', 'icon_night': 'snow.svg', 'grad': 'snow'},
    75: {'ru': 'Сильный снегопад', 'en': 'Heavy snow', 'icon_day': 'snow.svg', 'icon_night': 'snow.svg', 'grad': 'snow'},
    77: {'ru': 'Снежные зерна', 'en': 'Snow grains', 'icon_day': 'snow.svg', 'icon_night': 'snow.svg', 'grad': 'snow'},
    80: {'ru': 'Ливень', 'en': 'Rain showers', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'rain'},
    81: {'ru': 'Умеренный ливень', 'en': 'Moderate showers', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'rain'},
    82: {'ru': 'Сильный ливень', 'en': 'Violent showers', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'rain'},
    85: {'ru': 'Снегопад', 'en': 'Snow showers', 'icon_day': 'snow.svg', 'icon_night': 'snow.svg', 'grad': 'snow'},
    86: {'ru': 'Метель', 'en': 'Heavy snow showers', 'icon_day': 'snow.svg', 'icon_night': 'snow.svg', 'grad': 'snow'},
    95: {'ru': 'Гроза', 'en': 'Thunderstorm', 'icon_day': 'thunderstorm.svg', 'icon_night': 'thunderstorm.svg', 'grad': 'storm'},
    96: {'ru': 'Гроза с градом', 'en': 'Thunderstorm with hail', 'icon_day': 'thunderstorm.svg', 'icon_night': 'thunderstorm.svg', 'grad': 'storm'},
    99: {'ru': 'Сильная гроза с градом', 'en': 'Thunderstorm with heavy hail', 'icon_day': 'thunderstorm.svg', 'icon_night': 'thunderstorm.svg', 'grad': 'storm'}
}


CONDITION_NAMES = {
    0: {
        'ru': ('Солнечно', 'Ясно'),
        'en': ('Sunny', 'Clear'),
        'es': ('Soleado', 'Despejado'),
        'de': ('Sonnig', 'Klar'),
        'fr': ('Ensoleillé', 'Dégagé'),
        'zh': ('晴朗', '晴朗'),
        'ja': ('快晴', '快晴'),
        'it': ('Soleggiato', 'Sereno'),
        'pt': ('Ensolarado', 'Limpo'),
        'tr': ('Güneşli', 'Açık'),
        'uk': ('Сонячно', 'Ясно'),
        'kk': ('Ашық', 'Ашық'),
        'ar': ('مشمس', 'صافٍ'),
    },
    1: {
        'ru': 'Преимущественно ясно', 'en': 'Mainly clear', 'es': 'Mayormente despejado', 'de': 'Überwiegend klar',
        'fr': 'Généralement dégagé', 'zh': '大部晴朗', 'ja': '概ね快晴', 'it': 'Prevalentemente sereno',
        'pt': 'Predominantemente limpo', 'tr': 'Çoğunlukla açık', 'uk': 'Переважно ясно', 'kk': 'Негізінен ашық', 'ar': 'صافٍ في معظمه'
    },
    2: {
        'ru': 'Переменная облачность', 'en': 'Partly cloudy', 'es': 'Parcialmente nublado', 'de': 'Teilweise bewölkt',
        'fr': 'Partiellement nuageux', 'zh': '多云', 'ja': '晴れ時々曇り', 'it': 'Parzialmente nuvoloso',
        'pt': 'Parcialmente nublado', 'tr': 'Parçalı bulutlu', 'uk': 'Мінлива хмарність', 'kk': 'Ауыспалы бұлттылық', 'ar': 'غائم جزئياً'
    },
    3: {
        'ru': 'Пасмурно', 'en': 'Overcast', 'es': 'Nublado', 'de': 'Bedeckt',
        'fr': 'Couvert', 'zh': '阴天', 'ja': '曇り', 'it': 'Coperto',
        'pt': 'Nublado', 'tr': 'Kapalı', 'uk': 'Хмарно', 'kk': 'Бұлтты', 'ar': 'غائم'
    },
    45: {
        'ru': 'Туман', 'en': 'Fog', 'es': 'Niebla', 'de': 'Nebel',
        'fr': 'Brouillard', 'zh': '大雾', 'ja': '霧', 'it': 'Nebbia',
        'pt': 'Nevoeiro', 'tr': 'Sisli', 'uk': 'Туман', 'kk': 'Тұман', 'ar': 'ضباب'
    },
    48: {
        'ru': 'Туман с изморозью', 'en': 'Rime fog', 'es': 'Niebla escarchada', 'de': 'Nebelfrost',
        'fr': 'Brouillard givrant', 'zh': '雾凇', 'ja': '着氷性の霧', 'it': 'Nebbia con brina',
        'pt': 'Nevoeiro com geada', 'tr': 'Kırağı sisi', 'uk': 'Туман з памороззю', 'kk': 'Қыраулы тұман', 'ar': 'ضباب صقيعي'
    },
    51: {
        'ru': 'Легкая морось', 'en': 'Light drizzle', 'es': 'Llovizna ligera', 'de': 'Leichter Nieselregen',
        'fr': 'Bruine légère', 'zh': '微量毛毛雨', 'ja': '弱い霧雨', 'it': 'Pioviggine leggera',
        'pt': 'Garoa leve', 'tr': 'Hafif çiseleme', 'uk': 'Легка мряка', 'kk': 'Жеңіл сіркіреме', 'ar': 'رذاذ خفيف'
    },
    53: {
        'ru': 'Умеренная морось', 'en': 'Moderate drizzle', 'es': 'Llovizna moderada', 'de': 'Mäßiger Nieselregen',
        'fr': 'Bruine modérée', 'zh': '中度毛毛雨', 'ja': '霧雨', 'it': 'Pioviggine moderata',
        'pt': 'Garoa moderada', 'tr': 'Orta çiseleme', 'uk': 'Помірна мряка', 'kk': 'Орташа сіркіреме', 'ar': 'رذاذ معتدل'
    },
    55: {
        'ru': 'Плотная морось', 'en': 'Dense drizzle', 'es': 'Llovizna densa', 'de': 'Dichter Nieselregen',
        'fr': 'Bruine dense', 'zh': '浓密毛毛雨', 'ja': '濃い霧雨', 'it': 'Pioviggine fitta',
        'pt': 'Garoa densa', 'tr': 'Yoğun çiseleme', 'uk': 'Щільна мряка', 'kk': 'Қалың сіркіреме', 'ar': 'رذاذ كثيف'
    },
    56: {
        'ru': 'Ледяная морось', 'en': 'Freezing drizzle', 'es': 'Llovizna helada', 'de': 'Gefrierender Nieselregen',
        'fr': 'Bruine verglaçante', 'zh': '冻毛毛雨', 'ja': '着氷性の霧雨', 'it': 'Pioviggine gelata',
        'pt': 'Garoa congelante', 'tr': 'Dondurucu çiseleme', 'uk': 'Крижана мряка', 'kk': 'Мұзды сіркіреме', 'ar': 'رذاذ متجمد'
    },
    57: {
        'ru': 'Плотная ледяная морось', 'en': 'Freezing drizzle', 'es': 'Llovizna helada densa', 'de': 'Dichter gefrierender Nieselregen',
        'fr': 'Bruine verglaçante dense', 'zh': '浓冻毛毛雨', 'ja': '激しい着氷性の霧雨', 'it': 'Pioviggine gelata fitta',
        'pt': 'Garoa congelante densa', 'tr': 'Yoğun dondurucu çiseleme', 'uk': 'Щільна крижана мряка', 'kk': 'Қалың мұзды сіркіреме', 'ar': 'رذاذ متجمد كثيف'
    },
    61: {
        'ru': 'Небольшой дождь', 'en': 'Slight rain', 'es': 'Lluvia ligera', 'de': 'Leichter Regen',
        'fr': 'Pluie légère', 'zh': '小雨', 'ja': '小雨', 'it': 'Pioggia leggera',
        'pt': 'Chuva fraca', 'tr': 'Hafif yağmur', 'uk': 'Невеликий дощ', 'kk': 'Шамалы жаңбыр', 'ar': 'مطر خفيف'
    },
    63: {
        'ru': 'Дождь', 'en': 'Rain', 'es': 'Lluvia', 'de': 'Regen',
        'fr': 'Pluie', 'zh': '中雨', 'ja': '雨', 'it': 'Pioggia',
        'pt': 'Chuva', 'tr': 'Yağmur', 'uk': 'Дощ', 'kk': 'Жаңбыр', 'ar': 'مطر'
    },
    65: {
        'ru': 'Сильный дождь', 'en': 'Heavy rain', 'es': 'Lluvia fuerte', 'de': 'Starker Regen',
        'fr': 'Forte pluie', 'zh': '大雨', 'ja': '大雨', 'it': 'Pioggia forte',
        'pt': 'Chuva forte', 'tr': 'Kuvvetli yağmur', 'uk': 'Сильний дощ', 'kk': 'Қатты жаңбыр', 'ar': 'مطر غزير'
    },
    66: {
        'ru': 'Ледяной дождь', 'en': 'Freezing rain', 'es': 'Lluvia helada', 'de': 'Gefrierender Regen',
        'fr': 'Pluie verglaçante', 'zh': '冻雨', 'ja': '着氷性の雨', 'it': 'Pioggia congelantesi',
        'pt': 'Chuva congelante', 'tr': 'Dondurucu yağmur', 'uk': 'Крижаний дощ', 'kk': 'Мұзды жаңбыр', 'ar': 'مطر متجمد'
    },
    67: {
        'ru': 'Сильный ледяной дождь', 'en': 'Freezing rain', 'es': 'Lluvia helada fuerte', 'de': 'Starker gefrierender Regen',
        'fr': 'Forte pluie verglaçante', 'zh': '暴冻雨', 'ja': '激しい着氷性の雨', 'it': 'Forte pioggia gelata',
        'pt': 'Chuva congelante forte', 'tr': 'Şiddetli dondurucu yağmur', 'uk': 'Сильний крижаний дощ', 'kk': 'Қатты мұзды жаңбыр', 'ar': 'مطر متجمد غزير'
    },
    71: {
        'ru': 'Небольшой снег', 'en': 'Slight snow', 'es': 'Nieve ligera', 'de': 'Leichter Schneefall',
        'fr': 'Neige légère', 'zh': '小雪', 'ja': '小雪', 'it': 'Neve debole',
        'pt': 'Neve fraca', 'tr': 'Hafif kar', 'uk': 'Невеликий сніг', 'kk': 'Шамалы қар', 'ar': 'ثلج خفيف'
    },
    73: {
        'ru': 'Снегопад', 'en': 'Snow fall', 'es': 'Nevada', 'de': 'Schneefall',
        'fr': 'Chute de neige', 'zh': '降雪', 'ja': '雪', 'it': 'Nevicata',
        'pt': 'Nevasca', 'tr': 'Kar yağışı', 'uk': 'Снігопад', 'kk': 'Қар жауу', 'ar': 'تساقط الثلوج'
    },
    75: {
        'ru': 'Сильный снегопад', 'en': 'Heavy snow', 'es': 'Nieve intensa', 'de': 'Starker Schneefall',
        'fr': 'Forte chute de neige', 'zh': '大雪', 'ja': '大雪', 'it': 'Forte nevicata',
        'pt': 'Neve intensa', 'tr': 'Yoğun kar', 'uk': 'Сильний снігопад', 'kk': 'Қалың қар', 'ar': 'ثلج كثيف'
    },
    77: {
        'ru': 'Снежные зерна', 'en': 'Snow grains', 'es': 'Cinarra', 'de': 'Schneegriesel',
        'fr': 'Neige en grains', 'zh': '雪粒', 'ja': '霧雪', 'it': 'Neve granulosa',
        'pt': 'Grãos de neve', 'tr': 'Kar taneleri', 'uk': 'Снігові зерна', 'kk': 'Қар түйіршіктері', 'ar': 'حبيبات ثلجية'
    },
    80: {
        'ru': 'Ливень', 'en': 'Rain showers', 'es': 'Chubasco', 'de': 'Regenschauer',
        'fr': 'Averses de pluie', 'zh': '阵雨', 'ja': 'にわか雨', 'it': 'Rovescio di pioggia',
        'pt': 'Pancadas de chuva', 'tr': 'Sağanak yağış', 'uk': 'Злива', 'kk': 'Нөсер', 'ar': 'زخات مطر'
    },
    81: {
        'ru': 'Умеренный ливень', 'en': 'Moderate showers', 'es': 'Chubasco moderado', 'de': 'Mäßige Regenschauer',
        'fr': 'Averses modérées', 'zh': '中度阵雨', 'ja': '中程度のにわか雨', 'it': 'Rovesci moderati',
        'pt': 'Pancadas moderadas', 'tr': 'Orta şiddette sağanak', 'uk': 'Помірна злива', 'kk': 'Орташа нөсер', 'ar': 'زخات مطر معتدلة'
    },
    82: {
        'ru': 'Сильный ливень', 'en': 'Violent showers', 'es': 'Chubasco violento', 'de': 'Heftige Schauer',
        'fr': 'Violentes averses', 'zh': '暴雨', 'ja': '激しいにわか雨', 'it': 'Forti rovesci',
        'pt': 'Pancadas violentas', 'tr': 'Şiddetli sağanak', 'uk': 'Сильна злива', 'kk': 'Қатты нөсер', 'ar': 'زخات مطر عنيفة'
    },
    85: {
        'ru': 'Снегопад', 'en': 'Snow showers', 'es': 'Chubasco de nieve', 'de': 'Schneeschauer',
        'fr': 'Averses de neige', 'zh': '阵雪', 'ja': 'にわか雪', 'it': 'Rovesci di neve',
        'pt': 'Pancadas de neve', 'tr': 'Kar sağanağı', 'uk': 'Снігові зливи', 'kk': 'Қарлы нөсер', 'ar': 'زخات ثلجية'
    },
    86: {
        'ru': 'Метель', 'en': 'Heavy snow showers', 'es': 'Nevada fuerte', 'de': 'Starke Schneeschauer',
        'fr': 'Fortes averses de neige', 'zh': '暴雪', 'ja': '激しいにわか雪', 'it': 'Forti rovesci di neve',
        'pt': 'Pancadas de neve fortes', 'tr': 'Yoğun kar sağanağı', 'uk': 'Хуртовина', 'kk': 'Бұрқасын', 'ar': 'عاصفة ثلجية'
    },
    95: {
        'ru': 'Гроза', 'en': 'Thunderstorm', 'es': 'Tormenta', 'de': 'Gewitter',
        'fr': 'Orage', 'zh': '雷暴', 'ja': '雷雨', 'it': 'Temporale',
        'pt': 'Trovoada', 'tr': 'Gök gürültülü fırtına', 'uk': 'Гроза', 'kk': 'Найзағай', 'ar': 'عاصفة رعدية'
    },
    96: {
        'ru': 'Гроза с градом', 'en': 'Thunderstorm with hail', 'es': 'Tormenta con granizo', 'de': 'Gewitter mit Hagel',
        'fr': 'Orage avec grêle', 'zh': '雷暴伴有冰雹', 'ja': '雹を伴う雷雨', 'it': 'Temporale con grandine',
        'pt': 'Trovoada com granizo', 'tr': 'Dolu fırtınası', 'uk': 'Гроза з градом', 'kk': 'Бұршақты найзағай', 'ar': 'عاصفة رعدية مع بَرَد'
    },
    99: {
        'ru': 'Сильная гроза с градом', 'en': 'Thunderstorm with heavy hail', 'es': 'Tormenta fuerte con granizo', 'de': 'Schweres Gewitter mit Hagel',
        'fr': 'Orage violent avec grêle', 'zh': '强雷暴伴有冰雹', 'ja': '激しい雹を伴う雷雨', 'it': 'Forte temporale con grandine',
        'pt': 'Trovoada violenta com granizo', 'tr': 'Şiddetli dolulu fırtına', 'uk': 'Сильна гроза з градом', 'kk': 'Қатты бұршақты найзағай', 'ar': 'عاصفة رعدية شديدة مع بَرَد'
    }
}

def get_condition_text(code: int, lang: str = 'en', is_day: bool = True) -> str:
    if not lang:
        lang = 'en'
    data = CONDITION_NAMES.get(code, CONDITION_NAMES[0])
    val = data.get(lang, data.get('en', 'Clear'))
    if isinstance(val, tuple):
        return val[0] if is_day else val[1]
    return val

FALLBACK_NEWYORK = {
    'name_ru': 'Нью-Йорк',
    'name_en': 'New York',
    'country_ru': 'США',
    'country_en': 'USA',
    'city_name': 'New York',
    'country': 'USA',
    'lat': 40.7128,
    'lon': -74.0060,
    'temp': 24,
    'feels_like': 24,
    'humidity': 55,
    'wind_speed': 5.2,
    'wind_gusts': 6.0,
    'pressure_mm': 762,
    'dew_point': 12,
    'wind_direction': 225,
    'wind_cardinal': 'ЮЗ',
    'wind_desc': 'Юго-западный ветер',
    'feels_like_desc': 'Похоже на фактическую температуру.',
    'avg_diff_str': '+1°',
    'avg_norm_max': 23,
    'avg_desc': 'выше средней макс. температуры 23° сегодня.',
    'uv_index': 4.0,
    'uv_level': 'Умеренный',
    'uv_desc': 'Умеренный уровень на протяжении остальной части дня.',
    'visibility_km': 10,
    'visibility_desc': 'Отличная видимость.',
    'precipitation': 0.0,
    'precipitation_sum': 0.0,
    'precip_desc': 'Осадки не ожидаются.',
    'sunrise_str': '05:45',
    'sunset_str': '19:42',
    'pressure_desc': 'Нормальное давление.',
    'is_day': 1,
    'weather_code': 0,
    'condition_text': 'Солнечно',
    'temp_min': 9,
    'temp_max': 25,
    'grad_type': 'clear',
    'time_of_day': 'day',
    'grad_class': 'weather-grad-clear-day',
    'bg_class': 'weather-bg-clear-day',
    'icon_name': 'clear-day.svg',
    'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg'),
    'summary': 'Порывы ветра до 6 м/с. Солнечно до конца дня.',
    'overall_min': 8,
    'overall_max': 28,
    'hourly': [
        {'time': 'Сейчас', 'temp': 24, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
        {'time': '16', 'temp': 25, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
        {'time': '17', 'temp': 25, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
        {'time': '18', 'temp': 24, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
        {'time': '19', 'temp': 22, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
        {'time': '20', 'temp': 20, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-night.svg')},
        {'time': '21', 'temp': 19, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-night.svg')},
        {'time': '22', 'temp': 18, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-night.svg')},
    ],
    'daily': [
        {'day': 'Сегодня', 'min': 9, 'max': 25, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
        {'day': 'Ср', 'min': 8, 'max': 27, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
        {'day': 'Чт', 'min': 9, 'max': 28, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
        {'day': 'Пт', 'min': 11, 'max': 26, 'code': 2, 'icon_file': os.path.join(ICONS_DIR, 'partly-cloudy-day.svg')},
        {'day': 'Сб', 'min': 14, 'max': 24, 'code': 61, 'icon_file': os.path.join(ICONS_DIR, 'rain.svg')},
        {'day': 'Вс', 'min': 13, 'max': 22, 'code': 3, 'icon_file': os.path.join(ICONS_DIR, 'cloudy.svg')},
        {'day': 'Пн', 'min': 12, 'max': 23, 'code': 1, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
        {'day': 'Вт', 'min': 13, 'max': 25, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
        {'day': 'Ср', 'min': 14, 'max': 26, 'code': 2, 'icon_file': os.path.join(ICONS_DIR, 'partly-cloudy-day.svg')},
        {'day': 'Чт', 'min': 15, 'max': 25, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
    ],
    'cached_at': time.time()
}

FALLBACK_NOVOKUZNETSK = {
    'name_ru': 'Новокузнецк',
    'name_en': 'Novokuznetsk',
    'country_ru': 'Россия',
    'country_en': 'Russia',
    'city_name': 'Novokuznetsk',
    'country': 'Russia',
    'lat': 53.7557,
    'lon': 87.1099,
    'temp': 15,
    'feels_like': 14,
    'humidity': 72,
    'wind_speed': 7.5,
    'wind_gusts': 9.0,
    'pressure_mm': 750,
    'is_day': 0,
    'weather_code': 0,
    'condition_text': 'Ясно',
    'temp_min': 7,
    'temp_max': 23,
    'grad_type': 'clear',
    'time_of_day': 'night',
    'grad_class': 'weather-grad-clear-night',
    'bg_class': 'weather-bg-clear-night',
    'icon_name': 'clear-night.svg',
    'icon_file': os.path.join(ICONS_DIR, 'clear-night.svg'),
    'summary': 'Порывы ветра до 9 м/с. Ясно до утра.',
    'overall_min': 6,
    'overall_max': 25,
    'hourly': [
        {'time': 'Сейчас', 'temp': 15, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-night.svg')},
        {'time': '01', 'temp': 14, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-night.svg')},
        {'time': '02', 'temp': 13, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-night.svg')},
        {'time': '03', 'temp': 12, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-night.svg')},
        {'time': '04', 'temp': 11, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-night.svg')},
        {'time': '05', 'temp': 11, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-night.svg')},
        {'time': '06', 'temp': 12, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
        {'time': '07', 'temp': 14, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
    ],
    'daily': [
        {'day': 'Сегодня', 'min': 7, 'max': 23, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-night.svg')},
        {'day': 'Ср', 'min': 8, 'max': 22, 'code': 2, 'icon_file': os.path.join(ICONS_DIR, 'partly-cloudy-day.svg')},
        {'day': 'Чт', 'min': 9, 'max': 24, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
        {'day': 'Пт', 'min': 10, 'max': 25, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
        {'day': 'Сб', 'min': 11, 'max': 21, 'code': 61, 'icon_file': os.path.join(ICONS_DIR, 'rain.svg')},
        {'day': 'Вс', 'min': 9, 'max': 19, 'code': 3, 'icon_file': os.path.join(ICONS_DIR, 'cloudy.svg')},
        {'day': 'Пн', 'min': 8, 'max': 20, 'code': 1, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
    ],
    'cached_at': time.time()
}


WEEKDAY_NAMES = {
    'ru': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
    'en': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    'es': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
    'de': ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'],
    'fr': ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
    'zh': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    'ja': ['月', '火', '水', '木', '金', '土', '日'],
    'it': ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom'],
    'pt': ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'],
    'tr': ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'],
    'uk': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд'],
    'kk': ['Дс', 'Сс', 'Ср', 'Бс', 'Жм', 'Сб', 'Жс'],
    'ar': ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد'],
}


def calculate_moon_phase(dt=None) -> dict:
    if dt is None:
        dt = datetime.now(timezone.utc)
    ref_new_moon = datetime(2024, 1, 11, 11, 57, tzinfo=timezone.utc)
    synodic_month = 29.53058867
    diff_days = (dt - ref_new_moon).total_seconds() / 86400.0
    cycles = diff_days / synodic_month
    cycle_frac = cycles - math.floor(cycles)
    age_days = cycle_frac * synodic_month
    illumination = 0.5 * (1.0 - math.cos(2 * math.pi * cycle_frac)) * 100.0
    if cycle_frac < 0.5:
        days_to_full = (0.5 - cycle_frac) * synodic_month
    else:
        days_to_full = (1.5 - cycle_frac) * synodic_month

    if cycle_frac < 0.03 or cycle_frac >= 0.97:
        p_ru, p_en = 'Новолуние', 'New Moon'
    elif cycle_frac < 0.22:
        p_ru, p_en = 'Молодая луна', 'Waxing Crescent'
    elif cycle_frac < 0.28:
        p_ru, p_en = 'Первая четверть', 'First Quarter'
    elif cycle_frac < 0.47:
        p_ru, p_en = 'Прибывающая луна', 'Waxing Gibbous'
    elif cycle_frac < 0.53:
        p_ru, p_en = 'Полнолуние', 'Full Moon'
    elif cycle_frac < 0.72:
        p_ru, p_en = 'Убывающая луна', 'Waning Gibbous'
    elif cycle_frac < 0.78:
        p_ru, p_en = 'Последняя четверть', 'Last Quarter'
    else:
        p_ru, p_en = 'Старая луна', 'Waning Crescent'

    return {
        'cycle_fraction': cycle_frac,
        'age_days': round(age_days, 1),
        'illumination': round(illumination),
        'days_to_full': max(0, round(days_to_full)),
        'phase_name': p_ru,
        'phase_name_en': p_en
    }

def get_wind_direction_info(deg: float, lang: str = 'ru') -> tuple[str, str]:
    deg = (float(deg) % 360 + 360) % 360
    directions_ru = [
        ('С', 'Северный ветер'),
        ('СВ', 'Северо-восточный ветер'),
        ('В', 'Восточный ветер'),
        ('ЮВ', 'Юго-восточный ветер'),
        ('Ю', 'Южный ветер'),
        ('ЮЗ', 'Юго-западный ветер'),
        ('З', 'Западный ветер'),
        ('СЗ', 'Северо-западный ветер'),
    ]
    directions_en = [
        ('N', 'North wind'),
        ('NE', 'Northeast wind'),
        ('E', 'East wind'),
        ('SE', 'Southeast wind'),
        ('S', 'South wind'),
        ('SW', 'Southwest wind'),
        ('W', 'West wind'),
        ('NW', 'Northwest wind'),
    ]
    dirs = directions_ru if lang == 'ru' else directions_en
    idx = int((deg + 22.5) // 45) % 8
    return dirs[idx][0], dirs[idx][1]

def get_weekday_name(weekday_idx: int, lang: str = 'en') -> str:
    if not lang:
        lang = 'en'
    names = WEEKDAY_NAMES.get(lang, WEEKDAY_NAMES.get('en', ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']))
    return names[weekday_idx % 7]

def get_fallback_data(city_key: str = 'newyork', lang: str = 'en') -> dict:
    import copy
    from datetime import datetime
    base = FALLBACK_NEWYORK if city_key == 'newyork' else FALLBACK_NOVOKUZNETSK
    data = copy.deepcopy(base)
    is_ru = (lang == 'ru')
    data['city_name'] = data['name_ru'] if is_ru else data['name_en']
    data['country'] = data['country_ru'] if is_ru else data['country_en']
    w_code = data.get('weather_code', 0)
    is_day = data.get('is_day', 1)
    data['condition_text'] = get_condition_text(w_code, lang=lang, is_day=(is_day == 1))
    
    today_w = datetime.now().weekday()
    for i, d in enumerate(data.get('daily', [])):
        d['weekday_idx'] = (today_w + i) % 7
        if i == 0:
            d['day'] = t('weather_today')
        else:
            d['day'] = get_weekday_name(d['weekday_idx'], lang=lang)
            
    if data.get('hourly'):
        for idx, h in enumerate(data.get('hourly', [])):
            if idx == 0:
                h['time'] = t('weather_now')
                h['is_now'] = True
            else:
                h['is_now'] = False
                
    max_gust = data.get('wind_gusts', 6)
    if is_day and w_code in (0, 1):
        data['summary'] = t('weather_summary_clear_day', gust=max_gust)
    elif not is_day and w_code in (0, 1):
        data['summary'] = t('weather_summary_clear_night', gust=max_gust)
    else:
        data['summary'] = t('weather_summary_generic', gust=max_gust, condition=data['condition_text'])
        
    data['moon_phase'] = calculate_moon_phase()
    return data

WEATHER_PREFIXES = [
    'погода в городе ', 'погода в г. ', 'погода в г ', 'погода в ', 'погода во ', 'погода на ', 'погода ',
    'прогноз погоды в ', 'прогноз в ', 'прогноз погоды ', 'прогноз ',
    'температура в ', 'температура ',
    'weather in ', 'weather for ', 'weather at ', 'weather ',
    'forecast in ', 'forecast for ', 'forecast '
]

class WeatherProvider(BaseProvider):
    def __init__(self, history_manager=None, config_manager=None):
        super().__init__(history_manager)
        self.config_manager = config_manager
        self.cache_dir = CACHE_DIR
        self.cache_file = CACHE_FILE
        self._cache = {'geocache': {}, 'forecasts': {}}
        self._in_flight = set()
        self._lock = threading.Lock()
        self.on_data_updated = None
        
        self._load_cache()
        if '40.7128,-74.0060' not in self._cache['forecasts']:
            self._cache['forecasts']['40.7128,-74.0060'] = FALLBACK_NEWYORK.copy()
        if '53.7557,87.1099' not in self._cache['forecasts']:
            self._cache['forecasts']['53.7557,87.1099'] = FALLBACK_NOVOKUZNETSK.copy()
            
        threading.Thread(target=self._initial_refresh, daemon=True).start()

    def _get_default_city_name(self) -> str:
        if self.config_manager:
            return self.config_manager.get('weather_default_city', 'Нью-Йорк')
        return 'Нью-Йорк'

    def _load_cache(self):
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                    if 'geocache' not in self._cache:
                        self._cache['geocache'] = {}
                    if 'forecasts' not in self._cache:
                        self._cache['forecasts'] = {}
                    # Purge outdated cache lacking stage 2 attributes
                    to_remove = [k for k, v in self._cache['forecasts'].items() if not isinstance(v, dict) or 'uv_index' not in v]
                    for k in to_remove:
                        del self._cache['forecasts'][k]
        except Exception as e:
            print(f'[WeatherProvider] Error loading cache: {e}')

    def _save_cache(self):
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f'[WeatherProvider] Error saving cache: {e}')

    def _initial_refresh(self):
        default_name = self._get_default_city_name().lower().strip()
        info = self._resolve_city_info(default_name)
        if info:
            self._fetch_forecast_sync(info.get('lat'), info.get('lon'), info)
        for c in ['нью-йорк', 'москва', 'новокузнецк', 'санкт-петербург']:
            c_info = MAJOR_CITIES.get(c)
            if c_info:
                time.sleep(0.15)
                self._fetch_forecast_sync(c_info['lat'], c_info['lon'], c_info)

    def _resolve_city_info(self, query_city: str) -> dict | None:
        q = query_city.lower().strip()
        if not q:
            return None
        
        if q in MAJOR_CITIES:
            return MAJOR_CITIES[q]
            
        for key, data in MAJOR_CITIES.items():
            if q == data.get('name_ru', '').lower() or q == data.get('name_en', '').lower():
                return data
            for kw in data.get('keywords', []):
                if q == kw.lower():
                    return data

        for key, data in MAJOR_CITIES.items():
            candidates = [key, data.get('name_ru', '').lower(), data.get('name_en', '').lower()] + [kw.lower() for kw in data.get('keywords', [])]
            for cand in candidates:
                if not cand:
                    continue
                stem = cand[:-1] if cand[-1] in ('а', 'я', 'ь', 'й', 'е', 'о', 'ы', 'и') else cand
                min_len = 2 if len(cand) <= 3 else 3
                if len(stem) >= min_len and (q.startswith(stem) or stem.startswith(q)):
                    return data

        with self._lock:
            if q in self._cache['geocache']:
                return self._cache['geocache'][q]
            for c_q, info in self._cache['geocache'].items():
                if not isinstance(info, dict):
                    continue
                if q == info.get('name_ru', '').lower() or q == info.get('name_en', '').lower():
                    return info
                for cand in [c_q, info.get('name_ru', '').lower(), info.get('name_en', '').lower()]:
                    if cand and len(cand) >= 3 and (cand.startswith(q) or q.startswith(cand)):
                        return info

        if len(q) >= 3 and q not in self._in_flight:
            self._in_flight.add(q)
            threading.Thread(target=self._geocode_bg, args=(q,), daemon=True).start()

        return None

    def _geocode_bg(self, query_city: str):
        try:
            url = f'https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(query_city)}&count=1&language=ru&format=json'
            req = urllib.request.Request(url, headers={'User-Agent': 'EchoSearch/1.0'})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                results = data.get('results', [])
                if results:
                    first = results[0]
                    city_id = first.get('id')
                    name_ru = first.get('name')
                    country_ru = first.get('country', '')
                    name_en = name_ru
                    country_en = country_ru

                    if city_id:
                        try:
                            en_url = f'https://geocoding-api.open-meteo.com/v1/get?id={city_id}'
                            en_req = urllib.request.Request(en_url, headers={'User-Agent': 'EchoSearch/1.0'})
                            with urllib.request.urlopen(en_req, timeout=2.5) as en_resp:
                                en_data = json.loads(en_resp.read().decode('utf-8'))
                                if en_data.get('name'):
                                    name_en = en_data.get('name')
                                if en_data.get('country'):
                                    country_en = en_data.get('country')
                        except Exception as ex_en:
                            print(f'[WeatherProvider] Error fetching EN name for {city_id}: {ex_en}')

                    info = {
                        'name_ru': name_ru,
                        'name_en': name_en,
                        'lat': first.get('latitude'),
                        'lon': first.get('longitude'),
                        'country_ru': country_ru,
                        'country_en': country_en,
                        'keywords': []
                    }
                    with self._lock:
                        q_clean = query_city.lower().strip()
                        self._cache['geocache'][q_clean] = info
                        if name_ru:
                            self._cache['geocache'][name_ru.lower().strip()] = info
                        if name_en:
                            self._cache['geocache'][name_en.lower().strip()] = info
                        self._save_cache()
                    self._fetch_forecast_sync(info['lat'], info['lon'], info)
                    if callable(getattr(self, 'on_data_updated', None)):
                        try:
                            from gi.repository import GLib
                            GLib.idle_add(self.on_data_updated)
                        except Exception:
                            try:
                                self.on_data_updated()
                            except Exception:
                                pass
        except Exception as e:
            print(f'[WeatherProvider] Geocode error for {query_city}: {e}')
        finally:
            self._in_flight.discard(query_city)

    def _fetch_forecast_sync(self, lat: float, lon: float, city_info: dict) -> dict | None:
        cache_key = f'{lat:.4f},{lon:.4f}'
        try:
            url = (
                f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}'
                f'&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,weather_code,wind_speed_10m,wind_direction_10m,wind_gusts_10m,surface_pressure,dew_point_2m,precipitation,uv_index,visibility'
                f'&hourly=temperature_2m,weather_code,wind_gusts_10m'
                f'&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max,precipitation_sum,precipitation_probability_max'
                f'&timezone=auto&forecast_days=10'
            )
            req = urllib.request.Request(url, headers={'User-Agent': 'EchoSearch/1.0'})
            with urllib.request.urlopen(req, timeout=7.0) as resp:
                raw = json.loads(resp.read().decode('utf-8'))
                current = raw.get('current', {})
                hourly = raw.get('hourly', {})
                daily = raw.get('daily', {})
                
                temp = round(current.get('temperature_2m', 0))
                feels_like = round(current.get('apparent_temperature', temp))
                humidity = round(current.get('relative_humidity_2m', 0))
                dew_point = round(current.get('dew_point_2m', temp - ((100 - max(0, min(100, humidity))) / 5)))
                wind = round(current.get('wind_speed_10m', 0), 1)
                wind_dir = current.get('wind_direction_10m', 0)
                
                press_hpa = current.get('surface_pressure', 1013)
                press_mm = round(press_hpa * 0.750062)
                
                uv_index = float(current.get('uv_index', (daily.get('uv_index_max', [0])[0] if daily.get('uv_index_max') else 0)))
                visibility_m = current.get('visibility', 10000.0)
                vis_km = round(visibility_m / 1000.0)
                
                precipitation = round(current.get('precipitation', 0.0), 1)
                precip_sum = round(daily.get('precipitation_sum', [0.0])[0] if daily.get('precipitation_sum') else 0.0, 1)
                
                sr_list = daily.get('sunrise', [])
                ss_list = daily.get('sunset', [])
                sr_raw = sr_list[0] if sr_list else ''
                ss_raw = ss_list[0] if ss_list else ''
                sunrise_str = sr_raw.split('T')[-1][:5] if 'T' in sr_raw else sr_raw
                sunset_str = ss_raw.split('T')[-1][:5] if 'T' in ss_raw else ss_raw
                
                is_day = current.get('is_day', 1)
                w_code = current.get('weather_code', 0)
                
                w_info = WMO_INFO.get(w_code, WMO_INFO[0])
                lang = get_current_language()
                is_ru = (lang == 'ru')
                cond_text = get_condition_text(w_code, lang=lang, is_day=(is_day == 1))
                icon_name = w_info['icon_day'] if is_day else w_info['icon_night']
                grad_type = w_info['grad']
                time_of_day = 'day' if is_day else 'night'
                grad_class = f'weather-grad-{grad_type}-{time_of_day}'
                bg_class = f'weather-bg-{grad_type}-{time_of_day}'
                
                max_list = daily.get('temperature_2m_max', [temp])
                min_list = daily.get('temperature_2m_min', [temp])
                t_max = round(max_list[0]) if max_list else temp
                t_min = round(min_list[0]) if min_list else temp
                
                # Wind description
                wind_cardinal, wind_desc = get_wind_direction_info(wind_dir, lang=lang)
                
                # Feels like description
                if is_ru:
                    if humidity >= 65 and feels_like > temp:
                        feels_like_desc = "Из-за влажности кажется, что сейчас теплее."
                    elif wind >= 15 and feels_like < temp:
                        feels_like_desc = "Из-за ветра кажется, что сейчас прохладнее."
                    elif feels_like < temp:
                        feels_like_desc = "Кажется прохладнее фактической температуры."
                    elif feels_like > temp:
                        feels_like_desc = "Кажется теплее фактической температуры."
                    else:
                        feels_like_desc = "Похоже на фактическую температуру."
                else:
                    if humidity >= 65 and feels_like > temp:
                        feels_like_desc = "Humidity makes it feel warmer."
                    elif wind >= 15 and feels_like < temp:
                        feels_like_desc = "Wind makes it feel cooler."
                    elif feels_like < temp:
                        feels_like_desc = "Feels cooler than actual temperature."
                    elif feels_like > temp:
                        feels_like_desc = "Feels warmer than actual temperature."
                    else:
                        feels_like_desc = "Similar to actual temperature."

                # Average climate comparison
                d_maxs_all = daily.get('temperature_2m_max', [temp])
                avg_norm_max = round(sum(d_maxs_all) / max(1, len(d_maxs_all)))
                diff_avg = t_max - avg_norm_max
                if diff_avg > 0:
                    avg_diff_str = f"+{diff_avg}°"
                    avg_desc = f"выше средней макс. температуры {avg_norm_max}° сегодня." if is_ru else f"above average high of {avg_norm_max}° today."
                elif diff_avg < 0:
                    avg_diff_str = f"{diff_avg}°"
                    avg_desc = f"ниже средней макс. температуры {avg_norm_max}° сегодня." if is_ru else f"below average high of {avg_norm_max}° today."
                else:
                    avg_diff_str = "0°"
                    avg_desc = f"соответствует средней макс. температуре {avg_norm_max}° сегодня." if is_ru else f"matches average high of {avg_norm_max}° today."

                # UV Index description
                uv_round = round(uv_index)
                if uv_round <= 2:
                    uv_level = "Низкий" if is_ru else "Low"
                    uv_desc = "Низкий уровень на протяжении остальной части дня." if is_ru else "Low levels for the rest of the day."
                elif uv_round <= 5:
                    uv_level = "Умеренный" if is_ru else "Moderate"
                    uv_desc = "Умеренный уровень. Защитите глаза в солнечные часы." if is_ru else "Moderate levels. Use eye protection."
                elif uv_round <= 7:
                    uv_level = "Высокий" if is_ru else "High"
                    uv_desc = "Высокий уровень. Необходима защита от солнца." if is_ru else "High levels. Sun protection needed."
                elif uv_round <= 10:
                    uv_level = "Очень высокий" if is_ru else "Very High"
                    uv_desc = "Очень высокий уровень. Избегайте полуденного солнца." if is_ru else "Very high levels. Avoid midday sun."
                else:
                    uv_level = "Экстремальный" if is_ru else "Extreme"
                    uv_desc = "Экстремальный уровень. Старайтесь оставаться в тени." if is_ru else "Extreme levels. Stay indoors or shaded."

                # Visibility description
                if vis_km >= 10:
                    vis_desc = "Отличная видимость." if is_ru else "Perfect visibility."
                elif vis_km >= 6:
                    vis_desc = "Хорошая видимость." if is_ru else "Good visibility."
                elif vis_km >= 3:
                    vis_desc = "Умеренная видимость." if is_ru else "Moderate visibility."
                else:
                    vis_desc = "Дымка или туман снижают видимость." if is_ru else "Haze or fog reduces visibility."

                # Precipitation description
                if precip_sum > 0 or precipitation > 0:
                    p_amt = precipitation if precipitation > 0 else precip_sum
                    precip_desc = f"Ожидается около {p_amt} мм осадков." if is_ru else f"Expected around {p_amt} mm precipitation."
                else:
                    precip_desc = "В ближайшее время осадков не ожидается." if is_ru else "No precipitation expected in the near future."

                # Pressure description
                if press_mm < 745:
                    press_desc = "Низкое давление." if is_ru else "Low pressure."
                elif press_mm > 765:
                    press_desc = "Высокое давление." if is_ru else "High pressure."
                else:
                    press_desc = "Нормальное давление." if is_ru else "Normal pressure."

                # Moon phase
                moon_data = calculate_moon_phase()

                # Hourly processing (next 8-12 hours)
                h_times = hourly.get('time', [])
                h_temps = hourly.get('temperature_2m', [])
                h_codes = hourly.get('weather_code', [])
                h_gusts = hourly.get('wind_gusts_10m', [])
                
                cur_time_str = current.get('time', '')
                cur_h_idx = 0
                for i, t_str in enumerate(h_times):
                    if t_str >= cur_time_str:
                        cur_h_idx = i
                        break
                        
                hourly_list = []
                max_gust = round(current.get('wind_gusts_10m', wind))
                
                for i in range(cur_h_idx, min(cur_h_idx + 10, len(h_times))):
                    t_str = h_times[i]
                    try:
                        dt = datetime.fromisoformat(t_str)
                        lbl = t('weather_now') if i == cur_h_idx else f'{dt.hour:02d}'
                        h_is_day = 1 if 6 <= dt.hour < 21 else 0
                        h_num = dt.hour
                    except Exception:
                        lbl = f'+{i - cur_h_idx}h'
                        h_is_day = is_day
                        h_num = (12 + i) % 24
                        
                    code_i = h_codes[i] if i < len(h_codes) else w_code
                    w_inf_i = WMO_INFO.get(code_i, WMO_INFO[0])
                    icon_i = w_inf_i['icon_day'] if h_is_day else w_inf_i['icon_night']
                    
                    if i < len(h_gusts) and h_gusts[i] is not None:
                        max_gust = max(max_gust, round(h_gusts[i]))
                        
                    hourly_list.append({
                        'time': lbl,
                        'hour_num': h_num,
                        'is_now': (i == cur_h_idx),
                        'temp': round(h_temps[i]) if i < len(h_temps) else temp,
                        'code': code_i,
                        'icon_name': icon_i,
                        'icon_file': os.path.join(ICONS_DIR, icon_i)
                    })
                    
                # Daily processing (10 days)
                d_times = daily.get('time', [])
                d_codes = daily.get('weather_code', [])
                d_mins = daily.get('temperature_2m_min', [])
                d_maxs = daily.get('temperature_2m_max', [])
                
                daily_list = []
                overall_min = 999
                overall_max = -999
                
                for i in range(len(d_times)):
                    try:
                        dt = datetime.fromisoformat(d_times[i])
                        w_idx = dt.weekday()
                        lbl = t('weather_today') if i == 0 else get_weekday_name(w_idx, lang=lang)
                    except Exception:
                        w_idx = (datetime.now().weekday() + i) % 7
                        lbl = f'Day {i+1}'
                        
                    code_i = d_codes[i] if i < len(d_codes) else w_code
                    w_inf_i = WMO_INFO.get(code_i, WMO_INFO[0])
                    icon_i = w_inf_i['icon_day']
                    
                    t_min_i = round(d_mins[i]) if i < len(d_mins) else temp
                    t_max_i = round(d_maxs[i]) if i < len(d_maxs) else temp
                    
                    overall_min = min(overall_min, t_min_i)
                    overall_max = max(overall_max, t_max_i)
                    
                    daily_list.append({
                        'day': lbl,
                        'weekday_idx': dt.weekday() if 'dt' in locals() else (i % 7),
                        'min': t_min_i,
                        'max': t_max_i,
                        'code': code_i,
                        'icon_name': icon_i,
                        'icon_file': os.path.join(ICONS_DIR, icon_i)
                    })
                    
                if overall_min >= overall_max:
                    overall_min = temp - 5
                    overall_max = temp + 5

                # Intelligent summary
                if is_day and w_code in (0, 1):
                    summary = t('weather_summary_clear_day', gust=max_gust)
                elif not is_day and w_code in (0, 1):
                    summary = t('weather_summary_clear_night', gust=max_gust)
                else:
                    summary = t('weather_summary_generic', gust=max_gust, condition=cond_text)

                city_name = city_info.get('name_ru' if is_ru else 'name_en', city_info.get('name_ru', ''))
                country = city_info.get('country_ru' if is_ru else 'country_en', '')
                
                weather_dict = {
                    'city_name': city_name,
                    'country': country,
                    'lat': lat,
                    'lon': lon,
                    'temp': temp,
                    'feels_like': feels_like,
                    'feels_like_desc': feels_like_desc,
                    'avg_diff_str': avg_diff_str,
                    'avg_norm_max': avg_norm_max,
                    'avg_desc': avg_desc,
                    'humidity': humidity,
                    'dew_point': dew_point,
                    'wind_speed': wind,
                    'wind_gusts': max_gust,
                    'wind_direction': wind_dir,
                    'wind_cardinal': wind_cardinal,
                    'wind_desc': wind_desc,
                    'pressure_mm': press_mm,
                    'pressure_desc': press_desc,
                    'uv_index': uv_index,
                    'uv_level': uv_level,
                    'uv_desc': uv_desc,
                    'visibility_km': vis_km,
                    'visibility_desc': vis_desc,
                    'precipitation': precipitation,
                    'precipitation_sum': precip_sum,
                    'precip_desc': precip_desc,
                    'sunrise_str': sunrise_str,
                    'sunset_str': sunset_str,
                    'moon_phase': moon_data,
                    'is_day': is_day,
                    'weather_code': w_code,
                    'condition_text': cond_text,
                    'temp_min': t_min,
                    'temp_max': t_max,
                    'grad_type': grad_type,
                    'time_of_day': time_of_day,
                    'grad_class': grad_class,
                    'bg_class': bg_class,
                    'icon_name': icon_name,
                    'icon_file': os.path.join(ICONS_DIR, icon_name),
                    'summary': summary,
                    'overall_min': overall_min,
                    'overall_max': overall_max,
                    'hourly': hourly_list,
                    'daily': daily_list,
                    'cached_at': time.time()
                }
                
                with self._lock:
                    self._cache['forecasts'][cache_key] = weather_dict
                    self._save_cache()
                return weather_dict
        except Exception as e:
            print(f'[WeatherProvider] Fetch forecast error for {cache_key}: {e}')
            return None

    def search(self, query: str, limit: int = 5, category_filter: str = None) -> list[SearchResult]:
        if category_filter not in (None, 'All', 'Weather'):
            return []
            
        if not query:
            return []
            
        raw_q = query.lower().strip()
        lang = get_current_language()
        is_ru = (lang == 'ru')
        
        has_weather_prefix = False
        target_city_name = ''
        score = 880
        
        for pref in WEATHER_PREFIXES:
            if raw_q.startswith(pref):
                has_weather_prefix = True
                target_city_name = raw_q[len(pref):].strip()
                break
                
        if not has_weather_prefix:
            if raw_q in ('погода', 'weather', 'прогноз'):
                has_weather_prefix = True
                target_city_name = ''
                
        if not has_weather_prefix:
            if len(raw_q) < 4:
                return []
            if raw_q in MAJOR_CITIES or raw_q in self._cache.get("geocache", {}):
                target_city_name = raw_q
                score = 80
            elif category_filter == "Weather":
                target_city_name = raw_q
                score = 80
            else:
                return []

        if not target_city_name:
            target_city_name = self._get_default_city_name()

        city_info = self._resolve_city_info(target_city_name)
        if not city_info:
            return []

        lat = city_info.get('lat')
        lon = city_info.get('lon')
        if lat is None or lon is None:
            return []

        cache_key = f'{lat:.4f},{lon:.4f}'
        weather_data = None
        
        with self._lock:
            weather_data = self._cache['forecasts'].get(cache_key)

        now = time.time()
        if not weather_data:
            if target_city_name.lower() in ('нью-йорк', 'new york', 'ny', 'нью йорк'):
                weather_data = get_fallback_data('newyork', lang)
            elif target_city_name.lower() in ('новокузнецк', 'novokuznetsk', 'кузня'):
                weather_data = get_fallback_data('novokuznetsk', lang)
            else:
                if cache_key not in self._in_flight:
                    self._in_flight.add(cache_key)
                    threading.Thread(
                        target=self._fetch_and_release,
                        args=(lat, lon, city_info, cache_key),
                        daemon=True
                    ).start()
                city_title = city_info.get('name_ru' if is_ru else 'name_en', target_city_name.capitalize())
                prov_data = {
                    'city_name': city_title,
                    'country': city_info.get('country_ru', ''),
                    'temp': 20,
                    'feels_like': 20,
                    'humidity': 50,
                    'wind_speed': 5,
                    'wind_gusts': 6,
                    'pressure_mm': 755,
                    'dew_point': 10,
                    'feels_like_desc': 'Похоже на фактическую температуру.' if is_ru else 'Similar to actual temperature.',
                    'avg_diff_str': '0°',
                    'avg_desc': 'соответствует норме' if is_ru else 'matches average',
                    'wind_direction': 0,
                    'wind_cardinal': 'С' if is_ru else 'N',
                    'wind_desc': 'Северный ветер' if is_ru else 'North wind',
                    'uv_index': 0.0,
                    'uv_level': 'Низкий' if is_ru else 'Low',
                    'uv_desc': 'Низкий уровень' if is_ru else 'Low levels',
                    'visibility_km': 10,
                    'visibility_desc': 'Отличная видимость.' if is_ru else 'Perfect visibility.',
                    'precipitation': 0.0,
                    'precipitation_sum': 0.0,
                    'precip_desc': 'Осадки не ожидаются.' if is_ru else 'No precipitation expected.',
                    'sunrise_str': '06:00',
                    'sunset_str': '20:00',
                    'pressure_desc': 'Нормальное давление.' if is_ru else 'Normal pressure.',
                    'moon_phase': calculate_moon_phase(),
                    'is_day': 1,
                    'weather_code': 0,
                    'condition_text': 'Загрузка...' if is_ru else 'Loading...',
                    'temp_min': 15,
                    'temp_max': 24,
                    'grad_type': 'clear',
                    'time_of_day': 'day',
                    'grad_class': 'weather-grad-clear-day',
                    'bg_class': 'weather-bg-clear-day',
                    'icon_name': 'clear-day.svg',
                    'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg'),
                    'summary': 'Загрузка прогноза...',
                    'overall_min': 15,
                    'overall_max': 24,
                    'hourly': [],
                    'daily': []
                }
                return [self._create_search_result(prov_data, score)]

        if now - weather_data.get('cached_at', 0) > 1200:
            if cache_key not in self._in_flight:
                self._in_flight.add(cache_key)
                threading.Thread(
                    target=self._fetch_and_release,
                    args=(lat, lon, city_info, cache_key),
                    daemon=True
                ).start()

        w_code = weather_data.get('weather_code', 0)
        is_day = bool(weather_data.get('is_day', 1))
        weather_data['condition_text'] = get_condition_text(w_code, lang=lang, is_day=is_day)
        city_display = city_info.get('name_ru' if is_ru else 'name_en', weather_data.get('city_name', ''))
        weather_data['city_name'] = city_display
        weather_data['name_ru'] = city_info.get('name_ru', city_display)
        weather_data['name_en'] = city_info.get('name_en', city_display)
        country_display = city_info.get('country_ru' if is_ru else 'country_en', weather_data.get('country', ''))
        weather_data['country'] = country_display
        
        max_gust = weather_data.get('wind_gusts', round(weather_data.get('wind_speed', 0)))
        if is_day and w_code in (0, 1):
            weather_data['summary'] = t('weather_summary_clear_day', gust=max_gust)
        elif not is_day and w_code in (0, 1):
            weather_data['summary'] = t('weather_summary_clear_night', gust=max_gust)
        else:
            weather_data['summary'] = t('weather_summary_generic', gust=max_gust, condition=weather_data['condition_text'])

        return [self._create_search_result(weather_data, score)]

    def _fetch_and_release(self, lat: float, lon: float, city_info: dict, cache_key: str):
        try:
            self._fetch_forecast_sync(lat, lon, city_info)
        finally:
            self._in_flight.discard(cache_key)

    def _create_search_result(self, data: dict, score: float) -> SearchResult:
        city_name = data.get('city_name', 'Погода')
        temp = data.get('temp', 0)
        temp_str = f'{temp:+d}°' if temp != 0 else '0°'
        cond_text = data.get('condition_text', 'Ясно')
        t_min = data.get('temp_min', temp)
        t_max = data.get('temp_max', temp)
        
        title = f'{city_name}: {temp_str}'
        feels_like = data.get('feels_like', temp)
        feels_str = f'{feels_like:+d}°' if feels_like != 0 else '0°'
        feels_prefix = t('weather_feels_like_prefix', temp=feels_str)
        subtitle = f'{cond_text} · {feels_prefix} · ↓ {t_min}° ↑ {t_max}°'
        
        icon_file = data.get('icon_file', os.path.join(ICONS_DIR, 'clear-night.svg'))
        
        copy_text = f'{city_name}: {temp_str}, {cond_text} (↓ {t_min}° ↑ {t_max}°)'

        def copy_action():
            try:
                display = Gdk.Display.get_default()
                if display:
                    clipboard = display.get_clipboard()
                    clipboard.set(copy_text)
            except Exception as e:
                print(f'[WeatherProvider] Copy error: {e}')

        res = SearchResult(
            id=f'weather_{city_name}',
            title=title,
            subtitle=subtitle,
            icon=icon_file,
            score=score,
            category='Weather',
            provider='WeatherProvider',
            preview_data=data,
            action_execute=copy_action,
            action_copy=copy_action
        )
        res._action_copy = True
        res.copy_value = copy_text
        return res
