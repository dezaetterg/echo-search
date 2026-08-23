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
        self.scroll.set_max_content_height(480)
        self.scroll.set_hexpand(True)
        self.scroll.set_vexpand(True)
        self.scroll.add_css_class("settings-scrolled")

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.content_box.set_margin_start(24)
        self.content_box.set_margin_end(24)
        self.content_box.set_margin_top(16)
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

        # --- Section 1: Внешний вид ---
        group_appearance = self._create_group("Внешний вид")
        
        # Тема
        theme_row = self._create_theme_row(cfg)
        group_appearance.append(theme_row)
        
        # Размытие
        blur_row = self._create_switch_row(
            "Размытие фона (Blur)",
            "Эффект матового стекла под окном лаунчера",
            cfg.get("blur", True),
            lambda active: self._on_setting_changed("blur", active)
        )
        group_appearance.append(blur_row)

        # Анимации
        anim_row = self._create_switch_row(
            "Плавные анимации",
            "Анимации открытия категорий и результатов",
            cfg.get("animations", True),
            lambda active: self._on_setting_changed("animations", active)
        )
        group_appearance.append(anim_row)

        self.content_box.append(group_appearance)

        # --- Section 2: Источники поиска ---
        group_search = self._create_group("Источники поиска")
        
        group_search.append(self._create_switch_row(
            "Приложения",
            "Поиск и запуск установленных программ",
            cfg.get("applications", True),
            lambda active: self._on_setting_changed("applications", active)
        ))

        group_search.append(self._create_switch_row(
            "Файлы и документы",
            "Глубокий поиск файлов через GNOME Tracker 3",
            cfg.get("files", True),
            lambda active: self._on_setting_changed("files", active)
        ))

        group_search.append(self._create_switch_row(
            "История буфера обмена",
            "Сохранение и быстрый поиск скопированного текста",
            cfg.get("clipboard", True),
            lambda active: self._on_setting_changed("clipboard", active)
        ))

        group_search.append(self._create_switch_row(
            "Калькулятор и конвертер",
            "Подсчет формул и перевод единиц измерения в строке ввода",
            cfg.get("calculator", True),
            lambda active: self._on_setting_changed("calculator", active)
        ))

        group_search.append(self._create_switch_row(
            "Эмодзи и символы",
            "Поиск смайлов по названию и ключевым словам",
            cfg.get("emoji", True),
            lambda active: self._on_setting_changed("emoji", active)
        ))

        group_search.append(self._create_switch_row(
            "Системные команды",
            "Быстрые действия (Перезагрузка, Выключение, Блокировка)",
            cfg.get("commands", True),
            lambda active: self._on_setting_changed("commands", active)
        ))

        self.content_box.append(group_search)

        # --- Section 3: Система и интерфейс ---
        group_system = self._create_group("Система и поведение")

        group_system.append(self._create_switch_row(
            "Автозапуск при входе",
            "Запускать фоновую службу Echo Search при старте системы",
            cfg.get("launch_at_login", False),
            lambda active: self._on_setting_changed("launch_at_login", active)
        ))

        group_system.append(self._create_switch_row(
            "Панель предпросмотра",
            "Отображать панель деталей и превью файлов справа",
            cfg.get("preview_enabled", True),
            lambda active: self._on_setting_changed("preview_enabled", active)
        ))

        group_system.append(self._create_switch_row(
            "История поиска",
            "Предлагать недавние запросы при пустом поиске",
            cfg.get("search_history", True),
            lambda active: self._on_setting_changed("search_history", active)
        ))

        self.content_box.append(group_system)

        # --- Кнопка сброса ---
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

    def _create_theme_row(self, cfg) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("settings-row")

        label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        label_box.set_hexpand(True)
        label_box.set_valign(Gtk.Align.CENTER)

        title_lbl = Gtk.Label(label="Тема оформления")
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.add_css_class("settings-row-title")
        label_box.append(title_lbl)

        sub_lbl = Gtk.Label(label="Стиль стеклянного интерфейса и подсветки")
        sub_lbl.set_halign(Gtk.Align.START)
        sub_lbl.add_css_class("settings-row-subtitle")
        label_box.append(sub_lbl)

        row.append(label_box)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_box.set_valign(Gtk.Align.CENTER)
        btn_box.add_css_class("settings-theme-selector")

        current_theme = cfg.get("theme", "silver")
        themes = [
            ("silver", "Liquid Glass"),
            ("dark", "Dark"),
            ("light", "Light")
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
