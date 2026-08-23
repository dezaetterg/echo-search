try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk, Pango
except ValueError:
    pass

from .base import BaseMode
from i18n import t

class SettingsMode(BaseMode):
    category_filter = "Settings"
    
    def _create_widget(self) -> Gtk.Widget:
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.box.add_css_class("settings-main-container")

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_min_content_height(420)
        self.scroll.set_max_content_height(520)
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

    def _build_settings_ui(self):
        # Clear existing
        while child := self.content_box.get_first_child():
            self.content_box.remove(child)

        cfg = self.main_window.config_manager

        # ========================================================
        # 1. ОСНОВНЫЕ ПАРАМЕТРЫ (General)
        # ========================================================
        group_general = self._create_group("ОСНОВНЫЕ ПАРАМЕТРЫ")
        
        # Запуск при входе
        group_general.append(self._create_switch_row(
            "Запуск при входе в систему",
            None,
            cfg.get("launch_at_login", False),
            lambda active: self._on_setting_changed("launch_at_login", active)
        ))

        # Сочетание клавиш
        shortcut_row = self._create_shortcut_row(
            "Сочетание клавиш запуска",
            cfg.get("launch_shortcut", "<Super>space")
        )
        group_general.append(shortcut_row)

        # История поиска
        group_general.append(self._create_switch_row(
            "История поиска",
            None,
            cfg.get("search_history", True),
            lambda active: self._on_setting_changed("search_history", active)
        ))

        # Показывать недавние элементы
        group_general.append(self._create_switch_row(
            "Показывать недавние элементы",
            None,
            cfg.get("recent_when_empty", True),
            lambda active: self._on_setting_changed("recent_when_empty", active)
        ))

        self.content_box.append(group_general)

        # ========================================================
        # 2. ПАРАМЕТРЫ ВЫДАЧИ (Search Parameters)
        # ========================================================
        group_params = self._create_group("ПАРАМЕТРЫ ВЫДАЧИ")

        group_params.append(self._create_slider_row(
            "Количество результатов",
            cfg.get("results_limit", 20),
            5, 50, 1,
            unit="",
            callback=lambda val: self._on_setting_changed("results_limit", int(val))
        ))

        self.content_box.append(group_params)

        # ========================================================
        # 3. ОФОРМЛЕНИЕ (Appearance)
        # ========================================================
        group_appearance = self._create_group("ОФОРМЛЕНИЕ")
        
        # Тема оформления
        group_appearance.append(self._create_theme_row(cfg))

        # Прозрачность окна (0% = непрозрачный, 100% = максимально прозрачный)
        trans_val = int((cfg.get("transparency", 0.30) if cfg.get("transparency") is not None else 0.30) * 100)
        group_appearance.append(self._create_slider_row(
            "Прозрачность окна",
            trans_val,
            0, 100, 1,
            unit="%",
            callback=lambda val: self._on_setting_changed("transparency", round(val / 100.0, 2))
        ))

        # Размытие фона
        group_appearance.append(self._create_switch_row(
            "Размытие фона (Blur)",
            None,
            cfg.get("blur", True),
            lambda active: self._on_setting_changed("blur", active)
        ))

        # Анимации интерфейса
        group_appearance.append(self._create_switch_row(
            "Анимации интерфейса",
            None,
            cfg.get("animations", True),
            lambda active: self._on_setting_changed("animations", active)
        ))

        self.content_box.append(group_appearance)

        # ========================================================
        # 4. ПАНЕЛЬ ПРЕДПРОСМОТРА (Preview Panel)
        # ========================================================
        group_preview = self._create_group("ПАНЕЛЬ ПРЕДПРОСМОТРА")

        # Панель быстрого просмотра
        group_preview.append(self._create_switch_row(
            "Панель быстрого просмотра",
            None,
            cfg.get("preview_enabled", True),
            lambda active: self._on_setting_changed("preview_enabled", active)
        ))

        # Ширина предпросмотра
        group_preview.append(self._create_slider_row(
            "Ширина предпросмотра",
            cfg.get("preview_width", 420),
            200, 800, 10,
            unit="px",
            callback=lambda val: self._on_setting_changed("preview_width", int(val))
        ))

        self.content_box.append(group_preview)

        # ========================================================
        # 5. КАТЕГОРИИ ПОИСКА (Search Categories)
        # ========================================================
        group_categories = self._create_group("КАТЕГОРИИ ПОИСКА")

        group_categories.append(self._create_switch_row(
            "Приложения",
            None,
            cfg.get("applications", True),
            lambda active: self._on_setting_changed("applications", active)
        ))

        group_categories.append(self._create_switch_row(
            "Файлы и документы",
            None,
            cfg.get("files", True),
            lambda active: self._on_setting_changed("files", active)
        ))

        group_categories.append(self._create_switch_row(
            "Буфер обмена",
            None,
            cfg.get("clipboard", True),
            lambda active: self._on_setting_changed("clipboard", active)
        ))

        group_categories.append(self._create_switch_row(
            "Символы и эмодзи",
            None,
            cfg.get("emoji", True),
            lambda active: self._on_setting_changed("emoji", active)
        ))

        group_categories.append(self._create_switch_row(
            "Калькулятор и конвертер",
            None,
            cfg.get("calculator", True),
            lambda active: self._on_setting_changed("calculator", active)
        ))

        group_categories.append(self._create_switch_row(
            "Системные команды",
            None,
            cfg.get("commands", True),
            lambda active: self._on_setting_changed("commands", active)
        ))

        self.content_box.append(group_categories)

        # ========================================================
        # 6. КНОПКА СБРОСА
        # ========================================================
        reset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        reset_box.set_halign(Gtk.Align.CENTER)
        reset_box.set_margin_top(8)

        reset_btn = Gtk.Button(label="Восстановить настройки по умолчанию")
        reset_btn.add_css_class("settings-reset-btn")
        reset_btn.connect("clicked", self._on_reset_defaults)
        reset_box.append(reset_btn)

        self.content_box.append(reset_box)

    def _create_group(self, title: str) -> Gtk.Box:
        group_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        group_box.add_css_class("settings-group-box")

        header_label = Gtk.Label(label=title)
        header_label.set_halign(Gtk.Align.START)
        header_label.add_css_class("settings-group-title")
        group_box.append(header_label)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        card.add_css_class("settings-card")
        group_box.append(card)
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

        def on_slider_change(sc):
            v = sc.get_value()
            val_lbl.set_text(f"{int(v)}{unit}")
            callback(v)

        scale.connect("value-changed", on_slider_change)

        ctrl_box.append(scale)
        ctrl_box.append(val_lbl)
        row.append(ctrl_box)
        return row

    def _create_theme_row(self, cfg) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("settings-row")

        title_lbl = Gtk.Label(label="Тема оформления")
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.set_hexpand(True)
        title_lbl.set_valign(Gtk.Align.CENTER)
        title_lbl.add_css_class("settings-row-title")
        row.append(title_lbl)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        btn_box.set_valign(Gtk.Align.CENTER)
        btn_box.add_css_class("settings-theme-selector")

        current_theme = cfg.get("theme", "light")
        themes = [
            ("silver", "Liquid Glass"),
            ("light", "Светлая"),
            ("dark", "Тёмная")
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

    def _create_shortcut_row(self, title: str, shortcut_text: str) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("settings-row")

        title_lbl = Gtk.Label(label=title)
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.set_hexpand(True)
        title_lbl.set_valign(Gtk.Align.CENTER)
        title_lbl.add_css_class("settings-row-title")
        row.append(title_lbl)

        badge = Gtk.Label(label="⌘ Space")
        badge.set_valign(Gtk.Align.CENTER)
        badge.add_css_class("shortcut-badge")
        row.append(badge)

        return row

    def _on_theme_selected(self, theme_code: str):
        self.main_window.config_manager.set("theme", theme_code)
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
        self._build_settings_ui()
        self.main_window.set_default_size(750, 1)
        self.main_window.queue_resize()

    def render(self, results: list):
        pass

    def on_key_pressed(self, keyval, state, current_results: list) -> bool:
        return False
