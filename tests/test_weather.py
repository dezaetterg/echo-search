import pytest

from providers.weather import (
    WMO_INFO,
    WeatherProvider,
    calculate_detailed_moon,
    calculate_moon_phase,
    calculate_solar_details,
    get_condition_text,
)


@pytest.fixture
def weather_provider():
    return WeatherProvider(None)


def test_wmo_info_codes():
    assert 0 in WMO_INFO
    assert WMO_INFO[0]["ru"] == "Солнечно"
    assert WMO_INFO[0]["en"] in ("Clear", "Clear sky")

    assert 3 in WMO_INFO
    assert WMO_INFO[3]["ru"] == "Облачно"
    assert WMO_INFO[3]["en"] == "Overcast"

    assert 61 in WMO_INFO
    assert "дождь" in WMO_INFO[61]["ru"].lower()
    assert "rain" in WMO_INFO[61]["en"].lower()


def test_condition_text_translation():
    # Day condition text is "Солнечно" for WMO 0, night is "Ясно"
    assert get_condition_text(0, lang="ru", is_day=True) == "Солнечно"
    assert get_condition_text(0, lang="ru", is_day=False) == "Ясно"
    assert get_condition_text(3, lang="en", is_day=True) == "Overcast"
    assert get_condition_text(61, lang="ru", is_day=True) == "Небольшой дождь"


def test_astronomy_moon_phase():
    phase = calculate_moon_phase()
    assert "cycle_fraction" in phase
    assert 0.0 <= phase["cycle_fraction"] <= 1.0
    assert "illumination" in phase
    assert 0.0 <= phase["illumination"] <= 100.0
    assert "phase_name" in phase


def test_astronomy_solar_details():
    from datetime import date

    sd = calculate_solar_details(55.7558, 37.6173, date.today(), 3.0, is_ru=True)
    assert "daylight_str" in sd
    assert "sunrise" in sd
    assert "sunset" in sd
    assert "curve_points" in sd


def test_astronomy_detailed_moon():
    from datetime import datetime, timezone

    dm = calculate_detailed_moon(55.7558, 37.6173, datetime.now(timezone.utc), 3.0, is_ru=True)
    assert "phase_name" in dm
    assert "distance_km" in dm
    assert "next_full_moon_date_str" in dm
    assert "next_new_moon_date_str" in dm


def test_weather_query_routing(weather_provider):
    # Empty query without category filter returns []
    assert weather_provider.search("") == []

    # Empty query with category_filter='Weather' returns default city
    res_cat = weather_provider.search("", category_filter="Weather")
    assert len(res_cat) == 1
    assert hasattr(res_cat[0], "preview_data")

    # Direct keyword 'погода' returns default city
    res_keyword = weather_provider.search("погода")
    assert len(res_keyword) == 1
    assert hasattr(res_keyword[0], "preview_data")


def test_weather_offline_fallback(weather_provider, monkeypatch):
    # Mock network fetch failure
    monkeypatch.setattr(weather_provider, "_fetch_forecast_sync", lambda *args, **kwargs: None)

    res = weather_provider.search("москва", limit=1)
    assert len(res) == 1
    data = res[0].preview_data
    assert data is not None
    assert "temp" in data
    assert "city_name" in data
    assert "summary" in data
    assert "hourly" in data
    assert "daily" in data


def test_temperature_unit_conversion():
    from providers.weather import convert_temp, convert_temp_diff, format_temp

    # Celsius passthrough
    assert convert_temp(0, 'celsius') == 0
    assert convert_temp(25, 'celsius') == 25
    assert convert_temp(-10, 'celsius') == -10
    assert convert_temp(None, 'celsius') == 0

    # Fahrenheit conversions: round(C * 1.8 + 32)
    assert convert_temp(0, 'fahrenheit') == 32
    assert convert_temp(100, 'fahrenheit') == 212
    assert convert_temp(-40, 'fahrenheit') == -40
    assert convert_temp(20, 'fahrenheit') == 68
    assert convert_temp(25, 'fahrenheit') == 77
    assert convert_temp(-10, 'fahrenheit') == 14
    assert convert_temp(None, 'fahrenheit') == 0

    # Delta conversions: round(delta_C * 1.8)
    assert convert_temp_diff(0, 'celsius') == 0
    assert convert_temp_diff(5, 'celsius') == 5
    assert convert_temp_diff(-5, 'celsius') == -5
    assert convert_temp_diff(0, 'fahrenheit') == 0
    assert convert_temp_diff(5, 'fahrenheit') == 9
    assert convert_temp_diff(-5, 'fahrenheit') == -9
    assert convert_temp_diff(1, 'fahrenheit') == 2

    # Formatting
    assert format_temp(25, 'celsius', show_unit=True) == '25°C'
    assert format_temp(25, 'celsius', show_unit=False) == '25°'
    assert format_temp(25, 'fahrenheit', show_unit=True) == '77°F'
    assert format_temp(25, 'fahrenheit', show_unit=False) == '77°'
    assert format_temp(5, 'fahrenheit', show_sign=True, show_unit=True) == '+41°F'
    assert format_temp(-5, 'fahrenheit', show_sign=True, show_unit=True) == '+23°F'
    assert format_temp(-25, 'fahrenheit', show_sign=True, show_unit=True) == '-13°F'


def test_weather_search_result_fahrenheit(weather_provider, monkeypatch, tmp_path):
    from config_manager import ConfigManager
    from i18n import i18n
    from providers.weather import convert_temp
    mock_cfg = ConfigManager(config_dir=tmp_path)
    i18n.set_language("ru")
    orig_get = mock_cfg.get
    monkeypatch.setattr(mock_cfg, "get", lambda key, default=None: "fahrenheit" if key == "temperature_unit" else ("ru" if key == "language" else orig_get(key, default)))
    weather_provider.config_manager = mock_cfg
    monkeypatch.setattr(weather_provider, "_fetch_forecast_sync", lambda *args, **kwargs: None)

    res = weather_provider.search("москва", limit=1)
    assert len(res) == 1
    item = res[0]
    raw_temp = item.preview_data.get("temp", 0)
    disp_temp = convert_temp(raw_temp, "fahrenheit")
    expected_title = f"Москва: {disp_temp:+d}°" if disp_temp != 0 else "Москва: 0°"
    assert item.title == expected_title
    raw_feels = item.preview_data.get("feels_like", raw_temp)
    disp_feels = convert_temp(raw_feels, "fahrenheit")
    assert f"Ощущается как {disp_feels:+d}°" in item.subtitle
    assert item.preview_data.get("temp_unit") == "fahrenheit"


def test_lightweight_weather_preview_rendering(weather_provider, monkeypatch):
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Gdk", "4.0")
    from gi.repository import Gtk
    Gtk.init()

    from preview_manager import PreviewManager

    monkeypatch.setattr(weather_provider, "_fetch_forecast_sync", lambda *args, **kwargs: None)
    res = weather_provider.search("москва", limit=1)
    result = res[0]

    widget = PreviewManager._render_weather(result)
    assert widget is not None
    assert isinstance(widget, Gtk.Widget)


def test_weather_popover_descriptions_localization():
    from i18n import i18n, t
    modes = ['conditions', 'uv', 'wind', 'precipitation', 'sun', 'moon', 'humidity', 'visibility', 'pressure', 'averages']
    
    i18n.set_language('ru')
    for m in modes:
        desc = t(f'weather_mode_desc_{m}')
        assert desc != f'weather_mode_desc_{m}', f'Missing RU translation for mode {m}'
        assert len(desc) > 0

    i18n.set_language('en')
    for m in modes:
        desc = t(f'weather_mode_desc_{m}')
        assert desc != f'weather_mode_desc_{m}', f'Missing EN translation for mode {m}'
        assert len(desc) > 0
    
    i18n.set_language('ru')


def test_lightweight_weather_metric_item():
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk
    Gtk.init()

    from preview_manager import PreviewManager

    item = PreviewManager._create_weather_metric_item("Влажность", "65%")
    assert isinstance(item, Gtk.Box)
    assert item.get_orientation() == Gtk.Orientation.VERTICAL


def test_preview_manager_lazy_weather_sheet(weather_provider, monkeypatch):
    import sys

    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Gdk", "4.0")
    from gi.repository import Gtk

    Gtk.init()

    from preview_manager import PreviewManager

    monkeypatch.setattr(weather_provider, "_fetch_forecast_sync", lambda *args, **kwargs: None)
    res = weather_provider.search("москва", limit=1)
    result = res[0]

    # Pop weather_detail_sheet if loaded by previous tests
    sys.modules.pop("weather_detail_sheet", None)

    preview_widget = PreviewManager._render_weather(result)
    assert preview_widget is not None

    # Crucial assertion: rendering weather preview must NOT load the heavy 7400-line weather_detail_sheet
    assert "weather_detail_sheet" not in sys.modules
