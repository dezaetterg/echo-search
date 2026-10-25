try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gdk, Gio, GLib, GObject, Gtk, Pango
except ValueError:
    pass

from i18n import t
from logger import get_logger

from .base import BaseMode

logger = get_logger("clipboard_mode")


class ClipboardItemWrapper(GObject.Object):
    def __init__(self, result):
        super().__init__()
        self.result = result

class ClipboardMode(BaseMode):
    category_filter = "Clipboard"

    def _create_widget(self) -> Gtk.Widget:
        self.current_results = []

        self.left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.left_box.set_hexpand(True)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(150)

        self.empty_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.empty_box.set_valign(Gtk.Align.CENTER)
        self.empty_box.set_halign(Gtk.Align.CENTER)
        self.empty_box.set_margin_top(40)
        self.empty_box.set_margin_bottom(40)
        self.empty_box.add_css_class("clipboard-empty-state")

        empty_icon = Gtk.Image.new_from_icon_name("edit-paste-symbolic")
        empty_icon.set_pixel_size(64)
        empty_icon.set_opacity(0.4)
        empty_icon.add_css_class("clipboard-empty-icon")
        self.empty_box.append(empty_icon)

        empty_label = Gtk.Label(label=t("clipboard_placeholder"))
        empty_label.add_css_class("clipboard-empty-label")
        self.empty_box.append(empty_label)

        empty_desc = Gtk.Label(label=t("preview_empty_desc"))
        empty_desc.add_css_class("result-desc")
        empty_desc.set_opacity(0.6)
        self.empty_box.append(empty_desc)

        self.stack.add_named(self.empty_box, "empty")

        self.list_store = Gio.ListStore.new(ClipboardItemWrapper)
        self.selection_model = Gtk.SingleSelection.new(self.list_store)
        self.selection_model.set_autoselect(True)

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)

        self.list_view = Gtk.ListView.new(self.selection_model, factory)
        self.list_view.set_name("results-list")
        self.list_view.add_css_class("clipboard-list-view")
        self.list_view.set_single_click_activate(False)
        self.list_view.connect("activate", self.on_item_activated)

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_min_content_height(380)
        self.scroll.set_max_content_height(420)
        self.scroll.set_child(self.list_view)

        self.stack.add_named(self.scroll, "list")
        self.stack.set_visible_child_name("empty")

        self.glass_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.glass_container.add_css_class("apps-glass-container")
        self.glass_container.append(self.stack)

        self.left_box.append(self.glass_container)

        # Attempt to hook into provider live updates
        try:
            for provider in self.main_window.engine.providers:
                if type(provider).__name__ == "ClipboardProvider":
                    provider.on_new_item = self.on_new_clipboard_item
                    break
        except Exception as e:
            logger.debug("Failed attaching on_new_item hook to ClipboardProvider: %s", e)

        return self.left_box

    def _on_factory_setup(self, factory, list_item):
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        row_box.add_css_class("result-row")
        row_box.set_spacing(12)

        icon = Gtk.Image.new_from_icon_name("edit-paste-symbolic")
        icon.set_pixel_size(28)
        icon.add_css_class("result-icon")
        icon.set_valign(Gtk.Align.CENTER)
        row_box.append(icon)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        text_box.set_valign(Gtk.Align.CENTER)
        text_box.set_hexpand(True)

        title = Gtk.Label()
        title.set_xalign(0)
        title.set_max_width_chars(80)
        title.set_wrap(True)
        title.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        title.set_lines(3)
        title.set_ellipsize(Pango.EllipsizeMode.END)
        title.add_css_class("result-title")
        text_box.append(title)

        desc = Gtk.Label()
        desc.set_xalign(0)
        desc.add_css_class("result-desc")
        text_box.append(desc)

        row_box.append(text_box)
        list_item.set_child(row_box)

    def _on_factory_bind(self, factory, list_item):
        row_box = list_item.get_child()
        if not row_box:
            return
        text_box = row_box.get_last_child()
        if not text_box:
            return
        title = text_box.get_first_child()
        desc = text_box.get_last_child()

        wrapper = list_item.get_item()
        if wrapper and wrapper.result:
            title.set_label(wrapper.result.title or "")
            desc.set_label(wrapper.result.subtitle or "")

    def render(self, results: list):
        self.current_results = results or []
        self.list_store.remove_all()

        for result in self.current_results:
            self.list_store.append(ClipboardItemWrapper(result))

        if len(self.current_results) > 0:
            self.stack.set_visible_child_name("list")
            self.selection_model.set_selected(0)
        else:
            self.stack.set_visible_child_name("empty")


    def on_new_clipboard_item(self, result):
        query = self.main_window.entry.get_text().strip()
        if not query:
            self.list_store.insert(0, ClipboardItemWrapper(result))
            if self.list_store.get_n_items() > 100:
                self.list_store.remove(100)

            if self.list_store.get_n_items() > 0:
                self.stack.set_visible_child_name("list")
                if self.selection_model.get_selected() == Gtk.INVALID_LIST_POSITION:
                    self.selection_model.set_selected(0)

    def on_item_activated(self, list_view, position):
        if position < self.list_store.get_n_items():
            wrapper = self.list_store.get_item(position)
            if wrapper and wrapper.result:
                self._launch_app(wrapper.result)

    def _launch_app(self, result):
        if getattr(result, 'execute', None):
            result.execute()
        self.main_window.hide()
        self.main_window.entry.set_text("")

    def _clear_all_clipboard(self):
        try:
            for provider in self.main_window.engine.providers:
                if type(provider).__name__ == "ClipboardProvider":
                    provider.history.clear()
                    break
        except Exception as e:
            logger.debug("Failed clearing ClipboardProvider history: %s", e)
        self.list_store.remove_all()
        self.current_results.clear()
        self.stack.set_visible_child_name("empty")

    def on_key_pressed(self, keyval, state, current_results: list) -> bool:
        if self.stack.get_visible_child_name() != "list":
            return False

        n_items = self.list_store.get_n_items()
        if n_items == 0:
            return False

        # Навигация вниз: стрелка вниз, Ctrl+N, Ctrl+J
        is_down = keyval == Gdk.KEY_Down or (
            (state & Gdk.ModifierType.CONTROL_MASK) and keyval in (Gdk.KEY_n, Gdk.KEY_N, Gdk.KEY_j, Gdk.KEY_J)
        )
        if is_down:
            pos = self.selection_model.get_selected()
            if pos < n_items - 1:
                new_pos = pos + 1
                self.selection_model.set_selected(new_pos)
                try:
                    self.list_view.scroll_to(new_pos, Gtk.ListScrollFlags.NONE, None)
                except (AttributeError, TypeError, GLib.Error) as e:
                    logger.debug("Clipboard scroll_to failed: %s", e)
            return True

        # Навигация вверх: стрелка вверх, Ctrl+P
        is_up = keyval == Gdk.KEY_Up or (
            (state & Gdk.ModifierType.CONTROL_MASK) and keyval in (Gdk.KEY_p, Gdk.KEY_P)
        )
        if is_up:
            pos = self.selection_model.get_selected()
            if pos > 0:
                new_pos = pos - 1
                self.selection_model.set_selected(new_pos)
                try:
                    self.list_view.scroll_to(new_pos, Gtk.ListScrollFlags.NONE, None)
                except (AttributeError, TypeError, GLib.Error) as e:
                    logger.debug("Clipboard scroll_to failed: %s", e)
            return True

        # Мгновенная вставка по Alt + 1..9
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
                if idx < n_items:
                    self.on_item_activated(self.list_view, idx)
                    return True

        # Удаление записи: Delete (одна запись) или Shift+Delete / Ctrl+Delete (вся история)
        if keyval in (Gdk.KEY_Delete, Gdk.KEY_KP_Delete):
            if (state & Gdk.ModifierType.SHIFT_MASK) or (state & Gdk.ModifierType.CONTROL_MASK):
                self._clear_all_clipboard()
                return True

            pos = self.selection_model.get_selected()
            if pos != Gtk.INVALID_LIST_POSITION and pos < n_items:
                wrapper = self.list_store.get_item(pos)
                if wrapper and wrapper.result:
                    if hasattr(wrapper.result, "delete"):
                        wrapper.result.delete()
                self.list_store.remove(pos)
                if pos < len(self.current_results):
                    self.current_results.pop(pos)
                new_count = self.list_store.get_n_items()
                if new_count == 0:
                    self.stack.set_visible_child_name("empty")
                else:
                    new_sel = min(pos, new_count - 1)
                    self.selection_model.set_selected(new_sel)
                return True

        elif keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            pos = self.selection_model.get_selected()
            if pos != Gtk.INVALID_LIST_POSITION and pos < n_items:
                self.on_item_activated(self.list_view, pos)
                return True
        return False
