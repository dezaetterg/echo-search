try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk, Pango
except ValueError:
    pass

from .base import BaseMode

class SettingsMode(BaseMode):
    category_filter = "Settings"
    
    def _create_widget(self) -> Gtk.Widget:
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_min_content_height(400)
        self.scroll.set_max_content_height(400)
        self.scroll.set_margin_start(16)
        self.scroll.set_margin_end(16)
        
        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(10)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.flowbox.connect("child-activated", self.on_child_activated)
        
        self.flowbox.set_column_spacing(12)
        self.flowbox.set_row_spacing(12)
        
        self.scroll.set_child(self.flowbox)
        self.box.append(self.scroll)
        
        self.current_results = []
        return self.box

    def render(self, results: list):
        self.current_results = results
        while child := self.flowbox.get_first_child():
            self.flowbox.remove(child)
            
        for result in self.current_results:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            card.add_css_class("app-card")
            card.set_halign(Gtk.Align.CENTER)
            card.set_valign(Gtk.Align.CENTER)
            card.set_size_request(84, 96)
            
            icon = Gtk.Image.new_from_icon_name(result.icon or "preferences-system")
            icon.set_pixel_size(64)
            icon.set_margin_bottom(8)
            card.append(icon)
            
            label = Gtk.Label(label=result.title)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_max_width_chars(12)
            label.add_css_class("app-card-title")
            card.append(label)
            
            child = Gtk.FlowBoxChild()
            child.set_child(card)
            child.result = result
            child.add_css_class("app-card-container")
            self.flowbox.append(child)
            
        self.main_window.set_default_size(700, 1)
        self.main_window.queue_resize()

    def on_child_activated(self, flowbox, child):
        result = child.result
        result.execute()
        self.main_window.hide()
        self.main_window.entry.set_text("")

    def on_key_pressed(self, keyval, state, current_results: list) -> bool:
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            selected = self.flowbox.get_selected_children()
            if selected:
                self.on_child_activated(self.flowbox, selected[0])
                return True
        return False
