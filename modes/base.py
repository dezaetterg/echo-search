try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk
except ValueError:
    pass

class BaseMode:
    """
    Abstract Base Class for all launcher modes (Search, Apps, Files, Settings, etc.)
    """
    category_filter = None # Overridden by subclasses

    def __init__(self, main_window):
        self.main_window = main_window # Reference to EchoUI
        self.widget = self._create_widget()

    def _create_widget(self) -> Gtk.Widget:
        """Create and return the root GTK widget for this mode."""
        raise NotImplementedError

    def get_widget(self) -> Gtk.Widget:
        return self.widget

    def get_category_filter(self) -> str:
        return self.category_filter

    def render(self, results: list):
        """Called when ModeManager provides new search results."""
        pass

    def on_activated(self):
        """Called when the user switches to this mode."""
        pass



    def on_key_pressed(self, keyval, state, current_results: list) -> bool:
        """
        Called when a key is pressed. 
        Return True if the key was handled, False otherwise.
        """
        return False
