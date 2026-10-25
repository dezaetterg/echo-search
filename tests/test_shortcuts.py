import gi
import pytest

gi.require_version("Gdk", "4.0")
from gi.repository import Gdk

from utils import format_shortcut_display, matches_shortcut


def test_matches_shortcut_basic():
    # Single keys
    assert matches_shortcut(Gdk.KEY_Escape, 0, "<Escape>") or matches_shortcut(Gdk.KEY_Escape, 0, "Escape")
    assert matches_shortcut(Gdk.KEY_Return, 0, "<Return>") or matches_shortcut(Gdk.KEY_Return, 0, "Return")


def test_matches_shortcut_modifiers():
    # Ctrl + Space
    assert matches_shortcut(Gdk.KEY_space, Gdk.ModifierType.CONTROL_MASK, "<Ctrl>space")
    assert matches_shortcut(Gdk.KEY_space, Gdk.ModifierType.CONTROL_MASK, "<Control>space")

    # Alt + Return
    assert matches_shortcut(Gdk.KEY_Return, Gdk.ModifierType.ALT_MASK, "<Alt>Return")

    # Super + Space
    assert matches_shortcut(Gdk.KEY_space, Gdk.ModifierType.SUPER_MASK, "<Super>space")


def test_matches_shortcut_reject_invalids():
    # Must reject lonely modifiers without base key
    assert not matches_shortcut(Gdk.KEY_space, 0, "<Ctrl>")
    assert not matches_shortcut(Gdk.KEY_space, Gdk.ModifierType.CONTROL_MASK, "<Ctrl>")
    assert not matches_shortcut(Gdk.KEY_space, 0, "")
    assert not matches_shortcut(Gdk.KEY_space, 0, None)

    # Must reject mismatched key or mismatched modifiers
    assert not matches_shortcut(Gdk.KEY_a, Gdk.ModifierType.CONTROL_MASK, "<Ctrl>b")
    assert not matches_shortcut(Gdk.KEY_space, Gdk.ModifierType.SHIFT_MASK, "<Ctrl>space")


def test_format_shortcut_display():
    assert format_shortcut_display("<Ctrl>space", lang="ru") == "Ctrl + Пробел"
    assert format_shortcut_display("<Ctrl>space", lang="en") == "Ctrl + Space"
    assert format_shortcut_display("<Super><Shift>Return", lang="en") == "Super + Shift + Enter"
    assert format_shortcut_display("<Alt>Escape", lang="ru") in ("Alt + Esc", "Alt + Escape")
