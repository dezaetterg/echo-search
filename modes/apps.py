try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk, Pango, Gio, GLib, GObject
except ValueError:
    pass

from .base import BaseMode
from utils import set_icon_safe
from i18n import t

class AppItemWrapper(GObject.Object):
    def __init__(self, result):
        super().__init__()
        self.result = result

class AppsMode(BaseMode):
    category_filter = "Apps"
    
    def _create_widget(self) -> Gtk.Widget:
        self.current_results = []
        self.active_category = "All"
        
        self.left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.left_box.set_hexpand(True)
        
        # --- FILTERS ---
        self.filters_scroll = Gtk.ScrolledWindow()
        self.filters_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        self.filters_scroll.set_margin_start(32)
        self.filters_scroll.set_margin_end(32)
        self.filters_scroll.set_margin_top(8)
        self.filters_scroll.set_margin_bottom(16)
        self.filters_scroll.add_css_class("apps-filters-scroll")
        
        hscrollbar = self.filters_scroll.get_hscrollbar()
        if hscrollbar:
            hscrollbar.set_visible(False)
            
        self.filters_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.filters_box.set_spacing(12)
        
        self.filter_buttons = {}
        categories = ["All", "Utilities", "Development", "Games", "Internet", "Office", "Graphics", "Multimedia", "System"]
        
        self.CAT_MAPPING = {
            "All": None,
            "Utilities": "Utility",
            "Development": "Development",
            "Games": "Game",
            "Internet": "Network",
            "Office": "Office",
            "Graphics": "Graphics",
            "Multimedia": "AudioVideo",
            "System": "System"
        }
        
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
        
        # --- GridView Setup ---
        self.list_store = Gio.ListStore.new(AppItemWrapper)
        
        self.custom_filter = Gtk.CustomFilter.new(self._filter_func)
        self.filter_list_model = Gtk.FilterListModel.new(self.list_store, self.custom_filter)
        
        self.selection_model = Gtk.SingleSelection.new(self.filter_list_model)
        self.selection_model.set_autoselect(False)
        self.selection_model.set_autoselect(False)
        
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)
        
        self.grid_view = Gtk.GridView.new(self.selection_model, factory)
        self.grid_view.set_max_columns(6)
        self.grid_view.set_min_columns(1)
        self.grid_view.set_single_click_activate(False)
        self.grid_view.connect("activate", self.on_item_activated)
        
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_min_content_height(420)
        self.scroll.set_max_content_height(420)
        self.scroll.set_child(self.grid_view)
        
        # Контейнер для эффекта стеклянной поверхности
        self.glass_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.glass_container.add_css_class("apps-glass-container")
        self.glass_container.append(self.scroll)
        
        self.left_box.append(self.glass_container)
        
        self.populated = False
        self.current_query = ""
        GLib.idle_add(self._preload_apps)
        return self.left_box

    def _preload_apps(self):
        if not self.populated and hasattr(self.main_window, "engine"):
            all_apps = self.main_window.engine.get_all_apps()
            for app in all_apps:
                self.list_store.append(AppItemWrapper(app))
            self.populated = True
        return False

    def _filter_func(self, item):
        target_cat = self.CAT_MAPPING.get(self.active_category)
        if target_cat and target_cat not in item.result.preview_data.get("categories", ""):
            return False
            
        if self.current_query:
            q = self.current_query.lower()
            t_match = q in item.result.title.lower()
            s_match = bool(item.result.subtitle and q in item.result.subtitle.lower())
            e_match = bool(item.result.preview_data and q in str(item.result.preview_data.get("exec", "")).lower())
            c_match = bool(item.result.preview_data and q in str(item.result.preview_data.get("categories", "")).lower())
            if not (t_match or s_match or e_match or c_match):
                return False
                
        return True

    def on_category_clicked(self, button, cat_name):
        if self.active_category == cat_name:
            return
            
        if self.active_category in self.filter_buttons:
            self.filter_buttons[self.active_category].remove_css_class("active")
            
        self.active_category = cat_name
        self.filter_buttons[cat_name].add_css_class("active")
        self.custom_filter.set_filter_func(self._filter_func)
        

    def _on_factory_setup(self, factory, list_item):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.add_css_class("launchpad-card")
        card.set_halign(Gtk.Align.CENTER)
        card.set_valign(Gtk.Align.CENTER)
        card.set_size_request(100, 120)
        
        icon = Gtk.Image()
        icon.set_pixel_size(80)
        icon.add_css_class("launchpad-icon")
        card.append(icon)
        
        title = Gtk.Label()
        title.set_max_width_chars(12)
        title.set_ellipsize(Pango.EllipsizeMode.END)
        title.add_css_class("launchpad-title")
        title.set_justify(Gtk.Justification.CENTER)
        card.append(title)
        
        list_item.set_child(card)

    def _on_factory_bind(self, factory, list_item):
        card = list_item.get_child()
        icon = card.get_first_child()
        title = icon.get_next_sibling()
        
        wrapper = list_item.get_item()
        if wrapper and wrapper.result:
            if wrapper.result.icon:
                set_icon_safe(icon, wrapper.result.icon, fallback_icon="application-x-executable", pixel_size=64)
            title.set_label(wrapper.result.title)
            
            if list_item.get_selected():
                card.add_css_class("selected")
            else:
                card.remove_css_class("selected")


    def on_item_activated(self, grid_view, position):
        wrapper = self.filter_list_model.get_item(position)
        if wrapper and wrapper.result:
            self._launch_app(wrapper.result)

    def render(self, results: list):
        self.current_query = self.main_window.entry.get_text().strip()
        
        if not self.populated:
            all_apps = self.main_window.engine.get_all_apps()
            for app in all_apps:
                self.list_store.append(AppItemWrapper(app))
            self.populated = True
            
        self.custom_filter.set_filter_func(self._filter_func)
        
        if self.filter_list_model.get_n_items() > 0:
            self.grid_view.set_visible(True)
        else:
            self.grid_view.set_visible(False)
            

    def _launch_app(self, result):
        if getattr(result, 'execute', None):
            result.execute()
        self.main_window.hide()
        self.main_window.entry.set_text("")

    def on_key_pressed(self, keyval, state, current_results: list) -> bool:
        n_items = self.filter_list_model.get_n_items()
        if n_items == 0:
            return False

        cols = 6

        def _select_and_scroll(new_pos):
            self.selection_model.set_selected(new_pos)
            try:
                self.grid_view.scroll_to(new_pos, Gtk.ListScrollFlags.NONE, None)
            except Exception:
                pass

        if keyval == Gdk.KEY_Right:
            pos = self.selection_model.get_selected()
            if pos == Gtk.INVALID_LIST_POSITION:
                _select_and_scroll(0)
            elif pos < n_items - 1:
                _select_and_scroll(pos + 1)
            return True

        elif keyval == Gdk.KEY_Left:
            pos = self.selection_model.get_selected()
            if pos == Gtk.INVALID_LIST_POSITION:
                _select_and_scroll(0)
            elif pos > 0:
                _select_and_scroll(pos - 1)
            return True

        elif keyval == Gdk.KEY_Down:
            pos = self.selection_model.get_selected()
            if pos == Gtk.INVALID_LIST_POSITION:
                _select_and_scroll(0)
            elif pos + cols < n_items:
                _select_and_scroll(pos + cols)
            else:
                _select_and_scroll(n_items - 1)
            return True

        elif keyval == Gdk.KEY_Up:
            pos = self.selection_model.get_selected()
            if pos == Gtk.INVALID_LIST_POSITION:
                _select_and_scroll(0)
            elif pos - cols >= 0:
                _select_and_scroll(pos - cols)
            else:
                _select_and_scroll(0)
            return True

        elif keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            pos = self.selection_model.get_selected()
            if pos == Gtk.INVALID_LIST_POSITION and n_items > 0:
                pos = 0
                
            if pos != Gtk.INVALID_LIST_POSITION and pos < n_items:
                wrapper = self.filter_list_model.get_item(pos)
                if wrapper and wrapper.result:
                    self._launch_app(wrapper.result)
                    return True
        elif keyval == Gdk.KEY_Escape:
            return False
        return False
