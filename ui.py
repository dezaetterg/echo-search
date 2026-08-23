import sys
import os
import gi

try:
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk, GObject, Pango, Gio, GLib
except ValueError as e:
    print(f"[FATAL] GTK version error: {e}", file=sys.stderr)
    sys.exit(1)

from search_engine import SearchEngine
from providers import SearchResult
from modes import ModeManager
from i18n import t, i18n

class EchoUI(Gtk.Window):
    def __init__(self, application=None, config_manager=None):
        super().__init__(application=application)
        self.config_manager = config_manager
        self.set_title("Echo")
        
        self.engine = SearchEngine(config_manager=self.config_manager)
        if self.config_manager:
            self.config_manager.apply_to_engine(self.engine)
            
        self.mode_manager = None
        
        self._setup_ui()
        self._setup_css()
        self._setup_shortcuts()

        # Initialize with default search mode
        if self.mode_manager:
            self.mode_manager.set_mode("Search")
            self.update_revealer_state()
            self.mode_manager.on_search_changed("")

    def _setup_css(self):
        provider = Gtk.CssProvider()
        css_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css'),
            "/usr/lib/echo-search/style.css",
            "/usr/share/echo-search/style.css",
            "/usr/local/share/echo-search/style.css",
            os.path.expanduser("~/.local/share/echo-search/style.css")
        ]
        
        for path in css_paths:
            if os.path.exists(path):
                try:
                    provider.load_from_path(path)
                    Gtk.StyleContext.add_provider_for_display(
                        Gdk.Display.get_default(),
                        provider,
                        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                    )
                    break
                except Exception as e:
                    print(f"Error loading CSS from {path}: {e}")
            
        if self.config_manager:
            theme = self.config_manager.get("theme", "light")
            transparency = self.config_manager.get("transparency", 0.70)
            blur = self.config_manager.get("blur", True)
            
            if theme == "light":
                bg_color = f"rgba(240, 240, 245, {transparency})"
            else:
                bg_color = f"rgba(40, 40, 45, {transparency})"
                
            backdrop = "backdrop-filter: blur(40px);" if blur else "backdrop-filter: none;"
            
            if theme == "light":
                # Точная копия светлой темы с референса
                theme_css = """
                .capsule-window-ui { color: #1c1c1e; }
                .capsule-window-ui .search-icon { color: #8e8e93; }
                
                .capsule-window-ui .search-wrapper {
                    background-color: #ffffff;
                    border-radius: 16px;
                    padding: 4px 12px;
                    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
                }
                
                .capsule-window-ui #search-entry,
                .capsule-window-ui #search-entry text,
                .capsule-window-ui .search-wrapper entry,
                .capsule-window-ui .search-wrapper text { 
                    background: transparent;
                    background-color: transparent;
                    color: #1c1c1e; 
                    caret-color: #007aff; 
                    border: none;
                    box-shadow: none;
                    outline: none;
                }
                .capsule-window-ui #search-entry:focus,
                .capsule-window-ui #search-entry text:focus,
                .capsule-window-ui .search-wrapper entry:focus { 
                    border: none;
                    box-shadow: none; 
                    outline: none;
                    background: transparent;
                    background-color: transparent;
                }
                
                .capsule-window-ui label.result-title { color: #1c1c1e; }
                .capsule-window-ui label.result-desc { color: #8e8e93; }
                
                .capsule-window-ui #results-list {
                    background-color: #ffffff;
                    border-radius: 16px;
                    margin: 0 8px 16px 16px;
                    padding: 8px;
                    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
                }
                
                .capsule-window-ui row, .capsule-window-ui .result-row { background-color: transparent; }
                .capsule-window-ui row:hover, .capsule-window-ui .result-row:hover { background-color: rgba(0,0,0,0.03); border-radius: 8px; }
                
                .capsule-window-ui row:selected, .capsule-window-ui .result-row:selected {
                    background-color: rgba(0,0,0,0.04);
                    color: #1c1c1e;
                    box-shadow: none;
                    border-radius: 8px;
                }
                
                .capsule-window-ui .chip,
                .capsule-window-ui .apps-filter-pill {
                    color: #8e8e93;
                    border: 1px solid rgba(0,0,0,0.05);
                    background-color: rgba(255,255,255,0.5);
                }
                .capsule-window-ui .chip:hover,
                .capsule-window-ui .apps-filter-pill:hover { 
                    background-color: #ffffff; 
                    color: #3c3c43;
                }
                .capsule-window-ui .chip.active,
                .capsule-window-ui .apps-filter-pill.active {
                    background-color: #ffffff;
                    color: #1c1c1e;
                    border: 1px solid rgba(0,0,0,0.1);
                    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
                }
                
                .capsule-window-ui .main-separator { background-color: transparent; }
                
                .capsule-window-ui label.preview-main-title { color: #1c1c1e; text-shadow: none; }
                .capsule-window-ui label.preview-main-subtitle { color: #8e8e93; text-shadow: none; }
                
                .capsule-window-ui label.launchpad-title,
                .capsule-window-ui label.finder-title,
                .capsule-window-ui label.emoji-title,
                .capsule-window-ui label.files-section-title { 
                    color: #1c1c1e; 
                    text-shadow: none; 
                }
                
                .capsule-window-ui .launchpad-card.selected label.launchpad-title,
                .capsule-window-ui .launchpad-card:selected label.launchpad-title,
                .capsule-window-ui .finder-card.selected label.finder-title,
                .capsule-window-ui .finder-card:selected label.finder-title,
                .capsule-window-ui .emoji-card.selected label.emoji-title,
                .capsule-window-ui .emoji-card:selected label.emoji-title {
                    color: #1c1c1e;
                }
                
                .capsule-window-ui .preview-panel {
                    background-color: #ffffff;
                    border-radius: 16px;
                    margin: 0 16px 16px 8px;
                    border-left: none;
                    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
                }
                
                .capsule-window-ui .preview-meta-card {
                    background: #f9f9fb;
                    border: none;
                }
                .capsule-window-ui label.preview-meta-key { color: rgba(0,0,0,0.5); font-weight: 600; }
                .capsule-window-ui label.preview-meta-val { color: #1c1c1e; font-weight: 500; }
                
                .capsule-window-ui .preview-btn {
                    background: #ffffff;
                    color: #1c1c1e;
                    border: 1px solid rgba(0,0,0,0.06);
                    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
                }
                .capsule-window-ui .preview-btn:hover {
                    background: #f9f9fb;
                    color: #000;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                }
                
                .capsule-window-ui .mode-button {
                    background: #ffffff;
                    color: #8e8e93;
                    border: none;
                    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
                }
                .capsule-window-ui .mode-button:hover {
                    background: #ffffff;
                    color: #3c3c43;
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
                }
                .capsule-window-ui .mode-button.active {
                    background: #ffffff;
                    color: #1c1c1e;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
                }
                """
            else:
                # Темная тема в стиле Liquid Glass
                theme_css = """
                .capsule-window-ui { color: #f5f5f7; }
                .capsule-window-ui .search-icon { color: rgba(255, 255, 255, 0.7); }
                
                .capsule-window-ui .search-wrapper {
                    background-color: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-radius: 16px;
                    padding: 4px 12px;
                    box-shadow: 0 4px 14px rgba(0,0,0,0.2);
                }
                
                .capsule-window-ui #search-entry,
                .capsule-window-ui #search-entry text,
                .capsule-window-ui .search-wrapper entry,
                .capsule-window-ui .search-wrapper text { 
                    background: transparent;
                    background-color: transparent;
                    color: #ffffff; 
                    caret-color: #007aff; 
                    border: none;
                    box-shadow: none;
                    outline: none;
                }
                .capsule-window-ui #search-entry:focus,
                .capsule-window-ui #search-entry text:focus,
                .capsule-window-ui .search-wrapper entry:focus { 
                    border: none;
                    box-shadow: none; 
                    outline: none;
                    background: transparent;
                    background-color: transparent;
                }
                
                .capsule-window-ui .mode-button {
                    background: rgba(255, 255, 255, 0.08);
                    color: rgba(255, 255, 255, 0.7);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
                }
                .capsule-window-ui .mode-button:hover {
                    background: rgba(255, 255, 255, 0.14);
                    color: #ffffff;
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
                }
                .capsule-window-ui .mode-button.active {
                    background: rgba(255, 255, 255, 0.22);
                    color: #ffffff;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
                }
                """
                
            dynamic_css = f"""
            .capsule-window-ui {{
                background-color: {bg_color};
                {backdrop}
            }}
            {theme_css}
            """
            
            if hasattr(self, '_dynamic_css_provider') and self._dynamic_css_provider:
                Gtk.StyleContext.remove_provider_for_display(
                    Gdk.Display.get_default(),
                    self._dynamic_css_provider
                )
                
            self._dynamic_css_provider = Gtk.CssProvider()
            self._dynamic_css_provider.load_from_data(dynamic_css.encode('utf-8'))
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                self._dynamic_css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_USER
            )

    def _setup_ui(self):
        # Самый внешний контейнер окна
        self.root_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.root_box.add_css_class("root-box")
        self.root_box.set_valign(Gtk.Align.START)
        # Обертка для перемещения окна на Wayland
        self.window_handle = Gtk.WindowHandle()
        self.window_handle.set_child(self.root_box)
        self.set_child(self.window_handle)

        # Наружный контейнер для градиентной окантовки основной капсулы
        self.outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.outer_box.add_css_class("outer-border-box")
        self.outer_box.set_valign(Gtk.Align.START)
        self.outer_box.set_hexpand(True)
        self.root_box.append(self.outer_box)

        # Основной контейнер-капсула (UI)
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.add_css_class("capsule-window-ui")
        self.main_box.set_valign(Gtk.Align.START) 
        self.outer_box.append(self.main_box)

        # --- ОБНОВЛЕННЫЙ HEADER ДЛЯ СВЕТЛОЙ ТЕМЫ ---
        # Общий контейнер для строки поиска и кнопок режимов
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.header_box.set_hexpand(True)
        self.header_box.set_spacing(12)
        self.header_box.set_margin_top(12)
        self.header_box.set_margin_start(16)
        self.header_box.set_margin_end(16)
        self.header_box.set_margin_bottom(8)
        self.main_box.append(self.header_box)
        
        # Контейнер только для поиска (иконка + ввод)
        self.search_wrapper = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.search_wrapper.set_hexpand(True)
        self.search_wrapper.add_css_class("search-wrapper")
        self.header_box.append(self.search_wrapper)

        # Иконка поиска
        search_icon = Gtk.Image.new_from_icon_name("system-search-symbolic")
        search_icon.set_pixel_size(24)
        search_icon.add_css_class("search-icon")
        self.search_wrapper.append(search_icon)

        # Поле ввода
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text(t("search_placeholder"))
        self.entry.set_hexpand(True)
        self.entry.set_name("search-entry")
        self.entry.connect("changed", self.on_search_changed)
        self.entry.connect("activate", self.on_search_activate)
        self.search_wrapper.append(self.entry)
        
        # Контейнер для кнопок режимов с анимацией появления (Revealer)
        self.mode_buttons_revealer = Gtk.Revealer()
        self.mode_buttons_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_LEFT)
        
        animations = self.config_manager.get("animations") if self.config_manager else True
        anim_duration = 200 if animations else 0
        self.mode_buttons_revealer.set_transition_duration(anim_duration)
        
        self.mode_buttons_revealer.set_halign(Gtk.Align.END)
        self.mode_buttons_revealer.set_valign(Gtk.Align.CENTER)
        
        self.mode_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.mode_buttons_box.set_spacing(6)
        self.mode_buttons_revealer.set_child(self.mode_buttons_box)
        
        # Кнопки режимов добавляются В HEADER (внутри основной капсулы)
        self.header_box.append(self.mode_buttons_revealer)
        
        # Кнопки режимов (Mode Buttons)
        all_modes = [
            ("Apps", "view-app-grid-symbolic"),
            ("Files", "folder-symbolic"),
            ("Clipboard", "edit-paste-symbolic"),
            ("Emoji", "emblem-favorite-symbolic"),
            ("Settings", "preferences-system-symbolic")
        ]
        
        # Проверка поддержки буфера обмена на текущем дисплее/сервере
        clipboard_supported = True
        try:
            disp = Gdk.Display.get_default()
            if not disp or not disp.get_clipboard():
                clipboard_supported = False
        except Exception:
            clipboard_supported = False

        enabled_modes_list = self.config_manager.get("enabled_modes") if self.config_manager else [m[0] for m in all_modes]
        self.mode_buttons = {}
        for name, icon_name in all_modes:
            btn = Gtk.Button()
            btn.set_valign(Gtk.Align.CENTER) # Запрещает растягивание по вертикали (чтобы были идеальные круги)
            btn.set_halign(Gtk.Align.CENTER)
            btn.add_css_class("mode-button")
            # Set fixed icon size using image
            image = Gtk.Image.new_from_icon_name(icon_name)
            image.set_pixel_size(16)
            btn.set_child(image)
            btn.connect("clicked", self.on_mode_button_clicked, name)
            
            is_visible = (name in enabled_modes_list)
            if name == "Clipboard" and not clipboard_supported:
                is_visible = False
                
            btn.set_visible(is_visible)
            self.mode_buttons_box.append(btn)
            self.mode_buttons[name] = btn
            
        # Инициализируем ModeManager и оборачиваем в Revealer для динамической высоты окна
        self.mode_manager = ModeManager(self)
        
        # Единый контейнер для всех режимов, задающий глобальные отступы
        self.results_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.results_container.add_css_class("results-container")
        self.results_container.append(self.mode_manager.get_widget())
        
        self.results_revealer = Gtk.Revealer()
        self.results_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.results_revealer.set_transition_duration(anim_duration)
        self.results_revealer.set_child(self.results_container)
        self.results_revealer.set_reveal_child(False)
        
        self.main_box.append(self.results_revealer)

    def _setup_shortcuts(self):
        key_ctrl = Gtk.EventControllerKey.new()
        key_ctrl.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_ctrl)

    def on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            query = self.entry.get_text()
            if self.mode_manager and self.mode_manager.active_mode_name != "Search":
                self.mode_manager.set_mode("Search")
                self.entry.set_text("")
                self.update_revealer_state()
                return True
            elif query:
                self.entry.set_text("")
                self.update_revealer_state()
                return True
            else:
                self.hide()
                return True
                
        # Выход из режима по Backspace, если строка поиска пустая
        if keyval == Gdk.KEY_BackSpace:
            if self.mode_manager and self.mode_manager.active_mode_name != "Search":
                if len(self.entry.get_text()) == 0:
                    self.mode_manager.set_mode("Search")
                    self.update_revealer_state()
                    return True
                
        elif state & Gdk.ModifierType.CONTROL_MASK:
            if keyval in (Gdk.KEY_l, Gdk.KEY_L):
                self.entry.grab_focus()
                self.entry.select_region(0, -1)
                return True
            elif keyval in (Gdk.KEY_k, Gdk.KEY_K):
                self.entry.set_text("")
                return True
            
        # Delegate other keys to active mode
        if self.mode_manager:
            return self.mode_manager.on_key_pressed(keyval, state)
            
        return False

    def update_revealer_state(self):
        active = self.mode_manager.active_mode_name
        should_reveal_modes = active != "Search"
        
        query = self.entry.get_text().strip()
        has_text = len(query) > 0
        should_reveal_results = has_text or should_reveal_modes
        
        # Кнопки видны всегда, когда активен глобальный поиск
        should_show_buttons = (active == "Search")
        self.mode_buttons_revealer.set_reveal_child(should_show_buttons)
        
        if hasattr(self, 'results_revealer'):
            self.results_revealer.set_reveal_child(should_reveal_results)
            if not should_reveal_results:
                self.set_default_size(650, 1)
        
        # Обновляем подсветку кнопок
        for name, btn in self.mode_buttons.items():
            if name == active:
                btn.add_css_class("active")
            else:
                btn.remove_css_class("active")

    def on_mode_button_clicked(self, button, mode_name):
        if self.mode_manager.active_mode_name == mode_name:
            # Toggle back to search if clicking the same mode
            self.mode_manager.set_mode("Search")
        else:
            self.mode_manager.set_mode(mode_name)
            
        self.update_revealer_state()
        self.entry.grab_focus()

    def on_search_changed(self, editable):
        query = self.entry.get_text().strip()
        
        # --- DEBUG MODE ENTRY POINTS ---
        if query == "/apps" and self.mode_manager:
            self.entry.set_text("")
            self.mode_manager.set_mode("Apps")
            self.update_revealer_state()
            return
        elif query == "/files" and self.mode_manager:
            self.entry.set_text("")
            self.mode_manager.set_mode("Files")
            self.update_revealer_state()
            return
        elif query == "/clip" and self.mode_manager:
            self.entry.set_text("")
            self.mode_manager.set_mode("Clipboard")
            self.update_revealer_state()
            return
        elif query == "/emoji" and self.mode_manager:
            self.entry.set_text("")
            self.mode_manager.set_mode("Emoji")
            self.update_revealer_state()
            return
        elif query == "/settings" and self.mode_manager:
            self.entry.set_text("")
            self.mode_manager.set_mode("Settings")
            self.update_revealer_state()
            return
        # -------------------------------
        
        self.update_revealer_state()
        if self.mode_manager:
            self.mode_manager.on_search_changed(query)

    def on_search_activate(self, entry):
        # Trigger enter on active mode
        if self.mode_manager:
            self.mode_manager.on_key_pressed(Gdk.KEY_Return, 0)
    def reload_config(self):
        # Обновляем CSS
        self._setup_css()
        
        # Обновляем длительность анимаций
        animations = self.config_manager.get("animations") if self.config_manager else True
        anim_duration = 200 if animations else 0
        self.mode_buttons_revealer.set_transition_duration(anim_duration)
        if hasattr(self, 'results_revealer'):
            self.results_revealer.set_transition_duration(anim_duration)
            
        # Применяем фильтр источников к движку
        if self.config_manager and hasattr(self, 'engine'):
            self.config_manager.apply_to_engine(self.engine)
            
        # Обновляем режимы
        enabled_modes_list = self.config_manager.get("enabled_modes") if self.config_manager else ["Apps", "Files", "Clipboard", "Emoji"]
        for name, btn in self.mode_buttons.items():
            btn.set_visible(name in enabled_modes_list)
            
        # Если активный режим был отключен, возвращаемся в Search
        if self.mode_manager and self.mode_manager.active_mode_name not in enabled_modes_list and self.mode_manager.active_mode_name != "Search":
            self.mode_manager.set_mode("Search")
            
        self.update_revealer_state()
        
        # Обновляем превью-панель "на лету"
        if hasattr(self, 'mode_manager') and self.mode_manager:
            search_mode = self.mode_manager.modes.get("Search")
            if search_mode and hasattr(search_mode, 'preview_container'):
                preview_width = self.config_manager.get("preview_width") if self.config_manager else 420
                search_mode.preview_container.set_size_request(preview_width, -1)
                
                preview_enabled = self.config_manager.get("preview_enabled") if self.config_manager else True
                if not preview_enabled:
                    search_mode.preview_container.set_visible(False)
                    self.set_default_size(650, 1)
