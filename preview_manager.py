import os
try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk, Pango
except ValueError:
    pass

from providers import SearchResult
from i18n import t

class PreviewManager:
    @staticmethod
    def render(result: SearchResult = None) -> Gtk.Widget:
        if result is None:
            return PreviewManager._render_empty_state()

        cat = result.category
        
        if cat == "Apps" or cat == "Settings":
            return PreviewManager._render_app(result)
        elif cat == "Math" or cat == "Units":
            return PreviewManager._render_math(result)
        elif cat == "Emoji":
            return PreviewManager._render_emoji(result)
        elif cat == "Clipboard":
            return PreviewManager._render_clipboard(result)
        elif cat == "Files":
            return PreviewManager._render_file(result)
        elif cat == "Commands":
            return PreviewManager._render_command(result)
            
        return PreviewManager._render_basic(result)

    @staticmethod
    def _create_base_structure():
        """
        Returns (root_box, content_box).
        root_box is the outer container with the background.
        content_box is the inner box inside the ScrolledWindow.
        """
        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root_box.set_vexpand(True)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        
        # Hide scrollbar for cleaner look
        vscrollbar = scroll.get_vscrollbar()
        if vscrollbar:
            vscrollbar.set_visible(False)
            
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_halign(Gtk.Align.FILL)
        scroll.set_child(content_box)
        
        root_box.append(scroll)
        return root_box, content_box

    @staticmethod
    def _create_hero_container():
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_halign(Gtk.Align.CENTER)
        box.add_css_class("preview-hero-container")
        return box

    @staticmethod
    def _create_icon(icon_name: str, size: int = 128):
        try:
            if icon_name and os.path.isabs(icon_name) and os.path.exists(icon_name):
                img = Gtk.Picture.new_for_filename(icon_name)
                img.set_can_shrink(True)
                img.set_size_request(size, size)
                img.add_css_class("preview-hero-icon")
                return img
        except: pass
        
        try:
            img = Gtk.Image.new_from_icon_name(icon_name or "application-x-executable")
            img.set_pixel_size(size)
            img.add_css_class("preview-hero-icon")
            return img
        except:
            img = Gtk.Image.new_from_icon_name("application-x-executable")
            img.set_pixel_size(size)
            return img

    @staticmethod
    def _create_title_block(title_text: str, subtitle_text: str):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_halign(Gtk.Align.CENTER)
        
        title = Gtk.Label(label=title_text)
        title.add_css_class("preview-main-title")
        title.set_justify(Gtk.Justification.CENTER)
        title.set_wrap(True)
        box.append(title)
        
        if subtitle_text:
            subtitle = Gtk.Label(label=subtitle_text)
            subtitle.add_css_class("preview-main-subtitle")
            subtitle.set_justify(Gtk.Justification.CENTER)
            subtitle.set_wrap(True)
            box.append(subtitle)
            
        return box

    @staticmethod
    def _create_meta_grid():
        # Gtk.Grid with homogeneous columns for perfect 50/50 split
        grid = Gtk.Grid()
        grid.set_column_spacing(16)
        grid.set_row_spacing(16)
        grid.set_column_homogeneous(True)
        grid.set_halign(Gtk.Align.FILL)
        grid.add_css_class("preview-meta-grid")
        return grid

    @staticmethod
    def _create_meta_card(key: str, value: str):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.add_css_class("preview-meta-card")
        
        lbl_key = Gtk.Label(label=key)
        lbl_key.add_css_class("preview-meta-key")
        lbl_key.set_halign(Gtk.Align.START)
        
        lbl_val = Gtk.Label(label=value)
        lbl_val.add_css_class("preview-meta-val")
        lbl_val.set_halign(Gtk.Align.START)
        lbl_val.set_ellipsize(Pango.EllipsizeMode.END)
        lbl_val.set_max_width_chars(15)
        
        card.append(lbl_key)
        card.append(lbl_val)
        
        return card

    @staticmethod
    def _create_action_footer(actions: list):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.END)
        box.set_margin_top(16)
        box.add_css_class("preview-action-box")
        
        for lbl, cb, destructive in actions:
            btn = Gtk.Button(label=lbl)
            btn.add_css_class("preview-btn")
            if destructive:
                btn.add_css_class("destructive")
            if cb:
                btn.connect("clicked", lambda b, func=cb: func())
            box.append(btn)
            
        return box

    @staticmethod
    def _render_empty_state() -> Gtk.Widget:
        root_box, content_box = PreviewManager._create_base_structure()
        
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)
        
        icon = Gtk.Image.new_from_icon_name("edit-find")
        icon.set_pixel_size(64)
        icon.set_opacity(0.3)
        icon.set_margin_bottom(16)
        
        lbl = Gtk.Label(label=t("preview_empty_desc"))
        lbl.add_css_class("preview-main-subtitle")
        
        content_box.append(icon)
        content_box.append(lbl)
        return root_box

    @staticmethod
    def _render_app(result: SearchResult) -> Gtk.Widget:
        root_box, content_box = PreviewManager._create_base_structure()
        
        hero_box = PreviewManager._create_hero_container()
        hero_box.append(PreviewManager._create_icon(result.icon, 128))
        content_box.append(hero_box)
        
        desc = result.preview_data.get("description") or result.subtitle
        content_box.append(PreviewManager._create_title_block(result.title, desc))
        
        grid = PreviewManager._create_meta_grid()
        col = 0
        if result.preview_data.get("developer"):
            grid.attach(PreviewManager._create_meta_card(t("label_developer"), result.preview_data["developer"]), col, 0, 1, 1)
            col += 1
        if result.preview_data.get("category"):
            grid.attach(PreviewManager._create_meta_card(t("label_categories"), result.preview_data["category"]), col, 0, 1, 1)
            
        content_box.append(grid)
        
        actions = []
        if result._action_execute:
            actions.append((t("action_open"), result.execute, False))
        if result._action_open_location:
            actions.append((t("action_open_location"), result.open_location, False))
        if result._action_copy:
            actions.append((t("action_copy_path"), result.copy_value, False))
            
        root_box.append(PreviewManager._create_action_footer(actions))
        return root_box

    @staticmethod
    def _render_file(result: SearchResult) -> Gtk.Widget:
        root_box, content_box = PreviewManager._create_base_structure()
        
        hero_box = PreviewManager._create_hero_container()
        hero_box.append(PreviewManager._create_icon(result.icon, 128))
        content_box.append(hero_box)
        
        content_box.append(PreviewManager._create_title_block(result.title, result.preview_data.get("mime", "")))
        
        grid = PreviewManager._create_meta_grid()
        col = 0
        if result.preview_data.get("size") and result.preview_data["size"] != "Unknown":
            grid.attach(PreviewManager._create_meta_card(t("label_size"), result.preview_data["size"]), col, 0, 1, 1)
            col += 1
        if result.preview_data.get("mtime") and result.preview_data["mtime"] != "Unknown":
            grid.attach(PreviewManager._create_meta_card(t("label_modified"), result.preview_data["mtime"]), col, 0, 1, 1)
            
        content_box.append(grid)
        
        actions = []
        if result._action_execute:
            actions.append((t("action_open"), result.execute, False))
        if result._action_open_location:
            actions.append((t("action_open_location"), result.open_location, False))
        if result._action_copy:
            actions.append((t("action_copy"), result.copy_value, False))
            
        root_box.append(PreviewManager._create_action_footer(actions))
        return root_box

    @staticmethod
    def _render_clipboard(result: SearchResult) -> Gtk.Widget:
        root_box, content_box = PreviewManager._create_base_structure()
        
        hero_box = PreviewManager._create_hero_container()
        lbl = Gtk.Label(label=result.preview_data.get("full_text", ""))
        lbl.add_css_class("preview-hero-text")
        lbl.set_wrap(True)
        lbl.set_max_width_chars(30)
        lbl.set_lines(6)
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
        hero_box.append(lbl)
        content_box.append(hero_box)
        
        content_box.append(PreviewManager._create_title_block(t("clip_copied_text"), result.preview_data.get("copy_time", "")))
        
        grid = PreviewManager._create_meta_grid()
        col = 0
        if result.preview_data.get("chars_count"):
            grid.attach(PreviewManager._create_meta_card(t("label_history"), str(result.preview_data["chars_count"])), col, 0, 1, 1)
            col += 1
        if result.preview_data.get("lines_count"):
            grid.attach(PreviewManager._create_meta_card(t("label_type"), str(result.preview_data["lines_count"])), col, 0, 1, 1)
            
        content_box.append(grid)
        
        actions = []
        if result._action_copy:
            actions.append((t("action_copy"), result.copy_value, False))
        if result._action_delete:
            actions.append((t("action_clear_history"), result.delete, True))
            
        root_box.append(PreviewManager._create_action_footer(actions))
        return root_box

    @staticmethod
    def _render_emoji(result: SearchResult) -> Gtk.Widget:
        root_box, content_box = PreviewManager._create_base_structure()
        
        hero_box = PreviewManager._create_hero_container()
        lbl = Gtk.Label(label=result.preview_data.get("char", "❓"))
        lbl.add_css_class("preview-hero-emoji")
        hero_box.append(lbl)
        content_box.append(hero_box)
        
        content_box.append(PreviewManager._create_title_block(
            result.title,
            result.preview_data.get("emoji_category", "")
        ))
        
        grid = PreviewManager._create_meta_grid()
        if result.preview_data.get("unicode_code"):
            grid.attach(PreviewManager._create_meta_card(t("label_desktop_path"), result.preview_data["unicode_code"]), 0, 0, 1, 1)
            
        content_box.append(grid)
        
        actions = []
        if result._action_copy:
            actions.append((t("action_copy"), result.copy_value, False))
        if result._action_open_location:
            actions.append((t("action_copy_path"), result.open_location, False))
            
        root_box.append(PreviewManager._create_action_footer(actions))
        return root_box

    @staticmethod
    def _render_math(result: SearchResult) -> Gtk.Widget:
        root_box, content_box = PreviewManager._create_base_structure()
        hero_box = PreviewManager._create_hero_container()
        
        lbl = Gtk.Label(label=result.preview_data.get("result", ""))
        lbl.add_css_class("preview-hero-text")
        lbl.set_wrap(True)
        lbl.set_max_width_chars(30)
        hero_box.append(lbl)
        content_box.append(hero_box)
        
        content_box.append(PreviewManager._create_title_block(result.title, t("label_result")))
        
        actions = []
        if result._action_copy:
            actions.append((t("action_copy"), result.copy_value, False))
            
        root_box.append(PreviewManager._create_action_footer(actions))
        return root_box

    @staticmethod
    def _render_command(result: SearchResult) -> Gtk.Widget:
        return PreviewManager._render_basic(result)

    @staticmethod
    def _render_basic(result: SearchResult) -> Gtk.Widget:
        root_box, content_box = PreviewManager._create_base_structure()
        hero_box = PreviewManager._create_hero_container()
        hero_box.append(PreviewManager._create_icon(result.icon, 96))
        content_box.append(hero_box)
        
        content_box.append(PreviewManager._create_title_block(result.title, result.subtitle))
        
        actions = []
        if result._action_execute:
            actions.append((t("action_execute"), result.execute, False))
        if result._action_copy:
            actions.append((t("action_copy"), result.copy_value, False))
            
        root_box.append(PreviewManager._create_action_footer(actions))
        return root_box
