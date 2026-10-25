"""Unit tests for style_generator module."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from style_generator import ThemeTokens, build_dynamic_css, resolve_tokens


class DummyConfig:
    def __init__(self, data: dict):
        self._data = data

    def get(self, key: str, default=None):
        return self._data.get(key, default)


def test_resolve_tokens_defaults():
    tokens = resolve_tokens()
    assert isinstance(tokens, ThemeTokens)
    assert tokens.theme == "dark_glass"
    assert not tokens.is_light
    assert tokens.is_glass
    assert "blur(40px)" in tokens.backdrop
    assert tokens.jelly_duration == 220


def test_resolve_tokens_silver_alias():
    cfg = DummyConfig({"theme": "silver"})
    tokens = resolve_tokens(cfg)
    assert tokens.theme == "dark_glass"


def test_resolve_tokens_light():
    cfg = DummyConfig({"theme": "light", "transparency": 0.10, "blur": False})
    tokens = resolve_tokens(cfg)
    assert tokens.is_light
    assert not tokens.is_glass
    assert tokens.backdrop == "backdrop-filter: none;"
    assert tokens.card_bg == "#ffffff"
    assert tokens.alpha == 0.90


def test_resolve_tokens_light_glass():
    cfg = DummyConfig({"theme": "light_glass", "transparency": 0.40})
    tokens = resolve_tokens(cfg)
    assert tokens.is_light
    assert tokens.is_glass
    assert "rgba" in tokens.card_bg
    assert tokens.alpha == 0.60


def test_resolve_tokens_aura_glow():
    cfg = DummyConfig({"theme": "aura_glow"})
    tokens = resolve_tokens(cfg)
    assert not tokens.is_light
    assert tokens.is_glass
    assert "160, 120, 255" in tokens.search_border


def test_animation_speed_and_jelly():
    # fast animation
    tokens_fast = resolve_tokens(DummyConfig({"animation_speed": 200}))
    assert tokens_fast.jelly_duration == 110

    # slow animation
    tokens_slow = resolve_tokens(DummyConfig({"animation_speed": 50}))
    assert tokens_slow.jelly_duration == 440

    # extreme clamp (min speed_factor 0.2 -> 220/0.2 = 1100)
    tokens_extreme = resolve_tokens(DummyConfig({"animation_speed": 1}))
    assert tokens_extreme.jelly_duration == 1100


def test_build_dynamic_css_gtk_compilation():
    for theme in ["dark_glass", "light_glass", "aura_glow", "light", "dark"]:
        cfg = DummyConfig({"theme": theme, "transparency": 0.5, "blur": True, "animation_speed": 100})
        css = build_dynamic_css(cfg)

        assert ".capsule-window-ui" in css
        assert ".search-wrapper" in css
        assert ".outer-border-box" in css
        assert ".anim-jelly-wobble" in css

        # Verify GTK4 parser compiles CSS without syntax error
        provider = Gtk.CssProvider()
        if hasattr(provider, "load_from_string"):
            provider.load_from_string(css)
        else:
            provider.load_from_data(css.encode("utf-8"))


def test_build_dynamic_css_quick_look_themes():
    for theme in ["light", "dark", "aura_glow"]:
        cfg = DummyConfig({"theme": theme, "transparency": 0.5, "blur": True, "animation_speed": 100})
        css = build_dynamic_css(cfg)
        assert ".quick-look-card" in css
        assert ".quick-look-theme-light" in css
        assert ".quick-look-theme-aura-glow" in css
        assert ".quick-look-theme-dark" in css
        assert ".quick-look-editor-card" in css
        assert ".quick-look-audio-hero" in css
        assert ".quick-look-folder-container" in css

        provider = Gtk.CssProvider()
        if hasattr(provider, "load_from_string"):
            provider.load_from_string(css)
        else:
            provider.load_from_data(css.encode("utf-8"))



def test_transparency_shield_and_gtk_theme_isolation():
    cfg = DummyConfig({"theme": "dark_glass", "transparency": 0.5, "blur": True})
    css = build_dynamic_css(cfg)

    # Check that transparency shield rules exist
    assert ".capsule-window-ui scrolledwindow" in css
    assert ".capsule-window-ui .apps-glass-container" in css
    assert ".capsule-window-ui #results-list" in css
    assert ".capsule-window-ui row:not(:hover):not(:selected)" in css
    assert "background: transparent" in css

    # Ensure no invalid !important syntax which causes GTK CSS parser to drop rules
    assert "!important" not in css

    # Verify GTK4 parses the full generated CSS cleanly
    provider = Gtk.CssProvider()
    if hasattr(provider, "load_from_string"):
        provider.load_from_string(css)
    else:
        provider.load_from_data(css.encode("utf-8"))


def test_resolve_tokens_echo_blue():
    cfg = DummyConfig({"theme": "echo_blue"})
    tokens = resolve_tokens(cfg)
    assert tokens.theme == "echo_blue"
    assert not tokens.is_light
    assert tokens.is_glass
    assert "rgba(13, 19, 38" in tokens.bg_color
    css = build_dynamic_css(cfg)
    assert "linear-gradient(180deg, #0a0d1a" in css
    # Test valid GTK4 CSS parsing
    provider = Gtk.CssProvider()
    provider.load_from_data(css.encode("utf-8"))
