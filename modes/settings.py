try:
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gdk, GLib, Gtk, Pango
except ValueError:
    pass

from i18n import SUPPORTED_LANGUAGES, t
from utils import set_icon_safe

from .base import BaseMode


class ShortcutButton(Gtk.Button):
    def __init__(self, current_shortcut: str, on_changed_callback, allow_single_key: bool = False):
        super().__init__()
        self.current_shortcut = current_shortcut or "<Super>space"
        self.on_changed_callback = on_changed_callback
        self.allow_single_key = allow_single_key
        self.is_recording = False

        self.add_css_class("shortcut-button")
        self.set_valign(Gtk.Align.CENTER)
        self.update_label()

        self.connect("clicked", self._on_clicked)

        self.key_ctrl = Gtk.EventControllerKey.new()
        self.key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(self.key_ctrl)

    def _format_display(self, shortcut: str) -> str:
        from i18n import get_current_language
        from utils import format_shortcut_display
        return format_shortcut_display(shortcut, get_current_language())

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

        if not mod_str and not key_str.lower().startswith("f"):
            if not self.allow_single_key:
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
                "id": "icon_theme",
                "group": t("settings_group_appearance"),
                "title": t("settings_icon_theme"),
                "keywords": "иконка значок тема иконки icon icon_theme app icon dark light aura",
                "builder": lambda: self._create_icon_theme_row(cfg)
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
                "id": "animation_speed",
                "group": t("settings_group_appearance"),
                "title": t("settings_animation_speed"),
                "keywords": "скорость анимаций animation speed плавность темп длительность регулятор",
                "builder": lambda: self._create_slider_row(
                    t("settings_animation_speed"),
                    int(cfg.get("animation_speed", 100)),
                    50, 200, 10, unit="%",
                    callback=lambda val: self._on_setting_changed("animation_speed", int(val))
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
                "id": "group_results_by_category",
                "group": t("settings_group_results"),
                "title": t("settings_group_results_by_cat"),
                "keywords": "группировка категории блоки секции заголовки group category results order",
                "builder": lambda: self._create_switch_row(
                    t("settings_group_results_by_cat"),
                    t("settings_group_results_by_cat_desc"),
                    cfg.get("group_results_by_category", True),
                    lambda active: self._on_setting_changed("group_results_by_category", active)
                )
            },
            {
                "id": "results_category_order",
                "group": t("settings_group_results"),
                "title": t("settings_category_order"),
                "keywords": "приоритет порядок категорий блоки сначала сверху приложения файлы буфер смайлики category order",
                "builder": lambda: self._create_category_order_row(cfg)
            },
            {
                "id": "highlight_matches",
                "group": t("settings_group_results"),
                "title": t("settings_highlight_matches"),
                "keywords": "подсветка совпадений highlight matches буквы слова поиск результаты",
                "builder": lambda: self._create_switch_row(
                    t("settings_highlight_matches"),
                    t("settings_highlight_matches_desc"),
                    cfg.get("highlight_matches", True),
                    lambda active: self._on_setting_changed("highlight_matches", active)
                )
            },
            {
                "id": "show_action_bar",
                "group": t("settings_group_results"),
                "title": t("settings_show_action_bar"),
                "keywords": "подсказки подсказка хоткеи клавиши панель быстрых действий action bar hotkey hints клавиш внизу",
                "builder": lambda: self._create_switch_row(
                    t("settings_show_action_bar"),
                    t("settings_show_action_bar_desc"),
                    cfg.get("show_action_bar", True),
                    lambda active: self._on_setting_changed("show_action_bar", active)
                )
            },
            {
                "id": "show_alt_badges",
                "group": t("settings_group_results"),
                "title": t("settings_show_alt_badges"),
                "keywords": "цифровые подсказки alt 1 9 номера бейджи быстрый выбор jump hints",
                "builder": lambda: self._create_switch_row(
                    t("settings_show_alt_badges"),
                    t("settings_show_alt_badges_desc"),
                    cfg.get("show_alt_badges", True),
                    lambda active: self._on_setting_changed("show_alt_badges", active)
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
                "id": "quick_look_shortcut",
                "group": t("settings_group_preview"),
                "title": t("settings_quick_look_shortcut"),
                "keywords": "горячие клавиши шорткат shortcut hotkey quick look просмотр пробел space клавиша",
                "builder": lambda: self._create_shortcut_row(
                    t("settings_quick_look_shortcut"),
                    cfg.get("quick_look_shortcut", "space"),
                    callback=lambda new_sc: self._on_setting_changed("quick_look_shortcut", new_sc),
                    allow_single_key=True
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
            },
            {
                "id": "web_search_engine",
                "group": t("settings_group_web_search"),
                "title": t("settings_web_search_engine"),
                "keywords": "интернет веб поиск поисковик браузер google yandex duckduckgo brave bing custom",
                "builder": lambda: self._create_search_engine_row(cfg)
            },
            {
                "id": "web_search_custom_url",
                "group": t("settings_group_web_search"),
                "title": t("settings_web_custom_url"),
                "keywords": "кастомный пользовательский url ссылка поиск query шаблон",
                "builder": lambda: self._create_entry_row(
                    t("settings_web_custom_url"),
                    cfg.get("web_search_custom_url", ""),
                    "https://duckduckgo.com/?q={query}",
                    lambda val: self._on_setting_changed("web_search_custom_url", val)
                )
            },
            {
                "id": "web_search_flags",
                "group": t("settings_group_web_search"),
                "title": t("settings_web_flags"),
                "keywords": "флаги префиксы быстрый поиск -g -ya -ddg -y -gh -w",
                "builder": lambda: self._create_switch_row(
                    t("settings_web_flags"), t("settings_web_flags_desc"), cfg.get("web_search_flags", True),
                    lambda active: self._on_setting_changed("web_search_flags", active)
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
        group_appearance.append(self._create_icon_theme_row(cfg))
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
        group_appearance.append(self._create_slider_row(
            t("settings_animation_speed"),
            int(cfg.get("animation_speed", 100)),
            50, 200, 10, unit="%",
            callback=lambda val: self._on_setting_changed("animation_speed", int(val))
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
        group_params.append(self._create_switch_row(
            t("settings_group_results_by_cat"),
            t("settings_group_results_by_cat_desc"),
            cfg.get("group_results_by_category", True),
            lambda active: self._on_setting_changed("group_results_by_category", active)
        ))
        group_params.append(self._create_category_order_row(cfg))
        group_params.append(self._create_switch_row(
            t("settings_highlight_matches"),
            t("settings_highlight_matches_desc"),
            cfg.get("highlight_matches", True),
            lambda active: self._on_setting_changed("highlight_matches", active)
        ))
        group_params.append(self._create_switch_row(
            t("settings_show_action_bar"),
            t("settings_show_action_bar_desc"),
            cfg.get("show_action_bar", True),
            lambda active: self._on_setting_changed("show_action_bar", active)
        ))
        group_params.append(self._create_switch_row(
            t("settings_show_alt_badges"),
            t("settings_show_alt_badges_desc"),
            cfg.get("show_alt_badges", True),
            lambda active: self._on_setting_changed("show_alt_badges", active)
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
        group_preview.append(self._create_shortcut_row(
            t("settings_quick_look_shortcut"),
            cfg.get("quick_look_shortcut", "space"),
            callback=lambda new_sc: self._on_setting_changed("quick_look_shortcut", new_sc),
            allow_single_key=True
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
        group_categories.append(self._create_switch_row(
            t("settings_cat_weather"), None, cfg.get("weather", True),
            lambda active: self._on_setting_changed("weather", active)
        ))
        group_categories.append(self._create_entry_row(
            t("settings_weather_default_city"),
            cfg.get("weather_default_city", "Новокузнецк"),
            placeholder="Новокузнецк, Москва, Лондон...",
            callback=lambda val: self._on_setting_changed("weather_default_city", val.strip() if val else "Новокузнецк")
        ))
        group_categories.append(self._create_temp_unit_row(cfg))

        # 6. ПОИСК В ИНТЕРНЕТЕ (WEB SEARCH)
        group_web = self._create_group(t("settings_group_web_search"))
        group_web.append(self._create_search_engine_row(cfg))
        group_web.append(self._create_entry_row(
            t("settings_web_custom_url"),
            cfg.get("web_search_custom_url", ""),
            placeholder="https://duckduckgo.com/?q={query}",
            callback=lambda val: self._on_setting_changed("web_search_custom_url", val.strip())
        ))
        group_web.append(self._create_switch_row(
            t("settings_web_flags"), t("settings_web_flags_desc"), cfg.get("web_search_flags", True),
            lambda active: self._on_setting_changed("web_search_flags", active)
        ))

        # 7. КНОПКА СБРОСА
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

    def _create_entry_row(self, title: str, current_val: str, placeholder: str, callback) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("settings-row")

        label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        label_box.set_hexpand(True)
        label_box.set_valign(Gtk.Align.CENTER)

        title_lbl = Gtk.Label(label=title)
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.add_css_class("settings-row-title")
        label_box.append(title_lbl)

        row.append(label_box)

        entry = Gtk.Entry()
        entry.set_text(current_val or "")
        entry.set_placeholder_text(placeholder or "")
        entry.set_valign(Gtk.Align.CENTER)
        entry.add_css_class("settings-entry")

        entry.connect("activate", lambda e: callback(e.get_text()))
        focus_ctrl = Gtk.EventControllerFocus.new()
        focus_ctrl.connect("leave", lambda ctrl: callback(entry.get_text()))
        entry.add_controller(focus_ctrl)

        row.append(entry)
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

    def _create_temp_unit_row(self, cfg) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("settings-row")

        label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        label_box.set_halign(Gtk.Align.START)
        label_box.set_hexpand(True)
        label_box.set_valign(Gtk.Align.CENTER)

        title_lbl = Gtk.Label(label=t("settings_temp_unit"))
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.add_css_class("settings-row-title")
        label_box.append(title_lbl)

        desc_lbl = Gtk.Label(label=t("settings_temp_unit_desc"))
        desc_lbl.set_halign(Gtk.Align.START)
        desc_lbl.add_css_class("settings-row-subtitle")
        label_box.append(desc_lbl)

        row.append(label_box)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        btn_box.set_valign(Gtk.Align.CENTER)
        btn_box.add_css_class("settings-theme-selector")

        current_unit = cfg.get("temperature_unit", "celsius")
        units = [
            ("celsius", "°C"),
            ("fahrenheit", "°F")
        ]

        buttons = []
        for code, name in units:
            btn = Gtk.Button(label=name)
            btn.add_css_class("theme-pill")
            if current_unit == code:
                btn.add_css_class("active")
            buttons.append((code, btn))

        def _on_unit_click(selected_code):
            for code, b in buttons:
                if code == selected_code:
                    b.add_css_class("active")
                else:
                    b.remove_css_class("active")
            self._on_setting_changed("temperature_unit", selected_code)

        for code, btn in buttons:
            btn.connect("clicked", lambda _, c=code: _on_unit_click(c))
            btn_box.append(btn)

        row.append(btn_box)
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
            ("aura_glow", "Aura Glow"),
            ("echo_blue", t("settings_theme_echo_blue"))
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

    def _create_icon_theme_row(self, cfg) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("settings-row")

        title_lbl = Gtk.Label(label=t("settings_icon_theme"))
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.set_hexpand(True)
        title_lbl.set_valign(Gtk.Align.CENTER)
        title_lbl.add_css_class("settings-row-title")
        row.append(title_lbl)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        btn_box.set_valign(Gtk.Align.CENTER)
        btn_box.add_css_class("settings-theme-selector")

        current_icon_theme = cfg.get("icon_theme", "dark")
        icon_themes = [
            ("dark", t("settings_icon_theme_dark")),
            ("light", t("settings_icon_theme_light")),
            ("aura", t("settings_icon_theme_aura")),
        ]

        for code, name in icon_themes:
            btn = Gtk.Button(label=name)
            btn.add_css_class("theme-pill")
            if current_icon_theme == code:
                btn.add_css_class("active")
            btn.connect("clicked", lambda b, c=code: self._on_icon_theme_selected(c))
            btn_box.append(btn)

        row.append(btn_box)
        return row

    def _on_icon_theme_selected(self, icon_theme_code: str):
        self.main_window.config_manager.set("icon_theme", icon_theme_code)
        self.main_window.reload_config()
        self._build_settings_ui()

    def _create_category_order_row(self, cfg) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("settings-row")

        label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        label_box.set_halign(Gtk.Align.START)
        label_box.set_hexpand(True)
        label_box.set_valign(Gtk.Align.CENTER)

        title_lbl = Gtk.Label(label=t("settings_category_order"))
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.add_css_class("settings-row-title")
        label_box.append(title_lbl)

        desc_lbl = Gtk.Label(label=t("settings_category_order_desc"))
        desc_lbl.set_halign(Gtk.Align.START)
        desc_lbl.add_css_class("settings-row-subtitle")
        label_box.append(desc_lbl)

        row.append(label_box)

        order_presets = [
            ("apps", t("settings_order_preset_apps"), ["instant", "apps", "files", "clipboard", "emoji", "web"]),
            ("files", t("settings_order_preset_files"), ["files", "instant", "apps", "clipboard", "emoji", "web"]),
            ("clipboard", t("settings_order_preset_clipboard"), ["clipboard", "instant", "apps", "files", "emoji", "web"]),
            ("emoji", t("settings_order_preset_emoji"), ["emoji", "instant", "apps", "files", "clipboard", "web"]),
            ("instant", t("settings_order_preset_instant"), ["instant", "apps", "files", "clipboard", "emoji", "web"]),
        ]

        current_order = cfg.get("results_category_order", ["instant", "apps", "files", "clipboard", "emoji", "web"])
        top_cat = current_order[0] if current_order else "apps"
        if top_cat == "instant" and len(current_order) > 1 and current_order[1] == "apps":
            top_cat = "apps"

        string_list = Gtk.StringList.new([label for _, label, _ in order_presets])
        dropdown = Gtk.DropDown.new(string_list, None)
        dropdown.set_valign(Gtk.Align.CENTER)
        dropdown.add_css_class("settings-dropdown")

        selected_idx = 0
        for idx, (code, _, _) in enumerate(order_presets):
            if code == top_cat:
                selected_idx = idx
                break
        dropdown.set_selected(selected_idx)

        def on_order_changed(dd, param):
            pos = dd.get_selected()
            if 0 <= pos < len(order_presets):
                new_order = order_presets[pos][2]
                self._on_setting_changed("results_category_order", new_order)

        dropdown.connect("notify::selected", on_order_changed)
        row.append(dropdown)
        return row


    def _create_search_engine_row(self, cfg) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("settings-row")

        title_lbl = Gtk.Label(label=t("settings_web_search_engine"))
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.set_hexpand(True)
        title_lbl.set_valign(Gtk.Align.CENTER)
        title_lbl.add_css_class("settings-row-title")
        row.append(title_lbl)

        current_engine = cfg.get("web_search_engine", "google")
        engine_options = [
            ("google", "Google"),
            ("yandex", "Яндекс"),
            ("duckduckgo", "DuckDuckGo"),
            ("brave", "Brave"),
            ("bing", "Bing"),
            ("youtube", "YouTube"),
            ("github", "GitHub"),
            ("wikipedia", "Wikipedia"),
            ("custom", "Пользовательский URL")
        ]

        from providers.web import get_engine_icon

        engine_icon = Gtk.Image()
        engine_icon.set_valign(Gtk.Align.CENTER)
        engine_icon.set_pixel_size(24)
        set_icon_safe(engine_icon, get_engine_icon(current_engine), fallback_icon="applications-internet-symbolic", pixel_size=24)
        row.append(engine_icon)

        string_list = Gtk.StringList.new([name for code, name in engine_options])
        dropdown = Gtk.DropDown.new(string_list, None)
        dropdown.set_valign(Gtk.Align.CENTER)
        dropdown.add_css_class("settings-dropdown")

        selected_idx = 0
        for idx, (code, name) in enumerate(engine_options):
            if code == current_engine:
                selected_idx = idx
                break
        dropdown.set_selected(selected_idx)

        def on_engine_changed(dd, param):
            pos = dd.get_selected()
            if 0 <= pos < len(engine_options):
                selected_code = engine_options[pos][0]
                set_icon_safe(engine_icon, get_engine_icon(selected_code), fallback_icon="applications-internet-symbolic", pixel_size=24)
                if selected_code != cfg.get("web_search_engine"):
                    self.main_window.config_manager.set("web_search_engine", selected_code)

        dropdown.connect("notify::selected", on_engine_changed)
        row.append(dropdown)
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

        current_anim = cfg.get("unfold_animation", "instant_dynamic")
        anim_options = [
            ("instant_dynamic", t("anim_instant_dynamic")),
            ("slide_down", t("anim_slide_down")),
            ("swing_down", t("anim_swing_down")),
            ("jelly_wobble", t("anim_jelly_wobble")),
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

    def _create_shortcut_row(self, title: str, shortcut_text: str, callback=None, allow_single_key: bool = False) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("settings-row")

        title_lbl = Gtk.Label(label=title)
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.set_hexpand(True)
        title_lbl.set_valign(Gtk.Align.CENTER)
        title_lbl.add_css_class("settings-row-title")
        row.append(title_lbl)

        cb = callback or (lambda new_sc: self._on_setting_changed("launch_shortcut", new_sc))
        btn = ShortcutButton(
            shortcut_text,
            cb,
            allow_single_key=allow_single_key
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
        if hasattr(self, "scroll") and self.scroll:
            adj = self.scroll.get_vadjustment()
            if adj:
                page_size = adj.get_page_size()
                lower = adj.get_lower()
                upper = adj.get_upper()
                curr = adj.get_value()

                if keyval in (Gdk.KEY_Page_Down, Gdk.KEY_KP_Page_Down):
                    adj.set_value(min(upper - page_size, curr + 180.0))
                    return True
                elif keyval in (Gdk.KEY_Page_Up, Gdk.KEY_KP_Page_Up):
                    adj.set_value(max(lower, curr - 180.0))
                    return True
                elif keyval in (Gdk.KEY_Down, Gdk.KEY_KP_Down) or ((state & Gdk.ModifierType.CONTROL_MASK) and keyval in (Gdk.KEY_n, Gdk.KEY_N, Gdk.KEY_j, Gdk.KEY_J)):
                    adj.set_value(min(upper - page_size, curr + 60.0))
                    return True
                elif keyval in (Gdk.KEY_Up, Gdk.KEY_KP_Up) or ((state & Gdk.ModifierType.CONTROL_MASK) and keyval in (Gdk.KEY_p, Gdk.KEY_P)):
                    adj.set_value(max(lower, curr - 60.0))
                    return True
                elif (state & Gdk.ModifierType.CONTROL_MASK) and keyval in (Gdk.KEY_Home, Gdk.KEY_KP_Home):
                    adj.set_value(lower)
                    return True
                elif (state & Gdk.ModifierType.CONTROL_MASK) and keyval in (Gdk.KEY_End, Gdk.KEY_KP_End):
                    adj.set_value(upper - page_size)
                    return True
        return False
