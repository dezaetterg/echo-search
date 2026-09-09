import os
import functools
from gi.repository import GdkPixbuf

try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import GLib, Gtk, Gdk, Pango
except ValueError:
    pass

from .base import BaseMode
import preview_manager
from utils import set_icon_safe, matches_shortcut
from i18n import t


@functools.lru_cache(maxsize=512)
def get_scaled_pixbuf_cached(icon_path: str, size: int = 48):
    try:
        if os.path.exists(icon_path):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_path)
            w, h = pixbuf.get_width(), pixbuf.get_height()
            s = min(w, h)
            cropped = pixbuf.new_subpixbuf((w - s) // 2, (h - s) // 2, s, s)
            return cropped.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
    except Exception:
        pass
    return None

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
        self.left_box.set_size_request(650, 0)
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
        
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_propagate_natural_height(True)
        self.scroll.set_max_content_height(480)
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
        
        self.left_box.append(self.empty_state_box)
        self.main_split.append(self.left_box)
        
        # Превью панель (Новая версия)
        self.preview_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.preview_container.add_css_class("preview-panel")
        self.preview_container.set_vexpand(True)
        preview_width = self.main_window.config_manager.get("preview_width") if getattr(self.main_window, "config_manager", None) else 420
        self.preview_container.set_size_request(preview_width, 440)
        self.main_split.append(self.preview_container)
        
        self.pool = []
        for i in range(25): # На случай если limit увеличат
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
                'desc': desc
            })
            
        return self.main_split

    def render(self, results: list):
        query = self.main_window.entry.get_text().strip()
        
        limit = self.main_window.config_manager.get("results_limit") if getattr(self.main_window, "config_manager", None) else 20
        self.current_results = results[:limit]
        self._navigated_with_arrows = False
        
        if not query:
            self.current_results = []
            self.separator.set_visible(False)
            self.empty_state_box.set_visible(False)
            self.scroll.set_visible(False)
            self.results_listbox.set_visible(False)
            
            for row_data in self.pool:
                row_data['row'].set_visible(False)
                
            self.preview_container.set_visible(False)
            return

        if not self.current_results:
            # Запрос введен, но ничего не найдено
            self.separator.set_visible(True)
            self.empty_state_title.set_label(t("nothing_found_title"))
            self.empty_state_desc.set_label(t("nothing_found_desc"))
            self.empty_state_box.set_visible(True)
            self.scroll.set_visible(False)
            self.results_listbox.set_visible(False)
            
            for row_data in self.pool:
                row_data['row'].set_visible(False)
                
            self.preview_container.set_visible(False)
            self.main_window.set_default_size(650, 560)
            return
            
        # Есть результаты поиска
        self.empty_state_box.set_visible(False)
        self.separator.set_visible(True)
        self.scroll.set_visible(True)
        self.results_listbox.set_visible(True)
            
        for i, row_data in enumerate(self.pool):
            if i < len(self.current_results):
                result = self.current_results[i]
                row_data['row'].result = result
                
                is_emoji = (result.category == "Emoji" or result.provider == "EmojiProvider")
                if is_emoji:
                    emoji_char = (result.preview_data.get("char") if result.preview_data else None) or result.icon or "😀"
                    clean_name = result.preview_data.get("name") if result.preview_data else None
                    if not clean_name:
                        clean_name = result.title.replace(emoji_char, "").strip() if emoji_char in result.title else result.title
                    
                    target_title = clean_name or result.title
                    if row_data['title'].get_text() != target_title:
                        row_data['title'].set_label(target_title)
                    if result.subtitle:
                        if row_data['desc'].get_text() != result.subtitle:
                            row_data['desc'].set_label(result.subtitle)
                        row_data['desc'].set_visible(True)
                    else:
                        row_data['desc'].set_visible(False)
                    
                    if row_data['emoji_label'].get_text() != emoji_char:
                        row_data['emoji_label'].set_label(emoji_char)
                    row_data['icon_stack'].set_visible_child_name("emoji")
                else:
                    if row_data['title'].get_text() != result.title:
                        row_data['title'].set_label(result.title)
                    if result.subtitle:
                        if row_data['desc'].get_text() != result.subtitle:
                            row_data['desc'].set_label(result.subtitle)
                        row_data['desc'].set_visible(True)
                    else:
                        row_data['desc'].set_visible(False)
                        
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
                        except Exception:
                            set_icon_safe(icon_widget, None, fallback_icon="application-x-executable", pixel_size=48)
                    
                row_data['row'].set_visible(True)
            else:
                row_data['row'].set_visible(False)
                row_data['row'].result = None
                row_data['row']._rendered_icon_key = None
            
        if self.current_results:
            self.selected_index = 0
            self.update_selection()
        else:
            self.selected_index = -1
            self.clear_preview_and_resources()

    def update_selection(self):
        row = self.results_listbox.get_row_at_index(self.selected_index)
        if row:
            self.results_listbox.select_row(row)
            try:
                adj = self.scroll.get_vadjustment()
                if adj:
                    row_h = row.get_height() or 54
                    r_top = self.selected_index * row_h
                    r_bottom = r_top + row_h
                    p_top = adj.get_value()
                    p_bottom = p_top + adj.get_page_size()
                    if r_top < p_top:
                        adj.set_value(r_top)
                    elif r_bottom > p_bottom:
                        adj.set_value(max(0, r_bottom - adj.get_page_size()))
            except Exception:
                pass
            if hasattr(row, 'result') and row.result:
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
                    preview_width = self.main_window.config_manager.get("preview_width") if getattr(self.main_window, "config_manager", None) else 420
                    target_w = 650 + preview_width
                    if hasattr(self.main_window, "_clamp_width_to_monitor"):
                        target_w = self.main_window._clamp_width_to_monitor(target_w)
                    self.main_window.set_default_size(target_w, 560)
                else:
                    self._update_weather_preview_style(None)
                    self._current_preview_id = None
                    while widget := self.preview_container.get_first_child():
                        self.preview_container.remove(widget)
                    self.preview_container.set_visible(False)
                    self.main_window.set_default_size(650, 560)

    ALL_WEATHER_CLASSES = [
        "preview-panel-weather",
        "weather-bg-clear-day", "weather-bg-clear-night",
        "weather-bg-clouds-day", "weather-bg-clouds-night",
        "weather-bg-rain-day", "weather-bg-rain-night",
        "weather-bg-storm-day", "weather-bg-storm-night",
        "weather-bg-snow-day", "weather-bg-snow-night",
        "weather-bg-fog-day", "weather-bg-fog-night",
    ]

    ALL_CANVAS_CLASSES = [
        "weather-canvas-active",
        "weather-canvas-clear-day", "weather-canvas-clear-night",
        "weather-canvas-clouds-day", "weather-canvas-clouds-night",
        "weather-canvas-rain-day", "weather-canvas-rain-night",
        "weather-canvas-storm-day", "weather-canvas-storm-night",
        "weather-canvas-snow-day", "weather-canvas-snow-night",
        "weather-canvas-fog-day", "weather-canvas-fog-night",
    ]

    def _update_weather_preview_style(self, result):
        main_box = getattr(self.main_window, "main_box", None) if hasattr(self, "main_window") and self.main_window else None
        outer_box = getattr(self.main_window, "outer_box", None) if hasattr(self, "main_window") and self.main_window else None
        
        for cls in self.ALL_WEATHER_CLASSES:
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
            
        if result and getattr(result, "category", None) == "Weather":
            self.preview_container.add_css_class("preview-panel-weather")
            bg_class = (result.preview_data or {}).get("bg_class", "weather-bg-clear-day")
            cond = bg_class.replace("weather-bg-", "")
            self.preview_container.add_css_class(bg_class)
            
            if self.main_window:
                try:
                    self.main_window.add_css_class(f"ambient-{bg_class}")
                    if outer_box:
                        outer_box.add_css_class(f"ambient-{bg_class}")
                    if main_box:
                        main_box.add_css_class("weather-canvas-active")
                        main_box.add_css_class(f"weather-canvas-{cond}")
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
        if keyval == Gdk.KEY_Down:
            if current_results and self.selected_index < len(current_results) - 1:
                self._navigated_with_arrows = True
                self.selected_index += 1
                self.update_selection()
            return True
            
        elif keyval == Gdk.KEY_Up:
            if current_results and self.selected_index > 0:
                self._navigated_with_arrows = True
                self.selected_index -= 1
                self.update_selection()
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
            
        elif keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            if current_results and self.selected_index >= 0:
                result = current_results[self.selected_index]
                if state & Gdk.ModifierType.SHIFT_MASK:
                    result.open_location()
                    self.main_window.hide()
                    self.main_window.entry.set_text("")
                elif state & Gdk.ModifierType.ALT_MASK:
                    # Функционал свойств пока не реализован. Отключаем действие, чтобы избежать AttributeError.
                    pass
                else:
                    self._launch_app(result)
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
            self.current_results = []
            for row_data in self.pool:
                row_data["row"].result = None
                row_data["row"]._rendered_icon_key = None
                row_data["row"].set_visible(False)
        except Exception:
            pass
