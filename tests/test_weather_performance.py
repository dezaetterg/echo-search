import time

import gi
import pytest

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from preview_manager import PreviewManager
from providers.base import SearchResult
from providers.weather import WeatherProvider, determine_solar_time_of_day


@pytest.fixture
def sample_weather_result():
    return SearchResult(
        id="weather:moscow",
        title="Москва: +18°C, Ясно",
        subtitle="Москва, Россия",
        icon="weather-clear",
        score=1.0,
        category="Weather",
        provider="Weather",
        preview_data={
            "city_name": "Москва",
            "name_ru": "Москва",
            "name_en": "Moscow",
            "temp": 18,
            "temp_min": 10,
            "temp_max": 20,
            "feels_like": 17,
            "weather_code": 0,
            "is_day": 1,
            "time_of_day": "day",
            "condition_text": "Ясно",
            "humidity": 55,
            "wind_speed": 3.2,
            "precipitation": 0.0,
            "pressure": 1015,
            "pressure_mm": 761,
            "bg_class": "weather-bg-clear-day",
        },
    )


def test_weather_preview_render_performance(sample_weather_result):
    """Assert weather preview renders in < 50 ms without Cairo particle lag."""
    # Warmup and clear any accumulated GC pressure from earlier tests
    import gc
    gc.collect()
    widget = PreviewManager.render(sample_weather_result)
    assert isinstance(widget, Gtk.Widget)

    # Performance measurement over 20 runs
    latencies = []
    for _ in range(20):
        t0 = time.perf_counter()
        w = PreviewManager.render(sample_weather_result)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)  # ms
        assert isinstance(w, Gtk.Widget)

    avg_ms = sum(latencies) / len(latencies)
    max_ms = max(latencies)

    # Must be strictly under 50 ms threshold
    assert avg_ms < 50.0, f"Average preview render exceeded 50 ms: {avg_ms:.2f} ms"
    assert max_ms < 50.0, f"Max preview render exceeded 50 ms: {max_ms:.2f} ms"


def test_geocoding_cache_limit(tmp_path):
    """Ensure geocache is capped at 50 items and purges oldest keys."""
    wp = WeatherProvider(None)
    cache_file = tmp_path / "weather_test_cache.json"
    wp.cache_file = cache_file

    # Populate 70 items
    wp.geo_cache = {f"city_{i}": {"lat": i, "lon": i, "name": f"City {i}"} for i in range(70)}
    wp._save_cache()

    # Reload from disk
    wp.geo_cache = {}
    wp._load_cache()

    assert len(wp.geo_cache) <= 50, f"Cache size {len(wp.geo_cache)} exceeds 50 cap"


def test_no_false_positives_for_apps():
    """Verify application queries like 'steam' never match weather."""
    wp = WeatherProvider(None)

    # These must NOT return weather results
    assert wp.search("steam") == []
    assert wp.search("stea") == []
    assert wp.search("telegram") == []
    assert wp.search("firefox") == []
    assert wp.search("echo") == []
    assert wp.search("pogi") == []


def test_exact_cities_and_prefixes():
    """Verify exact cities, Russian declensions, and weather prefix keywords still return results."""
    wp = WeatherProvider(None)

    # Prefix queries
    res_pogoda = wp.search("погода")
    assert len(res_pogoda) == 1
    assert res_pogoda[0].category == "Weather"

    res_weather = wp.search("weather")
    assert len(res_weather) == 1
    assert res_weather[0].category == "Weather"

    # Exact major cities in nominative case
    res_moscow = wp.search("москва")
    assert len(res_moscow) == 1
    assert "Москва" in res_moscow[0].title or "Moscow" in res_moscow[0].title

    res_nvkz = wp.search("новокузнецк")
    assert len(res_nvkz) == 1
    assert "Новокузнецк" in res_nvkz[0].title or "Novokuznetsk" in res_nvkz[0].title

    res_london = wp.search("london")
    assert len(res_london) == 1
    assert "London" in res_london[0].title or "Лондон" in res_london[0].title

    # Russian prepositional case queries with prefix
    res_v_msk = wp.search("погода в москве")
    assert len(res_v_msk) == 1
    assert "Москва" in res_v_msk[0].title or "Moscow" in res_v_msk[0].title

    res_v_nvkz = wp.search("погода в новокузнецке")
    assert len(res_v_nvkz) == 1
    assert "Новокузнецк" in res_v_nvkz[0].title or "Novokuznetsk" in res_v_nvkz[0].title

    res_v_piter = wp.search("погода в питере")
    assert len(res_v_piter) == 1
    assert "Санкт-Петербург" in res_v_piter[0].title or "Saint Petersburg" in res_v_piter[0].title

    res_v_kazan = wp.search("погода в казани")
    assert len(res_v_kazan) == 1
    assert "Казань" in res_v_kazan[0].title or "Kazan" in res_v_kazan[0].title

    # Prepositional queries without 'погода' prefix
    res_prep_msk = wp.search("в москве")
    assert len(res_prep_msk) == 1
    assert "Москва" in res_prep_msk[0].title or "Moscow" in res_prep_msk[0].title

    res_prep_nvkz = wp.search("в новокузнецке")
    assert len(res_prep_nvkz) == 1
    assert "Новокузнецк" in res_prep_nvkz[0].title or "Novokuznetsk" in res_prep_nvkz[0].title


def test_solar_time_of_day_sync():
    """Verify solar time of day returns valid day/dusk/night state."""
    import datetime

    # Noon UTC at 0 lon -> should be day
    noon = datetime.datetime(2026, 6, 21, 12, 0, tzinfo=datetime.timezone.utc)
    tod, is_day = determine_solar_time_of_day(51.5, 0.0, noon)
    assert tod == "day"
    assert is_day == 1

    # Midnight UTC at 0 lon -> should be night
    midnight = datetime.datetime(2026, 6, 21, 0, 0, tzinfo=datetime.timezone.utc)
    tod_night, is_day_night = determine_solar_time_of_day(51.5, 0.0, midnight)
    assert tod_night == "night"
    assert is_day_night == 0


def test_weather_preview_bounded_geometry_and_no_canvas_leak(sample_weather_result):
    from weather_atmosphere import WeatherAtmosphereBox
    widget = PreviewManager.render(sample_weather_result)
    assert isinstance(widget, Gtk.Box)
    # Must NOT be an AtmosphericCapsuleBox or WeatherAtmosphereBox
    assert not isinstance(widget, WeatherAtmosphereBox)
    # Check classes: must have preview-panel, but not canvas active
    classes = widget.get_css_classes()
    assert "preview-panel" in classes
    assert "weather-canvas-active" not in classes
