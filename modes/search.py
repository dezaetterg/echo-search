import functools
import os

from gi.repository import GdkPixbuf

try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gdk, GLib, Gtk, Pango
except ValueError:
    pass

import preview_manager
from i18n import t
from logger import get_logger
from search_engine import get_result_category_group
from utils import matches_shortcut, set_icon_safe

from .base import BaseMode

logger = get_logger("modes.search")


@functools.lru_cache(maxsize=512)
def get_scaled_pixbuf_cached(icon_path: str, size: int = 48):
    try:
        if os.path.exists(icon_path):
            return GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_path, size, size, True)
    except GLib.Error as e:
        logger.debug("Failed to load scaled pixbuf for %s: %s", icon_path, e)
    return None

EXCLUDED_HIGHLIGHT_CATEGORIES = {"Math", "Units", "Currency", "Time", "Weather"}


def get_highlight_accent_color(config_manager) -> str:
    theme = config_manager.get("theme", "dark_glass") if config_manager else "dark_glass"
    if theme in ("light", "light_glass"):
        return "#007aff"
    elif theme == "aura_glow":
        return "#c084fc"
    else:
        return "#5dade2"


def extract_search_terms(query: str) -> list[str]:
    clean_q = query.strip()
    if not clean_q:
        return []
    try:
        from providers import parse_search_flag
        flag_info = parse_search_flag(clean_q)
        if flag_info:
            clean_q = flag_info[1]
    except Exception as e:
        logger.debug("parse_search_flag failed: %s", e)

    if clean_q.startswith(">"):
        clean_q = clean_q[1:].strip()
    elif clean_q.startswith("/") and " " in clean_q:
        clean_q = clean_q.split(maxsplit=1)[1].strip()

    terms = []
    seen = set()
    for t_word in clean_q.split():
        t_clean = t_word.strip().lower()
        if t_clean and t_clean not in seen:
            seen.add(t_clean)
            terms.append(t_clean)
    terms.sort(key=len, reverse=True)
    return terms


def highlight_matches(text: str, terms: list[str], accent_color: str) -> str:
    if not text:
        return ""
    if not terms:
        return GLib.markup_escape_text(text)

    lower_text = text.lower()
    intervals = []
    for term in terms:
        t_len = len(term)
        if t_len == 0:
            continue
        start = 0
        while True:
            idx = lower_text.find(term, start)
            if idx == -1:
                break
            intervals.append((idx, idx + t_len))
            start = idx + 1

    if not intervals:
        return GLib.markup_escape_text(text)

    intervals.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    merged = []
    for start, end in intervals:
        if not merged:
            merged.append([start, end])
        else:
            last_start, last_end = merged[-1]
            if start <= last_end:
                merged[-1][1] = max(last_end, end)
            else:
                merged.append([start, end])

    parts = []
    curr = 0
    for start, end in merged:
        if start > curr:
            parts.append(GLib.markup_escape_text(text[curr:start]))
        matched = GLib.markup_escape_text(text[start:end])
        parts.append(f'<span weight="bold" foreground="{accent_color}">{matched}</span>')
        curr = end
    if curr < len(text):
        parts.append(GLib.markup_escape_text(text[curr:]))

    return "".join(parts)


def _update_label_markup(label_widget: Gtk.Label, text: str, marked_text: str, should_highlight: bool):
    if should_highlight and marked_text:
        if getattr(label_widget, '_rendered_markup', None) != marked_text:
            try:
                label_widget.set_markup(marked_text)
                label_widget._rendered_markup = marked_text
            except GLib.Error as e:
                logger.debug("Failed to set label markup: %s", e)
                label_widget.set_label(text)
                label_widget._rendered_markup = None
    else:
        if getattr(label_widget, '_rendered_markup', None) is not None or label_widget.get_text() != text:
            label_widget.set_label(text)
            label_widget._rendered_markup = None


class SearchMode(BaseMode):
    category_filter = "All"

    def _create_widget(self) -> Gtk.Widget:
        self.current_results = []
        self.selected_index = -1
        self._navigated_with_arrows = False
        self.is_scrolling = False
        self._current_preview_id = None

        self.main_split = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        self.left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.left_box.set_size_request(610, 500)
        self.left_box.set_vexpand(True)

        # Разделитель
        self.separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.separator.add_css_class("main-separator")
        self.separator.set_visible(False)
        self.left_box.append(self.separator)

        # Список результатов
        self.results_listbox = Gtk.ListBox()
        self.results_listbox.set_name("results-list")
        self.results_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.results_listbox.connect("row-activated", self.on_row_activated)
        self.results_listbox.connect("row-selected", self.on_row_selected)
        self.results_listbox.set_header_func(self._header_func)

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_max_content_height(560)
        self.scroll.set_min_content_height(480)
        self.scroll.set_propagate_natural_height(True)
        self.scroll.set_vexpand(True)
        self.scroll.set_child(self.results_listbox)

        self.left_box.append(self.scroll)

        # Виджет "Ничего не найдено" (Empty State)
        self.empty_state_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.empty_state_box.add_css_class("empty-state-box")
        self.empty_state_box.set_valign(Gtk.Align.CENTER)
        self.empty_state_box.set_halign(Gtk.Align.FILL)
        self.empty_state_box.set_vexpand(True)
        self.empty_state_box.set_hexpand(True)
        self.empty_state_box.set_visible(False)

        self.empty_state_icon = Gtk.Image.new_from_icon_name("system-search-symbolic")
        self.empty_state_icon.set_pixel_size(44)
        self.empty_state_icon.add_css_class("empty-state-icon")
        self.empty_state_box.append(self.empty_state_icon)

        self.empty_state_title = Gtk.Label()
        self.empty_state_title.add_css_class("empty-state-title")
        self.empty_state_box.append(self.empty_state_title)

        self.empty_state_desc = Gtk.Label()
        self.empty_state_desc.add_css_class("empty-state-desc")
        self.empty_state_box.append(self.empty_state_desc)

        # Контейнер интерактивных действий (Web Search / Terminal)
        self.empty_actions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.empty_actions_box.add_css_class("empty-actions-container")
        self.empty_actions_box.set_halign(Gtk.Align.CENTER)
        self.empty_actions_box.set_valign(Gtk.Align.CENTER)
        self.empty_actions_box.set_margin_top(16)

        # 1. Карточка поиска в интернете
        cfg = getattr(self.main_window, "config_manager", None)
        initial_engine = cfg.get("web_search_engine", "google") if cfg else "google"
        from providers.web import get_engine_icon
        initial_web_icon = get_engine_icon(initial_engine)

        self.empty_web_btn, self.empty_web_sub_lbl, self.empty_web_icon = self._create_empty_action_card(
            icon_name=initial_web_icon,
            title=t("empty_action_web_title"),
            badge_text="↵ Enter",
            on_click=lambda btn: self._execute_web_search()
        )
        self.empty_actions_box.append(self.empty_web_btn)

        # 2. Карточка запуска в терминале
        self.empty_terminal_btn, self.empty_terminal_sub_lbl, self.empty_terminal_icon = self._create_empty_action_card(
            icon_name="utilities-terminal-symbolic",
            title=t("empty_action_terminal_title"),
            badge_text="Ctrl + ↵",
            on_click=lambda btn: self._execute_terminal_search()
        )
        self.empty_actions_box.append(self.empty_terminal_btn)

        self.empty_state_box.append(self.empty_actions_box)

        self.left_box.append(self.empty_state_box)
        self.main_split.append(self.left_box)

        # Превью панель (Новая версия)
        self.preview_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.preview_container.add_css_class("preview-panel")
        self.preview_container.set_vexpand(True)
        preview_width = self.main_window.config_manager.get("preview_width") if getattr(self.main_window, "config_manager", None) else 420
        self.preview_container.set_size_request(preview_width, 500)
        self.main_split.append(self.preview_container)

        # Нижняя интерактивная панель быстрых действий (Action Bar) на всю ширину окна в самом низу
        self.footer_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.footer_container.set_valign(Gtk.Align.END)
        self.footer_container.set_visible(False)

        self.action_bar_separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.action_bar_separator.add_css_class("action-bar-separator")
        self.footer_container.append(self.action_bar_separator)

        self.action_bar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.action_bar_box.add_css_class("action-footer-bar")
        self.action_bar_box.set_valign(Gtk.Align.CENTER)

        self.action_pills_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.action_pills_box.add_css_class("action-pills-container")
        self.action_pills_box.set_valign(Gtk.Align.CENTER)
        self.action_bar_box.append(self.action_pills_box)

        spacer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        spacer.set_hexpand(True)
        self.action_bar_box.append(spacer)

        self.action_meta_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.action_meta_box.add_css_class("action-meta-container")
        self.action_meta_box.set_valign(Gtk.Align.CENTER)
        self.action_bar_box.append(self.action_meta_box)

        self.footer_container.append(self.action_bar_box)

        # Главный вертикальный контейнер режима поиска (сплит сверху, Action Bar в самом низу)
        self.root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.root_box.set_vexpand(True)
        self.root_box.set_hexpand(True)
        self.root_box.append(self.main_split)
        self.root_box.append(self.footer_container)

        self.pool = []
        POOL_SIZE = 25  # Предварительно выделенный пул строк для быстрого рендеринга
        for i in range(POOL_SIZE):
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            row_box.add_css_class("result-row")

            icon_stack = Gtk.Stack()
            icon_stack.set_valign(Gtk.Align.CENTER)
            icon_stack.set_size_request(48, 48)
            icon_stack.set_margin_end(12)

            icon = Gtk.Image()
            icon.add_css_class("result-icon")
            icon.set_valign(Gtk.Align.CENTER)
            icon_stack.add_named(icon, "icon")

            emoji_badge = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            emoji_badge.add_css_class("result-emoji-badge")
            emoji_badge.set_valign(Gtk.Align.CENTER)
            emoji_badge.set_halign(Gtk.Align.CENTER)

            emoji_label = Gtk.Label()
            emoji_label.add_css_class("result-emoji-label")
            emoji_label.set_valign(Gtk.Align.CENTER)
            emoji_label.set_halign(Gtk.Align.CENTER)
            emoji_badge.append(emoji_label)

            icon_stack.add_named(emoji_badge, "emoji")
            row_box.append(icon_stack)

            text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            text_box.set_valign(Gtk.Align.CENTER)
            text_box.set_hexpand(True)

            title = Gtk.Label()
            title.set_xalign(0)
            title.add_css_class("result-title")
            title.set_ellipsize(Pango.EllipsizeMode.END)
            text_box.append(title)

            desc = Gtk.Label()
            desc.set_xalign(0)
            desc.set_ellipsize(Pango.EllipsizeMode.END)
            desc.add_css_class("result-desc")
            text_box.append(desc)

            row_box.append(text_box)

            alt_badge = Gtk.Label()
            alt_badge.add_css_class("alt-shortcut-badge")
            alt_badge.set_valign(Gtk.Align.CENTER)
            alt_badge.set_halign(Gtk.Align.END)
            alt_badge.set_visible(False)
            row_box.append(alt_badge)

            row = Gtk.ListBoxRow()
            row.set_child(row_box)
            row.set_visible(False)

            self.results_listbox.append(row)

            self.pool.append({
                'row': row,
                'icon': icon,
                'icon_stack': icon_stack,
                'emoji_label': emoji_label,
                'title': title,
                'desc': desc,
                'alt_badge': alt_badge
            })

        return self.root_box

    def render(self, results: list):
        query = self.main_window.entry.get_text().strip()

        limit = self.main_window.config_manager.get("results_limit") if getattr(self.main_window, "config_manager", None) else 20
        self.current_results = results[:limit]
        self._navigated_with_arrows = False

        if not query:
            self.clear_preview_and_resources()
            self.separator.set_visible(False)
            self.empty_state_box.set_visible(False)
            self.scroll.set_visible(False)
            self.results_listbox.set_visible(False)
            if hasattr(self, "footer_container"):
                self.footer_container.set_visible(False)
            self.results_listbox.invalidate_headers()

            for row_data in self.pool:
                row_data['row'].set_visible(False)
                row_data['title']._rendered_markup = None
                row_data['desc']._rendered_markup = None
                if 'alt_badge' in row_data:
                    row_data['alt_badge'].set_visible(False)

            self.preview_container.set_visible(False)
            return

        if not self.current_results:
            # Запрос введен, но ничего не найдено
            self._update_weather_preview_style(None)
            self._current_preview_id = None
            while widget := self.preview_container.get_first_child():
                self.preview_container.remove(widget)
            if hasattr(self, "footer_container"):
                self.footer_container.set_visible(False)
            self._clear_box_children(getattr(self, "action_pills_box", None))
            self._clear_box_children(getattr(self, "action_meta_box", None))
            self.selected_index = -1
            self.results_listbox.select_row(None)

            self.separator.set_visible(True)
            self.empty_state_title.set_label(t("nothing_found_title"))
            self.empty_state_desc.set_label(t("nothing_found_desc"))

            cfg = getattr(self.main_window, "config_manager", None)
            engine_key = cfg.get("web_search_engine", "google") if cfg else "google"
            from providers.web import SEARCH_ENGINES, get_engine_icon

            engine_name = SEARCH_ENGINES.get(engine_key, {}).get("name", "Web") if engine_key != "custom" else t("settings_web_custom_url")
            engine_icon = get_engine_icon(engine_key)
            set_icon_safe(self.empty_web_icon, engine_icon, fallback_icon="applications-internet-symbolic", pixel_size=24)

            truncated_q = (query[:32] + "…") if len(query) > 32 else query
            self.empty_web_sub_lbl.set_label(f"{engine_name}: «{truncated_q}»")
            if query:
                self.empty_terminal_sub_lbl.set_label(f"bash: «{truncated_q}»")
            else:
                self.empty_terminal_sub_lbl.set_label(t("action_open_terminal"))

            if hasattr(self, "footer_container"):
                self.footer_container.set_visible(False)
            self.empty_state_box.set_visible(True)
            self.scroll.set_visible(False)
            self.results_listbox.set_visible(False)
            self.results_listbox.invalidate_headers()

            for row_data in self.pool:
                row_data['row'].result = None
                row_data['row'].set_visible(False)
                if 'alt_badge' in row_data:
                    row_data['alt_badge'].set_visible(False)

            self._update_weather_preview_style(None)
            self._current_preview_id = None
            while widget := self.preview_container.get_first_child():
                self.preview_container.remove(widget)
            self.preview_container.set_visible(False)
            self.main_window.set_default_size(650, 650)
            return

        # Есть результаты поиска
        self.empty_state_box.set_visible(False)
        self.separator.set_visible(True)
        self.scroll.set_visible(True)
        self.results_listbox.set_visible(True)

        cfg = getattr(self.main_window, "config_manager", None)
        show_bar = cfg.get("show_action_bar", True) if cfg else True
        show_alt = cfg.get("show_alt_badges", True) if cfg else True
        if hasattr(self, "footer_container"):
            self.footer_container.set_visible(show_bar)

        highlight_enabled = cfg.get("highlight_matches", True) if cfg else True
        accent_color = get_highlight_accent_color(cfg)
        search_terms = extract_search_terms(query) if (highlight_enabled and query) else []

        for i, row_data in enumerate(self.pool):
            if i < len(self.current_results):
                result = self.current_results[i]
                row_data['row'].result = result

                should_highlight = (
                    highlight_enabled
                    and bool(search_terms)
                    and result.category not in EXCLUDED_HIGHLIGHT_CATEGORIES
                    and not result.id.startswith(("math_", "unit_", "cur_", "tz_"))
                )

                is_emoji = (result.category == "Emoji" or result.provider == "EmojiProvider")
                if is_emoji:
                    emoji_char = (result.preview_data.get("char") if result.preview_data else None) or result.icon or "😀"
                    clean_name = result.preview_data.get("name") if result.preview_data else None
                    if not clean_name:
                        clean_name = result.title.replace(emoji_char, "").strip() if emoji_char in result.title else result.title

                    target_title = clean_name or result.title
                    marked_title = highlight_matches(target_title, search_terms, accent_color) if should_highlight else None
                    _update_label_markup(row_data['title'], target_title, marked_title, should_highlight)

                    if result.subtitle:
                        marked_desc = highlight_matches(result.subtitle, search_terms, accent_color) if should_highlight else None
                        _update_label_markup(row_data['desc'], result.subtitle, marked_desc, should_highlight)
                        row_data['desc'].set_visible(True)
                    else:
                        row_data['desc'].set_visible(False)
                        row_data['desc']._rendered_markup = None

                    if row_data['emoji_label'].get_text() != emoji_char:
                        row_data['emoji_label'].set_label(emoji_char)
                    row_data['icon_stack'].set_visible_child_name("emoji")
                else:
                    marked_title = highlight_matches(result.title, search_terms, accent_color) if should_highlight else None
                    _update_label_markup(row_data['title'], result.title, marked_title, should_highlight)

                    if result.subtitle:
                        marked_desc = highlight_matches(result.subtitle, search_terms, accent_color) if should_highlight else None
                        _update_label_markup(row_data['desc'], result.subtitle, marked_desc, should_highlight)
                        row_data['desc'].set_visible(True)
                    else:
                        row_data['desc'].set_visible(False)
                        row_data['desc']._rendered_markup = None

                    row_data['icon_stack'].set_visible_child_name("icon")

                    # Загружаем иконку только при реальном изменении ключа
                    new_icon_key = result.icon or "default"
                    if getattr(row_data['row'], '_rendered_icon_key', None) != new_icon_key:
                        row_data['row']._rendered_icon_key = new_icon_key
                        icon_widget = row_data['icon']
                        try:
                            if result.icon and os.path.isabs(result.icon):
                                pixbuf = get_scaled_pixbuf_cached(result.icon, 48)
                                if pixbuf:
                                    set_icon_safe(icon_widget, None, raw_pixbuf=pixbuf, pixel_size=48)
                                else:
                                    set_icon_safe(icon_widget, result.icon, fallback_icon="application-x-executable", pixel_size=48)
                            else:
                                set_icon_safe(icon_widget, result.icon, fallback_icon="application-x-executable", pixel_size=48)
                        except Exception as e:
                            logger.debug("Setting result icon failed: %s", e)
                            set_icon_safe(icon_widget, None, fallback_icon="application-x-executable", pixel_size=48)

                if show_alt and i < 9:
                    row_data['alt_badge'].set_label(f"Alt+{i+1}")
                    row_data['alt_badge'].set_visible(True)
                else:
                    row_data['alt_badge'].set_visible(False)
                row_data['row'].set_visible(True)
            else:
                row_data['row'].set_visible(False)
                row_data['row'].result = None
                row_data['row']._rendered_icon_key = None
                row_data['title']._rendered_markup = None
                row_data['desc']._rendered_markup = None
                if 'alt_badge' in row_data:
                    row_data['alt_badge'].set_visible(False)

        self.results_listbox.invalidate_headers()
        if self.current_results:
            self.selected_index = 0
            self.update_selection()
        else:
            self.selected_index = -1
            self.clear_preview_and_resources()

    def _get_category_header_title(self, group_key: str) -> str:
        key_map = {
            "instant": "category_header_instant",
            "apps": "category_header_apps",
            "files": "category_header_files",
            "clipboard": "category_header_clipboard",
            "emoji": "category_header_emoji",
            "web": "category_header_web",
        }
        i18n_key = key_map.get(group_key, "category_header_apps")
        return t(i18n_key)

    def _create_category_header_widget(self, group_key: str, is_first: bool = False) -> Gtk.Box:
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.add_css_class("category-section-header")
        if is_first:
            header_box.add_css_class("first-section")
        header_box._is_category_header = True

        dash = Gtk.Box()
        dash.add_css_class("category-header-dash")
        dash.set_valign(Gtk.Align.CENTER)
        header_box.append(dash)

        title_lbl = Gtk.Label(label=self._get_category_header_title(group_key))
        title_lbl.add_css_class("category-header-title")
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.set_valign(Gtk.Align.CENTER)
        header_box.append(title_lbl)

        line = Gtk.Box()
        line.add_css_class("category-header-line")
        line.set_hexpand(True)
        line.set_valign(Gtk.Align.CENTER)
        header_box.append(line)

        header_box._title_label = title_lbl
        header_box._group_key = group_key
        return header_box

    def _update_category_header_widget(self, header: Gtk.Box, group_key: str, is_first: bool = False):
        if getattr(header, "_group_key", None) != group_key:
            header._group_key = group_key
            if hasattr(header, "_title_label"):
                header._title_label.set_label(self._get_category_header_title(group_key))
        if is_first:
            header.add_css_class("first-section")
        else:
            header.remove_css_class("first-section")

    def _header_func(self, row, before):
        if not getattr(self, "current_results", None):
            row.set_header(None)
            return

        cfg = getattr(self.main_window, "config_manager", None)
        group_enabled = cfg.get("group_results_by_category", True) if cfg else True
        if not group_enabled:
            row.set_header(None)
            return

        res = getattr(row, "result", None)
        if not res or not row.get_visible():
            row.set_header(None)
            return

        current_grp = get_result_category_group(res)

        before_grp = None
        if before and before.get_visible() and getattr(before, "result", None):
            before_grp = get_result_category_group(before.result)

        if current_grp != before_grp:
            header = row.get_header()
            is_first = (before is None)
            if header is None or not getattr(header, "_is_category_header", False):
                header = self._create_category_header_widget(current_grp, is_first=is_first)
                row.set_header(header)
            else:
                self._update_category_header_widget(header, current_grp, is_first=is_first)
        else:
            row.set_header(None)

    def update_selection(self):
        row = self.results_listbox.get_row_at_index(self.selected_index)
        if row:
            self.results_listbox.select_row(row)
            try:
                adj = self.scroll.get_vadjustment()
                if adj:
                    ok, bounds = row.compute_bounds(self.results_listbox)
                    if ok:
                        r_top = bounds.origin.y
                        r_bottom = r_top + bounds.size.height
                        header = row.get_header()
                        if header and header.get_visible():
                            h_ok, h_bounds = header.compute_bounds(self.results_listbox)
                            if h_ok:
                                r_top = min(r_top, h_bounds.origin.y)
                    else:
                        row_h = row.get_height() or 54
                        r_top = self.selected_index * row_h
                        r_bottom = r_top + row_h

                    p_top = adj.get_value()
                    p_bottom = p_top + adj.get_page_size()
                    if r_top < p_top:
                        adj.set_value(r_top)
                    elif r_bottom > p_bottom:
                        adj.set_value(max(0, r_bottom - adj.get_page_size()))
            except Exception as e:
                logger.debug("Adjusting scroll position failed: %s", e)
            if hasattr(row, 'result') and row.result:
                self._update_action_bar(row.result)
                if getattr(self.main_window, 'quick_look', None) and self.main_window.quick_look.is_visible():
                    self.main_window.quick_look.preview_result(row.result)

                preview_enabled = self.main_window.config_manager.get("preview_enabled") if getattr(self.main_window, "config_manager", None) else True

                if preview_enabled:
                    self._update_weather_preview_style(row.result)
                    if getattr(self, "_current_preview_id", None) != row.result.id or not self.preview_container.get_first_child():
                        self._current_preview_id = row.result.id
                        while widget := self.preview_container.get_first_child():
                            self.preview_container.remove(widget)
                        preview_widget = preview_manager.PreviewManager.render(row.result)
                        self.preview_container.append(preview_widget)
                    self.preview_container.set_visible(True)
                    preview_width = self.main_window.config_manager.get("preview_width", 420) if getattr(self.main_window, "config_manager", None) else 420
                    target_w = 650 + preview_width
                    if hasattr(self.main_window, "_clamp_width_to_monitor"):
                        target_w = self.main_window._clamp_width_to_monitor(target_w)
                    self.main_window.set_default_size(target_w, 650)
                else:
                    self._update_weather_preview_style(None)
                    self._current_preview_id = None
                    while widget := self.preview_container.get_first_child():
                        self.preview_container.remove(widget)
                    self.preview_container.set_visible(False)
                    self.main_window.set_default_size(650, 650)
            else:
                self._update_weather_preview_style(None)
                self._current_preview_id = None
                while widget := self.preview_container.get_first_child():
                    self.preview_container.remove(widget)
                self.preview_container.set_visible(False)
                self.main_window.set_default_size(650, 650)
        else:
            self._update_weather_preview_style(None)
            self._current_preview_id = None
            while widget := self.preview_container.get_first_child():
                self.preview_container.remove(widget)
            self.preview_container.set_visible(False)
            self.main_window.set_default_size(650, 650)

    ALL_WEATHER_CLASSES = [
        "preview-panel-weather",
        "weather-bg-clear-day", "weather-bg-clear-dusk", "weather-bg-clear-night",
        "weather-bg-clouds-day", "weather-bg-clouds-night",
        "weather-bg-rain-day", "weather-bg-rain-night",
        "weather-bg-drizzle-day", "weather-bg-drizzle-night",
        "weather-bg-storm-day", "weather-bg-storm-night",
        "weather-bg-snow-day", "weather-bg-snow-night",
        "weather-bg-fog-day", "weather-bg-fog-night",
    ]

    ALL_CANVAS_CLASSES = [
        "weather-canvas-active",
        "weather-canvas-clear-day", "weather-canvas-clear-dusk", "weather-canvas-clear-night",
        "weather-canvas-clouds-day", "weather-canvas-clouds-night",
        "weather-canvas-rain-day", "weather-canvas-rain-night",
        "weather-canvas-drizzle-day", "weather-canvas-drizzle-night",
        "weather-canvas-storm-day", "weather-canvas-storm-night",
        "weather-canvas-snow-day", "weather-canvas-snow-night",
        "weather-canvas-fog-day", "weather-canvas-fog-night",
    ]

    def _update_weather_preview_style(self, result):
        main_box = getattr(self.main_window, "main_box", None) if hasattr(self, "main_window") and self.main_window else None
        outer_box = getattr(self.main_window, "outer_box", None) if hasattr(self, "main_window") and self.main_window else None

        # Clean up any residual weather classes
        for cls in self.ALL_WEATHER_CLASSES:
            if hasattr(self, "preview_container") and self.preview_container:
                self.preview_container.remove_css_class(cls)
            if self.main_window:
                try:
                    self.main_window.remove_css_class(f"ambient-{cls}")
                    self.main_window.remove_css_class(cls)
                    if outer_box:
                        outer_box.remove_css_class(f"ambient-{cls}")
                        outer_box.remove_css_class(cls)
                except Exception:
                    pass

        if main_box:
            for ccls in self.ALL_CANVAS_CLASSES:
                try:
                    main_box.remove_css_class(ccls)
                except Exception:
                    pass
            try:
                main_box.remove_css_class("weather-night-mode")
                main_box.remove_css_class("weather-dusk-mode")
                if hasattr(main_box, "set_weather_atmosphere"):
                    main_box.set_weather_atmosphere(None)
            except Exception:
                pass

    def on_row_activated(self, listbox, row):
        if hasattr(row, 'result') and row.result:
            self._launch_app(row.result)

    def _launch_app(self, result):
        current_query = self.main_window.entry.get_text().strip()
        if hasattr(self.main_window, 'engine'):
            self.main_window.engine.record_launch(result.id, current_query)
        result.execute()
        self.main_window.hide()
        self.main_window.entry.set_text("")

    def on_key_pressed(self, keyval, state, current_results: list) -> bool:
        # Навигация вниз: стрелка вниз, Ctrl+N, Ctrl+J
        is_down = keyval == Gdk.KEY_Down or (
            (state & Gdk.ModifierType.CONTROL_MASK) and keyval in (Gdk.KEY_n, Gdk.KEY_N, Gdk.KEY_j, Gdk.KEY_J)
        )
        if is_down:
            if current_results and self.selected_index < len(current_results) - 1:
                self._navigated_with_arrows = True
                self.selected_index += 1
                self.update_selection()
            return True

        # Навигация вверх: стрелка вверх, Ctrl+P
        is_up = keyval == Gdk.KEY_Up or (
            (state & Gdk.ModifierType.CONTROL_MASK) and keyval in (Gdk.KEY_p, Gdk.KEY_P)
        )
        if is_up:
            if current_results and self.selected_index > 0:
                self._navigated_with_arrows = True
                self.selected_index -= 1
                self.update_selection()
            return True

        # Home / End с зажатым Ctrl
        if (state & Gdk.ModifierType.CONTROL_MASK) and keyval in (Gdk.KEY_Home, Gdk.KEY_KP_Home):
            if current_results:
                self.selected_index = 0
                self.update_selection()
                return True
        elif (state & Gdk.ModifierType.CONTROL_MASK) and keyval in (Gdk.KEY_End, Gdk.KEY_KP_End):
            if current_results:
                self.selected_index = len(current_results) - 1
                self.update_selection()
                return True

        # Мгновенный запуск результата по Alt + 1..9
        if (state & Gdk.ModifierType.ALT_MASK) and not (state & Gdk.ModifierType.CONTROL_MASK):
            alt_digits = {
                Gdk.KEY_1: 0, Gdk.KEY_KP_1: 0,
                Gdk.KEY_2: 1, Gdk.KEY_KP_2: 1,
                Gdk.KEY_3: 2, Gdk.KEY_KP_3: 2,
                Gdk.KEY_4: 3, Gdk.KEY_KP_4: 3,
                Gdk.KEY_5: 4, Gdk.KEY_KP_5: 4,
                Gdk.KEY_6: 5, Gdk.KEY_KP_6: 5,
                Gdk.KEY_7: 6, Gdk.KEY_KP_7: 6,
                Gdk.KEY_8: 7, Gdk.KEY_KP_8: 7,
                Gdk.KEY_9: 8, Gdk.KEY_KP_8: 8,
            }
            if keyval in alt_digits:
                idx = alt_digits[keyval]
                if current_results and 0 <= idx < len(current_results):
                    self.selected_index = idx
                    self.update_selection()
                    self._launch_app(current_results[idx])
                    return True

        # Удаление выбранного элемента (буфер обмена / история) по Shift+Delete
        if (state & Gdk.ModifierType.SHIFT_MASK) and keyval in (Gdk.KEY_Delete, Gdk.KEY_KP_Delete):
            if current_results and 0 <= self.selected_index < len(current_results):
                result = current_results[self.selected_index]
                if getattr(result, '_action_delete', None):
                    self._on_action_delete()
                    return True

        # Быстрое переключение подсказок хоткеев (Action Bar) по Ctrl + / или Ctrl + ?
        if (state & Gdk.ModifierType.CONTROL_MASK) and keyval in (Gdk.KEY_slash, Gdk.KEY_question):
            cfg = getattr(self.main_window, "config_manager", None)
            if cfg:
                new_state = not cfg.get("show_action_bar", True)
                cfg.set("show_action_bar", new_state)
                self.main_window.reload_config()
                return True

        # Переключение Quick Look через Ctrl+Y
        if (keyval in (Gdk.KEY_y, Gdk.KEY_Y)) and (state & Gdk.ModifierType.CONTROL_MASK):
            if getattr(self.main_window, 'quick_look', None):
                if self.main_window.quick_look.is_visible():
                    self.main_window.quick_look.hide_preview()
                    return True
                elif current_results and 0 <= self.selected_index < len(current_results):
                    if self.main_window.quick_look.preview_result(current_results[self.selected_index]):
                        return True

        # Копирование пути/значения через Alt+C или Ctrl+Shift+C
        if (keyval in (Gdk.KEY_c, Gdk.KEY_C)) and (
            (state & Gdk.ModifierType.ALT_MASK) or
            ((state & Gdk.ModifierType.CONTROL_MASK) and (state & Gdk.ModifierType.SHIFT_MASK))
        ):
            if current_results and self.selected_index >= 0:
                result = current_results[self.selected_index]
                result.copy_value()
                self.main_window.hide()
                self.main_window.entry.set_text("")
                return True

        elif keyval in (Gdk.KEY_Page_Down, Gdk.KEY_Page_Up):
            if hasattr(self, "preview_container") and self.preview_container.is_visible():
                if child := self.preview_container.get_first_child():
                    sw = child.get_first_child()
                    if isinstance(sw, Gtk.ScrolledWindow):
                        adj = sw.get_vadjustment()
                        if adj:
                            step = 180.0 if keyval == Gdk.KEY_Page_Down else -180.0
                            new_val = max(adj.get_lower(), min(adj.get_upper() - adj.get_page_size(), adj.get_value() + step))
                            adj.set_value(new_val)
                            return True

        elif matches_shortcut(keyval, state, getattr(self.main_window, "config_manager", None).get("quick_look_shortcut", "space") if getattr(self.main_window, "config_manager", None) else "space"):
            if getattr(self.main_window, 'quick_look', None) and self.main_window.quick_look.is_visible():
                self.main_window.quick_look.hide_preview()
                return True
            ql_sc = getattr(self.main_window, "config_manager", None).get("quick_look_shortcut", "space") if getattr(self.main_window, "config_manager", None) else "space"
            if ql_sc != "space" or self._navigated_with_arrows or (state & Gdk.ModifierType.SHIFT_MASK):
                if current_results and 0 <= self.selected_index < len(current_results):
                    result = current_results[self.selected_index]
                    if getattr(self.main_window, 'quick_look', None):
                        if self.main_window.quick_look.preview_result(result):
                            return True
            return False

        elif keyval == Gdk.KEY_Escape:
            def find_stack(w):
                if isinstance(w, Gtk.Stack):
                    return w
                child = w.get_first_child()
                while child:
                    res = find_stack(child)
                    if res:
                        return res
                    child = child.get_next_sibling()
                return None
            st = find_stack(self.preview_container)
            if st and st.get_visible_child_name() == "detail":
                st.set_visible_child_name("overview")
                return True

        elif keyval in (Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab):
            if current_results and 0 <= self.selected_index < len(current_results):
                result = current_results[self.selected_index]
                if result.category == "Weather":
                    from preview_manager import launch_echo_weather
                    city_name = ""
                    if result.preview_data and isinstance(result.preview_data, dict):
                        city_name = result.preview_data.get("city_name", "")
                    if launch_echo_weather(city_name):
                        self.main_window.hide()
                        self.main_window.entry.set_text("")
                    return True

        elif keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            if state & Gdk.ModifierType.CONTROL_MASK:
                self._execute_terminal_search()
                return True
            elif current_results and self.selected_index >= 0:
                result = current_results[self.selected_index]
                if (state & Gdk.ModifierType.SHIFT_MASK) or (state & Gdk.ModifierType.ALT_MASK):
                    result.open_location()
                    self.main_window.hide()
                    self.main_window.entry.set_text("")
                else:
                    self._launch_app(result)
                return True
            elif not current_results and self.empty_state_box.get_visible():
                self._execute_web_search()
                return True
            return False

        elif (keyval == Gdk.KEY_c or keyval == Gdk.KEY_C) and (state & Gdk.ModifierType.CONTROL_MASK):
            if self.main_window and hasattr(self.main_window, 'entry') and self.main_window.entry.get_selection_bounds():
                return False

            if current_results and self.selected_index >= 0:
                result = current_results[self.selected_index]
                result.copy_value()
                self.main_window.hide()
                self.main_window.entry.set_text("")
                return True

        elif keyval == Gdk.KEY_Tab:
            if current_results and self.selected_index >= 0:
                result = current_results[self.selected_index]
                if not result.id.startswith("math_") and not result.id.startswith("unit_"):
                    self.main_window.entry.set_text(result.title)
                    self.main_window.entry.set_position(-1)
            return True

        return False

    def on_activated(self):
        pass

    def on_deactivated(self):
        self.clear_preview_and_resources()

    def clear_preview_and_resources(self):
        try:
            self._update_weather_preview_style(None)
            self._current_preview_id = None
            while widget := self.preview_container.get_first_child():
                self.preview_container.remove(widget)
            if hasattr(self, "footer_container"):
                self.footer_container.set_visible(False)
            self._clear_box_children(getattr(self, "action_pills_box", None))
            self._clear_box_children(getattr(self, "action_meta_box", None))
            self.current_results = []
            for row_data in self.pool:
                row_data["row"].result = None
                row_data["row"]._rendered_icon_key = None
                row_data["row"].set_visible(False)
                if 'alt_badge' in row_data:
                    row_data['alt_badge'].set_visible(False)
            if hasattr(self, "results_listbox"):
                self.results_listbox.invalidate_headers()
        except Exception as e:
            logger.debug("Error in clear_preview_and_resources: %s", e)

    def _create_empty_action_card(self, icon_name: str, title: str, badge_text: str, on_click):
        btn = Gtk.Button()
        btn.add_css_class("empty-action-card")
        btn.set_cursor(Gdk.Cursor.new_from_name("pointer", None))
        btn.connect("clicked", on_click)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        hbox.set_valign(Gtk.Align.CENTER)

        icon = Gtk.Image()
        set_icon_safe(icon, icon_name, fallback_icon="applications-internet-symbolic", pixel_size=24)
        icon.add_css_class("empty-action-icon")
        hbox.append(icon)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        text_box.set_hexpand(True)
        text_box.set_valign(Gtk.Align.CENTER)

        title_lbl = Gtk.Label(label=title)
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.add_css_class("empty-action-title")
        text_box.append(title_lbl)

        sub_lbl = Gtk.Label(label="")
        sub_lbl.set_halign(Gtk.Align.START)
        sub_lbl.add_css_class("empty-action-sub")
        text_box.append(sub_lbl)

        hbox.append(text_box)

        badge_lbl = Gtk.Label(label=badge_text)
        badge_lbl.set_valign(Gtk.Align.CENTER)
        badge_lbl.add_css_class("empty-action-badge")
        hbox.append(badge_lbl)

        btn.set_child(hbox)
        return btn, sub_lbl, icon

    def _execute_web_search(self):
        query = self.main_window.entry.get_text().strip() if self.main_window and hasattr(self.main_window, 'entry') else ""
        if not query:
            return

        cfg = getattr(self.main_window, "config_manager", None)
        engine_key = cfg.get("web_search_engine", "google") if cfg else "google"
        custom_url = cfg.get("web_search_custom_url", "") if cfg else ""

        from providers.web import build_search_url, open_url_in_browser
        url = build_search_url(query, engine_key=engine_key, custom_url=custom_url)
        open_url_in_browser(url)

        self.main_window.hide()
        self.main_window.entry.set_text("")

    def _execute_terminal_search(self):
        query = self.main_window.entry.get_text().strip() if self.main_window and hasattr(self.main_window, 'entry') else ""
        clean_cmd = query.lstrip("> :").strip() if query.startswith((">", ":")) else query

        from providers.web import open_in_terminal
        open_in_terminal(clean_cmd)

        self.main_window.hide()
        self.main_window.entry.set_text("")

    def on_row_selected(self, listbox, row):
        if row and hasattr(row, 'result') and row.result:
            idx = row.get_index()
            if 0 <= idx < len(self.current_results) and idx != self.selected_index:
                self.selected_index = idx
                self.update_selection()

    def _clear_box_children(self, box):
        if not box:
            return
        while child := box.get_first_child():
            box.remove(child)

    def _create_action_pill(self, key_text: str, label_text: str, on_click=None):
        if on_click:
            btn = Gtk.Button()
            btn.add_css_class("action-pill-btn")
            btn.set_cursor(Gdk.Cursor.new_from_name("pointer", None))
            btn.set_focus_on_click(False)
            btn.connect("clicked", lambda b: on_click())

            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            hbox.set_valign(Gtk.Align.CENTER)

            kbd = Gtk.Label(label=key_text)
            kbd.add_css_class("kbd-badge")
            kbd.set_valign(Gtk.Align.CENTER)
            hbox.append(kbd)

            lbl = Gtk.Label(label=label_text)
            lbl.add_css_class("action-pill-text")
            lbl.set_valign(Gtk.Align.CENTER)
            hbox.append(lbl)

            btn.set_child(hbox)
            return btn
        else:
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            hbox.add_css_class("action-pill-btn")
            hbox.set_valign(Gtk.Align.CENTER)

            kbd = Gtk.Label(label=key_text)
            kbd.add_css_class("kbd-badge")
            kbd.set_valign(Gtk.Align.CENTER)
            hbox.append(kbd)

            lbl = Gtk.Label(label=label_text)
            lbl.add_css_class("action-pill-text")
            lbl.set_valign(Gtk.Align.CENTER)
            hbox.append(lbl)

            return hbox

    def _update_action_bar(self, result):
        cfg = getattr(self.main_window, "config_manager", None)
        show_bar = cfg.get("show_action_bar", True) if cfg else True
        if not show_bar:
            if hasattr(self, "footer_container"):
                self.footer_container.set_visible(False)
            return

        if hasattr(self, "footer_container"):
            self.footer_container.set_visible(True)

        self._clear_box_children(self.action_pills_box)
        self._clear_box_children(self.action_meta_box)

        if not result:
            return

        # 1. Основное действие (↵ Enter)
        primary_label = t("action_launch")
        if result.category in ("Math", "Units", "Currency", "Time", "Weather", "Emoji"):
            primary_label = t("action_copy")
        elif result.category == "Files" or getattr(result, "provider", None) == "FilesProvider":
            primary_label = t("action_open")
        elif getattr(result, "provider", None) == "ClipboardProvider":
            primary_label = t("action_copy")
        elif getattr(result, "category", None) == "Web":
            primary_label = t("action_open")

        self.action_pills_box.append(
            self._create_action_pill("↵", primary_label, lambda: self._on_action_primary())
        )

        # 2. Открыть папку / расположение (⇧↵ Shift+Enter)
        has_location = bool(getattr(result, "_action_open_location", None))
        if not has_location and (result.category == "Files" or "path" in (result.preview_data or {})):
            has_location = True
        if has_location:
            self.action_pills_box.append(
                self._create_action_pill("⇧↵", t("action_open_location"), lambda: self._on_action_reveal())
            )

        # 3. Скопировать путь/значение (Alt+C)
        has_copy = bool(getattr(result, "_action_copy", None))
        if not has_copy and ("path" in (result.preview_data or {}) or getattr(result, "subtitle", None)):
            has_copy = True
        if has_copy and primary_label != t("action_copy"):
            copy_label = t("action_copy_path") if (result.category == "Files" or "path" in (result.preview_data or {})) else t("action_copy")
            self.action_pills_box.append(
                self._create_action_pill("Alt+C", copy_label, lambda: self._on_action_copy())
            )

        # 4. Просмотр Quick Look (Space)
        if getattr(self.main_window, "quick_look", None):
            path = None
            if result.preview_data and isinstance(result.preview_data, dict):
                path = result.preview_data.get("path")
            if not path and getattr(result, "id", None) and os.path.exists(result.id):
                path = result.id
            if path and os.path.exists(path):
                ql_sc = cfg.get("quick_look_shortcut", "space") if cfg else "space"
                ql_badge = "Ctrl+Y" if ql_sc in ("ctrl_y", "ctrl+y") else "Space"
                self.action_pills_box.append(
                    self._create_action_pill(ql_badge, t("action_quick_look"), lambda: self._on_action_quicklook())
                )

        # 4b. Погода: подробнее в приложении (Клик / Tab)
        if result.category == "Weather":
            def _open_weather():
                from preview_manager import launch_echo_weather
                city_name = ""
                if result.preview_data and isinstance(result.preview_data, dict):
                    city_name = result.preview_data.get("city_name", "")
                if launch_echo_weather(city_name):
                    self.main_window.hide()
                    self.main_window.entry.set_text("")
            self.action_pills_box.append(
                self._create_action_pill("Tab", "Echo Weather ↗", _open_weather)
            )

        # 5. Удалить (Shift+Delete) - например для истории буфера обмена
        if getattr(result, "_action_delete", None):
            self.action_pills_box.append(
                self._create_action_pill("⇧Del", t("action_delete_item"), lambda: self._on_action_delete())
            )

        # 6. Правая часть - Быстрый выбор Alt+1..9 (если результатов >= 2)
        if len(self.current_results) >= 2:
            max_idx = min(9, len(self.current_results))
            badge_key = f"Alt+1..{max_idx}" if max_idx > 1 else "Alt+1"
            self.action_meta_box.append(
                self._create_action_pill(badge_key, t("action_quick_jump"), None)
            )

    def _on_action_primary(self):
        if self.current_results and 0 <= self.selected_index < len(self.current_results):
            result = self.current_results[self.selected_index]
            self._launch_app(result)

    def _on_action_reveal(self):
        if self.current_results and 0 <= self.selected_index < len(self.current_results):
            result = self.current_results[self.selected_index]
            try:
                result.open_location()
            except Exception as e:
                logger.warning("Failed to reveal item location: %s", e)
            self.main_window.hide()
            self.main_window.entry.set_text("")

    def _on_action_copy(self):
        if self.current_results and 0 <= self.selected_index < len(self.current_results):
            result = self.current_results[self.selected_index]
            try:
                result.copy_value()
            except Exception as e:
                logger.warning("Failed to copy item value: %s", e)
            self.main_window.hide()
            self.main_window.entry.set_text("")

    def _on_action_quicklook(self):
        if self.current_results and 0 <= self.selected_index < len(self.current_results):
            result = self.current_results[self.selected_index]
            if getattr(self.main_window, "quick_look", None):
                try:
                    if self.main_window.quick_look.is_visible():
                        self.main_window.quick_look.hide_preview()
                    else:
                        self.main_window.quick_look.preview_result(result)
                except Exception as e:
                    logger.warning("QuickLook preview toggle failed: %s", e)

    def _on_action_delete(self):
        if self.current_results and 0 <= self.selected_index < len(self.current_results):
            result = self.current_results[self.selected_index]
            try:
                if getattr(result, "_action_delete", None):
                    result.delete()
                    new_results = list(self.current_results)
                    del new_results[self.selected_index]
                    self.selected_index = min(self.selected_index, max(0, len(new_results) - 1))
                    self.render(new_results)
            except Exception as e:
                logger.warning("Failed to delete item: %s", e)

    def on_config_reloaded(self):
        cfg = getattr(self.main_window, "config_manager", None)
        show_bar = cfg.get("show_action_bar", True) if cfg else True
        show_alt = cfg.get("show_alt_badges", True) if cfg else True

        if hasattr(self, "footer_container"):
            if not self.current_results:
                self.footer_container.set_visible(False)
            else:
                self.footer_container.set_visible(show_bar)

        for i, row_data in enumerate(self.pool):
            if "alt_badge" in row_data:
                if show_alt and self.current_results and i < min(9, len(self.current_results)):
                    row_data["alt_badge"].set_label(f"Alt+{i+1}")
                    row_data["alt_badge"].set_visible(True)
                else:
                    row_data["alt_badge"].set_visible(False)

        if self.current_results and 0 <= self.selected_index < len(self.current_results):
            self._update_action_bar(self.current_results[self.selected_index])
