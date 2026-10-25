"""Unit tests for Quick Look theme adaptation, editor features, and fullscreen."""
from __future__ import annotations

import os
import tempfile

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk

from quick_look import QuickLookWindow


class DummyConfigManager:
    def __init__(self, theme: str = "dark_glass"):
        self.theme = theme

    def get(self, key: str, default=None):
        if key == "theme":
            return self.theme
        return default


class DummyParentWindow:
    def __init__(self, theme: str = "dark_glass"):
        self.config_manager = DummyConfigManager(theme)


def test_quick_look_get_active_theme():
    # Light variants
    ql = QuickLookWindow(parent_window=DummyParentWindow("light"))
    assert ql.get_active_theme() == "light"

    ql_glass = QuickLookWindow(parent_window=DummyParentWindow("light_glass"))
    assert ql_glass.get_active_theme() == "light"

    # Aura Glow
    ql_aura = QuickLookWindow(parent_window=DummyParentWindow("aura_glow"))
    assert ql_aura.get_active_theme() == "aura_glow"

    # Dark variants
    ql_dark = QuickLookWindow(parent_window=DummyParentWindow("dark"))
    assert ql_dark.get_active_theme() == "dark"

    ql_dark_glass = QuickLookWindow(parent_window=DummyParentWindow("dark_glass"))
    assert ql_dark_glass.get_active_theme() == "dark"

    ql_silver = QuickLookWindow(parent_window=DummyParentWindow("silver"))
    assert ql_silver.get_active_theme() == "dark"


def test_quick_look_apply_theme_classes():
    ql = QuickLookWindow(parent_window=DummyParentWindow("dark_glass"))

    # Initial state should have dark theme class
    assert ql.has_css_class("quick-look-theme-dark")
    assert ql.card_box.has_css_class("quick-look-theme-dark")
    assert not ql.card_box.has_css_class("outer-border-box")

    # Switch to light
    ql.apply_theme("light")
    assert ql.has_css_class("quick-look-theme-light")
    assert ql.card_box.has_css_class("quick-look-theme-light")
    assert not ql.has_css_class("quick-look-theme-dark")
    assert not ql.card_box.has_css_class("quick-look-theme-dark")

    # Switch to aura_glow
    ql.apply_theme("aura_glow")
    assert ql.has_css_class("quick-look-theme-aura-glow")
    assert ql.card_box.has_css_class("quick-look-theme-aura-glow")
    assert not ql.has_css_class("quick-look-theme-light")
    assert not ql.card_box.has_css_class("quick-look-theme-light")


def test_quick_look_syntax_palettes():
    ql = QuickLookWindow(parent_window=DummyParentWindow("dark_glass"))

    light_palette = ql._get_syntax_palette("light")
    aura_palette = ql._get_syntax_palette("aura_glow")
    dark_palette = ql._get_syntax_palette("dark")

    # Validate distinct palettes
    assert light_palette["tok_kw"]["foreground"] == "#cf222e"  # GitHub Light red
    assert aura_palette["tok_kw"]["foreground"] == "#ff79c6"   # Dracula Pink
    assert dark_palette["tok_kw"]["foreground"] == "#ff7b72"   # GitHub Dark coral

    assert light_palette["tok_str"]["foreground"] == "#0a3069" # Deep blue
    assert aura_palette["tok_str"]["foreground"] == "#f1fa8c"  # Dracula Yellow
    assert dark_palette["tok_str"]["foreground"] == "#a5d6ff"  # Light blue


def test_quick_look_dynamic_syntax_tag_updates():
    ql = QuickLookWindow(parent_window=DummyParentWindow("dark_glass"))
    buffer = Gtk.TextBuffer()
    ql._init_syntax_tags(buffer)
    ql._text_buffer = buffer

    tag_table = buffer.get_tag_table()
    kw_tag = tag_table.lookup("tok_kw")
    assert kw_tag is not None
    # Initially dark theme (#ff7b72 -> 255, 123, 114)
    rgba_dark = kw_tag.get_property("foreground-rgba")
    assert rgba_dark is not None
    assert round(rgba_dark.red * 255) == 255
    assert round(rgba_dark.green * 255) == 123
    assert round(rgba_dark.blue * 255) == 114

    # Switch to light theme via apply_theme (#cf222e -> 207, 34, 46)
    ql.apply_theme("light")
    rgba_light = kw_tag.get_property("foreground-rgba")
    assert rgba_light is not None
    assert round(rgba_light.red * 255) == 207
    assert round(rgba_light.green * 255) == 34
    assert round(rgba_light.blue * 255) == 46

    # Switch to aura_glow (#ff79c6 -> 255, 121, 198)
    ql.apply_theme("aura_glow")
    rgba_aura = kw_tag.get_property("foreground-rgba")
    assert rgba_aura is not None
    assert round(rgba_aura.red * 255) == 255
    assert round(rgba_aura.green * 255) == 121
    assert round(rgba_aura.blue * 255) == 198


def test_quick_look_fullscreen_toggle():
    ql = QuickLookWindow(parent_window=DummyParentWindow("dark_glass"))
    assert ql.is_fullscreen() is False
    assert ql.maximize_btn.get_icon_name() == "view-fullscreen-symbolic"

    # Toggle to fullscreen
    ql._toggle_fullscreen()
    assert ql.is_fullscreen() is True
    assert ql.maximize_btn.get_icon_name() == "view-restore-symbolic"
    assert "view-restore-symbolic" in ql.maximize_btn.get_icon_name()

    # Toggle back to windowed
    ql._toggle_fullscreen()
    assert ql.is_fullscreen() is False
    assert ql.maximize_btn.get_icon_name() == "view-fullscreen-symbolic"

    # Fullscreen then hide_preview should restore windowed state
    ql._toggle_fullscreen()
    assert ql.is_fullscreen() is True
    ql.hide_preview()
    assert ql.is_fullscreen() is False
    assert ql.maximize_btn.get_icon_name() == "view-fullscreen-symbolic"


def test_quick_look_text_editor_features():
    ql = QuickLookWindow(parent_window=DummyParentWindow("dark_glass"))
    lines = "\n".join([f"code_line_{i} = {i}" for i in range(150)])
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(lines)
        fpath = f.name

    try:
        ql._render_text_view(fpath, 1, ".py")
        assert ql._text_editor_active is True
        assert ql._text_is_writable is True
        assert ql._text_view.get_editable() is True
        assert ql._text_save_btn.get_sensitive() is True

        # Undo / Redo must be enabled on the buffer
        buf = ql._text_view.get_buffer()
        assert buf.get_enable_undo() is True

        # Line numbers TextView must be wrapped in ScrolledWindow with natural height propagation disabled
        lines_tv = ql._text_line_numbers_tv
        lines_scroll = lines_tv.get_parent()
        assert isinstance(lines_scroll, Gtk.ScrolledWindow)
        assert lines_scroll.get_propagate_natural_height() is False
        assert lines_scroll.get_policy() == (Gtk.PolicyType.NEVER, Gtk.PolicyType.EXTERNAL)

        # Vertical adjustment must be synchronized with editor scroll
        editor_scroll = ql._text_view.get_parent()
        assert isinstance(editor_scroll, Gtk.ScrolledWindow)
        assert lines_scroll.get_vadjustment() == editor_scroll.get_vadjustment()
    finally:
        if os.path.exists(fpath):
            os.remove(fpath)


def test_quick_look_readonly_file():
    ql = QuickLookWindow(parent_window=DummyParentWindow("dark_glass"))
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("read only content\n")
        fpath = f.name

    os.chmod(fpath, 0o444)
    try:
        ql._render_text_view(fpath, 1, ".txt")
        assert ql._text_editor_active is True
        assert ql._text_is_writable is False
        assert ql._text_view.get_editable() is False
        assert ql._text_save_btn.get_sensitive() is False
    finally:
        os.chmod(fpath, 0o666)
        if os.path.exists(fpath):
            os.remove(fpath)


def test_quick_look_key_handling_escape_and_f11():
    ql = QuickLookWindow(parent_window=DummyParentWindow("dark_glass"))
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write("val = 42\n")
        fpath = f.name

    try:
        ql._render_text_view(fpath, 1, ".py")
        ql._text_view.grab_focus()

        # 1. F11 toggles fullscreen even when editor is active
        assert ql.is_fullscreen() is False
        ret = ql._on_key_pressed(None, Gdk.KEY_F11, 0, 0)
        assert ret is True
        assert ql.is_fullscreen() is True

        # 2. Escape in fullscreen exits fullscreen, doesn't hide window
        ret = ql._on_key_pressed(None, Gdk.KEY_Escape, 0, 0)
        assert ret is True
        assert ql.is_fullscreen() is False

        # 3. Dirty editor: first Escape prompts confirmation, doesn't close
        ql._text_dirty = True
        ret = ql._on_key_pressed(None, Gdk.KEY_Escape, 0, 0)
        assert ret is True
        assert "⚠️" in ql._text_status_badge.get_label()
        assert getattr(ql, "_last_esc_timestamp", 0) > 0

        # Second Escape within 2.5s closes preview
        ret = ql._on_key_pressed(None, Gdk.KEY_Escape, 0, 0)
        assert ret is True
    finally:
        if os.path.exists(fpath):
            os.remove(fpath)

