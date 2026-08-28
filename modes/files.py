import os
import urllib.parse
import collections
try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk, Pango, GLib
except ValueError:
    pass

try:
    gi.require_version('GnomeDesktop', '4.0')
    from gi.repository import GnomeDesktop
    thumbnail_factory = GnomeDesktop.DesktopThumbnailFactory()
except (ValueError, ImportError):
    thumbnail_factory = None

from .base import BaseMode
from utils import set_icon_safe
from i18n import t

class FilesMode(BaseMode):
    category_filter = "Files"
    
    def __init__(self, main_window):
        self.current_query = ""
        self.active_category = "All"
        self._THUMBNAIL_CACHE = collections.OrderedDict()
        self._CACHE_LIMIT = 100
        super().__init__(main_window)
        
        self.CAT_MAPPING = {
            "All": None,
            "Documents": ["pdf", "text", "document", "vnd.ms-", "vnd.oasis.opendocument", "rtf", "pages"],
            "Images": ["image/"],
            "Videos": ["video/"],
            "Audio": ["audio/"],
            "PDF": ["pdf"],
            "Folders": ["inode/directory"],
            "Archives": ["zip", "rar", "tar", "gzip", "7z", "x-bzip", "x-xz"]
        }
        
        self.suggestions_flowbox.set_filter_func(self._filter_func)
        self.recents_flowbox.set_filter_func(self._filter_func)
        
    def _create_widget(self) -> Gtk.Widget:

        
        # Левая часть (Списки файлов)
        self.left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.left_box.set_hexpand(True)
        
        # --- HEADER (Filters) ---
        self.filters_scroll = Gtk.ScrolledWindow()
        self.filters_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        self.filters_scroll.set_margin_start(16)
        self.filters_scroll.set_margin_end(16)
        self.filters_scroll.set_margin_bottom(12)
        self.filters_scroll.add_css_class("apps-filters-scroll")
        
        hscrollbar = self.filters_scroll.get_hscrollbar()
        if hscrollbar:
            hscrollbar.set_visible(False)
            
        self.filters_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.filters_box.set_spacing(8)
        
        self.filter_buttons = {}
        categories = ["All", "Documents", "Images", "Videos", "Audio", "PDF", "Folders", "Archives"]
        for cat in categories:
            label_text = t(f"cat_{cat.lower()}")
            btn = Gtk.Button(label=label_text)
            btn.add_css_class("apps-filter-pill")
            if cat == "All":
                btn.add_css_class("active")
            btn.connect("clicked", self.on_category_clicked, cat)
            self.filters_box.append(btn)
            self.filter_buttons[cat] = btn
            
        self.filters_scroll.set_child(self.filters_box)
        self.left_box.append(self.filters_scroll)
        
        # --- SEPARATOR ---
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.add_css_class("apps-separator")
        self.left_box.append(separator)
        
        # --- SCROLLABLE CONTENT ---
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_min_content_height(420)
        self.scroll.set_max_content_height(420)
        
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.content_box.set_spacing(12)
        
        # Suggestions Section
        self.suggestions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.suggestions_box.set_spacing(8)
        
        self.suggestions_label = Gtk.Label(label=t("section_suggestions"))
        self.suggestions_label.add_css_class("files-section-title")
        self.suggestions_label.set_halign(Gtk.Align.START)
        self.suggestions_label.set_margin_start(16)
        self.suggestions_box.append(self.suggestions_label)
        
        self.suggestions_flowbox = Gtk.FlowBox()
        self.suggestions_flowbox.set_valign(Gtk.Align.START)
        self.suggestions_flowbox.set_halign(Gtk.Align.START)
        self.suggestions_flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.suggestions_flowbox.set_max_children_per_line(5)
        self.suggestions_flowbox.set_column_spacing(12)
        self.suggestions_flowbox.set_row_spacing(12)
        self.suggestions_flowbox.set_activate_on_single_click(False)
        self.suggestions_flowbox.connect("child-activated", self.on_child_activated)
        self.suggestions_flowbox.connect("selected-children-changed", self.on_selection_changed)
        self.suggestions_box.append(self.suggestions_flowbox)
        
        self.content_box.append(self.suggestions_box)
        
        # Recents Section
        self.recents_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.recents_box.set_spacing(8)
        
        self.recents_label = Gtk.Label(label=t("section_recent"))
        self.recents_label.add_css_class("files-section-title")
        self.recents_label.set_halign(Gtk.Align.START)
        self.recents_label.set_margin_start(16)
        self.recents_box.append(self.recents_label)
        
        self.recents_flowbox = Gtk.FlowBox()
        self.recents_flowbox.set_valign(Gtk.Align.START)
        self.recents_flowbox.set_halign(Gtk.Align.START)
        self.recents_flowbox.set_max_children_per_line(10)
        self.recents_flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.recents_flowbox.set_column_spacing(12)
        self.recents_flowbox.set_row_spacing(12)
        self.recents_flowbox.set_margin_start(16)
        self.recents_flowbox.set_margin_end(16)
        self.recents_flowbox.set_margin_bottom(16)
        self.recents_flowbox.set_activate_on_single_click(False)
        self.recents_flowbox.connect("child-activated", self.on_child_activated)
        self.recents_flowbox.connect("selected-children-changed", self.on_selection_changed)
        self.recents_box.append(self.recents_flowbox)
        
        self.content_box.append(self.recents_box)
        
        self.scroll.set_child(self.content_box)
        self.glass_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.glass_container.add_css_class("apps-glass-container")
        self.glass_container.append(self.scroll)
        
        self.left_box.append(self.glass_container)
        
        self.populated = False
        return self.left_box

    def _preload_files(self):
        if not self.populated and hasattr(self.main_window, "engine"):
            file_provider = next((p for p in self.main_window.engine.providers if type(p).__name__ == "FileProvider"), None)
            if file_provider and hasattr(file_provider, "get_recent_files"):
                results = file_provider.get_recent_files()
                self._populate(results)
                self.populated = True
        return False

    def _create_card(self, result):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.add_css_class("finder-card")
        card.set_halign(Gtk.Align.CENTER)
        card.set_valign(Gtk.Align.START)
        card.set_size_request(130, 160)
        
        icon = Gtk.Image()
        icon.set_pixel_size(120)
        icon.set_margin_bottom(8)
        icon.set_valign(Gtk.Align.CENTER)
        icon.add_css_class("finder-icon")
        
        path = result.preview_data.get("path", "")
        try:
            uri = GLib.filename_to_uri(path)
        except GLib.Error:
            uri = f"file://{urllib.parse.quote(path)}"
        
        # Проверка кэша для мгновенной загрузки
        if uri in self._THUMBNAIL_CACHE:
            set_icon_safe(icon, None, raw_pixbuf=self._THUMBNAIL_CACHE[uri], is_paintable=True)
            icon.add_css_class("loaded") # Мгновенно показываем без анимации
            self._THUMBNAIL_CACHE.move_to_end(uri)
        else:
            # Placeholder (opacity 0.5 через CSS)
            set_icon_safe(icon, "text-x-generic", fallback_icon="application-x-executable")
            
            import threading
            from gi.repository import GdkPixbuf
            
            def _load_icon():
                try:
                    pixbuf = None
                    mime_type = result.preview_data.get("mime", "unknown")
                    
                    if thumbnail_factory and os.path.exists(path) and "unknown" not in mime_type:
                        mtime = int(os.path.getmtime(path))
                        
                        try:
                            if not thumbnail_factory.has_valid_failed_thumbnail(uri, mtime):
                                thumb_path = thumbnail_factory.lookup(uri, mtime)
                                if thumb_path:
                                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(thumb_path, 96, 96, True)
                                else:
                                    if thumbnail_factory.can_thumbnail(uri, mime_type, mtime):
                                        pixbuf = thumbnail_factory.generate_thumbnail(uri, mime_type)
                                        if pixbuf:
                                            thumbnail_factory.save_thumbnail(pixbuf, uri, mtime)
                                            pixbuf = pixbuf.scale_simple(96, 96, GdkPixbuf.InterpType.BILINEAR)
                        except Exception:
                            pass

                    # Fallback
                    if not pixbuf and result.icon and os.path.exists(result.icon) and os.path.isabs(result.icon):
                        try:
                            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(result.icon, 96, 96, True)
                        except Exception: pass

                    def _set():
                        if pixbuf:
                            self._THUMBNAIL_CACHE[uri] = pixbuf
                            if len(self._THUMBNAIL_CACHE) > self._CACHE_LIMIT:
                                self._THUMBNAIL_CACHE.popitem(last=False)
                            set_icon_safe(icon, None, raw_pixbuf=pixbuf, is_paintable=True)
                            icon.add_css_class("loaded") # Fade-in effect
                        else:
                            set_icon_safe(icon, result.icon, fallback_icon="application-x-executable", pixel_size=96)
                    GLib.idle_add(_set)
                except Exception as e:
                    print(f"Thumbnail error: {e}")
                    GLib.idle_add(lambda: set_icon_safe(icon, "application-x-executable", fallback_icon="application-x-executable", pixel_size=96))
                    
            threading.Thread(target=_load_icon, daemon=True).start()
            
        card.append(icon)
        
        title = Gtk.Label(label=result.title)
        title.set_wrap(True)
        title.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        title.set_lines(2)
        title.set_ellipsize(Pango.EllipsizeMode.END)
        title.set_justify(Gtk.Justification.CENTER)
        title.set_max_width_chars(12)
        title.add_css_class("finder-title")
        card.append(title)
        
        return card

    def _populate(self, results: list):
        child = self.suggestions_flowbox.get_first_child()
        while child:
            self.suggestions_flowbox.remove(child)
            child = self.suggestions_flowbox.get_first_child()
            
        child = self.recents_flowbox.get_first_child()
        while child:
            self.recents_flowbox.remove(child)
            child = self.recents_flowbox.get_first_child()
            
        suggestions = results[:5]
        recents = results[5:30]
        
        for result in suggestions:
            card = self._create_card(result)
            child = Gtk.FlowBoxChild()
            child.set_child(card)
            child.result = result
            child.add_css_class("app-card-container")
            self.suggestions_flowbox.append(child)
            
        for result in recents:
            card = self._create_card(result)
            child = Gtk.FlowBoxChild()
            child.set_child(card)
            child.result = result
            child.add_css_class("app-card-container")
            self.recents_flowbox.append(child)
            
        self.populated = True

    def on_child_activated(self, flowbox, child):
        if getattr(child.result, 'execute', None):
            child.result.execute()
        self.main_window.hide()
        self.main_window.entry.set_text("")
        
    def on_selection_changed(self, flowbox):
        if not hasattr(self, 'preview_container') or not self.preview_container:
            return
        selected = flowbox.get_selected_children()
        if not selected:
            self.preview_container.set_visible(False)
            self.main_window.set_default_size(650, 1)
            return
            
        child = selected[0]
        if not hasattr(child, 'result') or not child.result:
            self.preview_container.set_visible(False)
            self.main_window.set_default_size(650, 1)
            return
            
        import preview_manager
        
        while widget := self.preview_container.get_first_child():
            self.preview_container.remove(widget)
            
        if getattr(self.main_window, 'quick_look', None) and self.main_window.quick_look.is_visible():
            self.main_window.quick_look.preview_result(child.result)

        preview_widget = preview_manager.PreviewManager.render(child.result)
        self.preview_container.append(preview_widget)
        self.preview_container.set_visible(True)
        self.main_window.set_default_size(1050, 1)

    def on_category_clicked(self, button, cat_name):
        if self.active_category == cat_name:
            return
            
        if self.active_category in self.filter_buttons:
            self.filter_buttons[self.active_category].remove_css_class("active")
        self.active_category = cat_name
        self.filter_buttons[cat_name].add_css_class("active")
        
        self.suggestions_flowbox.set_filter_func(None)
        self.suggestions_flowbox.set_filter_func(self._filter_func)
        self.recents_flowbox.set_filter_func(None)
        self.recents_flowbox.set_filter_func(self._filter_func)

    def _filter_func(self, child):
        if not hasattr(child, "result"):
            return True
            
        if self.active_category != "All":
            target_cats = self.CAT_MAPPING.get(self.active_category, [])
            mime = child.result.preview_data.get("mime", "").lower()
            
            matched = False
            for target in target_cats:
                if target in mime:
                    matched = True
                    break
            
            if self.active_category == "Folders" and mime == "unknown" and os.path.isdir(child.result.preview_data.get("path", "")):
                matched = True
                
            if not matched:
                return False
                
        if not self.current_query:
            return True
        q = self.current_query.lower()
        return q in child.result.title.lower()

    def render(self, results: list):
        self.current_query = self.main_window.entry.get_text().strip()
        
        if not self.current_query and not results:
            file_provider = next((p for p in self.main_window.engine.providers if type(p).__name__ == "FileProvider"), None)
            if file_provider and hasattr(file_provider, "get_recent_files"):
                results = file_provider.get_recent_files()

        self.current_results = results
        
        # Пересобираем сетку для обновления карточек при каждом новом рендеринге (важно для кэша и пула)
        self._populate(results)
            
        if not self.current_query:
            self.suggestions_box.set_visible(False)
            self.recents_label.set_label(t("section_recent"))
        else:
            self.suggestions_box.set_visible(True)
            self.recents_label.set_label(t("section_recent"))
            
        self.suggestions_flowbox.set_filter_func(None)
        self.suggestions_flowbox.set_filter_func(self._filter_func)
        self.recents_flowbox.set_filter_func(None)
        self.recents_flowbox.set_filter_func(self._filter_func)
            

    def on_activated(self):
        pass

    def on_deactivated(self):
        pass

    def on_key_pressed(self, keyval, state, results) -> bool:
        child = self.suggestions_flowbox.get_selected_children()
        if not child:
            child = self.recents_flowbox.get_selected_children()
            
        if not child:
            return False
            
        result = getattr(child[0], 'result', None)
        if not result:
            return False

        if keyval == Gdk.KEY_space:
            if getattr(self.main_window, 'quick_look', None):
                if self.main_window.quick_look.is_visible():
                    self.main_window.quick_look.hide_preview()
                    return True
                else:
                    return self.main_window.quick_look.preview_result(result)

        is_ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)

        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            if is_ctrl and getattr(result, 'open_location', None):
                result.open_location()
                self.main_window.hide()
                self.main_window.entry.set_text("")
                return True
            elif not is_ctrl and getattr(result, 'execute', None):
                result.execute()
                self.main_window.hide()
                self.main_window.entry.set_text("")
                return True
                
        if is_ctrl and keyval in (Gdk.KEY_c, Gdk.KEY_C):
            if getattr(result, 'copy_value', None):
                result.copy_value()
                return True
                
        return False
