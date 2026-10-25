import os
import sys

import gi

from logger import get_logger

logger = get_logger("ui")

try:
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk, Pango
    HAS_ADW = True
except (ValueError, ImportError):
    try:
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gdk, Gio, GLib, GObject, Gtk, Pango
        HAS_ADW = False
        Adw = None
    except ValueError as e:
        logger.critical("GTK version error: %s", e)
        sys.exit(1)

from i18n import i18n, t
from modes import ModeManager
from providers import SearchResult
from quick_look import QuickLookWindow
from search_engine import SearchEngine
from style_generator import build_dynamic_css

UNFOLD_TRANSITION_MAP = {
    "instant_dynamic": Gtk.RevealerTransitionType.SLIDE_DOWN,
    "slide_down": Gtk.RevealerTransitionType.SLIDE_DOWN,
    "swing_down": Gtk.RevealerTransitionType.SWING_DOWN,
    "jelly_wobble": Gtk.RevealerTransitionType.SLIDE_DOWN,
    "none": Gtk.RevealerTransitionType.NONE
}


class EchoUI(Gtk.Window):
    def __init__(self, application=None, config_manager=None):
        super().__init__(application=application)
        self.config_manager = config_manager
        self.set_title("Echo")

        self.engine = SearchEngine(config_manager=self.config_manager)
        if self.config_manager:
            self.config_manager.apply_to_engine(self.engine)

        self.mode_manager = None
        self.quick_look = None

        self._setup_ui()
        self._setup_css()
        self._setup_shortcuts()
        self.connect("unmap", self._on_unmap)

        # Initialize with default search mode
        if self.mode_manager:
            self.mode_manager.set_mode("Search")
            self.update_revealer_state()
        if self.mode_manager:
            self.mode_manager.retranslate()
            self.mode_manager.on_search_changed("")

    def _on_unmap(self, widget):
        """Reclaims preview resources and triggers garbage collection when window is hidden."""
        try:
            if getattr(self, "quick_look", None) and self.quick_look.is_visible():
                self.quick_look.hide_preview()
            if getattr(self, "mode_manager", None):
                self.mode_manager.set_mode("Search")
            if hasattr(self, "entry"):
                self.entry.set_text("")
            self.update_revealer_state()
            super().set_default_size(1050, 1)
            self.queue_resize()
            import gc
            if self.mode_manager and hasattr(self.mode_manager, "modes"):
                search_mode = self.mode_manager.modes.get("Search")
                if search_mode and hasattr(search_mode, "clear_preview_and_resources"):
                    search_mode.clear_preview_and_resources()
            gc.collect()
        except Exception as e:
            logger.debug("Error during window hide cleanup: %s", e)

    def _setup_base_css(self):
        """Loads and registers static base CSS from system and user paths."""
        if hasattr(self, "_base_css_provider") and self._base_css_provider:
            try:
                Gtk.StyleContext.remove_provider_for_display(
                    Gdk.Display.get_default(),
                    self._base_css_provider
                )
            except Exception as e:
                logger.debug("Error removing old CSS provider: %s", e)
            self._base_css_provider = None

        provider = Gtk.CssProvider()
        css_paths = [
            os.path.expanduser("~/.local/share/echo-search/style.css"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css'),
            "/usr/share/echo-search/style.css",
            "/usr/lib/echo-search/style.css",
            "/usr/local/share/echo-search/style.css"
        ]

        for path in css_paths:
            if os.path.exists(path):
                try:
                    provider.load_from_path(path)
                    Gtk.StyleContext.add_provider_for_display(
                        Gdk.Display.get_default(),
                        provider,
                        Gtk.STYLE_PROVIDER_PRIORITY_USER + 10
                    )
                    self._base_css_provider = provider
                    break
                except Exception as e:
                    logger.error("Error loading CSS from %s: %s", path, e)

    def _setup_css(self):
        """Sets up base stylesheet and applies dynamic theme CSS tokens."""
        self._setup_base_css()

        if not self.config_manager:
            return

        theme = self.config_manager.get("theme", "dark_glass")
        if theme == "silver":
            theme = "dark_glass"

        is_light = theme in ("light", "light_glass")

        try:
            import gi
            gi.require_version("Adw", "1")
            from gi.repository import Adw
            sm = Adw.StyleManager.get_default()
            if is_light:
                sm.set_color_scheme(Adw.ColorScheme.PREFER_LIGHT)
            else:
                sm.set_color_scheme(Adw.ColorScheme.PREFER_DARK)
        except Exception as e:
            logger.debug("Error setting Adw color scheme: %s", e)

        dynamic_css = build_dynamic_css(self.config_manager)

        if hasattr(self, '_dynamic_css_provider') and self._dynamic_css_provider:
            Gtk.StyleContext.remove_provider_for_display(
                Gdk.Display.get_default(),
                self._dynamic_css_provider
            )

        self._dynamic_css_provider = Gtk.CssProvider()
        if hasattr(self._dynamic_css_provider, "load_from_string"):
            self._dynamic_css_provider.load_from_string(dynamic_css)
        else:
            self._dynamic_css_provider.load_from_data(dynamic_css.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self._dynamic_css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER + 20
        )

        if hasattr(self, 'main_box') and self.main_box:
            theme_classes = ['theme-dark-glass', 'theme-light-glass', 'theme-light', 'theme-dark', 'theme-aura-glow', 'light-theme', 'light_glass']
            for c in theme_classes:
                self.main_box.remove_css_class(c)
            if is_light:
                self.main_box.add_css_class('light-theme')
            if theme == 'light_glass':
                self.main_box.add_css_class('light_glass')
            self.main_box.add_css_class(f'theme-{theme.replace("_", "-")}')

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
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_box.add_css_class("capsule-window-ui")
        self.main_box.set_valign(Gtk.Align.START)
        self.outer_box.append(self.main_box)

        # Стили заголовка для светлой темы
        # Общий контейнер для строки поиска и кнопок режимов
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.header_box.set_hexpand(True)
        self.header_box.set_spacing(12)
        self.header_box.set_margin_top(10)
        self.header_box.set_margin_start(16)
        self.header_box.set_margin_end(16)
        self.header_box.set_margin_bottom(10)
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
        self.entry.set_overwrite_mode(False)
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
        anim_speed = self.config_manager.get("animation_speed", 100) if self.config_manager else 100
        speed_factor = max(0.2, min(3.0, float(anim_speed) / 100.0))
        anim_duration = max(30, int(220 / speed_factor)) if animations else 0
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
            ("Emoji", "emojichooser-symbolic"),
            ("Settings", "preferences-system-symbolic")
        ]

        # Проверка поддержки буфера обмена и регистрация путей иконок
        clipboard_supported = True
        try:
            disp = Gdk.Display.get_default()
            if disp:
                icon_theme = Gtk.IconTheme.get_for_display(disp)
                local_icons = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icons")
                if os.path.isdir(local_icons):
                    icon_theme.add_search_path(local_icons)
            if not disp or not disp.get_clipboard():
                clipboard_supported = False
        except Exception as e:
            logger.debug("Clipboard/display check failed: %s", e)
            clipboard_supported = False

        enabled_modes_list = self.config_manager.get("enabled_modes") if self.config_manager else [m[0] for m in all_modes]
        self.mode_buttons = {}
        for name, icon_name in all_modes:
            btn = Gtk.Button()
            btn.set_valign(Gtk.Align.CENTER) # Запрещает растягивание по вертикали (чтобы были идеальные круги)
            btn.set_halign(Gtk.Align.CENTER)
            btn.add_css_class("mode-button")
            btn.add_css_class("circular")
            # Фиксированный размер иконки
            image = Gtk.Image.new_from_icon_name(icon_name)
            image.set_pixel_size(16)
            btn.set_child(image)
            MODE_TOOLTIP_KEYS = {
                "Apps": "mode_apps",
                "Files": "mode_files",
                "Clipboard": "mode_clipboard",
                "Emoji": "mode_emoji",
                "Settings": "mode_settings"
            }
            MODE_SHORTCUTS = {
                "Apps": "Ctrl+2",
                "Files": "Ctrl+3",
                "Clipboard": "Ctrl+4",
                "Emoji": "Ctrl+5",
                "Settings": "Ctrl+6"
            }
            sc = MODE_SHORTCUTS.get(name, "")
            label_text = t(MODE_TOOLTIP_KEYS.get(name, name))
            btn.set_tooltip_text(f"{label_text} ({sc})" if sc else label_text)
            btn.connect("clicked", self.on_mode_button_clicked, name)

            is_visible = (name in enabled_modes_list)
            if name == "Clipboard" and not clipboard_supported:
                is_visible = False

            btn.set_visible(is_visible)
            self.mode_buttons_box.append(btn)
            self.mode_buttons[name] = btn

        # Инициализируем ModeManager и оборачиваем в Revealer для динамической высоты окна
        self.mode_manager = ModeManager(self)
        self.quick_look = QuickLookWindow(parent_window=self)

        # Единый контейнер для всех режимов, задающий глобальные отступы
        self.results_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.results_container.add_css_class("results-container")
        self.results_container.add_css_class("folded")
        self.results_container.append(self.mode_manager.get_widget())

        # Настройка нативной пружинной физики Adw.SpringAnimation
        self._spring_anim = None
        if HAS_ADW and hasattr(Adw, "SpringAnimation") and hasattr(Adw, "SpringParams"):
            try:
                self._spring_params = Adw.SpringParams.new(0.86, 0.5, 1500.0)
                self._spring_target = Adw.CallbackAnimationTarget.new(self._on_spring_tick)
                self._spring_anim = Adw.SpringAnimation.new(self.results_container, 0.0, 1.0, self._spring_params, self._spring_target)
                self._spring_anim.set_clamp(True)
            except Exception as e:
                logger.debug("SpringAnimation setup failed: %s", e)
                self._spring_anim = None

        unfold_mode = self.config_manager.get("unfold_animation", "instant_dynamic") if self.config_manager else "instant_dynamic"
        transition_type = UNFOLD_TRANSITION_MAP.get(unfold_mode, Gtk.RevealerTransitionType.SLIDE_DOWN)
        animations = self.config_manager.get("animations", True) if self.config_manager else True
        anim_speed = self.config_manager.get("animation_speed", 100) if self.config_manager else 100
        speed_factor = max(0.2, min(3.0, float(anim_speed) / 100.0))
        if unfold_mode == "instant_dynamic":
            revealer_duration = max(10, int(45 / speed_factor)) if animations else 0
        elif unfold_mode == "slide_down":
            revealer_duration = max(20, int(140 / speed_factor)) if animations else 0
        elif unfold_mode == "swing_down":
            revealer_duration = max(20, int(160 / speed_factor)) if animations else 0
        elif unfold_mode == "jelly_wobble":
            revealer_duration = max(30, int(220 / speed_factor)) if animations else 0
        elif unfold_mode == "none" or not animations:
            revealer_duration = 0
        else:
            revealer_duration = max(20, int(140 / speed_factor)) if animations else 0

        self.results_revealer = Gtk.Revealer()
        self.results_revealer.set_transition_type(transition_type)
        self.results_revealer.set_transition_duration(revealer_duration)
        self.results_revealer.set_child(self.results_container)
        self.results_revealer.set_reveal_child(False)
        self.results_revealer.connect("notify::child-revealed", self._on_results_revealed_changed)
        self.set_default_size(1050, 1)

        self.main_box.append(self.results_revealer)

    def _on_spring_tick(self, value: float):
        try:
            clamped = max(0.0, min(1.0, value))
            self.results_container.set_opacity(clamped)
        except Exception as e:
            logger.debug("Error setting spring opacity: %s", e)

    def _on_results_revealed_changed(self, revealer, param):
        if not revealer.get_reveal_child() and not revealer.get_child_revealed():
            # Анимация сворачивания завершена - возвращаем окно к компактному состоянию
            super().set_default_size(1050, 1)
            self.queue_resize()
            self.results_container.set_opacity(0.0)
            if self.mode_manager and hasattr(self.mode_manager, "modes"):
                search_mode = self.mode_manager.modes.get("Search")
                if search_mode and hasattr(search_mode, "clear_preview_and_resources"):
                    search_mode.clear_preview_and_resources()
        elif revealer.get_reveal_child() and revealer.get_child_revealed():
            # Анимация раскрытия завершена - калибруем под точный размер контента
            self.results_container.set_opacity(1.0)
            active = self.mode_manager.active_mode_name if self.mode_manager else "Search"
            target_w, target_h = self._calculate_target_geometry(active, True)
            target_w, target_h = self._clamp_geometry_to_monitor(target_w, target_h)
            cur_w, cur_h = self.get_default_size()
            if cur_w != target_w or cur_h != target_h:
                super().set_default_size(target_w, target_h)

    def hide(self):
        """Hides the window safely using set_visible(False) to prevent GTK4 deprecation warnings."""
        self.set_visible(False)

    def prepare_for_show(self):
        """Prepares the window to be shown freshly: resets to Search mode, collapses revealer, resets geometry."""
        try:
            if getattr(self, "quick_look", None) and self.quick_look.is_visible():
                self.quick_look.hide_preview()
            if getattr(self, "mode_manager", None):
                self.mode_manager.set_mode("Search")
                search_mode = self.mode_manager.modes.get("Search")
                if search_mode and hasattr(search_mode, "clear_preview_and_resources"):
                    search_mode.clear_preview_and_resources()
            if hasattr(self, "entry"):
                self.entry.set_text("")
            self.update_revealer_state()
            super().set_default_size(1050, 1)
            self.queue_resize()
        except Exception as e:
            logger.debug("Error during prepare_for_show: %s", e)

    def set_default_size(self, width: int, height: int):
        if hasattr(self, "results_revealer"):
            if self.results_revealer.get_reveal_child():
                # Окно раскрыто - высота не должна схлопываться до 1, -1 или мелкого размера
                if height <= 1:
                    active = self.mode_manager.active_mode_name if getattr(self, "mode_manager", None) else "Search"
                    _, target_h = self._calculate_target_geometry(active, True)
                    height = target_h
                if width < 1050:
                    width = 1050
            else:
                # Окно свернуто или в процессе сворачивания
                if self.is_visible() and self.results_revealer.get_child_revealed():
                    # Анимация сворачивания еще идет - не трогаем геометрию раньше времени
                    return
                width = 1050
                height = 1
        super().set_default_size(width, height)

    def _setup_shortcuts(self):
        key_ctrl = Gtk.EventControllerKey.new()
        key_ctrl.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_ctrl)



    def on_key_pressed(self, controller, keyval, keycode, state):
        from utils import matches_shortcut
        cfg = getattr(self, "config_manager", None)
        ql_sc = cfg.get("quick_look_shortcut", "space") if cfg else "space"

        if getattr(self, "quick_look", None) and self.quick_look.is_visible():
            if keyval == Gdk.KEY_Escape or matches_shortcut(keyval, state, ql_sc):
                self.quick_look.hide_preview()
                return True

        if (state & Gdk.ModifierType.SHIFT_MASK and keyval == Gdk.KEY_space) or (ql_sc != "space" and matches_shortcut(keyval, state, ql_sc)):
            if getattr(self, "quick_look", None) and self.mode_manager:
                mode = self.mode_manager.get_active_mode()
                if mode and hasattr(mode, "current_results") and hasattr(mode, "selected_index"):
                    if 0 <= mode.selected_index < len(mode.current_results):
                        if self.quick_look.preview_result(mode.current_results[mode.selected_index]):
                            return True
                elif mode and hasattr(mode, "suggestions_flowbox"):
                    sel = mode.suggestions_flowbox.get_selected_children() or mode.recents_flowbox.get_selected_children()
                    if sel and getattr(sel[0], "result", None):
                        if self.quick_look.preview_result(sel[0].result):
                            return True

        if keyval == Gdk.KEY_Insert:
            self.entry.set_overwrite_mode(False)
            return True

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

        # Глобальные хоткеи с клавишей Ctrl
        if (state & Gdk.ModifierType.CONTROL_MASK) and not (state & Gdk.ModifierType.ALT_MASK):
            # Переключение режимов: Ctrl + 1..6
            mode_keys = {
                Gdk.KEY_1: "Search", Gdk.KEY_KP_1: "Search", Gdk.KEY_exclam: "Search",
                Gdk.KEY_2: "Apps", Gdk.KEY_KP_2: "Apps", Gdk.KEY_at: "Apps",
                Gdk.KEY_3: "Files", Gdk.KEY_KP_3: "Files", Gdk.KEY_numbersign: "Files",
                Gdk.KEY_4: "Clipboard", Gdk.KEY_KP_4: "Clipboard", Gdk.KEY_dollar: "Clipboard",
                Gdk.KEY_5: "Emoji", Gdk.KEY_KP_5: "Emoji", Gdk.KEY_percent: "Emoji",
                Gdk.KEY_6: "Settings", Gdk.KEY_KP_6: "Settings", Gdk.KEY_asciicircum: "Settings",
            }
            if keyval in mode_keys and self.mode_manager:
                target_mode = mode_keys[keyval]
                if target_mode != self.mode_manager.active_mode_name:
                    self.mode_manager.set_mode(target_mode)
                    self.entry.set_text("")
                    self.update_revealer_state()
                    self.entry.grab_focus()
                return True

            # Циклическое переключение режимов: Ctrl + Tab / Ctrl + Shift + Tab
            if keyval in (Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab) and self.mode_manager:
                modes_order = ["Search", "Apps", "Files", "Clipboard", "Emoji", "Settings"]
                current_mode = self.mode_manager.active_mode_name
                if current_mode in modes_order:
                    curr_idx = modes_order.index(current_mode)
                    if state & Gdk.ModifierType.SHIFT_MASK:
                        next_idx = (curr_idx - 1) % len(modes_order)
                    else:
                        next_idx = (curr_idx + 1) % len(modes_order)
                    self.mode_manager.set_mode(modes_order[next_idx])
                    self.update_revealer_state()
                    self.entry.grab_focus()
                    return True

            # Редактирование строки в стиле Readline
            if keyval in (Gdk.KEY_l, Gdk.KEY_L):
                self.entry.grab_focus()
                self.entry.select_region(0, -1)
                return True
            elif keyval in (Gdk.KEY_k, Gdk.KEY_K) or keyval in (Gdk.KEY_u, Gdk.KEY_U):
                self.entry.set_text("")
                self.update_revealer_state()
                return True
            elif keyval in (Gdk.KEY_w, Gdk.KEY_W):
                text = self.entry.get_text()
                pos = self.entry.get_position()
                if pos > 0:
                    before = text[:pos].rstrip()
                    idx = before.rfind(" ")
                    new_pos = idx + 1 if idx >= 0 else 0
                    new_text = text[:new_pos] + text[pos:]
                    self.entry.set_text(new_text)
                    self.entry.set_position(new_pos)
                    self.update_revealer_state()
                    return True

        # Delegate other keys to active mode
        if self.mode_manager:
            return self.mode_manager.on_key_pressed(keyval, state)

        return False

    def _clamp_width_to_monitor(self, target_width: int) -> int:
        w, _ = self._clamp_geometry_to_monitor(target_width, 1)
        return w

    def _clamp_geometry_to_monitor(self, target_width: int, target_height: int) -> tuple:
        max_w = target_width
        max_h = target_height
        try:
            display = Gdk.Display.get_default()
            if display:
                surface = self.get_surface()
                mon = display.get_monitor_at_surface(surface) if surface else None
                if not mon:
                    monitors = display.get_monitors()
                    if monitors and monitors.get_n_items() > 0:
                        mon = monitors.get_item(0)
                if mon:
                    geom = mon.get_geometry()
                    if geom.width > 0:
                        max_w = min(target_width, int(geom.width * 0.94))
                    if geom.height > 0:
                        max_h = min(target_height, int(geom.height * 0.88))
        except Exception as e:
            logger.debug("Error getting monitor geometry: %s", e)
        return max_w, max_h

    def _calculate_target_geometry(self, active: str, should_reveal: bool) -> tuple:
        if not should_reveal:
            return 1050, 1

        if active == "Search":
            search_mode = self.mode_manager.modes.get("Search") if self.mode_manager else None
            preview_enabled = self.config_manager.get("preview_enabled", True) if getattr(self, "config_manager", None) else True
            preview_width = self.config_manager.get("preview_width", 420) if getattr(self, "config_manager", None) else 420
            target_w = 1050 if not preview_enabled else 1070
            target_h = 650
            return target_w, target_h

        elif active in ("Apps", "Files", "Clipboard", "Emoji"):
            return 1050, 560

        elif active == "Settings":
            return 820, 660

        return 1050, 650

    def update_revealer_state(self):
        active = self.mode_manager.active_mode_name
        should_reveal_modes = active != "Search"

        query = self.entry.get_text().strip()
        has_text = len(query) > 0
        should_reveal_results = has_text or should_reveal_modes

        # Кнопки видны всегда, когда активен глобальный поиск
        should_show_buttons = True
        self.mode_buttons_revealer.set_reveal_child(should_show_buttons)

        if hasattr(self, 'results_revealer'):
            unfold_mode = self.config_manager.get("unfold_animation", "instant_dynamic") if self.config_manager else "instant_dynamic"
            was_revealed = self.results_revealer.get_reveal_child()

            if should_reveal_results:
                target_w, target_h = self._calculate_target_geometry(active, True)
                target_w, target_h = self._clamp_geometry_to_monitor(target_w, target_h)

                # Заранее выделяем необходимый холст окна, чтобы избежать ресайзов во время анимации
                super().set_default_size(target_w, target_h)

                self.results_revealer.set_reveal_child(True)
                self.results_container.remove_css_class("folded")

                if getattr(self, "_spring_anim", None) and unfold_mode not in ("instant_dynamic", "none", "jelly_wobble"):
                    self._spring_anim.set_value_from(self.results_container.get_opacity())
                    self._spring_anim.set_value_to(1.0)
                    self._spring_anim.play()
                else:
                    self.results_container.set_opacity(1.0)

                if unfold_mode == "jelly_wobble":
                    if not was_revealed:
                        self.results_container.remove_css_class("anim-jelly-wobble")
                        self.results_container.add_css_class("anim-jelly-wobble")
                else:
                    self.results_container.remove_css_class("anim-jelly-wobble")
            else:
                self.results_container.add_css_class("folded")
                self.results_container.remove_css_class("anim-jelly-wobble")
                self.results_revealer.set_reveal_child(False)
                if getattr(self, "_spring_anim", None) and unfold_mode not in ("instant_dynamic", "none", "jelly_wobble"):
                    self._spring_anim.set_value_from(self.results_container.get_opacity())
                    self._spring_anim.set_value_to(0.0)
                    self._spring_anim.play()

                if unfold_mode in ("instant_dynamic", "none") or not self.is_visible():
                    super().set_default_size(1050, 1)
                    self.queue_resize()

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
            self.entry.set_text("")
        else:
            self.mode_manager.set_mode(mode_name)
            self.entry.set_text("")

        self.update_revealer_state()
        self.entry.grab_focus()

    def on_search_changed(self, editable):
        query = self.entry.get_text().strip()

        # Переключение режимов через слэш-команды (/apps, /files, /clip, /emoji, /settings)
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
        # Стандартная обработка поискового ввода

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

        # Обновляем анимации и стиль развертывания
        animations = self.config_manager.get("animations") if self.config_manager else True
        anim_speed = self.config_manager.get("animation_speed", 100) if self.config_manager else 100
        speed_factor = max(0.2, min(3.0, float(anim_speed) / 100.0))
        unfold_mode = self.config_manager.get("unfold_animation", "instant_dynamic") if self.config_manager else "instant_dynamic"
        anim_duration = max(30, int(220 / speed_factor)) if animations else 0
        if unfold_mode == "instant_dynamic":
            revealer_duration = max(10, int(45 / speed_factor)) if animations else 0
        elif unfold_mode == "slide_down":
            revealer_duration = max(20, int(140 / speed_factor)) if animations else 0
        elif unfold_mode == "swing_down":
            revealer_duration = max(20, int(160 / speed_factor)) if animations else 0
        elif unfold_mode == "jelly_wobble":
            revealer_duration = max(30, int(220 / speed_factor)) if animations else 0
        elif unfold_mode == "none" or not animations:
            revealer_duration = 0
        else:
            revealer_duration = max(20, int(140 / speed_factor)) if animations else 0
        self.mode_buttons_revealer.set_transition_duration(anim_duration)
        if hasattr(self, 'results_revealer'):
            transition_type = UNFOLD_TRANSITION_MAP.get(unfold_mode, Gtk.RevealerTransitionType.SLIDE_DOWN)
            self.results_revealer.set_transition_type(transition_type)
            self.results_revealer.set_transition_duration(revealer_duration)

        # Применяем фильтр источников к движку
        if self.config_manager and hasattr(self, 'engine'):
            self.config_manager.apply_to_engine(self.engine)
            if hasattr(self.engine, 'reload_providers'):
                self.engine.reload_providers()

        # Обновляем режимы
        enabled_modes_list = self.config_manager.get("enabled_modes") if self.config_manager else ["Apps", "Files", "Clipboard", "Emoji", "Settings"]
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
                search_mode.preview_container.set_size_request(preview_width, 500)

                preview_enabled = self.config_manager.get("preview_enabled") if self.config_manager else True
                if not preview_enabled:
                    search_mode.preview_container.set_visible(False)
                    self.set_default_size(1050, 650)
            if search_mode and hasattr(search_mode, 'on_config_reloaded'):
                search_mode.on_config_reloaded()

        # Обновление подсказок и плейсхолдера при смене языка
        MODE_TOOLTIP_KEYS = {
            "Apps": "mode_apps",
            "Files": "mode_files",
            "Clipboard": "mode_clipboard",
            "Emoji": "mode_emoji",
            "Settings": "mode_settings"
        }
        MODE_SHORTCUTS = {
            "Apps": "Ctrl+2",
            "Files": "Ctrl+3",
            "Clipboard": "Ctrl+4",
            "Emoji": "Ctrl+5",
            "Settings": "Ctrl+6"
        }
        for name, btn in self.mode_buttons.items():
            sc = MODE_SHORTCUTS.get(name, "")
            label_text = t(MODE_TOOLTIP_KEYS.get(name, name))
            btn.set_tooltip_text(f"{label_text} ({sc})" if sc else label_text)
        if hasattr(self, 'mode_manager') and self.mode_manager:
            self.mode_manager.retranslate()

        # Обновляем тему Quick Look при перезагрузке конфига
        if getattr(self, "quick_look", None):
            self.quick_look.apply_theme()

