from unittest.mock import MagicMock, patch

from config_manager import _detect_system_theme
from utils import normalize_theme_mode, set_clipboard_text


def test_normalize_theme_mode():
    assert normalize_theme_mode("light") == "light"
    assert normalize_theme_mode("light_glass") == "light"
    assert normalize_theme_mode("LIGHT_GLASS") == "light"
    assert normalize_theme_mode("aura_glow") == "aura_glow"
    assert normalize_theme_mode("AURA_GLOW") == "aura_glow"
    assert normalize_theme_mode("dark") == "dark"
    assert normalize_theme_mode("dark_glass") == "dark"
    assert normalize_theme_mode("silver") == "dark"
    assert normalize_theme_mode(None) == "dark"
    assert normalize_theme_mode("") == "dark"


def test_set_clipboard_text_safe():
    assert set_clipboard_text(None) is False
    # Calling with valid string shouldn't crash regardless of display server state
    res = set_clipboard_text("test_echo_search")
    assert isinstance(res, bool)


def test_detect_system_theme_portal_dark():
    mock_proxy = MagicMock()
    mock_variant = MagicMock()
    mock_variant.get_variant().get_variant().get_uint32.return_value = 1
    mock_res = MagicMock()
    mock_res.get_child_value.return_value = mock_variant
    mock_proxy.call_sync.return_value = mock_res

    with patch("gi.repository.Gio.DBusProxy.new_sync", return_value=mock_proxy):
        assert _detect_system_theme() == "dark"


def test_detect_system_theme_portal_light():
    mock_proxy = MagicMock()
    mock_variant = MagicMock()
    mock_variant.get_variant().get_variant().get_uint32.return_value = 2
    mock_res = MagicMock()
    mock_res.get_child_value.return_value = mock_variant
    mock_proxy.call_sync.return_value = mock_res

    with patch("gi.repository.Gio.DBusProxy.new_sync", return_value=mock_proxy):
        assert _detect_system_theme() == "light"


def test_detect_system_theme_kde_fallback():
    with patch("gi.repository.Gio.DBusProxy.new_sync", side_effect=Exception("No Portal")), \
         patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "KDE"}), \
         patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.read_text", return_value="[General]\nColorScheme=BreezeDark\n"):
        assert _detect_system_theme() == "dark"


def test_i18n_formatting_resilience():
    from i18n import t

    # Normal format
    text = t("weather_high_low", high=25, low=15)
    assert "25" in text and "15" in text

    # Missing or mismatch kwargs shouldn't crash
    text_fallback = t("weather_high_low", invalid_kwarg="foo")
    assert isinstance(text_fallback, str)


def test_icon_theme_config_and_assets(tmp_path):
    from pathlib import Path

    from config_manager import ConfigManager

    cfg = ConfigManager(config_dir=str(tmp_path))
    assert cfg.get("icon_theme") == "dark"

    # Check asset paths
    base_dir = Path(__file__).parent.parent / "assets" / "icons" / "themes"
    for theme in ["dark", "light", "aura"]:
        assert (base_dir / theme).exists()
        for size in [48, 64, 128, 256, 512]:
            icon_file = base_dir / theme / f"{size}x{size}" / "apps" / "com.echo.search.png"
            assert icon_file.exists(), f"Missing icon {icon_file}"

    # Test apply_icon_theme
    assert cfg.apply_icon_theme("light") is True
    assert cfg.apply_icon_theme("aura") is True
    assert cfg.apply_icon_theme("dark") is True


def test_icon_theme_localization():
    from i18n import TRANSLATIONS

    keys = [
        "settings_icon_theme",
        "settings_icon_theme_dark",
        "settings_icon_theme_light",
        "settings_icon_theme_aura"
    ]
    for lang, d in TRANSLATIONS.items():
        for k in keys:
            assert k in d, f"Missing {k} in language {lang}"
