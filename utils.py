import os
import sys

try:
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
except ValueError as e:
    print(f"[FATAL] GTK/LayerShell version error: {e}", file=sys.stderr)
    sys.exit(1)

# In-memory LRU Pixbuf Cache for ultra-fast icon loading
_PIXBUF_CACHE = {}
_MAX_CACHE_SIZE = 256

def set_icon_safe(widget: Gtk.Image, icon_ref: str, fallback_icon: str = "application-x-executable", pixel_size: int = None, is_paintable: bool = False, raw_pixbuf=None):
    if pixel_size:
        widget.set_pixel_size(pixel_size)

    # 1. Если передан готовый pixbuf / paintable
    if raw_pixbuf is not None:
        try:
            if is_paintable:
                try:
                    texture = Gdk.Texture.new_for_pixbuf(raw_pixbuf)
                    widget.set_from_paintable(texture)
                    return
                except Exception:
                    pass
            widget.set_from_pixbuf(raw_pixbuf)
            return
        except Exception:
            pass

    # 2. Если передан путь к файлу (сверхбыстрый LRU кэш)
    if icon_ref and os.path.isabs(icon_ref):
        cache_key = (icon_ref, pixel_size)
        cached_pixbuf = _PIXBUF_CACHE.get(cache_key)
        if cached_pixbuf:
            widget.set_from_pixbuf(cached_pixbuf)
            return

        if os.path.exists(icon_ref):
            try:
                if pixel_size:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_ref, pixel_size, pixel_size, True)
                else:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_ref)
                
                if len(_PIXBUF_CACHE) >= _MAX_CACHE_SIZE:
                    _PIXBUF_CACHE.pop(next(iter(_PIXBUF_CACHE)))
                _PIXBUF_CACHE[cache_key] = pixbuf
                
                widget.set_from_pixbuf(pixbuf)
                return
            except Exception:
                pass

    # 3. Если передано системное имя темы иконок
    if icon_ref and not os.path.isabs(icon_ref):
        try:
            widget.set_from_icon_name(icon_ref)
            return
        except Exception:
            pass

    # 4. Fallback 1: Попытка установить fallback_icon
    if fallback_icon:
        try:
            widget.set_from_icon_name(fallback_icon)
            return
        except Exception:
            pass

    # 5. Ultimate Fallback
    try:
        widget.set_from_icon_name("application-x-executable")
    except Exception:
        pass


def matches_shortcut(keyval: int, state: int, shortcut: str) -> bool:
    if not shortcut:
        return False
    s = shortcut.strip()
    clean_modifiers = (
        Gdk.ModifierType.CONTROL_MASK |
        Gdk.ModifierType.ALT_MASK |
        Gdk.ModifierType.SHIFT_MASK |
        Gdk.ModifierType.SUPER_MASK
    )
    clean_state = state & clean_modifiers
    req_ctrl = "<ctrl>" in s.lower() or "<control>" in s.lower()
    req_alt = "<alt>" in s.lower()
    req_shift = "<shift>" in s.lower()
    req_super = "<super>" in s.lower()

    if bool(clean_state & Gdk.ModifierType.CONTROL_MASK) != req_ctrl:
        return False
    if bool(clean_state & Gdk.ModifierType.ALT_MASK) != req_alt:
        return False
    if bool(clean_state & Gdk.ModifierType.SHIFT_MASK) != req_shift:
        return False
    if bool(clean_state & Gdk.ModifierType.SUPER_MASK) != req_super:
        return False

    base_key = s
    for mod in ["<Ctrl>", "<ctrl>", "<Control>", "<Alt>", "<alt>", "<Shift>", "<shift>", "<Super>", "<super>"]:
        base_key = base_key.replace(mod, "")
    base_key = base_key.strip().lower()

    key_name = (Gdk.keyval_name(keyval) or "").lower()
    if base_key == "space":
        return keyval in (Gdk.KEY_space, Gdk.KEY_KP_Space) or key_name in ("space", "kp_space")
    elif base_key == "return":
        return keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) or key_name in ("return", "kp_enter")
    elif base_key == "tab":
        return keyval in (Gdk.KEY_Tab, Gdk.KEY_KP_Tab, Gdk.KEY_ISO_Left_Tab)
    else:
        return key_name == base_key


def format_shortcut_display(shortcut: str, lang: str = "en") -> str:
    if not shortcut:
        return "-"
    s = shortcut
    s = s.replace("<Super>", "Super + ").replace("<super>", "Super + ")
    s = s.replace("<Ctrl>", "Ctrl + ").replace("<ctrl>", "Ctrl + ")
    s = s.replace("<Alt>", "Alt + ").replace("<alt>", "Alt + ")
    s = s.replace("<Shift>", "Shift + ").replace("<shift>", "Shift + ")
    parts = s.split(" + ")
    last = parts[-1].strip().lower()
    if last == "space":
        if lang in ("ru", "kk"):
            last_display = "Пробел"
        elif lang == "uk":
            last_display = "Пробіл"
        else:
            last_display = "Space"
    elif last == "return":
        last_display = "Enter"
    else:
        last_display = last.capitalize()

    if len(parts) > 1:
        return " + ".join(parts[:-1]) + " + " + last_display
    return last_display
