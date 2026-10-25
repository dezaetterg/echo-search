import json
import math
import os
import threading
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from i18n import get_current_language, i18n, t
from logger import get_logger
from providers.base import BaseProvider, SearchResult
from utils import set_clipboard_text

logger = get_logger("weather")

ICONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons', 'weather'))

def convert_temp(celsius: float | int, unit: str = "celsius") -> int:
    if celsius is None:
        return 0
    try:
        val = float(celsius)
        if unit == "fahrenheit":
            return round(val * 1.8 + 32)
        return round(val)
    except Exception:
        return 0

def convert_temp_diff(celsius_diff: float | int, unit: str = "celsius") -> int:
    if celsius_diff is None:
        return 0
    try:
        val = float(celsius_diff)
        if unit == "fahrenheit":
            return round(val * 1.8)
        return round(val)
    except Exception:
        return 0

def format_temp(celsius: float | int, unit: str = "celsius", show_sign: bool = False, show_unit: bool = False) -> str:
    t_val = convert_temp(celsius, unit)
    sign = "+" if show_sign and t_val > 0 else ""
    unit_suffix = ("°C" if unit == "celsius" else "°F") if show_unit else "°"
    return f"{sign}{t_val}{unit_suffix}"

def determine_solar_time_of_day(lat: float, lon: float, utc_dt: datetime = None) -> tuple[str, int]:
    if utc_dt is None:
        utc_dt = datetime.now(timezone.utc)
    elif utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)

    gamma = 2.0 * math.pi / 365.0 * (utc_dt.timetuple().tm_yday - 1 + (utc_dt.hour - 12) / 24.0)
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma) - 0.014615 * math.cos(2*gamma) - 0.040849 * math.sin(2*gamma))
    decl = 0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma) - 0.006758 * math.cos(2*gamma) + 0.000907 * math.sin(2*gamma) - 0.002697 * math.cos(3*gamma) + 0.00148 * math.sin(3*gamma)

    time_offset = eqtime + 4.0 * lon
    t_solar_min = (utc_dt.hour * 60.0 + utc_dt.minute + utc_dt.second / 60.0 + time_offset) % 1440.0
    hour_angle_deg = (t_solar_min - 720.0) / 4.0

    lat_rad = math.radians(lat)
    ha_rad = math.radians(hour_angle_deg)
    sin_elev = math.sin(lat_rad) * math.sin(decl) + math.cos(lat_rad) * math.cos(decl) * math.cos(ha_rad)
    sin_elev = max(-1.0, min(1.0, sin_elev))
    elev_deg = math.degrees(math.asin(sin_elev))

    if elev_deg > 6.0:
        return ("day", 1)
    elif elev_deg >= -6.0:
        return ("dusk", 1 if elev_deg >= 0 else 0)
    else:
        return ("night", 0)

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
    'онтарио': {'name_ru': 'Онтарио', 'name_en': 'Ontario', 'lat': 43.6532, 'lon': -79.3832, 'country_ru': 'Канада', 'country_en': 'Canada', 'keywords': ['ontario']},
    'лондон': {'name_ru': 'Лондон', 'name_en': 'London', 'lat': 51.5074, 'lon': -0.1278, 'country_ru': 'Великобритания', 'country_en': 'UK', 'keywords': ['london']},
    'париж': {'name_ru': 'Париж', 'name_en': 'Paris', 'lat': 48.8566, 'lon': 2.3522, 'country_ru': 'Франция', 'country_en': 'France', 'keywords': ['paris']},
    'токио': {'name_ru': 'Токио', 'name_en': 'Tokyo', 'lat': 35.6762, 'lon': 139.6503, 'country_ru': 'Япония', 'country_en': 'Japan', 'keywords': ['tokyo']},
    'берлин': {'name_ru': 'Берлин', 'name_en': 'Berlin', 'lat': 52.5200, 'lon': 13.4050, 'country_ru': 'Германия', 'country_en': 'Germany', 'keywords': ['berlin']},
    'рим': {'name_ru': 'Рим', 'name_en': 'Rome', 'lat': 41.9028, 'lon': 12.4964, 'country_ru': 'Италия', 'country_en': 'Italy', 'keywords': ['rome']},
    'дубай': {'name_ru': 'Дубай', 'name_en': 'Dubai', 'lat': 25.2048, 'lon': 55.2708, 'country_ru': 'ОАЭ', 'country_en': 'UAE', 'keywords': ['dubai']},
}

def normalize_russian_city_candidates(query_str: str) -> list[str]:
    q = (query_str or "").lower().strip()
    if not q:
        return []
    candidates = [q]
    if q in ("нижнем новгороде", "нижнего новгорода", "нижнем"):
        candidates.append("нижний новгород")
    elif q in ("ростове-на-дону", "ростове на дону", "ростова-на-дону", "ростове", "ростов"):
        candidates.append("ростов-на-дону")
    elif q in ("санкт-петербурге", "петербурге", "питере", "питер", "спб", "петербург"):
        candidates.append("санкт-петербург")
    elif q in ("нью-йорке", "нью йорке", "нью-йорк", "нью йорк"):
        candidates.append("нью-йорк")
    elif q in ("лос-анджелесе", "лос анджелесе"):
        candidates.append("лос-анджелес")
    elif q in ("лас-вегасе", "лас вегасе"):
        candidates.append("лас-вегас")

    if q.endswith("е"):
        stem = q[:-1]
        candidates.extend([stem, stem + "а", stem + "о", stem + "ь", stem + "й"])
    elif q.endswith("и"):
        stem = q[:-1]
        candidates.extend([stem + "ь", stem + "я", stem])
    elif q.endswith("у"):
        stem = q[:-1]
        candidates.append(stem + "а")
    elif q.endswith("ом") or q.endswith("ем"):
        stem = q[:-2]
        candidates.append(stem)
    return list(dict.fromkeys(candidates))

def _is_exact_major_city(query_str: str) -> dict | None:
    q = (query_str or "").lower().strip()
    if not q:
        return None
    candidates = normalize_russian_city_candidates(q)
    for cand in candidates:
        if cand in MAJOR_CITIES:
            return MAJOR_CITIES[cand]
        for k, data in MAJOR_CITIES.items():
            if cand == data.get("name_ru", "").lower() or cand == data.get("name_en", "").lower():
                return data
            for kw in data.get("keywords", []):
                if cand == kw.lower():
                    return data
    return None

WMO_INFO = {
    0: {'ru': 'Солнечно', 'en': 'Clear', 'icon_day': 'clear-day.svg', 'icon_night': 'clear-night.svg', 'grad': 'clear'},
    1: {'ru': 'В основном ясно', 'en': 'Mainly clear', 'icon_day': 'clear-day.svg', 'icon_night': 'clear-night.svg', 'grad': 'clear'},
    2: {'ru': 'В основном облачно', 'en': 'Partly cloudy', 'icon_day': 'partly-cloudy-day.svg', 'icon_night': 'partly-cloudy-night.svg', 'grad': 'clouds'},
    3: {'ru': 'Облачно', 'en': 'Overcast', 'icon_day': 'cloudy.svg', 'icon_night': 'cloudy.svg', 'grad': 'clouds'},
    45: {'ru': 'Туман', 'en': 'Fog', 'icon_day': 'fog.svg', 'icon_night': 'fog.svg', 'grad': 'fog'},
    48: {'ru': 'Туман с изморозью', 'en': 'Rime fog', 'icon_day': 'fog.svg', 'icon_night': 'fog.svg', 'grad': 'fog'},
    51: {'ru': 'Изморось', 'en': 'Light drizzle', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'drizzle'},
    53: {'ru': 'Умеренная изморось', 'en': 'Moderate drizzle', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'drizzle'},
    55: {'ru': 'Плотная изморось', 'en': 'Dense drizzle', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'drizzle'},
    56: {'ru': 'Ледяная изморось', 'en': 'Freezing drizzle', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'drizzle'},
    57: {'ru': 'Плотная ледяная изморось', 'en': 'Freezing drizzle', 'icon_day': 'rain.svg', 'icon_night': 'rain.svg', 'grad': 'drizzle'},
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

WWO_TO_WMO = {
    113: 0, 116: 2, 119: 3, 122: 3, 143: 45, 176: 80, 179: 85, 182: 66,
    185: 56, 200: 95, 227: 73, 230: 86, 248: 45, 260: 48, 263: 51,
    266: 51, 281: 56, 284: 57, 293: 61, 296: 61, 299: 63, 302: 63,
    305: 65, 308: 65, 311: 66, 314: 67, 317: 66, 320: 67, 323: 71,
    326: 71, 329: 73, 332: 73, 335: 75, 338: 75, 350: 77, 353: 80,
    356: 81, 359: 82, 362: 66, 365: 67, 368: 85, 371: 86, 374: 77,
    377: 77, 386: 95, 389: 95, 392: 96, 395: 99
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
    1: {'ru': 'В основном ясно', 'en': 'Mainly clear'},
    2: {'ru': 'В основном облачно', 'en': 'Partly cloudy'},
    3: {'ru': 'Облачно', 'en': 'Overcast'},
    45: {'ru': 'Туман', 'en': 'Fog'},
    48: {'ru': 'Туман с изморозью', 'en': 'Rime fog'},
    51: {'ru': 'Изморось', 'en': 'Light drizzle'},
    53: {'ru': 'Умеренная изморось', 'en': 'Moderate drizzle'},
    55: {'ru': 'Плотная изморось', 'en': 'Dense drizzle'},
    56: {'ru': 'Ледяная изморось', 'en': 'Freezing drizzle'},
    57: {'ru': 'Плотная ледяная изморось', 'en': 'Freezing drizzle'},
    61: {'ru': 'Небольшой дождь', 'en': 'Slight rain'},
    63: {'ru': 'Дождь', 'en': 'Rain'},
    65: {'ru': 'Сильный дождь', 'en': 'Heavy rain'},
    66: {'ru': 'Ледяной дождь', 'en': 'Freezing rain'},
    67: {'ru': 'Сильный ледяной дождь', 'en': 'Freezing rain'},
    71: {'ru': 'Небольшой снег', 'en': 'Slight snow'},
    73: {'ru': 'Снегопад', 'en': 'Snow fall'},
    75: {'ru': 'Сильный снегопад', 'en': 'Heavy snow'},
    77: {'ru': 'Снежные зерна', 'en': 'Snow grains'},
    80: {'ru': 'Ливень', 'en': 'Rain showers'},
    81: {'ru': 'Умеренный ливень', 'en': 'Moderate showers'},
    82: {'ru': 'Сильный ливень', 'en': 'Violent showers'},
    85: {'ru': 'Снегопад', 'en': 'Snow showers'},
    86: {'ru': 'Метель', 'en': 'Heavy snow showers'},
    95: {'ru': 'Гроза', 'en': 'Thunderstorm'},
    96: {'ru': 'Гроза с градом', 'en': 'Thunderstorm with hail'},
    99: {'ru': 'Сильная гроза с градом', 'en': 'Thunderstorm with heavy hail'}
}

def get_condition_text(code: int, lang: str = 'en', is_day: bool = True) -> str:
    if not lang:
        lang = 'en'
    data = CONDITION_NAMES.get(code, CONDITION_NAMES[0])
    val = data.get(lang, data.get('en', 'Clear'))
    if isinstance(val, tuple):
        return val[0] if is_day else val[1]
    return val

WEEKDAY_LETTERS = {
    'ru': ['П', 'В', 'С', 'Ч', 'П', 'С', 'В'],
    'en': ['M', 'T', 'W', 'T', 'F', 'S', 'S'],
    'es': ['L', 'M', 'X', 'J', 'V', 'S', 'D'],
    'de': ['M', 'D', 'M', 'D', 'F', 'S', 'S'],
    'fr': ['L', 'M', 'M', 'J', 'V', 'S', 'D'],
    'zh': ['一', '二', '三', '四', '五', '六', '日'],
    'ja': ['月', '火', '水', '木', '金', '土', '日'],
    'it': ['L', 'M', 'M', 'G', 'V', 'S', 'D'],
    'pt': ['S', 'T', 'Q', 'Q', 'S', 'S', 'D'],
    'tr': ['P', 'S', 'Ç', 'P', 'C', 'C', 'P'],
    'uk': ['П', 'В', 'С', 'Ч', 'П', 'С', 'Н'],
    'kk': ['Д', 'С', 'С', 'Б', 'Ж', 'С', 'Ж'],
    'ar': ['ن', 'ث', 'ر', 'خ', 'ج', 'س', 'ح']
}

WEEKDAY_FULL = {
    'ru': ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'],
    'en': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
    'es': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'],
    'de': ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'],
    'fr': ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'],
    'zh': ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'],
    'ja': ['月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日', '日曜日'],
    'it': ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica'],
    'pt': ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo'],
    'tr': ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar'],
    'uk': ['Понеділок', 'Вівторок', 'Середа', 'Четвер', 'Пʼятниця', 'Субота', 'Неділя'],
    'kk': ['Дүйсенбі', 'Сейсенбі', 'Сәрсенбі', 'Бейсенбі', 'Жұма', 'Сенбі', 'Жексенбі'],
    'ar': ['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
}

MONTH_NAMES_GENITIVE = {
    'ru': ['', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'],
    'en': ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
    'es': ['', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'],
    'de': ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'],
    'fr': ['', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'],
    'zh': ['', '1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
    'ja': ['', '1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
    'it': ['', 'gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'octobre', 'novembre', 'dicembre'],
    'pt': ['', 'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'],
    'tr': ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'],
    'uk': ['', 'січня', 'лютого', 'березня', 'квітня', 'травня', 'червня', 'липня', 'серпня', 'вересня', 'жовтня', 'листопада', 'грудня'],
    'kk': ['', 'қаңтар', 'ақпан', 'наурыз', 'сәуір', 'мамыр', 'маусым', 'шілде', 'тамыз', 'қыркүйек', 'қазан', 'қараша', 'желтоқсан'],
    'ar': ['', 'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
}

def format_full_date(dt: datetime, lang: str = 'en') -> str:
    if not lang or lang not in WEEKDAY_FULL:
        lang = 'en'
    w_idx = dt.weekday()
    w_full = WEEKDAY_FULL.get(lang, WEEKDAY_FULL['en'])[w_idx % 7]
    m_list = MONTH_NAMES_GENITIVE.get(lang, MONTH_NAMES_GENITIVE['en'])
    m_name = m_list[dt.month if 1 <= dt.month <= 12 else 1]

    if lang == 'ru':
        return f"{w_full}, {dt.day} {m_name} {dt.year} г."
    elif lang == 'uk':
        return f"{w_full}, {dt.day} {m_name} {dt.year} р."
    elif lang == 'kk':
        return f"{w_full}, {dt.year} жылғы {dt.day} {m_name}"
    elif lang in ('zh', 'ja'):
        return f"{dt.year}年{m_name}{dt.day}日 {w_full}"
    elif lang in ('es', 'pt'):
        return f"{w_full}, {dt.day} de {m_name} de {dt.year}"
    elif lang == 'de':
        return f"{w_full}, {dt.day}. {m_name} {dt.year}"
    elif lang in ('fr', 'it'):
        return f"{w_full} {dt.day} {m_name} {dt.year}"
    elif lang == 'tr':
        return f"{dt.day} {m_name} {dt.year} {w_full}"
    elif lang == 'ar':
        return f"{w_full}، {dt.day} {m_name} {dt.year}"
    else:
        return f"{w_full}, {m_name} {dt.day}, {dt.year}"

def get_smart_day_summary(
    day_info: dict,
    lang: str = 'en',
    is_today: bool = False,
    temp_unit: str = 'celsius',
    current_temp: int = None
) -> str:
    if not lang:
        lang = get_current_language()

    code = day_info.get('code', day_info.get('weather_code', 0))
    cond_text = get_condition_text(code, lang=lang, is_day=True)

    t_min = convert_temp(day_info.get('min', day_info.get('temp_min', 0)), temp_unit)
    t_max = convert_temp(day_info.get('max', day_info.get('temp_max', 0)), temp_unit)
    app_min = convert_temp(day_info.get('apparent_min', day_info.get('min', 0)), temp_unit)
    app_max = convert_temp(day_info.get('apparent_max', day_info.get('max', 0)), temp_unit)

    if is_today:
        if current_temp is not None:
            now_t = convert_temp(current_temp, temp_unit)
        else:
            now_t = convert_temp(day_info.get('temp', day_info.get('max', 20)), temp_unit)

        hum = day_info.get('humidity', 50)
        wind = day_info.get('wind_speed', 10)
        feels_like = convert_temp(day_info.get('feels_like', now_t), temp_unit)

        if hum >= 65 and feels_like > now_t:
            feels_desc = t('weather_feels_humidity_warmer')
        elif wind >= 15 and feels_like < now_t:
            feels_desc = t('weather_feels_wind_cooler')
        elif feels_like < now_t - 1:
            feels_desc = t('weather_feels_cooler')
        elif feels_like > now_t + 1:
            feels_desc = t('weather_feels_warmer')
        else:
            feels_desc = t('weather_feels_similar')

        s_now = t('weather_summary_now_cond', temp=now_t, cond=cond_text.lower())
        s_range = t('weather_summary_range_today', min=t_min, max=t_max, app_min=app_min, app_max=app_max)
        return f"{s_now} {feels_desc} {s_range}".strip()
    else:
        p_prob = day_info.get('precip_prob_max', day_info.get('precipitation_probability', 0))
        return t('weather_summary_future', cond=cond_text.lower(), min=t_min, max=t_max, app_min=app_min, app_max=app_max, prob=p_prob)

def calculate_moon_phase(dt=None) -> dict:
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    ref_new_moon = datetime(2024, 1, 11, 11, 57, tzinfo=timezone.utc)
    diff_days = (dt - ref_new_moon).total_seconds() / 86400.0
    synodic_month = 29.53058867
    cycle_fraction = (diff_days % synodic_month) / synodic_month
    illumination = (1.0 - math.cos(cycle_fraction * 2 * math.pi)) / 2.0 * 100.0
    phases = [
        (0.0625, "Новолуние", "New Moon"),
        (0.1875, "Молодая луна", "Waxing Crescent"),
        (0.3125, "Первая четверть", "First Quarter"),
        (0.4375, "Прибывающая луна", "Waxing Gibbous"),
        (0.5625, "Полнолуние", "Full Moon"),
        (0.6875, "Убывающая луна", "Waning Gibbous"),
        (0.8125, "Последняя четверть", "Last Quarter"),
        (0.9375, "Старая луна", "Waning Crescent"),
        (1.0, "Новолуние", "New Moon")
    ]
    p_ru, p_en = "Новолуние", "New Moon"
    for threshold, ru_name, en_name in phases:
        if cycle_fraction <= threshold:
            p_ru, p_en = ru_name, en_name
            break
    lang = get_current_language()
    return {
        "cycle_fraction": round(cycle_fraction, 4),
        "illumination": round(illumination, 1),
        "phase_name": p_ru if lang == "ru" else p_en
    }

def calculate_solar_details(lat: float, lon: float, dt: date = None, utc_offset_hours: float = 0.0, is_ru: bool = True) -> dict:
    if dt is None:
        dt = datetime.now().date()
    gamma = 2 * math.pi / 365.0 * (dt.timetuple().tm_yday - 1)
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma))
    decl = 0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma)
    time_offset = eqtime + 4 * lon - 60 * utc_offset_hours
    t_noon_min = 720 - time_offset
    lat_rad = math.radians(lat)
    denom = math.cos(lat_rad) * math.cos(decl)
    cos_ha = (math.sin(math.radians(-0.833)) - math.sin(lat_rad) * math.sin(decl)) / (denom if abs(denom) > 1e-6 else 1e-6)
    ha = math.degrees(math.acos(max(-1.0, min(1.0, cos_ha))))
    sr_min = max(0, min(1440, t_noon_min - ha * 4))
    ss_min = max(0, min(1440, t_noon_min + ha * 4))
    sr_h, sr_m = int(sr_min // 60), int(sr_min % 60)
    ss_h, ss_m = int(ss_min // 60), int(ss_min % 60)
    day_min = int(ss_min - sr_min)
    day_h, day_m = int(day_min // 60), int(day_min % 60)
    return {
        "sunrise": f"{sr_h:02d}:{sr_m:02d}",
        "sunset": f"{ss_h:02d}:{ss_m:02d}",
        "daylight_str": f"{day_h} ч {day_m} мин" if is_ru else f"{day_h} h {day_m} m",
        "curve_points": [(sr_min, 0.0), (t_noon_min, 1.0), (ss_min, 0.0)]
    }

def calculate_detailed_moon(lat: float, lon: float, target_dt: datetime = None, utc_offset_hours: float = 0.0, is_ru: bool = True) -> dict:
    mp = calculate_moon_phase(target_dt)
    frac = mp["cycle_fraction"]
    days_to_full = round(((0.5 - frac) % 1.0) * 29.53)
    days_to_new = round(((1.0 - frac) % 1.0) * 29.53)
    now = datetime.now()
    full_date = now + timedelta(days=days_to_full)
    new_date = now + timedelta(days=days_to_new)
    m_names_ru = ['', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    full_str = f"{full_date.day} {m_names_ru[full_date.month]}" if is_ru else full_date.strftime("%B %d")
    new_str = f"{new_date.day} {m_names_ru[new_date.month]}" if is_ru else new_date.strftime("%B %d")
    return {
        "phase_name": mp["phase_name"],
        "distance_km": 384400,
        "next_full_moon_date_str": full_str,
        "next_new_moon_date_str": new_str
    }

WEATHER_PREFIXES = [
    'погода в городе ', 'погода в г. ', 'погода в г ', 'погода в ', 'погода во ', 'погода на ', 'погода ',
    'прогноз погоды в ', 'прогноз в ', 'прогноз погоды ', 'прогноз ',
    'температура в ', 'температура ',
    'weather in ', 'weather for ', 'weather at ', 'weather ',
    'forecast in ', 'forecast for ', 'forecast '
]

def get_fallback_data(city_key: str = 'newyork', lang: str = 'en') -> dict:
    ck = str(city_key).lower().strip()
    is_ru = (lang == 'ru')

    matched = _is_exact_major_city(ck)
    if matched:
        city_title = matched.get('name_ru' if is_ru else 'name_en', ck.capitalize())
        country = matched.get('country_ru' if is_ru else 'country_en', '')
        lat = matched.get('lat', 55.7520)
        lon = matched.get('lon', 37.6178)
    else:
        city_title = ck.capitalize()
        country = ''
        lat = 55.7520
        lon = 37.6178

    return {
        'name_ru': city_title,
        'name_en': city_title,
        'city_name': city_title,
        'country': country,
        'country_ru': country,
        'country_en': country,
        'lat': lat,
        'lon': lon,
        'temp': 18,
        'feels_like': 17,
        'temp_min': 10,
        'temp_max': 20,
        'humidity': 55,
        'wind_speed': 3.5,
        'wind_gusts': 5.0,
        'pressure': 1015,
        'pressure_mm': 761,
        'precipitation': 0.0,
        'weather_code': 0,
        'is_day': 1,
        'time_of_day': 'day',
        'condition_text': 'Ясно' if is_ru else 'Clear',
        'grad_type': 'clear',
        'grad_class': 'weather-grad-clear-day',
        'bg_class': 'weather-bg-clear-day',
        'icon_name': 'clear-day.svg',
        'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg'),
        'summary': t('weather_summary_clear_day', gust=5),
        'overall_min': 10,
        'overall_max': 20,
        'hourly': [
            {'time': t('weather_now'), 'temp': 18, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
            {'time': '12:00', 'temp': 19, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
            {'time': '15:00', 'temp': 20, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
            {'time': '18:00', 'temp': 17, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
            {'time': '21:00', 'temp': 14, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-night.svg')},
        ],
        'daily': [
            {'day': t('weather_today'), 'min': 10, 'max': 20, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
            {'day': '+1d', 'min': 11, 'max': 21, 'code': 0, 'icon_file': os.path.join(ICONS_DIR, 'clear-day.svg')},
            {'day': '+2d', 'min': 9, 'max': 18, 'code': 2, 'icon_file': os.path.join(ICONS_DIR, 'partly-cloudy-day.svg')},
        ],
        'cached_at': time.time(),
        'forecast_date': datetime.now().strftime('%Y-%m-%d')
    }

class WeatherProvider(BaseProvider):
    def __init__(self, history_manager=None, config_manager=None):
        super().__init__(history_manager)
        self.config_manager = config_manager
        self.on_data_updated = None
        self._lock = threading.Lock()
        self._in_flight = set()

        cache_dir = Path(os.path.expanduser('~/.cache/echo_search'))
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = cache_dir / 'weather_geo_cache.json'
        self._forecast_cache_file = cache_dir / 'weather_forecast_cache.json'

        self.geo_cache = {}
        self._cache = {}
        self._load_cache()
        self._load_forecast_cache()

    def _load_cache(self):
        if self.cache_file and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.geo_cache = dict(list(data.items())[-50:])
            except Exception as e:
                logger.debug(f"Failed to load geo cache: {e}")

    def _save_cache(self):
        if not self.cache_file:
            return
        try:
            items = list(self.geo_cache.items())
            if len(items) > 50:
                self.geo_cache = dict(items[-50:])
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.geo_cache, f, ensure_ascii=False)
        except Exception as e:
            logger.debug(f"Failed to save geo cache: {e}")

    def _load_forecast_cache(self):
        if self._forecast_cache_file and os.path.exists(self._forecast_cache_file):
            try:
                with open(self._forecast_cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            except Exception as e:
                logger.debug(f"Failed to load forecast cache: {e}")

    def _save_forecast_cache(self):
        if not self._forecast_cache_file:
            return
        try:
            with open(self._forecast_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False)
        except Exception as e:
            logger.debug(f"Failed to save forecast cache: {e}")

    def _get_default_city_name(self) -> str:
        if self.config_manager:
            configured = self.config_manager.get('weather_default_city')
            if configured and configured != 'Нью-Йорк':
                return configured
        try:
            tz_path = os.path.realpath('/etc/localtime')
            for city_key, city_data in MAJOR_CITIES.items():
                name_en = city_data.get('name_en', '')
                if name_en and name_en.lower() in tz_path.lower():
                    return city_data.get('name_ru', name_en)
        except Exception:
            pass
        return 'Новокузнецк' if 'Novokuznetsk' in str(os.path.realpath('/etc/localtime')) else 'Москва'

    def _resolve_city_info(self, city_name: str, allow_geocode: bool = True) -> dict | None:
        if not city_name:
            return None
        city_lower = city_name.lower().strip()
        matched = _is_exact_major_city(city_lower)
        if matched:
            return matched
        if city_lower in self.geo_cache:
            return self.geo_cache[city_lower]

        if allow_geocode:
            try:
                url = f"https://wttr.in/{urllib.parse.quote_plus(city_lower)}?format=j1"
                req = urllib.request.Request(url, headers={'User-Agent': 'curl/8.0'})
                with urllib.request.urlopen(req, timeout=2.5) as resp:
                    raw = json.loads(resp.read().decode('utf-8'))
                    area = raw.get('nearest_area', [{}])[0]
                    lat = float(area.get('latitude', 0))
                    lon = float(area.get('longitude', 0))
                    area_name = area.get('areaName', [{}])[0].get('value', city_name.capitalize())
                    country = area.get('country', [{}])[0].get('value', '')
                    info = {
                        'name_ru': area_name,
                        'name_en': area_name,
                        'lat': lat,
                        'lon': lon,
                        'country_ru': country,
                        'country_en': country,
                        'keywords': []
                    }
                    self.geo_cache[city_lower] = info
                    self._save_cache()
                    return info
            except Exception as e:
                logger.debug(f"Geocoding failed for {city_name}: {e}")
        return None

    def _fetch_forecast_wttr(self, lat: float, lon: float, city_info: dict) -> dict | None:
        try:
            url = f"https://wttr.in/{lat:.4f},{lon:.4f}?format=j1"
            req = urllib.request.Request(url, headers={'User-Agent': 'curl/8.0'})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                raw = json.loads(resp.read().decode('utf-8'))

            curr = raw.get('current_condition', [{}])[0]
            weather_days = raw.get('weather', [])
            if not weather_days:
                return None
            day0 = weather_days[0]
            astro0 = day0.get('astronomy', [{}])[0] if day0 else {}

            temp = round(float(curr.get('temp_C', 0)))
            feels_like = round(float(curr.get('FeelsLikeC', temp)))
            humidity = round(float(curr.get('humidity', 0)))
            wind_kmph = float(curr.get('windspeedKmph', 0))
            wind_speed = round(wind_kmph / 3.6, 1)
            wind_gusts = wind_speed
            press_hpa = float(curr.get('pressure', 1013))
            press_mm = round(press_hpa * 0.750062)
            precipitation = float(curr.get('precipMM', 0.0))

            t_max = round(float(day0.get('maxtempC', temp)))
            t_min = round(float(day0.get('mintempC', temp)))

            wwo_code = int(curr.get('weatherCode', 113))
            w_code = WWO_TO_WMO.get(wwo_code, 0)
            w_info = WMO_INFO.get(w_code, WMO_INFO[0])

            tod, is_day_val = determine_solar_time_of_day(lat, lon, datetime.now(timezone.utc))
            is_day = is_day_val
            time_of_day = tod
            icon_name = w_info['icon_day'] if is_day else w_info['icon_night']
            icon_file = os.path.join(ICONS_DIR, icon_name)
            grad_type = w_info['grad']

            lang = get_current_language()
            is_ru = (lang == 'ru')
            cond_text = get_condition_text(w_code, lang=lang, is_day=(is_day == 1))

            hourly_list = []
            for h in day0.get('hourly', []):
                h_time_raw = int(h.get('time', 0))
                h_str = f"{h_time_raw // 100:02d}:00"
                h_code = WWO_TO_WMO.get(int(h.get('weatherCode', 113)), 0)
                h_info = WMO_INFO.get(h_code, WMO_INFO[0])
                h_icon = os.path.join(ICONS_DIR, h_info['icon_day'] if is_day else h_info['icon_night'])
                hourly_list.append({
                    'time': h_str,
                    'temp': round(float(h.get('tempC', temp))),
                    'code': h_code,
                    'icon_file': h_icon
                })

            daily_list = []
            today_w = datetime.now().weekday()
            for idx, d in enumerate(weather_days[:5]):
                d_code = WWO_TO_WMO.get(int(d.get('hourly', [{}])[0].get('weatherCode', 113)), 0)
                d_info = WMO_INFO.get(d_code, WMO_INFO[0])
                d_icon = os.path.join(ICONS_DIR, d_info['icon_day'])
                day_label = t('weather_today') if idx == 0 else WEEKDAY_FULL.get(lang, WEEKDAY_FULL['en'])[(today_w + idx) % 7]
                daily_list.append({
                    'day': day_label,
                    'min': round(float(d.get('mintempC', t_min))),
                    'max': round(float(d.get('maxtempC', t_max))),
                    'code': d_code,
                    'icon_file': d_icon
                })

            city_name = city_info.get('name_ru' if is_ru else 'name_en', city_info.get('name_en', ''))

            return {
                'name_ru': city_info.get('name_ru', city_name),
                'name_en': city_info.get('name_en', city_name),
                'city_name': city_name,
                'country': city_info.get('country_ru' if is_ru else 'country_en', ''),
                'country_ru': city_info.get('country_ru', ''),
                'country_en': city_info.get('country_en', ''),
                'lat': lat,
                'lon': lon,
                'temp': temp,
                'feels_like': feels_like,
                'humidity': humidity,
                'wind_speed': wind_speed,
                'wind_gusts': wind_gusts,
                'pressure': press_hpa,
                'pressure_mm': press_mm,
                'precipitation': precipitation,
                'weather_code': w_code,
                'is_day': is_day,
                'time_of_day': time_of_day,
                'condition_text': cond_text,
                'temp_min': t_min,
                'temp_max': t_max,
                'grad_type': grad_type,
                'grad_class': f"weather-grad-{grad_type}-{time_of_day}",
                'bg_class': f"weather-bg-{grad_type}-{time_of_day}",
                'icon_name': icon_name,
                'icon_file': icon_file,
                'summary': t('weather_summary_clear_day', gust=round(wind_gusts)) if is_day else t('weather_summary_clear_night', gust=round(wind_gusts)),
                'hourly': hourly_list,
                'daily': daily_list,
                'cached_at': time.time(),
                'forecast_date': datetime.now().strftime('%Y-%m-%d')
            }
        except Exception as e:
            logger.warning(f"Fetch forecast error for {lat:.4f},{lon:.4f}: {e}")
            return None

    def _fetch_forecast_sync(self, lat: float, lon: float, city_info: dict) -> dict | None:
        return self._fetch_forecast_wttr(lat, lon, city_info)

    def _fetch_and_release(self, lat: float, lon: float, city_info: dict, cache_key: str):
        try:
            data = self._fetch_forecast_sync(lat, lon, city_info)
            if data:
                with self._lock:
                    self._cache[cache_key] = data
                self._save_forecast_cache()
                if callable(self.on_data_updated):
                    from gi.repository import GLib
                    GLib.idle_add(self.on_data_updated)
        finally:
            with self._lock:
                self._in_flight.discard(cache_key)

    def search(self, query: str, limit: int = 5, category_filter: str = None) -> list[SearchResult]:
        if category_filter not in (None, 'All', 'Weather'):
            return []

        if not query:
            if category_filter == 'Weather':
                has_weather_prefix = True
                target_city_name = ''
                raw_q = ''
            else:
                return []
        else:
            raw_q = query.lower().strip()
            has_weather_prefix = False
            target_city_name = ''

        lang = get_current_language()
        is_ru = (lang == 'ru')
        score = 880

        for pref in WEATHER_PREFIXES:
            if raw_q.startswith(pref):
                has_weather_prefix = True
                target_city_name = raw_q[len(pref):].strip().lstrip(":- ")
                break

        if not has_weather_prefix:
            if raw_q in ('погода', 'weather', 'прогноз'):
                has_weather_prefix = True
                target_city_name = ''

        if not has_weather_prefix:
            if raw_q.startswith(('в ', 'во ')) and len(raw_q) > 3:
                cand_after_prep = raw_q.split(None, 1)[1].strip()
                if _is_exact_major_city(cand_after_prep) is not None:
                    has_weather_prefix = True
                    target_city_name = cand_after_prep

        if not has_weather_prefix:
            if category_filter == "Weather":
                target_city_name = raw_q
                score = 80
            else:
                matched_city = _is_exact_major_city(raw_q)
                if matched_city is not None:
                    target_city_name = raw_q
                    score = 95
                else:
                    return []

        if not target_city_name:
            target_city_name = self._get_default_city_name()

        city_info = self._resolve_city_info(target_city_name, allow_geocode=True)
        if not city_info:
            city_info = {
                'name_ru': target_city_name.capitalize(),
                'name_en': target_city_name.capitalize(),
                'lat': 55.7520,
                'lon': 37.6178,
                'country_ru': '',
                'country_en': '',
                'keywords': []
            }

        lat = city_info.get('lat', 55.7520)
        lon = city_info.get('lon', 37.6178)
        cache_key = f"{lat:.4f},{lon:.4f}"

        weather_data = None
        with self._lock:
            weather_data = self._cache.get(cache_key)

        now = time.time()
        if not weather_data or (now - weather_data.get('cached_at', 0) > 1200):
            if cache_key not in self._in_flight:
                self._in_flight.add(cache_key)
                threading.Thread(
                    target=self._fetch_and_release,
                    args=(lat, lon, city_info, cache_key),
                    daemon=True
                ).start()

        if not weather_data:
            weather_data = get_fallback_data(target_city_name, lang)
            city_title = city_info.get('name_ru' if is_ru else 'name_en', target_city_name.capitalize())
            weather_data['city_name'] = city_title
            weather_data['name_ru'] = city_info.get('name_ru', city_title)
            weather_data['name_en'] = city_info.get('name_en', city_title)
            weather_data['lat'] = lat
            weather_data['lon'] = lon

        w_code = weather_data.get('weather_code', 0)
        is_day = bool(weather_data.get('is_day', 1))
        weather_data['condition_text'] = get_condition_text(w_code, lang=lang, is_day=is_day)
        city_display = city_info.get('name_ru' if is_ru else 'name_en', weather_data.get('city_name', ''))
        weather_data['city_name'] = city_display
        weather_data['name_ru'] = city_info.get('name_ru', city_display)
        weather_data['name_en'] = city_info.get('name_en', city_display)

        return [self._create_search_result(weather_data, score)]

    def _create_search_result(self, data: dict, score: float) -> SearchResult:
        if self.config_manager:
            temp_unit = self.config_manager.get('temperature_unit', 'celsius')
        else:
            temp_unit = 'celsius'
        data['temp_unit'] = temp_unit

        city_name = data.get('city_name', 'Погода')
        temp = data.get('temp', 0)
        temp_disp = convert_temp(temp, temp_unit)
        temp_str = f'{temp_disp:+d}°' if temp_disp != 0 else '0°'
        cond_text = data.get('condition_text', 'Ясно')
        t_min = convert_temp(data.get('temp_min', temp), temp_unit)
        t_max = convert_temp(data.get('temp_max', temp), temp_unit)

        title = f'{city_name}: {temp_str}'
        feels_like = convert_temp(data.get('feels_like', temp), temp_unit)
        feels_str = f'{feels_like:+d}°' if feels_like != 0 else '0°'
        feels_prefix = t('weather_feels_like_prefix', temp=feels_str)
        subtitle = f'{cond_text} · {feels_prefix} · ↓ {t_min}° ↑ {t_max}°'

        icon_file = data.get('icon_file', os.path.join(ICONS_DIR, 'clear-night.svg'))
        copy_text = f'{city_name}: {temp_str}, {cond_text} (↓ {t_min}° ↑ {t_max}°)'

        def copy_action():
            set_clipboard_text(copy_text)

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
