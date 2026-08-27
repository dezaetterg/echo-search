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
