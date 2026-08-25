import sys
import os
import signal

# --- Проверка критических зависимостей с понятными подсказками по установке ---
def _check_system_dependencies():
    missing = []
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk, Gio, GLib
    except Exception:
        missing.append("GTK4 / PyGObject (gir1.2-gtk-4.0, python3-gi)")

    try:
        import rapidfuzz
    except ImportError:
        missing.append("rapidfuzz (python3-rapidfuzz или pip install rapidfuzz)")

    if missing:
        print("\n=======================================================", file=sys.stderr)
        print("🌊 Echo Search — Не найдены необходимые зависимости:", file=sys.stderr)
        for item in missing:
            print(f"  • {item}", file=sys.stderr)
        print("\nУстановите зависимости с помощью пакетного менеджера вашей системы:", file=sys.stderr)
        print("  Debian / Ubuntu / Mint: sudo apt install python3-gi gir1.2-gtk-4.0 python3-rapidfuzz", file=sys.stderr)
        print("  Arch Linux:             sudo pacman -S python-gobject gtk4 python-rapidfuzz", file=sys.stderr)
        print("  Fedora:                 sudo dnf install python3-gobject gtk4 python3-rapidfuzz", file=sys.stderr)
        print("  openSUSE:               sudo zypper install python3-gobject typelib-1_0-Gtk-4_0 python3-rapidfuzz", file=sys.stderr)
        print("  Или выполните:          ./install.sh", file=sys.stderr)
        print("=======================================================\n", file=sys.stderr)
        sys.exit(1)

_check_system_dependencies()

import gi
gi.require_version("Gtk", "4.0")

HAS_ADW = False
try:
    gi.require_version("Adw", "1")
    from gi.repository import Adw
    HAS_ADW = True
except Exception:
    HAS_ADW = False

HAS_LAYER_SHELL = False
Gtk4LayerShell = None
try:
    gi.require_version("Gtk4LayerShell", "1.0")
    from gi.repository import Gtk4LayerShell
    HAS_LAYER_SHELL = True
except (ValueError, ImportError):
    HAS_LAYER_SHELL = False

from gi.repository import Gtk, Gio, GLib
from config_manager import ConfigManager
from ui import EchoUI

BaseApplication = Adw.Application if HAS_ADW else Gtk.Application

class EchoApp(BaseApplication):
    def __init__(self):
        # Используем APPLICATION_HANDLES_COMMAND_LINE для обработки повторных вызовов
        super().__init__(application_id="com.echo.search",
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.window = None

    def sync_color_scheme(self):
        if HAS_ADW and hasattr(self, 'config_manager') and self.config_manager:
            try:
                theme = self.config_manager.get("theme", "light")
                sm = Adw.StyleManager.get_default()
                if theme == "dark":
                    sm.set_color_scheme(Adw.ColorScheme.PREFER_DARK)
                elif theme == "light":
                    sm.set_color_scheme(Adw.ColorScheme.PREFER_LIGHT)
                else:
                    sm.set_color_scheme(Adw.ColorScheme.DEFAULT)
            except Exception:
                pass

    def do_activate(self):
        if not self.window:
            self.config_manager = ConfigManager()
            self.sync_color_scheme()
            self.window = EchoUI(application=self, config_manager=self.config_manager)
            
            # Настройка Gtk4LayerShell (Wayland) с fallback для X11 / других DE
            is_layer_shell = False
            if HAS_LAYER_SHELL and Gtk4LayerShell is not None:
                try:
                    if Gtk4LayerShell.is_supported():
                        is_layer_shell = True
                except Exception:
                    is_layer_shell = False

            if is_layer_shell:
                Gtk4LayerShell.init_for_window(self.window)
                Gtk4LayerShell.set_layer(self.window, Gtk4LayerShell.Layer.OVERLAY) # Поверх всего
                Gtk4LayerShell.set_keyboard_mode(self.window, Gtk4LayerShell.KeyboardMode.ON_DEMAND)
                
                # Центрирование с отступом сверху
                Gtk4LayerShell.set_anchor(self.window, Gtk4LayerShell.Edge.TOP, True)
                Gtk4LayerShell.set_anchor(self.window, Gtk4LayerShell.Edge.BOTTOM, False)
                Gtk4LayerShell.set_anchor(self.window, Gtk4LayerShell.Edge.LEFT, False)
                Gtk4LayerShell.set_anchor(self.window, Gtk4LayerShell.Edge.RIGHT, False)
                Gtk4LayerShell.set_margin(self.window, Gtk4LayerShell.Edge.TOP, 160)
            else:
                # Fallback для X11 и сред без LayerShell
                self.window.set_decorated(False)
            
            self.window.set_decorated(False)
            self.window.present()
        else:
            # Тогл видимости окна при повторном запуске (например, шорткатом)
            if self.window.is_visible():
                self.window.hide()
            else:
                self.config_manager.load()
                self.sync_color_scheme()
                self.window.reload_config()
                if self.window.mode_manager:
                    self.window.mode_manager.set_mode("Search")
                self.window.entry.set_text("")
                self.window.update_revealer_state()
                self.window.present()
                self.window.entry.grab_focus()

    def do_command_line(self, command_line):
        self.activate()
        return 0

def on_signal(signum, frame):
    sys.exit(0)

if __name__ == "__main__":
    # Корректная обработка Ctrl+C
    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)
    
    app = EchoApp()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
