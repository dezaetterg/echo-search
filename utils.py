import os
import sys

try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
except ValueError as e:
    print(f"[FATAL] GTK/LayerShell version error: {e}", file=sys.stderr)
    sys.exit(1)

def set_icon_safe(widget: Gtk.Image, icon_ref: str, fallback_icon: str = "application-x-executable", pixel_size: int = None, is_paintable: bool = False, raw_pixbuf=None):
    """
    Safely sets an icon to a Gtk.Image widget.
    
    :param widget: The Gtk.Image widget
    :param icon_ref: The path to the image file or the name of the system icon
    :param fallback_icon: The name of the system icon to use as a fallback
    :param pixel_size: Optional pixel size for scaling/sizing
    :param is_paintable: If true, tries to treat raw_pixbuf as a Paintable/Texture first
    :param raw_pixbuf: Direct GdkPixbuf or Paintable object to load
    """
    
    if pixel_size:
        widget.set_pixel_size(pixel_size)

    # 1. Если передан готовый pixbuf / paintable (используется в асинхронных миниатюрах)
    if raw_pixbuf is not None:
        try:
            if is_paintable:
                try:
                    texture = Gdk.Texture.new_for_pixbuf(raw_pixbuf)
                    widget.set_from_paintable(texture)
                    return
                except Exception as e:
                    print(f"[WARN] Failed to create texture from pixbuf, falling back to pixbuf: {e}")
                    # Ошибка создания текстуры, падаем на pixbuf
            widget.set_from_pixbuf(raw_pixbuf)
            return
        except Exception as e:
            print(f"[WARN] Failed to set raw pixbuf/paintable, falling back: {e}")

    # 2. Если передан путь к файлу
    if icon_ref and os.path.isabs(icon_ref):
        if os.path.exists(icon_ref):
            try:
                if pixel_size:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_ref, pixel_size, pixel_size, True)
                else:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_ref)
                widget.set_from_pixbuf(pixbuf)
                return
            except Exception as e:
                print(f"[WARN] Failed to load absolute path '{icon_ref}', falling back: {e}")
        else:
            pass # Файл не существует, идём к fallback

    # 3. Если передано системное имя или предыдущие шаги провалились
    if icon_ref and not os.path.isabs(icon_ref):
        try:
            # Пробуем установить переданное имя (если это не путь)
            widget.set_from_icon_name(icon_ref)
            return
        except Exception as e:
            print(f"[WARN] Failed to load icon name '{icon_ref}', falling back: {e}")

    # 4. Fallback 1: Попытка установить fallback_icon
    if fallback_icon:
        try:
            widget.set_from_icon_name(fallback_icon)
            return
        except Exception as e:
            print(f"[WARN] Failed to load fallback icon '{fallback_icon}', ultimate fallback: {e}")

    # 5. Ultimate Fallback (всегда должно работать)
    try:
        widget.set_from_icon_name("application-x-executable")
    except Exception as e:
        print(f"[ERROR] Ultimate fallback failed, icon will be broken: {e}")
