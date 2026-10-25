try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gdk, Gio, GLib, GObject, Gtk, Pango
except ValueError:
    pass

from i18n import get_current_language, t
from logger import get_logger

from .base import BaseMode

logger = get_logger("emoji_mode")


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
        EMOJI_CAT_KEYS = {
            "All": "cat_all",
            "Characters": "emoji_cat_characters",
            "Smileys & Emotion": "emoji_cat_smileys",
            "People & Body": "emoji_cat_people",
            "Animals & Nature": "emoji_cat_animals",
            "Food & Drink": "emoji_cat_food",
            "Travel & Places": "emoji_cat_travel",
            "Activities": "emoji_cat_activities",
            "Objects": "emoji_cat_objects",
            "Symbols": "emoji_cat_symbols",
            "Flags": "emoji_cat_flags"
        }
        categories = ["All", "Characters", "Smileys & Emotion", "People & Body", "Animals & Nature", "Food & Drink", "Travel & Places", "Activities", "Objects", "Symbols", "Flags"]
        for cat in categories:
            label_text = t(EMOJI_CAT_KEYS.get(cat, cat))
            btn = Gtk.Button(label=label_text)
            btn.add_css_class("apps-filter-pill")
            if cat == "All":
                btn.add_css_class("active")
            btn.connect("clicked", self.on_category_clicked, cat)
            self.filters_box.append(btn)
            self.filter_buttons[cat] = btn

        self.filters_scroll.set_child(self.filters_box)
        self.left_box.append(self.filters_scroll)

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
        self.scroll.set_min_content_height(420)
        self.scroll.set_max_content_height(420)

        self.scroll.set_child(self.grid_view)

        self.glass_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.glass_container.add_css_class("apps-glass-container")
        self.glass_container.append(self.scroll)

        self.left_box.append(self.glass_container)
        self.populated = False
        self.current_query = ""
        from gi.repository import GLib
        GLib.idle_add(self._preload_emojis)
        return self.left_box

    def _preload_emojis(self):
        if not self.populated and hasattr(self.main_window, "engine"):
            all_emojis = self.main_window.engine.get_all_emojis()
            for em in all_emojis:
                self.list_store.append(EmojiItemWrapper(em))
            self.populated = True
        return False

    def _filter_func(self, item):
        if not item or not item.result:
            return False
        if self.active_category != "All":
            cat = item.result.preview_data.get("emoji_category", "") if item.result.preview_data else ""
            if cat != self.active_category:
                return False
        if self.current_query:
            q = self.current_query.lower()
            pdata = item.result.preview_data or {}
            ru_name = pdata.get("name_ru", "").lower()
            en_name = pdata.get("name", "").lower()
            if (q not in item.result.title.lower() and 
                q not in ru_name and 
                q not in en_name):
                kw = pdata.get("keywords", [])
                if not any(q in str(k).lower() for k in kw):
                    return False
        return True


    def retranslate(self):
        EMOJI_CAT_KEYS = {
            "All": "cat_all",
            "Characters": "emoji_cat_characters",
            "Smileys & Emotion": "emoji_cat_smileys",
            "People & Body": "emoji_cat_people",
            "Animals & Nature": "emoji_cat_animals",
            "Food & Drink": "emoji_cat_food",
            "Travel & Places": "emoji_cat_travel",
            "Activities": "emoji_cat_activities",
            "Objects": "emoji_cat_objects",
            "Symbols": "emoji_cat_symbols",
            "Flags": "emoji_cat_flags"
        }
        for cat, btn in self.filter_buttons.items():
            btn.set_label(t(EMOJI_CAT_KEYS.get(cat, cat)))

        if hasattr(self, "list_store") and hasattr(self.main_window, "engine"):
            self.list_store.remove_all()
            all_emojis = self.main_window.engine.get_all_emojis()
            for em in all_emojis:
                self.list_store.append(EmojiItemWrapper(em))
            if hasattr(self, "custom_filter"):
                self.custom_filter.set_filter_func(None)
                self.custom_filter.set_filter_func(self._filter_func)

    def on_category_clicked(self, button, cat_name):
        if self.active_category == cat_name:
            return

        if self.active_category in self.filter_buttons:
            self.filter_buttons[self.active_category].remove_css_class("active")

        self.active_category = cat_name
        self.filter_buttons[cat_name].add_css_class("active")

        # Re-evaluate the filter
        self.custom_filter.set_filter_func(self._filter_func)


    def _on_factory_setup(self, factory, list_item):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.add_css_class("emoji-card")
        card.set_halign(Gtk.Align.CENTER)
        card.set_valign(Gtk.Align.CENTER)
        card.set_size_request(80, 80)

        emoji_lbl = Gtk.Label()
        emoji_lbl.add_css_class("emoji-char")
        emoji_lbl.set_hexpand(True)
        emoji_lbl.set_vexpand(True)
        emoji_lbl.set_halign(Gtk.Align.CENTER)
        emoji_lbl.set_valign(Gtk.Align.CENTER)
        emoji_lbl.set_xalign(0.5)
        emoji_lbl.set_yalign(0.5)
        card.append(emoji_lbl)

        title = Gtk.Label()
        title.set_max_width_chars(10)
        title.set_ellipsize(Pango.EllipsizeMode.END)
        title.add_css_class("emoji-title")
        title.set_hexpand(True)
        title.set_halign(Gtk.Align.CENTER)
        title.set_xalign(0.5)
        card.append(title)

        list_item.set_child(card)

    def _on_factory_bind(self, factory, list_item):
        card = list_item.get_child()
        emoji_lbl = card.get_first_child()
        title = emoji_lbl.get_next_sibling()

        wrapper = list_item.get_item()
        if wrapper and wrapper.result:
            emoji_lbl.set_label(wrapper.result.icon)

            pdata = wrapper.result.preview_data or {}
            is_ru = (get_current_language() == "ru")
            ru_name = pdata.get("name_ru")
            if not ru_name:
                try:
                    from providers.emoji_ru import get_emoji_ru_name
                    ru_name = get_emoji_ru_name(wrapper.result.icon, pdata.get("name", ""))
                except Exception:
                    ru_name = ""

            display_name = ru_name if is_ru else pdata.get("name", "").capitalize()
            if not display_name:
                raw_title = wrapper.result.title
                if raw_title.startswith(wrapper.result.icon):
                    display_name = raw_title[len(wrapper.result.icon):].strip()
                else:
                    display_name = raw_title

            title.set_label(display_name)

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
        self.current_query = self.main_window.entry.get_text().strip()
        if not self.populated:
            self._preload_emojis()
        self.custom_filter.set_filter_func(self._filter_func)

        n = self.filter_list_model.get_n_items()
        self.grid_view.set_visible(n > 0)


    def _launch_app(self, result):
        if getattr(result, "execute", None):
            result.execute()
        self.main_window.hide()
        self.main_window.entry.set_text("")

    def on_key_pressed(self, keyval, state, current_results: list) -> bool:
        n_items = self.filter_list_model.get_n_items()
        if n_items == 0:
            return False

        cols = self.grid_view.get_max_columns() or 10
        pos = self.selection_model.get_selected()

        def _select_and_scroll(new_pos):
            self.selection_model.set_selected(new_pos)
            try:
                self.grid_view.scroll_to(new_pos, Gtk.ListScrollFlags.NONE, None)
            except (AttributeError, TypeError, GLib.Error) as e:
                logger.debug("Emoji scroll_to failed: %s", e)

        # Мгновенный выбор по Alt + 1..9
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
                    wrapper = self.filter_list_model.get_item(idx)
                    if wrapper and wrapper.result:
                        self._launch_app(wrapper.result)
                        return True

        if keyval == Gdk.KEY_Right:
            if pos == Gtk.INVALID_LIST_POSITION:
                _select_and_scroll(0)
            elif pos < n_items - 1:
                _select_and_scroll(pos + 1)
            return True

        elif keyval == Gdk.KEY_Left:
            if pos == Gtk.INVALID_LIST_POSITION:
                _select_and_scroll(0)
            elif pos > 0:
                _select_and_scroll(pos - 1)
            return True

        elif keyval == Gdk.KEY_Down or ((state & Gdk.ModifierType.CONTROL_MASK) and keyval in (Gdk.KEY_n, Gdk.KEY_N, Gdk.KEY_j, Gdk.KEY_J)):
            if pos == Gtk.INVALID_LIST_POSITION:
                _select_and_scroll(0)
            elif pos + cols < n_items:
                _select_and_scroll(pos + cols)
            else:
                _select_and_scroll(n_items - 1)
            return True

        elif keyval == Gdk.KEY_Up or ((state & Gdk.ModifierType.CONTROL_MASK) and keyval in (Gdk.KEY_p, Gdk.KEY_P)):
            if pos == Gtk.INVALID_LIST_POSITION:
                _select_and_scroll(0)
            elif pos - cols >= 0:
                _select_and_scroll(pos - cols)
            else:
                _select_and_scroll(0)
            return True

        elif keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            if pos == Gtk.INVALID_LIST_POSITION and n_items > 0:
                pos = 0
            if pos != Gtk.INVALID_LIST_POSITION and pos < n_items:
                wrapper = self.filter_list_model.get_item(pos)
                if wrapper and wrapper.result:
                    self._launch_app(wrapper.result)
                    return True
        return False
