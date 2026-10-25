import os
import zoneinfo
from datetime import datetime

from logger import get_logger

from .base import BaseProvider, SearchResult

logger = get_logger("timezone")
from i18n import get_current_language, t

try:
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gdk
except (ValueError, ImportError):
    pass

CITIES = [
    # Russia & CIS
    {"id": "novokuznetsk", "name_ru": "Новокузнецк", "name_en": "Novokuznetsk", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Novokuznetsk", "keywords": ["новокузнецк", "novokuznetsk", "кузня", "nvkz"]},
    {"id": "moscow", "name_ru": "Москва", "name_en": "Moscow", "country_ru": "Россия", "country_en": "Russia", "tz": "Europe/Moscow", "keywords": ["москва", "moscow", "мск", "msk"]},
    {"id": "spb", "name_ru": "Санкт-Петербург", "name_en": "Saint Petersburg", "country_ru": "Россия", "country_en": "Russia", "tz": "Europe/Moscow", "keywords": ["санкт-петербург", "питер", "петербург", "спб", "saint petersburg", "st petersburg"]},
    {"id": "novosibirsk", "name_ru": "Новосибирск", "name_en": "Novosibirsk", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Novosibirsk", "keywords": ["новосибирск", "novosibirsk", "нск"]},
    {"id": "yekaterinburg", "name_ru": "Екатеринбург", "name_en": "Yekaterinburg", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Yekaterinburg", "keywords": ["екатеринбург", "yekaterinburg", "екб"]},
    {"id": "kazan", "name_ru": "Казань", "name_en": "Kazan", "country_ru": "Россия", "country_en": "Russia", "tz": "Europe/Moscow", "keywords": ["казань", "kazan"]},
    {"id": "nizhny_novgorod", "name_ru": "Нижний Новгород", "name_en": "Nizhny Novgorod", "country_ru": "Россия", "country_en": "Russia", "tz": "Europe/Moscow", "keywords": ["нижний новгород", "nizhny новгород", "нн"]},
    {"id": "samara", "name_ru": "Самара", "name_en": "Samara", "country_ru": "Россия", "country_en": "Russia", "tz": "Europe/Samara", "keywords": ["самара", "samara"]},
    {"id": "omsk", "name_ru": "Омск", "name_en": "Omsk", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Omsk", "keywords": ["омск", "omsk"]},
    {"id": "chelyabinsk", "name_ru": "Челябинск", "name_en": "Chelyabinsk", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Yekaterinburg", "keywords": ["челябинск", "chelyabinsk"]},
    {"id": "krasnoyarsk", "name_ru": "Красноярск", "name_en": "Krasnoyarsk", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Krasnoyarsk", "keywords": ["красноярск", "krasnoyarsk", "крск"]},
    {"id": "kemerovo", "name_ru": "Кемерово", "name_en": "Kemerovo", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Novokuznetsk", "keywords": ["кемерово", "kemerovo"]},
    {"id": "tomsk", "name_ru": "Томск", "name_en": "Tomsk", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Tomsk", "keywords": ["томск", "tomsk"]},
    {"id": "barnaul", "name_ru": "Барнаул", "name_en": "Barnaul", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Barnaul", "keywords": ["барнаул", "barnaul"]},
    {"id": "irkutsk", "name_ru": "Иркутск", "name_en": "Irkutsk", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Irkutsk", "keywords": ["иркутск", "irkutsk", "байкал"]},
    {"id": "vladivostok", "name_ru": "Владивосток", "name_en": "Vladivostok", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Vladivostok", "keywords": ["владивосток", "vladivostok", "владик"]},
    {"id": "khabarovsk", "name_ru": "Хабаровск", "name_en": "Khabarovsk", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Vladivostok", "keywords": ["хабаровск", "khabarovsk"]},
    {"id": "kaliningrad", "name_ru": "Калининград", "name_en": "Kaliningrad", "country_ru": "Россия", "country_en": "Russia", "tz": "Europe/Kaliningrad", "keywords": ["калининград", "kaliningrad", "клд"]},
    {"id": "sochi", "name_ru": "Сочи", "name_en": "Sochi", "country_ru": "Россия", "country_en": "Russia", "tz": "Europe/Moscow", "keywords": ["сочи", "sochi", "адлер"]},
    {"id": "krasnodar", "name_ru": "Краснодар", "name_en": "Krasnodar", "country_ru": "Россия", "country_en": "Russia", "tz": "Europe/Moscow", "keywords": ["краснодар", "krasnodar"]},
    {"id": "rostov", "name_ru": "Ростов-на-Дону", "name_en": "Rostov-on-Don", "country_ru": "Россия", "country_en": "Russia", "tz": "Europe/Moscow", "keywords": ["ростов", "ростов-на-дону", "rostov"]},
    {"id": "volgograd", "name_ru": "Волгоград", "name_en": "Volgograd", "country_ru": "Россия", "country_en": "Russia", "tz": "Europe/Volgograd", "keywords": ["волгоград", "volgograd"]},
    {"id": "ufa", "name_ru": "Уфа", "name_en": "Ufa", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Yekaterinburg", "keywords": ["уфа", "ufa"]},
    {"id": "perm", "name_ru": "Пермь", "name_en": "Perm", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Yekaterinburg", "keywords": ["пермь", "perm"]},
    {"id": "tyumen", "name_ru": "Тюмень", "name_en": "Tyumen", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Yekaterinburg", "keywords": ["тюмень", "tyumen"]},
    {"id": "yakutsk", "name_ru": "Якутск", "name_en": "Yakutsk", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Yakutsk", "keywords": ["якутск", "yakutsk"]},
    {"id": "magadan", "name_ru": "Магадан", "name_en": "Magadan", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Magadan", "keywords": ["магадан", "magadan"]},
    {"id": "kamchatka", "name_ru": "Петропавловск-Камчатский", "name_en": "Petropavlovsk-Kamchatsky", "country_ru": "Россия", "country_en": "Russia", "tz": "Asia/Kamchatka", "keywords": ["камчатка", "петропавловск-камчатский", "kamchatka"]},
    {"id": "minsk", "name_ru": "Минск", "name_en": "Minsk", "country_ru": "Беларусь", "country_en": "Belarus", "tz": "Europe/Minsk", "keywords": ["минск", "minsk", "беларусь", "belarus"]},
    {"id": "almaty", "name_ru": "Алматы", "name_en": "Almaty", "country_ru": "Казахстан", "country_en": "Kazakhstan", "tz": "Asia/Almaty", "keywords": ["алматы", "алма-ата", "almaty", "казахстан"]},
    {"id": "astana", "name_ru": "Астана", "name_en": "Astana", "country_ru": "Казахстан", "country_en": "Kazakhstan", "tz": "Asia/Almaty", "keywords": ["астана", "astana", "нур-султан"]},
    {"id": "tashkent", "name_ru": "Ташкент", "name_en": "Tashkent", "country_ru": "Узбекистан", "country_en": "Uzbekistan", "tz": "Asia/Tashkent", "keywords": ["ташкент", "tashkent", "узбекистан"]},
    {"id": "samarkand", "name_ru": "Самарканд", "name_en": "Samarkand", "country_ru": "Узбекистан", "country_en": "Uzbekistan", "tz": "Asia/Samarkand", "keywords": ["самарканд", "samarkand"]},
    {"id": "baku", "name_ru": "Баку", "name_en": "Baku", "country_ru": "Азербайджан", "country_en": "Azerbaijan", "tz": "Asia/Baku", "keywords": ["баку", "baku", "азербайджан"]},
    {"id": "tbilisi", "name_ru": "Тбилиси", "name_en": "Tbilisi", "country_ru": "Грузия", "country_en": "Georgia", "tz": "Asia/Tbilisi", "keywords": ["тбилиси", "tbilisi", "грузия"]},
    {"id": "yerevan", "name_ru": "Ереван", "name_en": "Yerevan", "country_ru": "Армения", "country_en": "Armenia", "tz": "Asia/Yerevan", "keywords": ["ереван", "yerevan", "армения"]},
    {"id": "bishkek", "name_ru": "Бишкек", "name_en": "Bishkek", "country_ru": "Кыргызстан", "country_en": "Kyrgyzstan", "tz": "Asia/Bishkek", "keywords": ["бишкек", "bishkek", "кыргызстан"]},
    {"id": "dushanbe", "name_ru": "Душанбе", "name_en": "Dushanbe", "country_ru": "Таджикистан", "country_en": "Tajikistan", "tz": "Asia/Dushanbe", "keywords": ["душанбе", "dushanbe", "таджикистан"]},
    {"id": "kyiv", "name_ru": "Киев", "name_en": "Kyiv", "country_ru": "Украина", "country_en": "Ukraine", "tz": "Europe/Kyiv", "keywords": ["киев", "kyiv", "kiev", "украина"]},

    # Europe
    {"id": "london", "name_ru": "Лондон", "name_en": "London", "country_ru": "Великобритания", "country_en": "United Kingdom", "tz": "Europe/London", "keywords": ["лондон", "london", "англия", "uk"]},
    {"id": "paris", "name_ru": "Париж", "name_en": "Paris", "country_ru": "Франция", "country_en": "France", "tz": "Europe/Paris", "keywords": ["париж", "paris", "франция"]},
    {"id": "berlin", "name_ru": "Берлин", "name_en": "Berlin", "country_ru": "Германия", "country_en": "Germany", "tz": "Europe/Berlin", "keywords": ["берлин", "berlin", "германия"]},
    {"id": "rome", "name_ru": "Рим", "name_en": "Rome", "country_ru": "Италия", "country_en": "Italy", "tz": "Europe/Rome", "keywords": ["рим", "rome", "италия"]},
    {"id": "madrid", "name_ru": "Мадрид", "name_en": "Madrid", "country_ru": "Испания", "country_en": "Spain", "tz": "Europe/Madrid", "keywords": ["мадрид", "madrid", "испания"]},
    {"id": "barcelona", "name_ru": "Барселона", "name_en": "Barcelona", "country_ru": "Испания", "country_en": "Spain", "tz": "Europe/Madrid", "keywords": ["барселона", "barcelona"]},
    {"id": "lisbon", "name_ru": "Лиссабон", "name_en": "Lisbon", "country_ru": "Португалия", "country_en": "Portugal", "tz": "Europe/Lisbon", "keywords": ["лиссабон", "lisbon", "португалия"]},
    {"id": "amsterdam", "name_ru": "Амстердам", "name_en": "Amsterdam", "country_ru": "Нидерланды", "country_en": "Netherlands", "tz": "Europe/Amsterdam", "keywords": ["амстердам", "amsterdam", "голландия"]},
    {"id": "brussels", "name_ru": "Брюссель", "name_en": "Brussels", "country_ru": "Бельгия", "country_en": "Belgium", "tz": "Europe/Brussels", "keywords": ["брюссель", "brussels", "бельгия"]},
    {"id": "vienna", "name_ru": "Вена", "name_en": "Vienna", "country_ru": "Австрия", "country_en": "Austria", "tz": "Europe/Vienna", "keywords": ["вена", "vienna", "австрия"]},
    {"id": "prague", "name_ru": "Прага", "name_en": "Prague", "country_ru": "Чехия", "country_en": "Czech Republic", "tz": "Europe/Prague", "keywords": ["прага", "prague", "чехия"]},
    {"id": "warsaw", "name_ru": "Варшава", "name_en": "Warsaw", "country_ru": "Польша", "country_en": "Poland", "tz": "Europe/Warsaw", "keywords": ["варшава", "warsaw", "польша"]},
    {"id": "budapest", "name_ru": "Будапешт", "name_en": "Budapest", "country_ru": "Венгрия", "country_en": "Hungary", "tz": "Europe/Budapest", "keywords": ["будапешт", "budapest", "венгрия"]},
    {"id": "stockholm", "name_ru": "Стокгольм", "name_en": "Stockholm", "country_ru": "Швеция", "country_en": "Sweden", "tz": "Europe/Stockholm", "keywords": ["стокгольм", "stockholm", "швеция"]},
    {"id": "oslo", "name_ru": "Осло", "name_en": "Oslo", "country_ru": "Норвегия", "country_en": "Norway", "tz": "Europe/Oslo", "keywords": ["осло", "oslo", "норвегия"]},
    {"id": "helsinki", "name_ru": "Хельсинки", "name_en": "Helsinki", "country_ru": "Финляндия", "country_en": "Finland", "tz": "Europe/Helsinki", "keywords": ["хельсинки", "helsinki", "финляндия"]},
    {"id": "copenhagen", "name_ru": "Копенгаген", "name_en": "Copenhagen", "country_ru": "Дания", "country_en": "Denmark", "tz": "Europe/Copenhagen", "keywords": ["копенгаген", "copenhagen", "дания"]},
    {"id": "dublin", "name_ru": "Дублин", "name_en": "Dublin", "country_ru": "Ирландия", "country_en": "Ireland", "tz": "Europe/Dublin", "keywords": ["дублин", "dublin", "ирландия"]},
    {"id": "zurich", "name_ru": "Цюрих", "name_en": "Zurich", "country_ru": "Швейцария", "country_en": "Switzerland", "tz": "Europe/Zurich", "keywords": ["цюрих", "zurich", "швейцария"]},
    {"id": "athens", "name_ru": "Афины", "name_en": "Athens", "country_ru": "Греция", "country_en": "Greece", "tz": "Europe/Athens", "keywords": ["афины", "athens", "греция"]},
    {"id": "istanbul", "name_ru": "Стамбул", "name_en": "Istanbul", "country_ru": "Турция", "country_en": "Turkey", "tz": "Europe/Istanbul", "keywords": ["стамбул", "istanbul", "турция"]},

    # Asia & Middle East
    {"id": "tokyo", "name_ru": "Токио", "name_en": "Tokyo", "country_ru": "Япония", "country_en": "Japan", "tz": "Asia/Tokyo", "keywords": ["токио", "tokyo", "япония", "japan"]},
    {"id": "seoul", "name_ru": "Сеул", "name_en": "Seoul", "country_ru": "Южная Корея", "country_en": "South Korea", "tz": "Asia/Seoul", "keywords": ["сеул", "seoul", "корея"]},
    {"id": "beijing", "name_ru": "Пекин", "name_en": "Beijing", "country_ru": "Китай", "country_en": "China", "tz": "Asia/Shanghai", "keywords": ["пекин", "beijing", "китай", "china"]},
    {"id": "shanghai", "name_ru": "Шанхай", "name_en": "Shanghai", "country_ru": "Китай", "country_en": "China", "tz": "Asia/Shanghai", "keywords": ["шанхай", "shanghai"]},
    {"id": "hong_kong", "name_ru": "Гонконг", "name_en": "Hong Kong", "country_ru": "Гонконг", "country_en": "Hong Kong", "tz": "Asia/Hong_Kong", "keywords": ["гонконг", "hong kong", "hk"]},
    {"id": "singapore", "name_ru": "Сингапур", "name_en": "Singapore", "country_ru": "Сингапур", "country_en": "Singapore", "tz": "Asia/Singapore", "keywords": ["сингапур", "singapore"]},
    {"id": "bangkok", "name_ru": "Бангкок", "name_en": "Bangkok", "country_ru": "Таиланд", "country_en": "Thailand", "tz": "Asia/Bangkok", "keywords": ["бангкок", "bangkok", "таиланд", "тайланд"]},
    {"id": "kuala_lumpur", "name_ru": "Куала-Лумпур", "name_en": "Kuala Lumpur", "country_ru": "Малайзия", "country_en": "Malaysia", "tz": "Asia/Kuala_Lumpur", "keywords": ["куала-лумпур", "kuala lumpur", "малайзия"]},
    {"id": "jakarta", "name_ru": "Джакарта", "name_en": "Jakarta", "country_ru": "Индонезия", "country_en": "Indonesia", "tz": "Asia/Jakarta", "keywords": ["джакарта", "jakarta", "индонезия"]},
    {"id": "bali", "name_ru": "Бали", "name_en": "Bali", "country_ru": "Индонезия", "country_en": "Indonesia", "tz": "Asia/Makassar", "keywords": ["бали", "bali", "денпасар"]},
    {"id": "delhi", "name_ru": "Нью-Дели", "name_en": "New Delhi", "country_ru": "Индия", "country_en": "India", "tz": "Asia/Kolkata", "keywords": ["дели", "нью-дели", "new delhi", "индия"]},
    {"id": "mumbai", "name_ru": "Мумбаи", "name_en": "Mumbai", "country_ru": "Индия", "country_en": "India", "tz": "Asia/Kolkata", "keywords": ["мумбаи", "mumbai", "бомбей"]},
    {"id": "dubai", "name_ru": "Дубай", "name_en": "Dubai", "country_ru": "ОАЭ", "country_en": "UAE", "tz": "Asia/Dubai", "keywords": ["дубай", "dubai", "оаэ", "uae"]},
    {"id": "doha", "name_ru": "Доха", "name_en": "Doha", "country_ru": "Катар", "country_en": "Qatar", "tz": "Asia/Qatar", "keywords": ["доха", "doha", "катар"]},
    {"id": "riyadh", "name_ru": "Эр-Рияд", "name_en": "Riyadh", "country_ru": "Саудовская Аравия", "country_en": "Saudi Arabia", "tz": "Asia/Riyadh", "keywords": ["эр-рияд", "riyadh", "саудовская аравия"]},
    {"id": "tel_aviv", "name_ru": "Тель-Авив", "name_en": "Tel Aviv", "country_ru": "Израиль", "country_en": "Israel", "tz": "Asia/Jerusalem", "keywords": ["тель-авив", "tel aviv", "израиль"]},

    # Americas
    {"id": "new_york", "name_ru": "Нью-Йорк", "name_en": "New York", "country_ru": "США", "country_en": "USA", "tz": "America/New_York", "keywords": ["нью-йорк", "new york", "nyc", "сша", "usa"]},
    {"id": "los_angeles", "name_ru": "Лос-Анджелес", "name_en": "Los Angeles", "country_ru": "США", "country_en": "USA", "tz": "America/Los_Angeles", "keywords": ["лос-анджелес", "los angeles", "la", "л-а"]},
    {"id": "chicago", "name_ru": "Чикаго", "name_en": "Chicago", "country_ru": "США", "country_en": "USA", "tz": "America/Chicago", "keywords": ["чикаго", "chicago"]},
    {"id": "san_francisco", "name_ru": "Сан-Франциско", "name_en": "San Francisco", "country_ru": "США", "country_en": "USA", "tz": "America/Los_Angeles", "keywords": ["сан-франциско", "san francisco", "sf", "кремниевая долина"]},
    {"id": "washington", "name_ru": "Вашингтон", "name_en": "Washington", "country_ru": "США", "country_en": "USA", "tz": "America/New_York", "keywords": ["вашингтон", "washington", "dc"]},
    {"id": "miami", "name_ru": "Майами", "name_en": "Miami", "country_ru": "США", "country_en": "USA", "tz": "America/New_York", "keywords": ["майами", "miami", "флорида"]},
    {"id": "toronto", "name_ru": "Торонто", "name_en": "Toronto", "country_ru": "Канада", "country_en": "Canada", "tz": "America/Toronto", "keywords": ["торонто", "toronto", "канада"]},
    {"id": "vancouver", "name_ru": "Ванкувер", "name_en": "Vancouver", "country_ru": "Канада", "country_en": "Canada", "tz": "America/Vancouver", "keywords": ["ванкувер", "vancouver"]},
    {"id": "buenos_aires", "name_ru": "Буэнос-Айрес", "name_en": "Buenos Aires", "country_ru": "Аргентина", "country_en": "Argentina", "tz": "America/Argentina/Buenos_Aires", "keywords": ["буэнос-айрес", "buenos aires", "аргентина"]},
    {"id": "sao_paulo", "name_ru": "Сан-Паулу", "name_en": "Sao Paulo", "country_ru": "Бразилия", "country_en": "Brazil", "tz": "America/Sao_Paulo", "keywords": ["сан-паулу", "sao paulo", "бразилия"]},
    {"id": "santiago", "name_ru": "Сантьяго", "name_en": "Santiago", "country_ru": "Чили", "country_en": "Chile", "tz": "America/Santiago", "keywords": ["сантьяго", "santiago", "чили"]},

    # Oceania & Africa
    {"id": "sydney", "name_ru": "Сидней", "name_en": "Sydney", "country_ru": "Австралия", "country_en": "Australia", "tz": "Australia/Sydney", "keywords": ["сидней", "sydney", "австралия"]},
    {"id": "melbourne", "name_ru": "Мельбурн", "name_en": "Melbourne", "country_ru": "Австралия", "country_en": "Australia", "tz": "Australia/Melbourne", "keywords": ["мельбурн", "melbourne"]},
    {"id": "auckland", "name_ru": "Окленд", "name_en": "Auckland", "country_ru": "Новая Зеландия", "country_en": "New Zealand", "tz": "Pacific/Auckland", "keywords": ["окленд", "auckland", "новая зеландия"]},
    {"id": "cairo", "name_ru": "Каир", "name_en": "Cairo", "country_ru": "Египет", "country_en": "Egypt", "tz": "Africa/Cairo", "keywords": ["каир", "cairo", "египет"]},
    {"id": "johannesburg", "name_ru": "Йоханнесбург", "name_en": "Johannesburg", "country_ru": "ЮАР", "country_en": "South Africa", "tz": "Africa/Johannesburg", "keywords": ["йоханнесбург", "johannesburg", "юар"]},

    # Standards
    {"id": "utc", "name_ru": "UTC (Всемирное время)", "name_en": "UTC (Universal Time)", "country_ru": "Стандарт", "country_en": "Standard", "tz": "UTC", "keywords": ["utc", "универсальное время", "всемирное время"]},
    {"id": "gmt", "name_ru": "GMT (Гринвич)", "name_en": "GMT (Greenwich Mean Time)", "country_ru": "Стандарт", "country_en": "Standard", "tz": "Etc/GMT", "keywords": ["gmt", "гринвич", "по гринвичу"]}
]

RU_MONTHS = ['', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
RU_DAYS = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

TIME_PREFIXES = [
    "время в ", "время во ", "время по ", "время ",
    "time in ", "time for ", "time at ", "time ",
    "в ", "во ", "in ", "at "
]

TIME_SUFFIXES = [
    " время", " time", " сейчас", " now", " сегодня", " today"
]

LOCAL_TIME_QUERIES = {
    "время", "time", "текущее время", "точное время", "сейчас время",
    "current time", "exact time", "clock", "часы", "сколько времени"
}


def _matches_declined(query_word: str, target: str) -> bool:
    if len(query_word) < 4 or len(target) < 4:
        return False
    stem = target[:-1]
    return query_word.startswith(stem) or stem.startswith(query_word[:-1])


class TimezoneProvider(BaseProvider):
    def __init__(self, history_manager):
        super().__init__(history_manager)

    def _get_date_string(self, dt: datetime, is_ru: bool) -> str:
        if is_ru:
            return f"{RU_DAYS[dt.weekday()]}, {dt.day} {RU_MONTHS[dt.month]}"
        return dt.strftime("%A, %B %d")

    def _get_diff_string(self, diff_h: int, diff_m: int, is_ru: bool) -> str:
        if diff_h == 0 and diff_m == 0:
            return "То же время, что у вас" if is_ru else "Same time as you"
        sign = "+" if diff_h > 0 else ""
        if is_ru:
            if diff_m > 0:
                return f"{sign}{diff_h} ч {diff_m} мин от вас"
            return f"{sign}{diff_h} ч от вас"
        else:
            if diff_m > 0:
                return f"{sign}{diff_h}h {diff_m}m from you"
            return f"{sign}{diff_h}h from you"

    def _create_result(self, city_data: dict, score: float) -> SearchResult:
        is_ru = get_current_language() == "ru"
        city_name = city_data["name_ru"] if is_ru else city_data["name_en"]
        country_name = city_data["country_ru"] if is_ru else city_data["country_en"]

        try:
            local_now = datetime.now().astimezone()
            local_offset = local_now.utcoffset()

            if city_data["tz"] == "LOCAL":
                now = local_now
                target_offset = local_offset
            else:
                target_tz = zoneinfo.ZoneInfo(city_data["tz"])
                now = datetime.now(target_tz)
                target_offset = now.utcoffset()

            diff_sec = (target_offset - local_offset).total_seconds()
            diff_h = int(diff_sec // 3600)
            diff_m = int((abs(diff_sec) % 3600) // 60)

            total_offset_sec = target_offset.total_seconds()
            tz_sign = "+" if total_offset_sec >= 0 else "-"
            tz_h = int(abs(total_offset_sec) // 3600)
            utc_offset = f"UTC{tz_sign}{tz_h}"
            tz_abbr = now.strftime("%Z") or utc_offset

            time_str = now.strftime("%H:%M")
            date_str = self._get_date_string(now, is_ru)
            diff_str = self._get_diff_string(diff_h, diff_m, is_ru)
            is_day = 6 <= now.hour < 21
            icon_name = "weather-clear" if is_day else "weather-clear-night"

            title = f"{time_str} — {city_name}"
            subtitle = f"{date_str} • {diff_str} • {tz_abbr} ({utc_offset})"
            copy_text = f"{time_str} — {city_name}, {country_name} ({date_str}, {utc_offset})"

            preview_data = {
                "time_str": time_str,
                "city_name": city_name,
                "country": country_name,
                "formatted_date": date_str,
                "diff_str": diff_str,
                "tz_abbr": tz_abbr,
                "utc_offset": utc_offset,
                "is_day": is_day,
                "day_of_week": RU_DAYS[now.weekday()] if is_ru else now.strftime("%A")
            }

            def _copy_callback():
                try:
                    display = Gdk.Display.get_default()
                    if display:
                        display.get_clipboard().set(copy_text)
                except Exception as e:
                    logger.debug("Clipboard copy failed: %s", e)

            return SearchResult(
                id=f"tz_{city_data['id']}",
                title=title,
                subtitle=subtitle,
                icon=icon_name,
                score=score,
                category="Time",
                provider="TimezoneProvider",
                preview_data=preview_data,
                action_copy=_copy_callback
            )
        except Exception as e:
            logger.warning("Error calculating timezone for %s: %s", city_data.get("id"), e)
            return None

    def search(self, query: str, limit: int = 5, category_filter: str = None) -> list[SearchResult]:
        if category_filter not in (None, "All", "Time"):
            return []

        if not query:
            return []

        raw_q = query.lower().strip()
        is_ru = get_current_language() == "ru"

        # Check local time request
        if raw_q in LOCAL_TIME_QUERIES:
            local_city = {
                "id": "local",
                "name_ru": "Ваше местное время",
                "name_en": "Your local time",
                "country_ru": "Текущий пояс",
                "country_en": "Current timezone",
                "tz": "LOCAL",
                "keywords": []
            }
            res = self._create_result(local_city, score=160)
            return [res] if res else []

        has_prefix = False
        clean_q = raw_q

        for prefix in TIME_PREFIXES:
            if clean_q.startswith(prefix):
                clean_q = clean_q[len(prefix):].strip()
                has_prefix = True
                break

        for suffix in TIME_SUFFIXES:
            if clean_q.endswith(suffix):
                clean_q = clean_q[:-len(suffix)].strip()
                has_prefix = True
                break

        if not clean_q:
            return []

        # Without an explicit time prefix, never trigger on 1-2 character queries
        if not has_prefix:
            if len(clean_q) < 3 and clean_q not in ("la", "sf", "ny", "uk", "нн", "екб", "клд", "нск", "спб", "мск"):
                return []

        results = []
        for city in CITIES:
            name_ru = city["name_ru"].lower()
            name_en = city["name_en"].lower()
            country_ru = city["country_ru"].lower()
            country_en = city["country_en"].lower()
            kws = [kw.lower() for kw in city.get("keywords", [])]

            score = 0
            # 1. Exact match on city name or keyword
            if clean_q in (name_ru, name_en) or clean_q in kws:
                score = 150 if has_prefix else 92

            # 2. Declension match (e.g. в париже, в лондоне, в питере) - only for len >= 4
            elif len(clean_q) >= 4 and (
                _matches_declined(clean_q, name_ru) or
                _matches_declined(clean_q, name_en) or
                any(_matches_declined(clean_q, k) for k in kws if len(k) >= 4)
            ):
                score = 145 if has_prefix else 85

            # 3. Prefix match:
            # If has_prefix: allow any length >= 1 (e.g. "время т...")
            # If no prefix: require at least 3 chars (e.g. "ток...", "лон...")
            elif (has_prefix or len(clean_q) >= 3) and (
                name_ru.startswith(clean_q) or
                name_en.startswith(clean_q) or
                any(k.startswith(clean_q) for k in kws)
            ):
                score = 130 if has_prefix else 65

            # 4. Substring match only if explicit prefix "время..." and query len >= 3
            elif has_prefix and len(clean_q) >= 3 and (
                clean_q in name_ru or
                clean_q in name_en or
                any(clean_q in k for k in kws)
            ):
                score = 110

            # 5. Country match only with explicit prefix
            elif has_prefix and len(clean_q) >= 3 and (clean_q == country_ru or clean_q == country_en):
                score = 100

            if score > 0:
                res = self._create_result(city, score)
                if res:
                    results.append(res)

        results.sort(key=lambda x: x.score, reverse=True)
        max_results = limit if has_prefix else min(limit, 2)
        return results[:max_results]
