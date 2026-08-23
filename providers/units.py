import re
from .base import BaseProvider, SearchResult

class UnitConverter:
    # Базовые единицы: метры, килограммы, цельсий, км/ч, кв.метры, литры, секунды, байты
    LENGTH = {'m': 1, 'km': 1000, 'cm': 0.01, 'mm': 0.001, 'mi': 1609.34, 'yd': 0.9144, 'ft': 0.3048, 'in': 0.0254}
    MASS = {'kg': 1, 'g': 0.001, 'mg': 0.000001, 'lb': 0.453592, 'lbs': 0.453592, 'oz': 0.0283495}
    SPEED = {'kmh': 1, 'mph': 1.60934, 'ms': 3.6, 'knots': 1.852}
    AREA = {'sqm': 1, 'sqkm': 1000000, 'hectare': 10000, 'acre': 4046.86}
    VOLUME = {'l': 1, 'ml': 0.001, 'gal': 3.78541, 'oz': 0.0295735}
    TIME = {'s': 1, 'sec': 1, 'min': 60, 'h': 3600, 'hr': 3600, 'd': 86400, 'day': 86400}
    DATA = {'b': 1, 'kb': 1024, 'mb': 1048576, 'gb': 1073741824, 'tb': 1099511627776}
    
    CATEGORIES = [LENGTH, MASS, SPEED, AREA, VOLUME, TIME, DATA]

    @classmethod
    def convert(cls, query: str) -> str:
        query = query.lower().strip()
        
        # Специальная обработка температуры
        temp_match = re.match(r'^([\d\.]+)\s*(c|f)$', query)
        if temp_match:
            val, unit = float(temp_match.group(1)), temp_match.group(2)
            if unit == 'c': return f"{val}°C = {round(val * 9/5 + 32, 2)}°F"
            if unit == 'f': return f"{val}°F = {round((val - 32) * 5/9, 2)}°C"

        # Общий парсер: число -> единица -> (опционально: in/to -> целевая единица)
        match = re.match(r'^([\d\.]+)\s*([a-z]+)\s*(?:in|to)?\s*([a-z]+)?$', query)
        if not match:
            return None

        val_str, unit_from, unit_to = match.groups()
        try:
            val = float(val_str)
        except:
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
                return f"{val} {unit_from} = {round(res, 4)} {unit_to}"
            return None
            
        # Если не указана, выводим все популярные
        results = []
        for u, factor in target_category.items():
            if u != unit_from:
                res = base_val / factor
                # Фильтруем слишком маленькие/большие значения для читаемости
                if 0.001 <= res <= 1000000:
                    results.append(f"{round(res, 2)} {u}")
                    
        if results:
            return f"{val} {unit_from} = " + ", ".join(results[:3])
            
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
            except: pass

        return SearchResult(
            id=f"unit_{query}",
            title=result_str,
            subtitle="Конвертация",
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
