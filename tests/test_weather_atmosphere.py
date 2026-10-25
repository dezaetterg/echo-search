import os
from unittest.mock import MagicMock

import cairo

from modes.search import SearchMode
from providers.base import SearchResult
from weather_atmosphere import AtmosphericCapsuleBox, CometParticle, StarParticle


def test_comet_particle_lifecycle():
    comet = CometParticle(500.0, 100.0, speed=800.0, angle_deg=205.0)
    assert comet.x == 500.0
    assert comet.y == 100.0
    assert comet.life == comet.max_life
    assert comet.alpha == 0.0

    # Advance small step: alpha should ramp up
    alive = comet.update(0.05)
    assert alive is True
    assert comet.alpha > 0.0

    # Advance until expiration
    alive = comet.update(2.0)
    assert alive is False
    assert comet.life <= 0.0


def test_star_particle_properties():
    star = StarParticle(
        x=100.0,
        y=50.0,
        radius=1.8,
        base_alpha=0.7,
        speed=2.5,
        phase=0.5,
        has_halo=True,
        color_rgb=(0.92, 0.96, 1.0),
    )
    assert star.has_halo is True
    assert star.radius == 1.8
    assert len(star.color_rgb) == 3


def test_atmospheric_capsule_night_state():
    box = AtmosphericCapsuleBox()
    assert len(box._stars) > 100
    assert box._night_clouds_surface is not None

    # Simulate night overcast data
    night_data = {
        'is_day': 0,
        'bg_class': 'weather-bg-clouds-night',
        'condition_text': 'Облачно',
        'weather_code': 3,
    }
    box.set_weather_atmosphere(night_data)
    assert box._is_night() is True
    assert box._is_overcast() is True
    assert box._has_active_animation() is True


def test_atmospheric_capsule_reset_state():
    box = AtmosphericCapsuleBox()
    night_data = {
        'is_day': 0,
        'bg_class': 'weather-bg-clouds-night',
        'condition_text': 'Облачно',
        'weather_code': 3,
    }
    box.set_weather_atmosphere(night_data)
    assert box._weather_data is not None
    assert 'weather-canvas-active' in box.get_css_classes()
    assert 'weather-night-mode' in box.get_css_classes()

    # Reset
    box.set_weather_atmosphere(None)
    assert box._weather_data is None
    assert 'weather-canvas-active' not in box.get_css_classes()
    assert 'weather-night-mode' not in box.get_css_classes()
    assert 'weather-canvas-clouds-night' not in box.get_css_classes()
    assert box._has_active_animation() is False
    assert len(box._particles) == 0


def test_search_mode_weather_style_reset():
    mock_window = MagicMock()
    mock_box = AtmosphericCapsuleBox()
    # Add lingering weather classes to simulate dirty state
    mock_box.add_css_class("weather-canvas-active")
    mock_box.add_css_class("weather-night-mode")
    mock_window.main_box = mock_box
    mock_window.outer_box = MagicMock()

    search_mode = MagicMock(spec=SearchMode)
    search_mode.main_window = mock_window
    search_mode.preview_container = MagicMock()
    search_mode.ALL_WEATHER_CLASSES = SearchMode.ALL_WEATHER_CLASSES
    search_mode.ALL_CANVAS_CLASSES = SearchMode.ALL_CANVAS_CLASSES
    search_mode._update_weather_preview_style = SearchMode._update_weather_preview_style.__get__(search_mode)

    weather_result = SearchResult(
        id="weather_current",
        title="Погода: Москва, +18°C",
        subtitle="Ясно",
        icon="weather-clear",
        score=100.0,
        category="Weather",
        provider="WeatherProvider",
        preview_data={"bg_class": "weather-bg-clear-night", "is_day": 0, "weather_code": 0}
    )

    # Weather result in echo-search must NOT pollute main_box with dynamic canvas classes
    search_mode._update_weather_preview_style(weather_result)
    assert "weather-canvas-active" not in mock_box.get_css_classes()
    assert "weather-night-mode" not in mock_box.get_css_classes()

    # Clear when nothing found or non-weather removes preview classes
    search_mode._update_weather_preview_style(None)
    assert "weather-canvas-active" not in mock_box.get_css_classes()
    assert "weather-night-mode" not in mock_box.get_css_classes()
    search_mode.preview_container.remove_css_class.assert_any_call("preview-panel-weather")

