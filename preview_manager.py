import os
try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk, Pango
except ValueError:
    pass

from providers import SearchResult
from i18n import t, get_current_language

WEATHER_ICONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'assets', 'icons', 'weather'))

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
        elif cat == "Time":
            return PreviewManager._render_timezone(result)
        elif cat == "Currency":
            return PreviewManager._render_currency(result)
        elif cat == "Weather":
            return PreviewManager._render_weather(result)
            
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
        root_box.set_hexpand(True)
        root_box.add_css_class("preview-root-box")
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        scroll.set_overlay_scrolling(True)
        scroll.set_kinetic_scrolling(True)
        scroll.add_css_class("preview-scrolled-window")
            
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_halign(Gtk.Align.FILL)
        content_box.set_hexpand(True)
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
        from utils import set_icon_safe
        img = Gtk.Image()
        img.set_pixel_size(size)
        img.add_css_class("preview-hero-icon")
        set_icon_safe(img, icon_name, fallback_icon="application-x-executable", pixel_size=size)
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
        
        # Lazy on-demand stat calculation for selected file
        path = result.preview_data.get("path")
        size = result.preview_data.get("size")
        mtime = result.preview_data.get("mtime")
        
        if (not size or not mtime) and path and os.path.exists(path):
            try:
                from datetime import datetime
                stat = os.stat(path)
                bytes_size = stat.st_size
                for unit in ["B", "KB", "MB", "GB", "TB"]:
                    if bytes_size < 1024.0:
                        size = f"{bytes_size:.1f} {unit}"
                        break
                    bytes_size /= 1024.0
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                result.preview_data["size"] = size
                result.preview_data["mtime"] = mtime
            except Exception:
                pass

        grid = PreviewManager._create_meta_grid()
        col = 0
        if size and size != "Unknown":
            grid.attach(PreviewManager._create_meta_card(t("label_size"), size), col, 0, 1, 1)
            col += 1
        if mtime and mtime != "Unknown":
            grid.attach(PreviewManager._create_meta_card(t("label_modified"), mtime), col, 0, 1, 1)
            
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
            grid.attach(PreviewManager._create_meta_card(t("label_unicode"), result.preview_data["unicode_code"]), 0, 0, 1, 1)
            
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

    @staticmethod
    def _render_timezone(result: SearchResult) -> Gtk.Widget:
        root_box, content_box = PreviewManager._create_base_structure()
        data = result.preview_data or {}
        
        hero_box = PreviewManager._create_hero_container()
        time_str = data.get("time_str", result.title)
        
        lbl_time = Gtk.Label(label=time_str)
        lbl_time.add_css_class("preview-timezone-clock")
        hero_box.append(lbl_time)
        content_box.append(hero_box)
        
        city_name = data.get("city_name", result.title)
        country_name = data.get("country", "")
        title_text = f"{city_name}, {country_name}" if country_name else city_name
        subtitle_text = data.get("formatted_date", "")
        content_box.append(PreviewManager._create_title_block(title_text, subtitle_text))
        
        grid = PreviewManager._create_meta_grid()
        
        diff_str = data.get("diff_str", "")
        if diff_str:
            grid.attach(PreviewManager._create_meta_card(t("label_offset"), diff_str), 0, 0, 1, 1)
            
        tz_abbr = data.get("tz_abbr", "")
        utc_offset = data.get("utc_offset", "")
        tz_val = f"{tz_abbr} ({utc_offset})" if tz_abbr and tz_abbr != utc_offset else utc_offset
        if tz_val:
            grid.attach(PreviewManager._create_meta_card(t("label_timezone"), tz_val), 1, 0, 1, 1)
            
        is_day = data.get("is_day", True)
        day_night_str = "День ☀️" if is_day else "Ночь 🌙"
        grid.attach(PreviewManager._create_meta_card(t("label_day_night"), day_night_str), 0, 1, 1, 1)
        
        day_of_week = data.get("day_of_week", "")
        if day_of_week:
            grid.attach(PreviewManager._create_meta_card(t("label_day_of_week"), day_of_week), 1, 1, 1, 1)
            
        content_box.append(grid)
        
        actions = []
        if result._action_copy:
            actions.append((t("time_copy_action"), result.copy_value, False))
            
        root_box.append(PreviewManager._create_action_footer(actions))
        return root_box

    @staticmethod
    def _render_currency(result: SearchResult) -> Gtk.Widget:
        root_box, content_box = PreviewManager._create_base_structure()
        data = result.preview_data or {}

        val_from = data.get("val_from", 1)
        cur_from = data.get("cur_from", "")
        cur_from_name = data.get("cur_from_name", cur_from)
        cur_from_flag = data.get("cur_from_flag", "")
        
        val_to = data.get("val_to", 0)
        cur_to = data.get("cur_to", "")
        cur_to_name = data.get("cur_to_name", cur_to)
        cur_to_flag = data.get("cur_to_flag", "")
        
        str_val_from = data.get("str_val_from", "")
        str_val_to = data.get("str_val_to", "")
        rate_str = data.get("rate_str", "")
        rate_inv_str = data.get("rate_inv_str", "")
        copy_text = data.get("copy_text", str(val_to))
        full_copy_text = data.get("full_copy_text", result.title)

        hero_box = PreviewManager._create_hero_container()
        hero_box.add_css_class("preview-currency-hero")

        val_lbl = Gtk.Label(label=str_val_to)
        val_lbl.add_css_class("preview-currency-hero-value")
        hero_box.append(val_lbl)

        sub_lbl = Gtk.Label(label=f"{str_val_from} = {str_val_to}")
        sub_lbl.add_css_class("preview-currency-hero-sub")
        hero_box.append(sub_lbl)

        content_box.append(hero_box)

        header_title = f"{cur_from_flag} {cur_from}  →  {cur_to_flag} {cur_to}" if (cur_from_flag and cur_to_flag) else f"{cur_from} → {cur_to}"
        content_box.append(PreviewManager._create_title_block(header_title, f"{cur_from_name} → {cur_to_name}"))

        grid = PreviewManager._create_meta_grid()
        lbl_rate = t("label_rate")
        lbl_inv = t("label_inverse_rate")
        lbl_giving = t("label_giving")
        lbl_getting = t("label_getting")

        grid.attach(PreviewManager._create_meta_card(lbl_rate, rate_str), 0, 0, 1, 1)
        grid.attach(PreviewManager._create_meta_card(lbl_inv, rate_inv_str), 1, 0, 1, 1)
        grid.attach(PreviewManager._create_meta_card(lbl_giving, f"{str_val_from}"), 0, 1, 1, 1)
        grid.attach(PreviewManager._create_meta_card(lbl_getting, f"{str_val_to}"), 1, 1, 1, 1)

        content_box.append(grid)

        def _copy_val_action():
            try:
                display = Gdk.Display.get_default()
                if display:
                    display.get_clipboard().set(copy_text)
            except Exception:
                pass

        def _copy_all_action():
            try:
                display = Gdk.Display.get_default()
                if display:
                    display.get_clipboard().set(full_copy_text)
            except Exception:
                pass

        actions = [
            (t("action_copy"), _copy_val_action, False),
            (t("action_copy_all"), _copy_all_action, False)
        ]

        root_box.append(PreviewManager._create_action_footer(actions))
        return root_box

    @staticmethod
    def _make_temp_bar_draw_func(day_min, day_max, overall_min, overall_max, cur_temp=None):
        def draw(area, cr, width, height, user_data):
            try:
                import cairo
                bar_h = 4.0
                bar_y = (height - bar_h) / 2.0
                
                # 1. Background track
                cr.set_source_rgba(1.0, 1.0, 1.0, 0.18)
                cr.arc(bar_h / 2.0, bar_y + bar_h / 2.0, bar_h / 2.0, 1.57, 4.71)
                cr.arc(max(bar_h, width - bar_h / 2.0), bar_y + bar_h / 2.0, bar_h / 2.0, -1.57, 1.57)
                cr.close_path()
                cr.fill()
                
                # 2. Active range
                span = max(1.0, float(overall_max - overall_min))
                x1 = ((float(day_min) - float(overall_min)) / span) * width
                x2 = ((float(day_max) - float(overall_min)) / span) * width
                x1 = max(0.0, min(width - bar_h, x1))
                x2 = max(x1 + bar_h, min(width, x2))
                
                # Spectral Apple-style gradient (Cyan -> Yellow -> Orange)
                pat = cairo.LinearGradient(x1, 0, x2, 0)
                pat.add_color_stop_rgb(0.0, 0.35, 0.78, 0.98)  # Cyan
                pat.add_color_stop_rgb(0.5, 0.96, 0.82, 0.22)  # Sunny Yellow
                pat.add_color_stop_rgb(1.0, 0.98, 0.52, 0.16)  # Warm Orange
                
                cr.set_source(pat)
                cr.arc(x1 + bar_h / 2.0, bar_y + bar_h / 2.0, bar_h / 2.0, 1.57, 4.71)
                cr.arc(x2 - bar_h / 2.0, bar_y + bar_h / 2.0, bar_h / 2.0, -1.57, 1.57)
                cr.close_path()
                cr.fill()
                
                # 3. Current temperature indicator dot (if Today)
                if cur_temp is not None:
                    dot_x = ((float(cur_temp) - float(overall_min)) / span) * width
                    dot_x = max(bar_h / 2.0, min(width - bar_h / 2.0, dot_x))
                    
                    # Outer subtle shadow/glow
                    cr.set_source_rgba(0.0, 0.0, 0.0, 0.35)
                    cr.arc(dot_x, height / 2.0, 4.5, 0, 6.28)
                    cr.fill()
                    
                    # White dot
                    cr.set_source_rgb(1.0, 1.0, 1.0)
                    cr.arc(dot_x, height / 2.0, 3.2, 0, 6.28)
                    cr.fill()
            except Exception as e:
                pass
        return draw

    @staticmethod
    def _make_compass_draw_func(wind_speed, wind_dir_deg, is_ru=True):
        def draw(area, cr, width, height, user_data):
            try:
                import cairo, math
                w = float(width)
                h = float(height)
                cx = w / 2.0
                cy = h / 2.0
                r = min(w, h) / 2.0 - 9.0
                if r <= 5.0:
                    return
                
                # Outer circle
                cr.set_source_rgba(1.0, 1.0, 1.0, 0.22)
                cr.set_line_width(1.5)
                cr.arc(cx, cy, r, 0, 2 * math.pi)
                cr.stroke()
                
                # Cardinal tick marks
                for deg in range(0, 360, 45):
                    rad = math.radians(deg - 90)
                    is_major = (deg % 90 == 0)
                    tick_len = 5.0 if is_major else 3.0
                    x1 = cx + (r - tick_len) * math.cos(rad)
                    y1 = cy + (r - tick_len) * math.sin(rad)
                    x2 = cx + r * math.cos(rad)
                    y2 = cy + r * math.sin(rad)
                    cr.set_source_rgba(1.0, 1.0, 1.0, 0.45 if is_major else 0.22)
                    cr.set_line_width(1.5 if is_major else 1.0)
                    cr.move_to(x1, y1)
                    cr.line_to(x2, y2)
                    cr.stroke()
                
                # Cardinal Labels
                cardinals = [('С', 0), ('В', 90), ('Ю', 180), ('З', 270)] if is_ru else [('N', 0), ('E', 90), ('S', 180), ('W', 270)]
                cr.select_font_face("sans-serif", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                cr.set_font_size(9.0)
                cr.set_source_rgba(1.0, 1.0, 1.0, 0.75)
                for txt, deg in cardinals:
                    rad = math.radians(deg - 90)
                    tx = cx + (r - 11.0) * math.cos(rad)
                    ty = cy + (r - 11.0) * math.sin(rad)
                    ext = cr.text_extents(txt)
                    cr.move_to(tx - ext.width / 2.0, ty + ext.height / 2.0)
                    cr.show_text(txt)
                
                # Direction arrow
                arrow_rad = math.radians(float(wind_dir_deg) - 90.0)
                tip_x = cx + (r - 7.0) * math.cos(arrow_rad)
                tip_y = cy + (r - 7.0) * math.sin(arrow_rad)
                
                cr.new_path()
                cr.move_to(tip_x, tip_y)
                b1_x = cx + 5.5 * math.cos(arrow_rad + 2.5)
                b1_y = cy + 5.5 * math.sin(arrow_rad + 2.5)
                b2_x = cx + 5.5 * math.cos(arrow_rad - 2.5)
                b2_y = cy + 5.5 * math.sin(arrow_rad - 2.5)
                cr.line_to(b1_x, b1_y)
                cr.line_to(cx, cy)
                cr.line_to(b2_x, b2_y)
                cr.close_path()
                
                cr.set_source_rgba(0.4, 0.85, 1.0, 0.95)
                cr.fill()
                
                # Center white dot
                cr.set_source_rgb(1.0, 1.0, 1.0)
                cr.arc(cx, cy, 3.0, 0, 2 * math.pi)
                cr.fill()
            except Exception:
                pass
        return draw

    @staticmethod
    def _make_uv_bar_draw_func(uv_val):
        def draw(area, cr, width, height, user_data):
            try:
                import cairo
                w = float(width)
                h = float(height)
                bar_h = 5.0
                bar_y = (h - bar_h) / 2.0
                
                # Background gradient spectrum
                pat = cairo.LinearGradient(0, 0, w, 0)
                pat.add_color_stop_rgb(0.0, 0.20, 0.85, 0.40)  # Green
                pat.add_color_stop_rgb(0.25, 1.00, 0.85, 0.10) # Yellow
                pat.add_color_stop_rgb(0.50, 1.00, 0.55, 0.10) # Orange
                pat.add_color_stop_rgb(0.75, 1.00, 0.25, 0.20) # Red
                pat.add_color_stop_rgb(1.00, 0.75, 0.35, 0.95) # Purple
                
                cr.set_source(pat)
                cr.arc(bar_h / 2.0, bar_y + bar_h / 2.0, bar_h / 2.0, 1.57, 4.71)
                cr.arc(max(bar_h, w - bar_h / 2.0), bar_y + bar_h / 2.0, bar_h / 2.0, -1.57, 1.57)
                cr.close_path()
                cr.fill()
                
                # Indicator dot
                pct = min(1.0, max(0.0, float(uv_val) / 11.0))
                dot_x = (bar_h / 2.0) + pct * (w - bar_h)
                dot_x = max(4.0, min(w - 4.0, dot_x))
                
                cr.set_source_rgba(0.0, 0.0, 0.0, 0.35)
                cr.arc(dot_x, h / 2.0, 4.5, 0, 6.28)
                cr.fill()
                
                cr.set_source_rgb(1.0, 1.0, 1.0)
                cr.arc(dot_x, h / 2.0, 3.2, 0, 6.28)
                cr.fill()
            except Exception:
                pass
        return draw

    @staticmethod
    def _make_sun_arc_draw_func(sunrise_str, sunset_str, is_day):
        def draw(area, cr, width, height, user_data):
            try:
                import cairo, math
                from datetime import datetime
                w = float(width)
                h = float(height)
                horizon_y = h - 14.0
                
                # Horizon line
                cr.set_source_rgba(1.0, 1.0, 1.0, 0.2)
                cr.set_line_width(1.0)
                cr.move_to(6.0, horizon_y)
                cr.line_to(w - 6.0, horizon_y)
                cr.stroke()
                
                # Arc curve
                p0 = (10.0, horizon_y)
                p1 = (w * 0.28, 8.0)
                p2 = (w * 0.72, 8.0)
                p3 = (w - 10.0, horizon_y)
                
                cr.set_source_rgba(1.0, 0.82, 0.25, 0.75)
                cr.set_line_width(2.0)
                cr.new_path()
                cr.move_to(p0[0], p0[1])
                cr.curve_to(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])
                cr.stroke()
                
                # Sun position calculation
                now = datetime.now()
                now_m = now.hour * 60 + now.minute
                
                sr_parts = str(sunrise_str).split(':')
                ss_parts = str(sunset_str).split(':')
                sr_m = int(sr_parts[0]) * 60 + int(sr_parts[1]) if len(sr_parts) >= 2 else 360
                ss_m = int(ss_parts[0]) * 60 + int(ss_parts[1]) if len(ss_parts) >= 2 else 1200
                
                if sr_m <= now_m <= ss_m:
                    t = max(0.0, min(1.0, (now_m - sr_m) / max(1.0, float(ss_m - sr_m))))
                    sx = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
                    sy = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
                    
                    cr.set_source_rgba(1.0, 0.85, 0.2, 0.35)
                    cr.arc(sx, sy, 7.0, 0, 2 * math.pi)
                    cr.fill()
                    
                    cr.set_source_rgba(1.0, 0.95, 0.5, 1.0)
                    cr.arc(sx, sy, 4.0, 0, 2 * math.pi)
                    cr.fill()
                else:
                    sx = w / 2.0
                    sy = horizon_y + 4.0
                    cr.set_source_rgba(0.7, 0.8, 1.0, 0.4)
                    cr.arc(sx, sy, 3.5, 0, 2 * math.pi)
                    cr.fill()
            except Exception:
                pass
        return draw

    @staticmethod
    def _make_moon_draw_func(cycle_fraction, illumination):
        def draw(area, cr, width, height, user_data):
            try:
                import cairo, math
                w = float(width)
                h = float(height)
                cx = w / 2.0
                cy = h / 2.0
                r = min(w, h) / 2.0 - 4.0
                if r <= 5.0:
                    return
                
                # Dark sphere base
                cr.set_source_rgba(0.12, 0.14, 0.18, 0.95)
                cr.arc(cx, cy, r, 0, 2 * math.pi)
                cr.fill()
                
                frac = float(cycle_fraction) % 1.0
                phi = frac * 2.0 * math.pi
                cos_phi = math.cos(phi)
                
                # Lit portion
                cr.save()
                cr.arc(cx, cy, r, 0, 2 * math.pi)
                cr.clip()
                
                pat = cairo.RadialGradient(cx - r * 0.3, cy - r * 0.3, r * 0.1, cx, cy, r)
                pat.add_color_stop_rgba(0.0, 0.98, 0.98, 1.0, 1.0)
                pat.add_color_stop_rgba(0.8, 0.88, 0.90, 0.95, 0.98)
                pat.add_color_stop_rgba(1.0, 0.75, 0.78, 0.85, 0.95)
                cr.set_source(pat)
                
                N = 28
                if 0.0 < frac < 0.5:
                    cr.new_path()
                    cr.arc(cx, cy, r, -math.pi / 2.0, math.pi / 2.0)
                    for i in range(N, -1, -1):
                        theta = -math.pi / 2.0 + (math.pi * i / N)
                        y = cy + r * math.sin(theta)
                        x = cx - r * cos_phi * math.cos(theta)
                        cr.line_to(x, y)
                    cr.close_path()
                    cr.fill()
                elif 0.5 <= frac < 1.0:
                    cr.new_path()
                    cr.arc(cx, cy, r, math.pi / 2.0, 3 * math.pi / 2.0)
                    for i in range(N, -1, -1):
                        theta = math.pi / 2.0 + (math.pi * i / N)
                        y = cy + r * math.sin(theta)
                        x = cx + r * cos_phi * math.cos(theta)
                        cr.line_to(x, y)
                    cr.close_path()
                    cr.fill()
                
                # Subtle lunar crater spots
                cr.set_source_rgba(0.2, 0.22, 0.28, 0.15)
                cr.arc(cx - r * 0.3, cy - r * 0.2, r * 0.15, 0, 2 * math.pi)
                cr.fill()
                cr.arc(cx + r * 0.2, cy + r * 0.25, r * 0.12, 0, 2 * math.pi)
                cr.fill()
                cr.arc(cx - r * 0.1, cy + r * 0.4, r * 0.18, 0, 2 * math.pi)
                cr.fill()
                cr.restore()
                
                # Outer delicate rim glow
                cr.set_source_rgba(1.0, 1.0, 1.0, 0.25)
                cr.set_line_width(1.0)
                cr.arc(cx, cy, r, 0, 2 * math.pi)
                cr.stroke()
            except Exception:
                pass
        return draw

    @staticmethod
    def _make_pressure_gauge_draw_func(pressure_mm):
        def draw(area, cr, width, height, user_data):
            try:
                import cairo, math
                w = float(width)
                h = float(height)
                cx = w / 2.0
                cy = h / 2.0 + 3.0
                r = min(w, h) / 2.0 - 8.0
                if r <= 5.0:
                    return
                
                start_ang = 2.443  # ~140 deg
                end_ang = 6.981    # ~400 deg (260 deg total)
                
                # Gauge background track
                cr.set_source_rgba(1.0, 1.0, 1.0, 0.18)
                cr.set_line_width(3.5)
                cr.arc(cx, cy, r, start_ang, end_ang)
                cr.stroke()
                
                # Active pressure arc
                p = float(pressure_mm)
                pct = max(0.0, min(1.0, (p - 720.0) / 60.0))
                val_ang = start_ang + pct * (end_ang - start_ang)
                
                cr.set_source_rgba(0.35, 0.78, 0.98, 0.85)
                cr.set_line_width(3.5)
                cr.arc(cx, cy, r, start_ang, val_ang)
                cr.stroke()
                
                # Needle line & center
                nx = cx + (r - 2.0) * math.cos(val_ang)
                ny = cy + (r - 2.0) * math.sin(val_ang)
                
                cr.set_source_rgb(1.0, 1.0, 1.0)
                cr.set_line_width(1.5)
                cr.move_to(cx, cy)
                cr.line_to(nx, ny)
                cr.stroke()
                
                # Center hub
                cr.arc(cx, cy, 2.5, 0, 2 * math.pi)
                cr.fill()
            except Exception:
                pass
        return draw

    @staticmethod
    def _create_weather_bento_card(icon_svg: str, title: str) -> tuple[Gtk.Box, Gtk.Box]:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.add_css_class("weather-bento-card")
        
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hdr.add_css_class("weather-bento-header")
        icon_path = os.path.join(WEATHER_ICONS_DIR, icon_svg)
        if os.path.exists(icon_path):
            img = Gtk.Image.new_from_file(icon_path)
            img.set_pixel_size(13)
            img.set_valign(Gtk.Align.CENTER)
            hdr.append(img)
        lbl = Gtk.Label(label=title)
        lbl.add_css_class("weather-bento-title")
        lbl.set_xalign(0.0)
        hdr.append(lbl)
        card.append(hdr)
        
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        body.set_vexpand(True)
        card.append(body)
        return card, body

    @staticmethod
    def _build_weather_bento_grid(data: dict, temp_val: int, lang: str, is_ru: bool) -> Gtk.Grid:
        grid = Gtk.Grid()
        grid.add_css_class("weather-bento-grid")
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(False)
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        
        # 1. Feels Like
        feels_like = data.get("feels_like", temp_val)
        card_feels, body_feels = PreviewManager._create_weather_bento_card("thermometer.svg", "ОЩУЩАЕТСЯ КАК" if is_ru else "FEELS LIKE")
        val_feels = Gtk.Label(label=f"{feels_like}°")
        val_feels.add_css_class("weather-bento-val-large")
        val_feels.set_xalign(0.0)
        body_feels.append(val_feels)
        sp1 = Gtk.Box()
        sp1.set_vexpand(True)
        body_feels.append(sp1)
        desc_text = data.get("feels_like_desc") or ("Похоже на фактическую температуру." if is_ru else "Similar to actual temperature.")
        lbl_desc = Gtk.Label(label=desc_text)
        lbl_desc.add_css_class("weather-bento-desc")
        lbl_desc.set_wrap(True)
        lbl_desc.set_xalign(0.0)
        body_feels.append(lbl_desc)
        grid.attach(card_feels, 0, 0, 1, 1)
        
        # 2. Average Norm
        avg_diff = data.get("avg_diff_str", "0°")
        card_avg, body_avg = PreviewManager._create_weather_bento_card("chart-norm.svg", "В СРЕДНЕМ" if is_ru else "AVERAGES")
        val_avg = Gtk.Label(label=str(avg_diff))
        val_avg.add_css_class("weather-bento-val-large")
        val_avg.set_xalign(0.0)
        body_avg.append(val_avg)
        sp2 = Gtk.Box()
        sp2.set_vexpand(True)
        body_avg.append(sp2)
        desc_avg = data.get("avg_desc") or ("соответствует норме" if is_ru else "matches average")
        lbl_desc_avg = Gtk.Label(label=desc_avg)
        lbl_desc_avg.add_css_class("weather-bento-desc")
        lbl_desc_avg.set_wrap(True)
        lbl_desc_avg.set_xalign(0.0)
        body_avg.append(lbl_desc_avg)
        grid.attach(card_avg, 1, 0, 1, 1)
        
        # 3. Wind (spans 2 columns)
        wind_spd = data.get("wind_speed", 0)
        wind_gust = data.get("wind_gusts", wind_spd)
        wind_dir = data.get("wind_direction", 0)
        wind_card, body_wind = PreviewManager._create_weather_bento_card("wind.svg", "ВЕТЕР" if is_ru else "WIND")
        w_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        w_left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        w_left.set_hexpand(True)
        
        s_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        lbl_spd = Gtk.Label(label=str(wind_spd))
        lbl_spd.add_css_class("weather-bento-val-hero")
        s_row.append(lbl_spd)
        lbl_spd_u = Gtk.Label(label="км/ч\nВЕТЕР" if is_ru else "km/h\nWIND")
        lbl_spd_u.add_css_class("weather-bento-unit")
        s_row.append(lbl_spd_u)
        w_left.append(s_row)
        
        div_w = Gtk.Box()
        div_w.add_css_class("weather-bento-divider")
        w_left.append(div_w)
        
        lbl_gust = Gtk.Label(label=f"{wind_gust} км/ч  ПОРЫВЫ" if is_ru else f"{wind_gust} km/h  GUSTS")
        lbl_gust.add_css_class("weather-bento-subval")
        lbl_gust.set_xalign(0.0)
        w_left.append(lbl_gust)
        
        w_desc = data.get("wind_desc") or ("Северо-западный ветер" if is_ru else "Northwest wind")
        lbl_w_desc = Gtk.Label(label=w_desc)
        lbl_w_desc.add_css_class("weather-bento-desc")
        lbl_w_desc.set_wrap(True)
        lbl_w_desc.set_xalign(0.0)
        w_left.append(lbl_w_desc)
        w_row.append(w_left)
        
        da_compass = Gtk.DrawingArea()
        da_compass.set_content_width(86)
        da_compass.set_content_height(86)
        da_compass.set_halign(Gtk.Align.END)
        da_compass.set_valign(Gtk.Align.CENTER)
        da_compass.set_draw_func(PreviewManager._make_compass_draw_func(wind_spd, wind_dir, is_ru), None)
        w_row.append(da_compass)
        body_wind.append(w_row)
        grid.attach(wind_card, 0, 1, 2, 1)
        
        # 4. UV Index
        uv_idx = data.get("uv_index", 0.0)
        uv_lvl = data.get("uv_level", "Низкий" if is_ru else "Low")
        card_uv, body_uv = PreviewManager._create_weather_bento_card("sun-uv.svg", "УФ-ИНДЕКС" if is_ru else "UV INDEX")
        uv_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        lbl_uv_val = Gtk.Label(label=str(round(uv_idx)))
        lbl_uv_val.add_css_class("weather-bento-val-large")
        uv_row.append(lbl_uv_val)
        lbl_uv_lvl = Gtk.Label(label=uv_lvl)
        lbl_uv_lvl.add_css_class("weather-bento-val-level")
        lbl_uv_lvl.set_valign(Gtk.Align.END)
        uv_row.append(lbl_uv_lvl)
        body_uv.append(uv_row)
        
        da_uv = Gtk.DrawingArea()
        da_uv.set_content_width(110)
        da_uv.set_content_height(14)
        da_uv.set_hexpand(True)
        da_uv.set_draw_func(PreviewManager._make_uv_bar_draw_func(uv_idx), None)
        body_uv.append(da_uv)
        
        sp3 = Gtk.Box()
        sp3.set_vexpand(True)
        body_uv.append(sp3)
        uv_desc = data.get("uv_desc") or ("Низкий уровень" if is_ru else "Low levels")
        lbl_uv_desc = Gtk.Label(label=uv_desc)
        lbl_uv_desc.add_css_class("weather-bento-desc")
        lbl_uv_desc.set_wrap(True)
        lbl_uv_desc.set_xalign(0.0)
        body_uv.append(lbl_uv_desc)
        grid.attach(card_uv, 0, 2, 1, 1)
        
        # 5. Sun Arc
        is_day = (data.get("is_day", 1) == 1)
        sr_str = data.get("sunrise_str", "06:00")
        ss_str = data.get("sunset_str", "20:00")
        sun_title = ("ЗАКАТ" if is_ru else "SUNSET") if is_day else ("ВОСХОД" if is_ru else "SUNRISE")
        card_sun, body_sun = PreviewManager._create_weather_bento_card("sunset.svg", sun_title)
        lbl_sun = Gtk.Label(label=ss_str if is_day else sr_str)
        lbl_sun.add_css_class("weather-bento-val-large")
        lbl_sun.set_xalign(0.0)
        body_sun.append(lbl_sun)
        
        da_sun = Gtk.DrawingArea()
        da_sun.set_content_width(110)
        da_sun.set_content_height(44)
        da_sun.set_hexpand(True)
        da_sun.set_draw_func(PreviewManager._make_sun_arc_draw_func(sr_str, ss_str, is_day), None)
        body_sun.append(da_sun)
        
        sun_desc = (f"Восход: {sr_str}" if is_ru else f"Sunrise: {sr_str}") if is_day else (f"Закат: {ss_str}" if is_ru else f"Sunset: {ss_str}")
        lbl_sun_desc = Gtk.Label(label=sun_desc)
        lbl_sun_desc.add_css_class("weather-bento-desc")
        lbl_sun_desc.set_xalign(0.0)
        body_sun.append(lbl_sun_desc)
        grid.attach(card_sun, 1, 2, 1, 1)
        
        # 6. Precipitation
        precip = data.get("precipitation", 0.0)
        card_p, body_p = PreviewManager._create_weather_bento_card("rain-drop.svg", "ОСАДКИ" if is_ru else "PRECIPITATION")
        lbl_p_val = Gtk.Label(label=f"{precip} мм" if is_ru else f"{precip} mm")
        lbl_p_val.add_css_class("weather-bento-val-large")
        lbl_p_val.set_xalign(0.0)
        body_p.append(lbl_p_val)
        lbl_p_sub = Gtk.Label(label="за последние 24 ч." if is_ru else "in last 24 h")
        lbl_p_sub.add_css_class("weather-bento-sublabel")
        lbl_p_sub.set_xalign(0.0)
        body_p.append(lbl_p_sub)
        sp4 = Gtk.Box()
        sp4.set_vexpand(True)
        body_p.append(sp4)
        p_desc = data.get("precip_desc") or ("Осадки не ожидаются." if is_ru else "No precipitation expected.")
        lbl_p_desc = Gtk.Label(label=p_desc)
        lbl_p_desc.add_css_class("weather-bento-desc")
        lbl_p_desc.set_wrap(True)
        lbl_p_desc.set_xalign(0.0)
        body_p.append(lbl_p_desc)
        grid.attach(card_p, 0, 3, 1, 1)
        
        # 7. Visibility
        vis_km = data.get("visibility_km", 10)
        card_v, body_v = PreviewManager._create_weather_bento_card("eye.svg", "ВИДИМОСТЬ" if is_ru else "VISIBILITY")
        lbl_v_val = Gtk.Label(label=f"{vis_km} км" if is_ru else f"{vis_km} km")
        lbl_v_val.add_css_class("weather-bento-val-large")
        lbl_v_val.set_xalign(0.0)
        body_v.append(lbl_v_val)
        sp5 = Gtk.Box()
        sp5.set_vexpand(True)
        body_v.append(sp5)
        v_desc = data.get("visibility_desc") or ("Отличная видимость." if is_ru else "Perfect visibility.")
        lbl_v_desc = Gtk.Label(label=v_desc)
        lbl_v_desc.add_css_class("weather-bento-desc")
        lbl_v_desc.set_wrap(True)
        lbl_v_desc.set_xalign(0.0)
        body_v.append(lbl_v_desc)
        grid.attach(card_v, 1, 3, 1, 1)
        
        # 8. Moon Phase (spans 2 columns)
        moon = data.get("moon_phase") or {}
        p_name = moon.get("phase_name", "Старая луна") if is_ru else moon.get("phase_name_en", "Waning Crescent")
        illum = moon.get("illumination", 14)
        days_full = moon.get("days_to_full", 18)
        cycle_frac = moon.get("cycle_fraction", 0.88)
        card_m, body_m = PreviewManager._create_weather_bento_card("moon.svg", "ФАЗА ЛУНЫ" if is_ru else "MOON PHASE")
        m_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        m_left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        m_left.set_hexpand(True)
        lbl_m_title = Gtk.Label(label=p_name)
        lbl_m_title.add_css_class("weather-bento-moon-title")
        lbl_m_title.set_xalign(0.0)
        m_left.append(lbl_m_title)
        lbl_m_illum = Gtk.Label(label=f"Освещенность: {illum}%" if is_ru else f"Illumination: {illum}%")
        lbl_m_illum.add_css_class("weather-bento-moon-info")
        lbl_m_illum.set_xalign(0.0)
        m_left.append(lbl_m_illum)
        div_m = Gtk.Box()
        div_m.add_css_class("weather-bento-divider")
        m_left.append(div_m)
        lbl_m_full = Gtk.Label(label=f"Следующее полнолуние через {days_full} дн." if is_ru else f"Next full moon in {days_full} days")
        lbl_m_full.add_css_class("weather-bento-desc")
        lbl_m_full.set_wrap(True)
        lbl_m_full.set_xalign(0.0)
        m_left.append(lbl_m_full)
        m_row.append(m_left)
        
        da_moon = Gtk.DrawingArea()
        da_moon.set_content_width(74)
        da_moon.set_content_height(74)
        da_moon.set_halign(Gtk.Align.END)
        da_moon.set_valign(Gtk.Align.CENTER)
        da_moon.set_draw_func(PreviewManager._make_moon_draw_func(cycle_frac, illum), None)
        m_row.append(da_moon)
        body_m.append(m_row)
        grid.attach(card_m, 0, 4, 2, 1)
        
        # 9. Humidity
        hum = data.get("humidity", 50)
        dew = data.get("dew_point", 10)
        card_h, body_h = PreviewManager._create_weather_bento_card("humidity.svg", "ВЛАЖНОСТЬ" if is_ru else "HUMIDITY")
        lbl_h_val = Gtk.Label(label=f"{hum}%")
        lbl_h_val.add_css_class("weather-bento-val-large")
        lbl_h_val.set_xalign(0.0)
        body_h.append(lbl_h_val)
        sp6 = Gtk.Box()
        sp6.set_vexpand(True)
        body_h.append(sp6)
        h_desc = f"Точка росы сейчас {dew}°." if is_ru else f"The dew point is {dew}° right now."
        lbl_h_desc = Gtk.Label(label=h_desc)
        lbl_h_desc.add_css_class("weather-bento-desc")
        lbl_h_desc.set_wrap(True)
        lbl_h_desc.set_xalign(0.0)
        body_h.append(lbl_h_desc)
        grid.attach(card_h, 0, 5, 1, 1)
        
        # 10. Pressure
        press = data.get("pressure_mm", 750)
        press_desc = data.get("pressure_desc") or ("Нормальное давление." if is_ru else "Normal pressure.")
        card_pr, body_pr = PreviewManager._create_weather_bento_card("gauge.svg", "ДАВЛЕНИЕ" if is_ru else "PRESSURE")
        pr_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        pr_left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        pr_left.set_hexpand(True)
        lbl_pr_val = Gtk.Label(label=str(press))
        lbl_pr_val.add_css_class("weather-bento-val-large")
        lbl_pr_val.set_xalign(0.0)
        pr_left.append(lbl_pr_val)
        lbl_pr_u = Gtk.Label(label="мм рт. ст." if is_ru else "mmHg")
        lbl_pr_u.add_css_class("weather-bento-unit")
        lbl_pr_u.set_xalign(0.0)
        pr_left.append(lbl_pr_u)
        lbl_pr_desc = Gtk.Label(label=press_desc)
        lbl_pr_desc.add_css_class("weather-bento-desc")
        lbl_pr_desc.set_wrap(True)
        lbl_pr_desc.set_xalign(0.0)
        pr_left.append(lbl_pr_desc)
        pr_row.append(pr_left)
        
        da_press = Gtk.DrawingArea()
        da_press.set_content_width(70)
        da_press.set_content_height(70)
        da_press.set_halign(Gtk.Align.END)
        da_press.set_valign(Gtk.Align.CENTER)
        da_press.set_draw_func(PreviewManager._make_pressure_gauge_draw_func(press), None)
        pr_row.append(da_press)
        body_pr.append(pr_row)
        grid.attach(card_pr, 1, 5, 1, 1)
        
        return grid

    @staticmethod
    def _render_weather(result: SearchResult) -> Gtk.Widget:
        from providers.weather import get_condition_text, get_weekday_name
        root_box, content_box = PreviewManager._create_base_structure()
        data = result.preview_data or {}
        
        bg_class = data.get("bg_class", "weather-bg-clear-day")
        root_box.add_css_class("preview-weather-full-bg")
        root_box.add_css_class(bg_class)
        
        content_box.set_spacing(10)
        content_box.add_css_class("weather-content-pad")
        
        lang = get_current_language()
        is_ru = (lang == 'ru')
        
        if scroll := root_box.get_first_child():
            scroll.add_css_class("weather-scrolled-window")

        # 1. Hero Header Section
        hero_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        hero_box.set_halign(Gtk.Align.CENTER)
        hero_box.add_css_class("weather-hero-box")
        
        # City Name
        city_name = data.get("city_name", result.title)
        if is_ru and data.get("name_ru"):
            city_name = data.get("name_ru")
        elif not is_ru and data.get("name_en"):
            city_name = data.get("name_en")
        lbl_city = Gtk.Label(label=city_name)
        lbl_city.add_css_class("weather-hero-city")
        hero_box.append(lbl_city)
        
        # Giant Temperature (72px thin font)
        temp_val = data.get("temp", 24)
        lbl_temp = Gtk.Label(label=f"{temp_val}°")
        lbl_temp.add_css_class("weather-hero-temp")
        hero_box.append(lbl_temp)
        
        # Condition
        w_code = data.get("weather_code", 0)
        is_day = bool(data.get("is_day", 1))
        cond_text = get_condition_text(w_code, lang=lang, is_day=is_day)
        lbl_cond = Gtk.Label(label=cond_text)
        lbl_cond.add_css_class("weather-hero-condition")
        hero_box.append(lbl_cond)
        
        # Extremes
        t_min = data.get("temp_min", 9)
        t_max = data.get("temp_max", 25)
        lbl_extremes = Gtk.Label(label=t("weather_high_low", high=t_max, low=t_min))
        lbl_extremes.add_css_class("weather-hero-extremes")
        hero_box.append(lbl_extremes)
        
        content_box.append(hero_box)
        
        # 2. Hourly Forecast Frosted Glass Card
        hourly_items = data.get("hourly", [])
        max_gust = data.get("wind_gusts", round(data.get("wind_speed", 0)))
        
        # Dynamic localized summary
        if is_day and w_code in (0, 1):
            summary = t("weather_summary_clear_day", gust=max_gust)
        elif not is_day and w_code in (0, 1):
            summary = t("weather_summary_clear_night", gust=max_gust)
        else:
            summary = t("weather_summary_generic", gust=max_gust, condition=cond_text)
            
        if hourly_items or summary:
            hourly_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            hourly_card.add_css_class("weather-glass-card")
            
            if summary:
                lbl_sum = Gtk.Label(label=summary)
                lbl_sum.add_css_class("weather-summary-text")
                lbl_sum.set_wrap(True)
                lbl_sum.set_xalign(0.0)
                hourly_card.append(lbl_sum)
                
                div = Gtk.Box()
                div.add_css_class("weather-card-divider")
                hourly_card.append(div)
                
            if hourly_items:
                scroll_h = Gtk.ScrolledWindow()
                scroll_h.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
                scroll_h.set_hexpand(True)
                hscrollbar = scroll_h.get_hscrollbar()
                if hscrollbar:
                    hscrollbar.set_visible(False)
                    
                h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
                h_box.add_css_class("weather-hourly-box")
                
                for idx, h in enumerate(hourly_items):
                    col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                    col.add_css_class("weather-hourly-col")
                    
                    if idx == 0 or h.get("is_now"):
                        lbl_t_text = t("weather_now")
                    elif h.get("hour_num") is not None:
                        lbl_t_text = f"{h.get('hour_num'):02d}"
                    else:
                        lbl_t_text = str(h.get("time", ""))
                        
                    lbl_t = Gtk.Label(label=lbl_t_text)
                    lbl_t.add_css_class("weather-hourly-time")
                    col.append(lbl_t)
                    
                    icon_file = h.get("icon_file")
                    if icon_file and os.path.exists(icon_file):
                        img = Gtk.Image.new_from_file(icon_file)
                        img.set_pixel_size(24)
                        col.append(img)
                        
                    lbl_tmp = Gtk.Label(label=f"{h.get('temp', 0)}°")
                    lbl_tmp.add_css_class("weather-hourly-temp")
                    col.append(lbl_tmp)
                    
                    h_box.append(col)
                    
                scroll_h.set_child(h_box)
                hourly_card.append(scroll_h)
                
            content_box.append(hourly_card)
            
        # 3. 10-Day Forecast Frosted Glass Card
        daily_items = data.get("daily", [])
        if daily_items:
            daily_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            daily_card.add_css_class("weather-glass-card")
            
            hdr_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            cal_path = os.path.join(WEATHER_ICONS_DIR, "calendar.svg")
            if os.path.exists(cal_path):
                cal_img = Gtk.Image.new_from_file(cal_path)
                cal_img.set_pixel_size(13)
                cal_img.set_valign(Gtk.Align.CENTER)
                hdr_box.append(cal_img)
            lbl_hdr = Gtk.Label(label=t("weather_10_day_forecast"))
            lbl_hdr.add_css_class("weather-section-title")
            hdr_box.append(lbl_hdr)
            daily_card.append(hdr_box)
            
            div2 = Gtk.Box()
            div2.add_css_class("weather-card-divider")
            daily_card.append(div2)
            
            overall_min = data.get("overall_min", 0)
            overall_max = data.get("overall_max", 30)
            
            for idx, d in enumerate(daily_items):
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                row.add_css_class("weather-daily-row")
                
                if idx == 0:
                    day_text = t("weather_today")
                else:
                    w_idx = d.get("weekday_idx")
                    if w_idx is None:
                        raw_day = str(d.get("day", ""))
                        weekday_map = {
                            'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6,
                            'Пн': 0, 'Вт': 1, 'Ср': 2, 'Чт': 3, 'Пт': 4, 'Сб': 5, 'Вс': 6,
                        }
                        if raw_day in weekday_map:
                            w_idx = weekday_map[raw_day]
                        else:
                            from datetime import datetime
                            w_idx = (datetime.now().weekday() + idx) % 7
                    day_text = get_weekday_name(w_idx, lang=lang)
                    
                lbl_d = Gtk.Label(label=day_text)
                lbl_d.add_css_class("weather-daily-day")
                lbl_d.set_xalign(0.0)
                lbl_d.set_size_request(60, 20)
                row.append(lbl_d)
                
                icon_file = d.get("icon_file")
                if icon_file and os.path.exists(icon_file):
                    img = Gtk.Image.new_from_file(icon_file)
                    img.set_pixel_size(18)
                    row.append(img)
                    
                d_min = d.get("min", 0)
                d_max = d.get("max", 0)
                
                lbl_min = Gtk.Label(label=f"{d_min}°")
                lbl_min.add_css_class("weather-daily-temp-min")
                lbl_min.set_xalign(1.0)
                lbl_min.set_size_request(28, 20)
                row.append(lbl_min)
                
                # Cairo Temperature Range Bar
                da = Gtk.DrawingArea()
                da.set_content_width(76)
                da.set_content_height(14)
                da.set_hexpand(True)
                is_today = (idx == 0)
                cur_t = temp_val if is_today else None
                da.set_draw_func(
                    PreviewManager._make_temp_bar_draw_func(d_min, d_max, overall_min, overall_max, cur_t),
                    None
                )
                row.append(da)
                
                lbl_max = Gtk.Label(label=f"{d_max}°")
                lbl_max.add_css_class("weather-daily-temp-max")
                lbl_max.set_xalign(0.0)
                lbl_max.set_size_request(28, 20)
                row.append(lbl_max)
                
                daily_card.append(row)
                
                if idx < len(daily_items) - 1:
                    row_div = Gtk.Box()
                    row_div.add_css_class("weather-row-divider")
                    daily_card.append(row_div)
                    
            content_box.append(daily_card)
            
        # 4. Apple Weather Bento Grid (10 Rich Cards)
        bento_grid = PreviewManager._build_weather_bento_grid(data, temp_val, lang, is_ru)
        content_box.append(bento_grid)
        
        # 5. Action Footer
        actions = []
        if result._action_copy:
            copy_val = f"{city_name}: {temp_val:+d}°, {cond_text} (↓ {t_min}° ↑ {t_max}°)"
            def _copy_forecast_action():
                try:
                    display = Gdk.Display.get_default()
                    if display:
                        display.get_clipboard().set(copy_val)
                except Exception:
                    pass
            actions.append((t("weather_copy_action"), _copy_forecast_action, False))
        footer = PreviewManager._create_action_footer(actions)
        footer.add_css_class("weather-action-box")
        content_box.append(footer)
        return root_box
