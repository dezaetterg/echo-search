try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk
except ValueError:
    pass

from .search import SearchMode
from .apps import AppsMode
from .files import FilesMode
from .settings import SettingsMode
from .clipboard import ClipboardMode
from .emoji import EmojiMode

from i18n import t

class ModeManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.engine = main_window.engine
        self.current_results = []
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(180)
        self.stack.set_interpolate_size(False)
        
        # Initialize modes
        self.modes = {
            "Search": SearchMode(main_window),
            "Apps": AppsMode(main_window),
            "Files": FilesMode(main_window),
            "Settings": SettingsMode(main_window),
            "Clipboard": ClipboardMode(main_window),
            "Emoji": EmojiMode(main_window)
        }
        
        # Add modes to stack
        for name, mode in self.modes.items():
            self.stack.add_named(mode.get_widget(), name)
            
        self.active_mode_name = "Search"
        self.stack.set_visible_child_name(self.active_mode_name)
        
        # Preload data in background idle without blocking UI
        from gi.repository import GLib
        if hasattr(self.modes["Apps"], "_preload_apps"):
            GLib.idle_add(self.modes["Apps"]._preload_apps)
        if hasattr(self.modes["Emoji"], "_preload_emojis"):
            GLib.idle_add(self.modes["Emoji"]._preload_emojis)
        if hasattr(self.modes["Files"], "_preload_files"):
            GLib.idle_add(self.modes["Files"]._preload_files)

    def get_widget(self) -> Gtk.Widget:
        return self.stack

    def refresh_placeholder(self):
        mode_name = self.active_mode_name
        if mode_name == "Apps":
            self.main_window.entry.set_placeholder_text(t("apps_placeholder"))
        elif mode_name == "Files":
            self.main_window.entry.set_placeholder_text(t("files_placeholder"))
        elif mode_name == "Clipboard":
            self.main_window.entry.set_placeholder_text(t("clipboard_placeholder"))
        elif mode_name == "Emoji":
            self.main_window.entry.set_placeholder_text(t("emoji_placeholder"))
        elif mode_name == "Settings":
            self.main_window.entry.set_placeholder_text(t("settings_placeholder"))
        else:
            self.main_window.entry.set_placeholder_text(t("search_placeholder"))

    def get_active_mode(self):
        return self.modes[self.active_mode_name]

    def set_mode(self, mode_name: str):
        if mode_name in self.modes and mode_name != self.active_mode_name:
            if self.active_mode_name in self.modes:
                old_mode = self.modes[self.active_mode_name]
                if hasattr(old_mode, 'on_deactivated'):
                    old_mode.on_deactivated()
                    
            self.active_mode_name = mode_name
            self.stack.set_visible_child_name(mode_name)
            
            # Обновление placeholder текста
            if mode_name == "Apps":
                self.main_window.entry.set_placeholder_text(t("apps_placeholder"))
            elif mode_name == "Files":
                self.main_window.entry.set_placeholder_text(t("files_placeholder"))
            elif mode_name == "Clipboard":
                self.main_window.entry.set_placeholder_text(t("clipboard_placeholder"))
            elif mode_name == "Emoji":
                self.main_window.entry.set_placeholder_text(t("emoji_placeholder"))
            elif mode_name == "Settings":
                self.main_window.entry.set_placeholder_text(t("settings_placeholder"))
            else:
                self.main_window.entry.set_placeholder_text(t("search_placeholder"))
                
            self.modes[mode_name].on_activated()
            self.on_search_changed(self.main_window.entry.get_text())

    def on_search_changed(self, query: str):
        active_mode = self.get_active_mode()
        category = active_mode.get_category_filter()
        query = query.strip()
        
        if not query:
            if category == "Apps":
                self.current_results = self.engine.get_all_apps()
                active_mode.render(self.current_results)
            elif category == "Clipboard":
                self.current_results = self.engine.get_clipboard_history()
                active_mode.render(self.current_results)
            elif category == "Files":
                self.current_results = self.engine.get_recent_files()
                active_mode.render(self.current_results)
            elif category == "Emoji":
                self.current_results = self.engine.get_all_emojis()
                active_mode.render(self.current_results)
            else:
                self.current_results = []
                active_mode.render(self.current_results)
            return
                
        cfg_limit = self.main_window.config_manager.get("results_limit", 20) if self.main_window.config_manager else 20
        limit = 100 if category in ("Apps", "Settings") else cfg_limit
        self.engine.search_async(query, limit=limit, category_filter=category, callback=self._on_search_completed)

    def _on_search_completed(self, results, search_id):
        if self.engine._current_search_id != search_id:
            return
            
        self.current_results = results
        self.get_active_mode().render(results)

    def on_key_pressed(self, keyval, state) -> bool:
        return self.get_active_mode().on_key_pressed(keyval, state, self.current_results)
