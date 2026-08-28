import re
from .base import BaseProvider, SearchResult
from i18n import t

import re
from .base import BaseProvider, SearchResult
from i18n import t

class UnitConverter:
    # Базовые единицы: метры, килограммы, цельсий, км/ч, кв.метры, литры, секунды, байты
    LENGTH = {'m': 1, 'km': 1000, 'cm': 0.01, 'mm': 0.001, 'mi': 1609.34, 'yd': 0.9144, 'ft': 0.3048, 'in': 0.0254}
    MASS = {'kg': 1, 'g': 0.001, 'mg': 0.000001, 'lb': 0.453592, 'lbs': 0.453592, 'oz': 0.0283495}
    SPEED = {'kmh': 1, 'mph': 1.60934, 'ms': 3.6, 'knots': 1.852}
    AREA = {'sqm': 1, 'sqkm': 1000000, 'hectare': 10000, 'acre': 4046.86}
    VOLUME = {'l': 1, 'ml': 0.001, 'gal': 3.78541, 'oz': 0.0295735}
    TIME = {'s': 1, 'sec': 1, 'min': 60, 'h': 3600, 'hr': 3600, 'd': 86400, 'day': 86400}
    DATA = {'b': 1, 'kb': 1024, 'mb': 1048576, 'gb': 1073741824, 'tb': 1099511627776}
    
    ALIASES = {
        'meter': 'm', 'meters': 'm', 'метр': 'm', 'метры': 'm', 'метров': 'm',
        'kilometer': 'km', 'kilometers': 'km', 'километр': 'km', 'километры': 'km', 'км': 'km',
        'centimeter': 'cm', 'centimeters': 'cm', 'сантиметр': 'cm', 'сантиметры': 'cm', 'см': 'cm',
        'millimeter': 'mm', 'millimeters': 'mm', 'миллиметр': 'mm', 'мм': 'mm',
        'mile': 'mi', 'miles': 'mi', 'миля': 'mi', 'мили': 'mi', 'миль': 'mi',
        'yard': 'yd', 'yards': 'yd', 'ярд': 'yd', 'ярды': 'yd',
        'foot': 'ft', 'feet': 'ft', 'фут': 'ft', 'футы': 'ft', 'футов': 'ft',
        'inch': 'in', 'inches': 'in', 'дюйм': 'in', 'дюймы': 'in', 'дюймов': 'in',
        'kilogram': 'kg', 'kilograms': 'kg', 'килограмм': 'kg', 'килограммы': 'kg', 'кг': 'kg',
        'gram': 'g', 'grams': 'g', 'грамм': 'g', 'граммы': 'g', 'г': 'g',
        'pound': 'lb', 'pounds': 'lb', 'фунт_масса': 'lb',
        'ounce': 'oz', 'ounces': 'oz', 'унция': 'oz', 'унции': 'oz',
        'celsius': 'c', 'цельсий': 'c', 'цельсия': 'c',
        'fahrenheit': 'f', 'фаренгейт': 'f', 'фаренгейта': 'f',
        'hour': 'h', 'hours': 'h', 'час': 'h', 'часы': 'h', 'часов': 'h',
        'minute': 'min', 'minutes': 'min', 'минута': 'min', 'минуты': 'min', 'минут': 'min',
        'second': 's', 'seconds': 's', 'секунда': 's', 'секунды': 's', 'секунд': 's',
        'byte': 'b', 'bytes': 'b', 'байт': 'b', 'байты': 'b', 'байтов': 'b',
        'kilobyte': 'kb', 'kilobytes': 'kb', 'килобайт': 'kb', 'кб': 'kb',
        'megabyte': 'mb', 'megabytes': 'mb', 'мегабайт': 'mb', 'мб': 'mb',
        'gigabyte': 'gb', 'gigabytes': 'gb', 'гигабайт': 'gb', 'гб': 'gb',
        'terabyte': 'tb', 'terabytes': 'tb', 'терабайт': 'tb', 'тб': 'tb',
    }

    CATEGORIES = [LENGTH, MASS, SPEED, AREA, VOLUME, TIME, DATA]

    @classmethod
    def normalize_unit(cls, u: str) -> str:
        if not u: return ""
        u = u.lower().strip()
        return cls.ALIASES.get(u, u)

    @classmethod
    def convert(cls, query: str) -> str:
        query = query.lower().strip()
        
        # Специальная обработка температуры
        temp_match = re.match(r'^([\d\.\-]+)\s*(?:°)?\s*([a-zа-яё]+)(?:\s*(?:in|to|в|->)\s*(?:°)?\s*([a-zа-яё]+))?$', query)
        if temp_match:
            try:
                val = float(temp_match.group(1))
                u_from = cls.normalize_unit(temp_match.group(2))
                u_to = cls.normalize_unit(temp_match.group(3)) if temp_match.group(3) else None
                if u_from == 'c' and (u_to in (None, 'f')):
                    return f"{val}°C = {round(val * 9/5 + 32, 2)}°F"
                if u_from == 'f' and (u_to in (None, 'c')):
                    return f"{val}°F = {round((val - 32) * 5/9, 2)}°C"
            except Exception:
                pass

        # Общий парсер: число -> единица -> (опционально: in/to/в -> целевая единица)
        match = re.match(r'^([\d\.]+)\s*([a-zа-яё_]+)(?:\s*(?:in|to|в|->)\s*([a-zа-яё_]+))?$', query)
        if not match:
            return None

        val_str, raw_u_from, raw_u_to = match.groups()
        unit_from = cls.normalize_unit(raw_u_from)
        unit_to = cls.normalize_unit(raw_u_to) if raw_u_to else None
        
        try:
            val = float(val_str)
        except Exception:
            return None

        # Ищем категорию исходной единицы
        target_category = None
        for cat in cls.CATEGORIES:
            if unit_from in cat:
                target_category = cat
                break
        
        if not target_category:
            return None

        # Конвертация в базовую единицу
        base_val = val * target_category[unit_from]

        # Если целевая единица указана
        if unit_to:
            if unit_to in target_category:
                res = base_val / target_category[unit_to]
                return f"{val} {raw_u_from} = {round(res, 4)} {raw_u_to}"
            return None
            
        # Если не указана, выводим популярные
        results = []
        for u, factor in target_category.items():
            if u != unit_from:
                res = base_val / factor
                if 0.001 <= res <= 10000000:
                    results.append(f"{round(res, 2)} {u}")
                    
        if results:
            return f"{val} {raw_u_from} = " + ", ".join(results[:3])
            
        return None


class UnitProvider(BaseProvider):
    def _create_result(self, query: str, result_str: str) -> SearchResult:
        def _copy_callback():
            try:
                import gi
                gi.require_version('Gtk', '4.0')
                from gi.repository import Gdk
                clipboard = Gdk.Display.get_default().get_clipboard()
                clipboard.set(str(result_str))
            except Exception: pass

        return SearchResult(
            id=f"unit_{query}",
            title=result_str,
            subtitle=t("provider_conversion_desc"),
            icon="view-refresh",
            score=150,
            category="Units",
            provider="UnitProvider",
            preview_data={"result": result_str},
            action_execute=_copy_callback,
            action_copy=_copy_callback
        )

    def search(self, query: str, limit: int = 10, category_filter: str = None) -> list[SearchResult]:
        if category_filter not in (None, "All"):
            return []
            
        res = UnitConverter.convert(query)
        if res:
            return [self._create_result(query, res)]
        return []
