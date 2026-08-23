import sys
import os
import signal

try:
    import gi
    gi.require_version('Gtk', '4.0')
    
    HAS_LAYER_SHELL = False
    Gtk4LayerShell = None
    try:
        gi.require_version('Gtk4LayerShell', '1.0')
        from gi.repository import Gtk4LayerShell
        HAS_LAYER_SHELL = True
    except (ValueError, ImportError):
        HAS_LAYER_SHELL = False

    from gi.repository import Gtk, Gio, GLib
except ValueError as e:
    print(f"[FATAL] GTK version error: {e}", file=sys.stderr)
    sys.exit(1)
except ImportError as e:
    print(f"[FATAL] PyGObject import error: {e}", file=sys.stderr)
    sys.exit(1)

from config_manager import ConfigManager
from ui import EchoUI

class EchoApp(Gtk.Application):
    def __init__(self):
        # Используем APPLICATION_HANDLES_COMMAND_LINE для обработки повторных вызовов
        super().__init__(application_id="com.echo.search",
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.window = None

    def do_activate(self):
        if not self.window:
            self.config_manager = ConfigManager()
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
                self.window.reload_config()
                self.window.entry.set_text("") # Очищаем ввод перед показом
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
