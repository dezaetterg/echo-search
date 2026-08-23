try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk, Pango, Gio, GObject
except ValueError:
    pass

from .base import BaseMode

class EmojiItemWrapper(GObject.Object):
    def __init__(self, result):
        super().__init__()
        self.result = result

class EmojiMode(BaseMode):
    category_filter = "Emoji"
    
    def _create_widget(self) -> Gtk.Widget:
        self.current_results = []
        self.active_category = "All"
        
        self.left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.left_box.set_hexpand(True)
        
        # --- FILTERS ---
        self.filters_scroll = Gtk.ScrolledWindow()
        self.filters_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        self.filters_scroll.set_margin_start(16)
        self.filters_scroll.set_margin_end(16)
        self.filters_scroll.set_margin_top(16)
        self.filters_scroll.set_margin_bottom(8)
        self.filters_scroll.add_css_class("apps-filters-scroll")
        
        hscrollbar = self.filters_scroll.get_hscrollbar()
        if hscrollbar:
            hscrollbar.set_visible(False)
            
        self.filters_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.filters_box.set_spacing(8)
        
        self.filter_buttons = {}
        categories = ["All", "Characters", "Smileys & Emotion", "People & Body", "Animals & Nature", "Food & Drink", "Travel & Places", "Activities", "Objects", "Symbols", "Flags"]
        for cat in categories:
            btn = Gtk.Button(label=cat)
            btn.add_css_class("apps-filter-pill")
            if cat == "All":
                btn.add_css_class("active")
            btn.connect("clicked", self.on_category_clicked, cat)
            self.filters_box.append(btn)
            self.filter_buttons[cat] = btn
            
        self.filters_scroll.set_child(self.filters_box)
        self.left_box.append(self.filters_scroll)
        
        # --- GridView Setup ---
        self.list_store = Gio.ListStore.new(EmojiItemWrapper)
        
        # Add a CustomFilter to support Category filtering
        self.custom_filter = Gtk.CustomFilter.new(self._filter_func)
        self.filter_list_model = Gtk.FilterListModel.new(self.list_store, self.custom_filter)
        
        self.selection_model = Gtk.SingleSelection.new(self.filter_list_model)
        self.selection_model.set_autoselect(False)
        
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)
        
        self.grid_view = Gtk.GridView.new(self.selection_model, factory)
        self.grid_view.set_max_columns(10)
        self.grid_view.set_min_columns(1)
        self.grid_view.set_single_click_activate(False)
        self.grid_view.connect("activate", self.on_item_activated)
        self.grid_view.set_margin_start(16)
        self.grid_view.set_margin_end(16)
        self.grid_view.set_margin_bottom(16)
        
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_min_content_height(400)
        self.scroll.set_max_content_height(400)
        
        self.scroll.set_child(self.grid_view)
        
        self.glass_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.glass_container.add_css_class("apps-glass-container")
        self.glass_container.append(self.scroll)
        
        self.left_box.append(self.glass_container)
        self.populated = False
        return self.left_box

    def _filter_func(self, item):
        if self.active_category == "All":
            return True
        return item.result.preview_data.get("emoji_category") == self.active_category

    def on_category_clicked(self, button, cat_name):
        if self.active_category == cat_name:
            return
            
        if self.active_category in self.filter_buttons:
            self.filter_buttons[self.active_category].remove_css_class("active")
            
        self.active_category = cat_name
        self.filter_buttons[cat_name].add_css_class("active")
        
        # Re-evaluate the filter
        self.custom_filter.set_filter_func(self._filter_func)
        
        self.main_window.set_default_size(1050, 1)
        self.main_window.queue_resize()

    def _on_factory_setup(self, factory, list_item):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.add_css_class("emoji-card")
        card.set_halign(Gtk.Align.CENTER)
        card.set_size_request(80, 80)
        
        emoji_lbl = Gtk.Label()
        emoji_lbl.add_css_class("emoji-char")
        card.append(emoji_lbl)
        
        title = Gtk.Label()
        title.set_max_width_chars(10)
        title.set_ellipsize(Pango.EllipsizeMode.END)
        title.add_css_class("emoji-title")
        card.append(title)
        
        list_item.set_child(card)

    def _on_factory_bind(self, factory, list_item):
        card = list_item.get_child()
        emoji_lbl = card.get_first_child()
        title = emoji_lbl.get_next_sibling()
        
        wrapper = list_item.get_item()
        if wrapper and wrapper.result:
            emoji_lbl.set_label(wrapper.result.icon)
            title.set_label(wrapper.result.title)
            
            # Since CSS :selected pseudo-class applies to the ListView/GridView item,
            # we don't strictly need manual class toggling, but just in case:
            if list_item.get_selected():
                card.add_css_class("selected")
            else:
                card.remove_css_class("selected")



    def on_item_activated(self, grid_view, position):
        wrapper = self.filter_list_model.get_item(position)
        if wrapper and wrapper.result:
            self._launch_app(wrapper.result)

    def render(self, results: list):
        self.current_results = results
        self.list_store.remove_all()
        
        for result in results:
            self.list_store.append(EmojiItemWrapper(result))
            
        if len(results) > 0:
            self.grid_view.set_visible(True)
        else:
            self.grid_view.set_visible(False)
            
        self.main_window.set_default_size(1050, 1)
        self.main_window.queue_resize()

    def _launch_app(self, result):
        if getattr(result, 'execute', None):
            result.execute()
        
        # Визуальный отклик перед закрытием
        self.main_window.entry.set_text(f"Скопировано: {result.icon}")
        
        from gi.repository import GLib
        def hide_after_delay():
            self.main_window.hide()
            self.main_window.entry.set_text("")
            return False
            
        GLib.timeout_add(1000, hide_after_delay)

    def on_key_pressed(self, keyval, state, current_results: list) -> bool:
        # Standard navigation is handled by Gtk.GridView
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            pos = self.selection_model.get_selected()
            if pos != Gtk.INVALID_LIST_POSITION:
                wrapper = self.filter_list_model.get_item(pos)
                if wrapper and wrapper.result:
                    self._launch_app(wrapper.result)
                    return True
        return False
