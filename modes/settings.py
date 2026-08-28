try:
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk, Gdk, Pango, GLib
except ValueError:
    pass

from .base import BaseMode
from i18n import t, SUPPORTED_LANGUAGES

class ShortcutButton(Gtk.Button):
    def __init__(self, current_shortcut: str, on_changed_callback):
        super().__init__()
        self.current_shortcut = current_shortcut or "<Super>space"
        self.on_changed_callback = on_changed_callback
        self.is_recording = False
        
        self.add_css_class("shortcut-button")
        self.set_valign(Gtk.Align.CENTER)
        self.update_label()
        
        self.connect("clicked", self._on_clicked)
        
        self.key_ctrl = Gtk.EventControllerKey.new()
        self.key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(self.key_ctrl)

    def _format_display(self, shortcut: str) -> str:
        if not shortcut: return "-"
        s = shortcut
        s = s.replace("<Super>", "Super + ")
        s = s.replace("<Ctrl>", "Ctrl + ")
        s = s.replace("<Alt>", "Alt + ")
        s = s.replace("<Shift>", "Shift + ")
        parts = s.split(" + ")
        if len(parts) > 1:
            return " + ".join(parts[:-1]) + " + " + parts[-1].capitalize()
        return s.capitalize()

    def update_label(self):
        if self.is_recording:
            self.set_label(t("settings_recording_shortcut"))
            self.add_css_class("recording")
        else:
            self.set_label(self._format_display(self.current_shortcut))
            self.remove_css_class("recording")

    def _on_clicked(self, btn):
        self.is_recording = not self.is_recording
        self.update_label()
        if self.is_recording:
            self.grab_focus()

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if not self.is_recording:
            return False

        # Отмена по Escape
        if keyval == Gdk.KEY_Escape:
            self.is_recording = False
            self.update_label()
            return True

        # Игнорируем нажатия только клавиш-модификаторов
        if keyval in (Gdk.KEY_Control_L, Gdk.KEY_Control_R,
                      Gdk.KEY_Shift_L, Gdk.KEY_Shift_R,
                      Gdk.KEY_Alt_L, Gdk.KEY_Alt_R,
                      Gdk.KEY_Super_L, Gdk.KEY_Super_R,
                      Gdk.KEY_Meta_L, Gdk.KEY_Meta_R):
            return True

        mod_str = ""
        if state & Gdk.ModifierType.CONTROL_MASK:
            mod_str += "<Ctrl>"
        if state & Gdk.ModifierType.ALT_MASK:
            mod_str += "<Alt>"
        if state & Gdk.ModifierType.SHIFT_MASK:
            mod_str += "<Shift>"
        if state & Gdk.ModifierType.SUPER_MASK:
            mod_str += "<Super>"

        # Привязка по физическому скан-коду (работает одинаково при любой раскладке)
        KEYCODE_TO_KEY = {
            65: "space", 36: "Return", 104: "Return", 23: "Tab",
            24: "q", 25: "w", 26: "e", 27: "r", 28: "t", 29: "y", 30: "u", 31: "i", 32: "o", 33: "p", 34: "bracketleft", 35: "bracketright",
            38: "a", 39: "s", 40: "d", 41: "f", 42: "g", 43: "h", 44: "j", 45: "k", 46: "l", 47: "semicolon", 48: "apostrophe",
            52: "z", 53: "x", 54: "c", 55: "v", 56: "b", 57: "n", 58: "m", 59: "comma", 60: "period", 61: "slash",
            10: "1", 11: "2", 12: "3", 13: "4", 14: "5", 15: "6", 16: "7", 17: "8", 18: "9", 19: "0", 20: "minus", 21: "equal",
            67: "F1", 68: "F2", 69: "F3", 70: "F4", 71: "F5", 72: "F6", 73: "F7", 74: "F8", 75: "F9", 76: "F10", 95: "F11", 96: "F12"
        }

        CYRILLIC_KEYSYM_TO_EN = {
            "cyrillic_shorti": "q", "cyrillic_tse": "w", "cyrillic_u": "e", "cyrillic_ka": "r", "cyrillic_ie": "t",
            "cyrillic_en": "y", "cyrillic_ge": "u", "cyrillic_sha": "i", "cyrillic_shcha": "o", "cyrillic_ze": "p",
            "cyrillic_ha": "bracketleft", "cyrillic_hardsign": "bracketright",
            "cyrillic_ef": "a", "cyrillic_yeru": "s", "cyrillic_ve": "d", "cyrillic_a": "f", "cyrillic_pe": "g",
            "cyrillic_er": "h", "cyrillic_o": "j", "cyrillic_el": "k", "cyrillic_de": "l", "cyrillic_zhe": "semicolon",
            "cyrillic_e": "apostrophe",
            "cyrillic_ya": "z", "cyrillic_che": "x", "cyrillic_es": "c", "cyrillic_em": "v", "cyrillic_i": "b",
            "cyrillic_te": "n", "cyrillic_softsign": "m", "cyrillic_be": "comma", "cyrillic_yu": "period", "cyrillic_io": "grave"
        }

        key_str = ""
        if keycode in KEYCODE_TO_KEY:
            key_str = KEYCODE_TO_KEY[keycode]
        else:
            key_name = (Gdk.keyval_name(keyval) or "").lower()
            if key_name in CYRILLIC_KEYSYM_TO_EN:
                key_str = CYRILLIC_KEYSYM_TO_EN[key_name]
            elif keyval == Gdk.KEY_space:
                key_str = "space"
            elif keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
                key_str = "Return"
            else:
                key_str = key_name

        if not key_str:
            return False

        if not mod_str and not key_str.startswith("f"):
            mod_str = "<Super>"

        new_shortcut = f"{mod_str}{key_str}"
        self.current_shortcut = new_shortcut
        self.is_recording = False
        self.update_label()
        
        if self.on_changed_callback:
            self.on_changed_callback(new_shortcut)
            
        return True

class SettingsMode(BaseMode):
    category_filter = "Settings"
    
    def _create_widget(self) -> Gtk.Widget:
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.box.add_css_class("settings-main-container")

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_min_content_height(160)
        self.scroll.set_max_content_height(520)
        self.scroll.set_propagate_natural_height(True)
        self.scroll.set_hexpand(True)
        self.scroll.set_vexpand(True)
        self.scroll.add_css_class("settings-scrolled")

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        self.content_box.set_margin_start(20)
        self.content_box.set_margin_end(20)
        self.content_box.set_margin_top(14)
        self.content_box.set_margin_bottom(24)

        self._build_settings_ui()

        self.scroll.set_child(self.content_box)
        self.box.append(self.scroll)
        return self.box

    def _get_setting_definitions(self):
        cfg = self.main_window.config_manager
        return [
            {
                "id": "language",
                "group": t("settings_group_general"),
                "title": t("settings_language"),
                "keywords": "язык language russian english русский интерфейс",
                "builder": lambda: self._create_language_row(cfg)
            },
            {
                "id": "autostart",
                "group": t("settings_group_general"),
                "title": t("settings_autostart"),
                "keywords": "автозапуск старт login autostart startup запуск при входе",
                "builder": lambda: self._create_switch_row(
                    t("settings_autostart"), None, cfg.get("launch_at_login", False),
                    lambda active: self._on_setting_changed("launch_at_login", active)
                )
            },
            {
                "id": "shortcut",
                "group": t("settings_group_general"),
                "title": t("settings_hotkey"),
                "keywords": "горячие клавиши шорткат shortcut hotkey keybinding super space запуск сочетание",
                "builder": lambda: self._create_shortcut_row(
                    t("settings_hotkey"), cfg.get("launch_shortcut", "<Super>space")
                )
            },
            {
                "id": "search_history",
                "group": t("settings_group_general"),
                "title": t("settings_search_history"),
                "keywords": "история history поиск search запросы",
                "builder": lambda: self._create_switch_row(
                    t("settings_search_history"), None, cfg.get("search_history", True),
                    lambda active: self._on_setting_changed("search_history", active)
                )
            },
            {
                "id": "recent_when_empty",
                "group": t("settings_group_general"),
                "title": t("settings_recent_when_empty"),
                "keywords": "недавние recent элементы файлы история пустой",
                "builder": lambda: self._create_switch_row(
                    t("settings_recent_when_empty"), None, cfg.get("recent_when_empty", True),
                    lambda active: self._on_setting_changed("recent_when_empty", active)
                )
            },
            {
                "id": "theme",
                "group": t("settings_group_appearance"),
                "title": t("settings_theme"),
                "keywords": "тема theme dark light стекло glass темная светлая оформление вид",
                "builder": lambda: self._create_theme_row(cfg)
            },
            {
                "id": "transparency",
                "group": t("settings_group_appearance"),
                "title": t("settings_transparency"),
                "keywords": "прозрачность transparency opacity альфа стекло",
                "builder": lambda: self._create_slider_row(
                    t("settings_transparency"),
                    int((cfg.get("transparency", 0.30) if cfg.get("transparency") is not None else 0.30) * 100),
                    0, 100, 1, unit="%",
                    callback=lambda val: self._on_setting_changed("transparency", round(val / 100.0, 2))
                )
            },
            {
                "id": "blur",
                "group": t("settings_group_appearance"),
                "title": t("settings_blur"),
                "keywords": "размытие блюр blur background фон размывать",
                "builder": lambda: self._create_switch_row(
                    t("settings_blur"), None, cfg.get("blur", True),
                    lambda active: self._on_setting_changed("blur", active)
                )
            },
            {
                "id": "animations",
                "group": t("settings_group_appearance"),
                "title": t("settings_animations"),
                "keywords": "анимация анимации animation speed плавность эффекты",
                "builder": lambda: self._create_switch_row(
                    t("settings_animations"), None, cfg.get("animations", True),
                    lambda active: self._on_setting_changed("animations", active)
                )
            },
            {
                "id": "unfold_animation",
                "group": t("settings_group_appearance"),
                "title": t("settings_unfold_animation"),
                "keywords": "анимация развертывания выезд скольжение unfold slide crossfade fade swing раскрытие динамический",
                "builder": lambda: self._create_unfold_animation_row(cfg)
            },
            {
                "id": "results_limit",
                "group": t("settings_group_results"),
                "title": t("settings_results_limit"),
                "keywords": "лимит количество results limit число выдача элементов",
                "builder": lambda: self._create_slider_row(
                    t("settings_results_limit"), cfg.get("results_limit", 20),
                    5, 50, 1, unit="",
                    callback=lambda val: self._on_setting_changed("results_limit", int(val))
                )
            },
            {
                "id": "preview_enabled",
                "group": t("settings_group_preview"),
                "title": t("settings_preview_enabled"),
                "keywords": "превью просмотр preview panel панель предпросмотра включить",
                "builder": lambda: self._create_switch_row(
                    t("settings_preview_enabled"), None, cfg.get("preview_enabled", True),
                    lambda active: self._on_setting_changed("preview_enabled", active)
                )
            },
            {
                "id": "preview_width",
                "group": t("settings_group_preview"),
                "title": t("settings_preview_width"),
                "keywords": "ширина размер preview width панель предпросмотра",
                "builder": lambda: self._create_slider_row(
                    t("settings_preview_width"), cfg.get("preview_width", 420),
                    200, 800, 10, unit="px",
                    callback=lambda val: self._on_setting_changed("preview_width", int(val))
                )
            },
            {
                "id": "cat_apps",
                "group": t("settings_group_categories"),
                "title": t("settings_cat_apps"),
                "keywords": "приложения apps программы категории поиск",
                "builder": lambda: self._create_switch_row(
                    t("settings_cat_apps"), None, cfg.get("applications", True),
                    lambda active: self._on_setting_changed("applications", active)
                )
            },
            {
                "id": "cat_files",
                "group": t("settings_group_categories"),
                "title": t("settings_cat_files"),
                "keywords": "файлы documents files папки категории поиск",
                "builder": lambda: self._create_switch_row(
                    t("settings_cat_files"), None, cfg.get("files", True),
                    lambda active: self._on_setting_changed("files", active)
                )
            },
            {
                "id": "cat_clipboard",
                "group": t("settings_group_categories"),
                "title": t("settings_cat_clipboard"),
                "keywords": "буфер история clipboard скопировано категории поиск",
                "builder": lambda: self._create_switch_row(
                    t("settings_cat_clipboard"), None, cfg.get("clipboard", True),
                    lambda active: self._on_setting_changed("clipboard", active)
                )
            },
            {
                "id": "cat_emoji",
                "group": t("settings_group_categories"),
                "title": t("settings_cat_emoji"),
                "keywords": "эмодзи emoji смайлы символы категории поиск",
                "builder": lambda: self._create_switch_row(
                    t("settings_cat_emoji"), None, cfg.get("emoji", True),
                    lambda active: self._on_setting_changed("emoji", active)
                )
            },
            {
                "id": "cat_calculator",
                "group": t("settings_group_categories"),
                "title": t("settings_cat_calc"),
                "keywords": "калькулятор calculator math конвертер валюты единицы категории поиск",
                "builder": lambda: self._create_switch_row(
                    t("settings_cat_calc"), None, cfg.get("calculator", True),
                    lambda active: self._on_setting_changed("calculator", active)
                )
            },
            {
                "id": "cat_commands",
                "group": t("settings_group_categories"),
                "title": t("settings_cat_commands"),
                "keywords": "команды commands bash терминал система категории поиск",
                "builder": lambda: self._create_switch_row(
                    t("settings_cat_commands"), None, cfg.get("commands", True),
                    lambda active: self._on_setting_changed("commands", active)
                )
            }
        ]

    def _build_settings_ui(self):
        while child := self.content_box.get_first_child():
            self.content_box.remove(child)

        cfg = self.main_window.config_manager

        # 1. ОФОРМЛЕНИЕ И АНИМАЦИИ (APPEARANCE & ANIMATIONS FIRST)
        group_appearance = self._create_group(t("settings_group_appearance"))
        group_appearance.append(self._create_theme_row(cfg))
        trans_val = int((cfg.get("transparency", 0.30) if cfg.get("transparency") is not None else 0.30) * 100)
        group_appearance.append(self._create_slider_row(
            t("settings_transparency"), trans_val, 0, 100, 1, unit="%",
            callback=lambda val: self._on_setting_changed("transparency", round(val / 100.0, 2))
        ))
        group_appearance.append(self._create_switch_row(
            t("settings_blur"), None, cfg.get("blur", True),
            lambda active: self._on_setting_changed("blur", active)
        ))
        group_appearance.append(self._create_switch_row(
            t("settings_animations"), None, cfg.get("animations", True),
            lambda active: self._on_setting_changed("animations", active)
        ))
        group_appearance.append(self._create_unfold_animation_row(cfg))

        # 2. ОСНОВНЫЕ ПАРАМЕТРЫ (GENERAL SETTINGS)
        group_general = self._create_group(t("settings_group_general"))
        group_general.append(self._create_language_row(cfg))
        group_general.append(self._create_switch_row(
            t("settings_autostart"), None, cfg.get("launch_at_login", False),
            lambda active: self._on_setting_changed("launch_at_login", active)
        ))
        group_general.append(self._create_shortcut_row(
            t("settings_hotkey"), cfg.get("launch_shortcut", "<Super>space")
        ))
        group_general.append(self._create_switch_row(
            t("settings_search_history"), None, cfg.get("search_history", True),
            lambda active: self._on_setting_changed("search_history", active)
        ))
        group_general.append(self._create_switch_row(
            t("settings_recent_when_empty"), None, cfg.get("recent_when_empty", True),
            lambda active: self._on_setting_changed("recent_when_empty", active)
        ))

        # 3. ПАРАМЕТРЫ ВЫДАЧИ
        group_params = self._create_group(t("settings_group_results"))
        group_params.append(self._create_slider_row(
            t("settings_results_limit"), cfg.get("results_limit", 20),
            5, 50, 1, unit="",
            callback=lambda val: self._on_setting_changed("results_limit", int(val))
        ))

        # 4. ПАНЕЛЬ ПРЕДПРОСМОТРА
        group_preview = self._create_group(t("settings_group_preview"))
        group_preview.append(self._create_switch_row(
            t("settings_preview_enabled"), None, cfg.get("preview_enabled", True),
            lambda active: self._on_setting_changed("preview_enabled", active)
        ))
        group_preview.append(self._create_slider_row(
            t("settings_preview_width"), cfg.get("preview_width", 420),
            200, 800, 10, unit="px",
            callback=lambda val: self._on_setting_changed("preview_width", int(val))
        ))

        # 5. КАТЕГОРИИ ПОИСКА
        group_categories = self._create_group(t("settings_group_categories"))
        group_categories.append(self._create_switch_row(
            t("settings_cat_apps"), None, cfg.get("applications", True),
            lambda active: self._on_setting_changed("applications", active)
        ))
        group_categories.append(self._create_switch_row(
            t("settings_cat_files"), None, cfg.get("files", True),
            lambda active: self._on_setting_changed("files", active)
        ))
        group_categories.append(self._create_switch_row(
            t("settings_cat_clipboard"), None, cfg.get("clipboard", True),
            lambda active: self._on_setting_changed("clipboard", active)
        ))
        group_categories.append(self._create_switch_row(
            t("settings_cat_emoji"), None, cfg.get("emoji", True),
            lambda active: self._on_setting_changed("emoji", active)
        ))
        group_categories.append(self._create_switch_row(
            t("settings_cat_calc"), None, cfg.get("calculator", True),
            lambda active: self._on_setting_changed("calculator", active)
        ))
        group_categories.append(self._create_switch_row(
            t("settings_cat_commands"), None, cfg.get("commands", True),
            lambda active: self._on_setting_changed("commands", active)
        ))

        # 6. КНОПКА СБРОСА
        reset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        reset_box.set_halign(Gtk.Align.CENTER)
        reset_box.set_margin_top(8)
        reset_btn = Gtk.Button(label=t("settings_reset_btn"))
        reset_btn.add_css_class("settings-reset-btn")
        reset_btn.connect("clicked", self._on_reset_defaults)
        reset_box.append(reset_btn)
        self.content_box.append(reset_box)

    def filter_settings(self, query: str):
        q = (query or "").strip().lower()
        if not q:
            self._build_settings_ui()
            return

        while child := self.content_box.get_first_child():
            self.content_box.remove(child)

        items = self._get_setting_definitions()
        matched_items = []
        tokens = q.split()

        for item in items:
            searchable = f"{item['title']} {item['group']} {item['keywords']}".lower()
            if all(tok in searchable for tok in tokens):
                matched_items.append(item)

        if not matched_items:
            empty_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            empty_box.add_css_class("empty-state-box")
            empty_box.set_halign(Gtk.Align.CENTER)
            empty_box.set_valign(Gtk.Align.CENTER)
            empty_box.set_margin_top(32)

            icon = Gtk.Image.new_from_icon_name("edit-find-symbolic")
            icon.set_pixel_size(48)
            icon.add_css_class("empty-state-icon")
            empty_box.append(icon)

            title = Gtk.Label(label=t("nothing_found_title"))
            title.add_css_class("empty-state-title")
            empty_box.append(title)

            desc = Gtk.Label(label=t("nothing_found_desc"))
            desc.add_css_class("empty-state-desc")
            empty_box.append(desc)

            self.content_box.append(empty_box)
            return

        group_results = self._create_group(f"{t('mode_settings')} — {len(matched_items)}")
        for item in matched_items:
            row = item["builder"]()
            group_results.append(row)

    def _create_group(self, title: str) -> Gtk.Box:
        group_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        group_box.add_css_class("settings-group-box")

        header_label = Gtk.Label(label=title)
        header_label.set_halign(Gtk.Align.START)
        header_label.add_css_class("settings-group-title")
        group_box.append(header_label)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        card.add_css_class("settings-card")
        group_box.append(card)

        self.content_box.append(group_box)
        return card

    def _create_switch_row(self, title: str, subtitle: str, active: bool, callback) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("settings-row")

        label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        label_box.set_hexpand(True)
        label_box.set_valign(Gtk.Align.CENTER)

        title_lbl = Gtk.Label(label=title)
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.add_css_class("settings-row-title")
        label_box.append(title_lbl)

        if subtitle:
            sub_lbl = Gtk.Label(label=subtitle)
            sub_lbl.set_halign(Gtk.Align.START)
            sub_lbl.add_css_class("settings-row-subtitle")
            label_box.append(sub_lbl)

        row.append(label_box)

        switch = Gtk.Switch()
        switch.set_active(active)
        switch.set_valign(Gtk.Align.CENTER)
        switch.add_css_class("settings-switch")
        switch.connect("state-set", lambda sw, state: callback(state))
        row.append(switch)

        return row

    def _create_slider_row(self, title: str, current_val: int, min_val: int, max_val: int, step: int, unit: str, callback) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("settings-row")

        title_lbl = Gtk.Label(label=title)
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.set_hexpand(True)
        title_lbl.set_valign(Gtk.Align.CENTER)
        title_lbl.add_css_class("settings-row-title")
        row.append(title_lbl)

        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ctrl_box.set_valign(Gtk.Align.CENTER)

        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, min_val, max_val, step)
        scale.set_value(current_val)
        scale.set_size_request(150, -1)
        scale.set_draw_value(False)
        scale.add_css_class("settings-slider")

        val_lbl = Gtk.Label(label=f"{int(current_val)}{unit}")
        val_lbl.set_size_request(45, -1)
        val_lbl.set_halign(Gtk.Align.END)
        val_lbl.set_valign(Gtk.Align.CENTER)
        val_lbl.add_css_class("settings-value-label")

        timer_id = [0]

        def on_slider_change(sc):
            v = sc.get_value()
            val_lbl.set_text(f"{int(v)}{unit}")
            if timer_id[0] != 0:
                GLib.source_remove(timer_id[0])

            def apply_change():
                callback(v)
                timer_id[0] = 0
                return False

            timer_id[0] = GLib.timeout_add(200, apply_change)

        scale.connect("value-changed", on_slider_change)

        ctrl_box.append(scale)
        ctrl_box.append(val_lbl)
        row.append(ctrl_box)
        return row

    def _create_theme_row(self, cfg) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("settings-row")

        title_lbl = Gtk.Label(label=t("settings_theme"))
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.set_hexpand(True)
        title_lbl.set_valign(Gtk.Align.CENTER)
        title_lbl.add_css_class("settings-row-title")
        row.append(title_lbl)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        btn_box.set_valign(Gtk.Align.CENTER)
        btn_box.add_css_class("settings-theme-selector")

        current_theme = cfg.get("theme", "dark_glass")
        themes = [
            ("dark_glass", t("settings_theme_dark_glass")),
            ("light_glass", t("settings_theme_light_glass")),
            ("dark", t("settings_theme_dark")),
            ("light", t("settings_theme_light")),
            ("aura_glow", "Aura Glow")
        ]

        for code, name in themes:
            btn = Gtk.Button(label=name)
            btn.add_css_class("theme-pill")
            if current_theme == code:
                btn.add_css_class("active")
            btn.connect("clicked", lambda b, c=code: self._on_theme_selected(c))
            btn_box.append(btn)

        row.append(btn_box)
        return row

    def _create_language_row(self, cfg) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("settings-row")

        title_lbl = Gtk.Label(label=t("settings_language"))
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.set_hexpand(True)
        title_lbl.set_valign(Gtk.Align.CENTER)
        title_lbl.add_css_class("settings-row-title")
        row.append(title_lbl)

        current_lang = cfg.get("language", "auto")
        lang_options = [("auto", t("settings_lang_auto"))] + list(SUPPORTED_LANGUAGES.items())
        
        string_list = Gtk.StringList.new([name for code, name in lang_options])
        dropdown = Gtk.DropDown.new(string_list, None)
        dropdown.set_valign(Gtk.Align.CENTER)
        dropdown.add_css_class("settings-dropdown")
        
        selected_idx = 0
        for idx, (code, name) in enumerate(lang_options):
            if code == current_lang:
                selected_idx = idx
                break
        dropdown.set_selected(selected_idx)

        def on_lang_changed(dd, param):
            pos = dd.get_selected()
            if 0 <= pos < len(lang_options):
                selected_code = lang_options[pos][0]
                if selected_code != cfg.get("language"):
                    self.main_window.config_manager.set("language", selected_code)
                    self.main_window.reload_config()
                    self._build_settings_ui()

        dropdown.connect("notify::selected", on_lang_changed)
        row.append(dropdown)
        return row

    def _create_unfold_animation_row(self, cfg) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("settings-row")

        title_lbl = Gtk.Label(label=t("settings_unfold_animation"))
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.set_hexpand(True)
        title_lbl.set_valign(Gtk.Align.CENTER)
        title_lbl.add_css_class("settings-row-title")
        row.append(title_lbl)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        btn_box.set_valign(Gtk.Align.CENTER)
        btn_box.add_css_class("settings-theme-selector")

        current_anim = cfg.get("unfold_animation", "slide_down")
        anim_options = [
            ("slide_down", t("anim_slide_down")),
            ("swing_down", t("anim_swing_down")),
            ("none", t("anim_none"))
        ]

        self.anim_buttons = {}
        for code, label in anim_options:
            btn = Gtk.Button(label=label)
            btn.add_css_class("theme-pill")
            if current_anim == code:
                btn.add_css_class("active")
            btn.connect("clicked", lambda b, c=code: self._on_anim_selected(c))
            btn_box.append(btn)
            self.anim_buttons[code] = btn

        row.append(btn_box)
        return row

    def _on_anim_selected(self, anim_code: str):
        self.main_window.config_manager.set("unfold_animation", anim_code)
        self.main_window.reload_config()
        if hasattr(self, 'anim_buttons'):
            for code, btn in self.anim_buttons.items():
                if code == anim_code:
                    btn.add_css_class("active")
                else:
                    btn.remove_css_class("active")

    def _create_shortcut_row(self, title: str, shortcut_text: str) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("settings-row")

        title_lbl = Gtk.Label(label=title)
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.set_hexpand(True)
        title_lbl.set_valign(Gtk.Align.CENTER)
        title_lbl.add_css_class("settings-row-title")
        row.append(title_lbl)

        btn = ShortcutButton(
            shortcut_text,
            lambda new_sc: self._on_setting_changed("launch_shortcut", new_sc)
        )
        row.append(btn)
        return row

    def _on_theme_selected(self, theme_code: str):
        self.main_window.config_manager.set("theme", theme_code)
        if theme_code in ("dark_glass", "light_glass", "aura_glow"):
            self.main_window.config_manager.set("transparency", 0.60)
            self.main_window.config_manager.set("blur", True)
        elif theme_code in ("dark", "light"):
            self.main_window.config_manager.set("transparency", 0.15)
        self.main_window.reload_config()
        self._build_settings_ui()

    def _on_setting_changed(self, key: str, value):
        self.main_window.config_manager.set(key, value)
        self.main_window.reload_config()
        return False

    def _on_reset_defaults(self, btn):
        cfg = self.main_window.config_manager
        for k, v in cfg.defaults.items():
            cfg.config[k] = v
        cfg.save()
        self.main_window.reload_config()
        self._build_settings_ui()

    def on_activated(self):
        query = self.main_window.entry.get_text() if hasattr(self.main_window, "entry") else ""
        if query and query.strip():
            self.filter_settings(query)
        else:
            self._build_settings_ui()
        
    def render(self, results: list):
        query = self.main_window.entry.get_text() if hasattr(self.main_window, "entry") else ""
        self.filter_settings(query)

    def on_key_pressed(self, keyval, state, current_results: list) -> bool:
        return False
