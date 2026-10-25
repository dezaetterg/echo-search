import collections
import hashlib
import os
import threading
from pathlib import Path

try:
    import gi
    gi.require_version('GnomeDesktop', '4.0')
    from gi.repository import GnomeDesktop
    preview_thumbnail_factory = GnomeDesktop.DesktopThumbnailFactory()
except (ValueError, ImportError):
    preview_thumbnail_factory = None

try:
    gi.require_version('GdkPixbuf', '2.0')
    from gi.repository import GdkPixbuf
except (ValueError, ImportError):
    GdkPixbuf = None

_PREVIEW_THUMBNAIL_CACHE = collections.OrderedDict()
_PREVIEW_CACHE_LIMIT = 150

def _load_file_thumbnail_pixbuf(path: str, mime: str = "", target_size: int = 280):
    if not path or not os.path.exists(path):
        return None

    if path in _PREVIEW_THUMBNAIL_CACHE:
        pix = _PREVIEW_THUMBNAIL_CACHE[path]
        _PREVIEW_THUMBNAIL_CACHE.move_to_end(path)
        return pix

    pixbuf = None
    ext = os.path.splitext(path)[1].lower()
    image_exts = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".svgz", ".gif", ".bmp", ".ico", ".tiff", ".avif", ".heic"}

    # 1. Direct load for images and vector graphics
    if GdkPixbuf and (ext in image_exts or (mime and mime.startswith("image/"))):
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, target_size, target_size, True)
        except Exception as e:
            logger.debug("Direct image thumbnail load failed: %s", e)

    # 2. Freedesktop thumbnail cache lookup (~/.cache/thumbnails/{large,x-large,normal})
    if not pixbuf and GdkPixbuf:
        try:
            uri = Path(path).as_uri()
            h = hashlib.md5(uri.encode("utf-8")).hexdigest()
            for subdir in ("large", "x-large", "normal"):
                thumb_path = os.path.expanduser(f"~/.cache/thumbnails/{subdir}/{h}.png")
                if os.path.exists(thumb_path):
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(thumb_path, target_size, target_size, True)
                    break
        except Exception as e:
            logger.debug("Freedesktop thumbnail cache lookup failed: %s", e)

    # 3. GnomeDesktop.DesktopThumbnailFactory for other files (PDF, videos, docs)
    if not pixbuf and GdkPixbuf and preview_thumbnail_factory and mime and "unknown" not in mime:
        try:
            uri = Path(path).as_uri()
            mtime = int(os.path.getmtime(path))
            if not preview_thumbnail_factory.has_valid_failed_thumbnail(uri, mtime):
                thumb_path = preview_thumbnail_factory.lookup(uri, mtime)
                if thumb_path and os.path.exists(thumb_path):
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(thumb_path, target_size, target_size, True)
                elif preview_thumbnail_factory.can_thumbnail(uri, mime, mtime):
                    generated = preview_thumbnail_factory.generate_thumbnail(uri, mime)
                    if generated:
                        try:
                            preview_thumbnail_factory.save_thumbnail(generated, uri, mtime)
                        except Exception:
                            pass
                        pixbuf = generated.scale_simple(target_size, target_size, GdkPixbuf.InterpType.BILINEAR)
        except Exception as e:
            logger.debug("DesktopThumbnailFactory generation failed: %s", e)

    if pixbuf:
        _PREVIEW_THUMBNAIL_CACHE[path] = pixbuf
        if len(_PREVIEW_THUMBNAIL_CACHE) > _PREVIEW_CACHE_LIMIT:
            _PREVIEW_THUMBNAIL_CACHE.popitem(last=False)

    return pixbuf

try:
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Gdk', '4.0')
    from gi.repository import Gdk, GLib, Gtk, Pango
except ValueError:
    pass

from i18n import get_current_language, t
from logger import get_logger
from providers import SearchResult
from providers.weather import convert_temp, convert_temp_diff, format_temp
from utils import set_clipboard_text

logger = get_logger("preview_manager")

WEATHER_ICONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'assets', 'icons', 'weather'))

def launch_echo_weather(city_name: str = "") -> bool:
    """Launch standalone Echo Weather application with optional target city."""
    import shutil
    import subprocess
    args = [city_name] if city_name else []

    # 1. System path
    exe = shutil.which("echo-weather")
    if exe:
        try:
            subprocess.Popen([exe] + args)
            return True
        except Exception as e:
            logger.debug(f"Failed to launch via {exe}: {e}")

    # 2. External project echo-weather
    user_project_main = os.path.expanduser("~/echo_project/echo-weather/main.py")
    if os.path.exists(user_project_main):
        try:
            subprocess.Popen(["python3", user_project_main] + args)
            return True
        except Exception as e:
            logger.debug(f"Failed to launch via {user_project_main}: {e}")

    # 3. User local installation
    local_main = os.path.expanduser("~/.local/share/echo-weather/main.py")
    if os.path.exists(local_main):
        try:
            subprocess.Popen(["python3", local_main] + args)
            return True
        except Exception as e:
            logger.debug(f"Failed to launch via {local_main}: {e}")

    logger.warning("Could not locate Echo Weather application executable.")
    return False




APP_CAT_I18N = {
    "utility": "cat_utilities",
    "utilities": "cat_utilities",
    "development": "cat_development",
    "game": "cat_games",
    "games": "cat_games",
    "network": "cat_internet",
    "internet": "cat_internet",
    "webbrowser": "cat_internet",
    "office": "cat_office",
    "graphics": "cat_graphics",
    "audiovideo": "cat_multimedia",
    "audio": "cat_audio",
    "video": "cat_videos",
    "multimedia": "cat_multimedia",
    "system": "cat_system",
    "settings": "provider_cat_settings",
    "accessories": "cat_utilities",
    "documents": "cat_documents",
    "2dgraphics": "cat_2d_graphics",
    "rastergraphics": "cat_raster_graphics",
    "rastereditor": "cat_raster_graphics",
    "vectorgraphics": "cat_vector_graphics",
    "vectoreditor": "cat_vector_graphics",
    "3dgraphics": "cat_3d_graphics",
    "photography": "cat_photography",
    "publishing": "cat_publishing",
    "viewer": "cat_viewer",
    "texteditor": "cat_text_editor",
    "terminalemulator": "cat_terminal",
    "terminal": "cat_terminal",
    "filemanager": "cat_file_manager",
    "filetransfer": "cat_file_transfer",
    "email": "cat_email",
    "chat": "cat_chat",
    "instantmessaging": "cat_chat",
    "ide": "cat_ide",
    "player": "cat_player",
    "audioplayer": "cat_player",
    "videoplayer": "cat_player",
    "recorder": "cat_recorder",
    "audiovideoediting": "cat_media_editor",
    "spreadsheet": "cat_spreadsheet",
    "presentation": "cat_presentation",
    "wordprocessor": "cat_word_processor",
    "database": "cat_database",
    "finance": "cat_finance",
    "calendar": "cat_calendar",
    "contactmanagement": "cat_contacts",
    "monitor": "cat_monitor",
    "security": "cat_security",
    "education": "cat_education",
    "science": "cat_science",
    "math": "cat_math",
    "mathematics": "cat_math",
    "actiongame": "cat_action_game",
    "adventuregame": "cat_adventure_game",
    "arcadegame": "cat_arcade_game",
    "boardgame": "cat_board_game",
    "cardgame": "cat_card_game",
    "puzzle": "cat_puzzle_game",
    "puzzlegame": "cat_puzzle_game",
    "strategygame": "cat_strategy_game",
    "simulation": "cat_simulation_game",
}

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
    "Flags": "emoji_cat_flags",
}

class PreviewManager:
    @staticmethod
    def render(result: SearchResult = None) -> Gtk.Widget:
        if result is None:
            return PreviewManager._render_empty_state()

        cat = result.category

        if cat in ("Apps", "Applications", "Settings"):
            return PreviewManager._render_app(result)
        elif cat in ("Math", "Calculator", "Units"):
            return PreviewManager._render_math(result)
        elif cat == "Emoji":
            return PreviewManager._render_emoji(result)
        elif cat == "Clipboard":
            return PreviewManager._render_clipboard(result)
        elif cat in ("Files", "Documents", "Images", "Videos", "Audio"):
            return PreviewManager._render_file(result)
        elif cat == "Commands":
            return PreviewManager._render_command(result)
        elif cat in ("Time", "Timezone"):
            return PreviewManager._render_timezone(result)
        elif cat == "Currency":
            return PreviewManager._render_currency(result)
        elif cat == "Weather":
            return PreviewManager._render_weather(result)
        elif cat == "Web":
            return PreviewManager._render_web(result)

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
        scroll.set_propagate_natural_height(False)
        scroll.set_propagate_natural_width(False)
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
    def _create_file_thumbnail(result: SearchResult, size: int = 128):
        from utils import set_icon_safe
        img = Gtk.Image()
        img.set_pixel_size(size)
        img.add_css_class("preview-hero-icon")

        path = result.preview_data.get("path") if result.preview_data else ""
        mime = result.preview_data.get("mime", "") if result.preview_data else ""

        # Check memory cache first for immediate zero-lag display
        if path and path in _PREVIEW_THUMBNAIL_CACHE:
            cached_pixbuf = _PREVIEW_THUMBNAIL_CACHE[path]
            _PREVIEW_THUMBNAIL_CACHE.move_to_end(path)
            set_icon_safe(img, None, raw_pixbuf=cached_pixbuf, is_paintable=True)
            img.add_css_class("preview-hero-thumbnail")
            return img

        # Fallback to standard icon while loading
        set_icon_safe(img, result.icon, fallback_icon="text-x-generic", pixel_size=size)

        if not path or not os.path.exists(path):
            return img

        # Background async thumbnail worker
        def _worker():
            pixbuf = _load_file_thumbnail_pixbuf(path, mime, target_size=size * 2)
            if pixbuf:
                def _update_ui():
                    set_icon_safe(img, None, raw_pixbuf=pixbuf, is_paintable=True)
                    img.add_css_class("preview-hero-thumbnail")
                GLib.idle_add(_update_ui)

        threading.Thread(target=_worker, daemon=True).start()
        return img

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
        box.add_css_class("preview-title-block")

        title = Gtk.Label(label=title_text)
        title.add_css_class("preview-main-title")
        title.set_justify(Gtk.Justification.CENTER)
        title.set_wrap(True)
        title.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        title.set_max_width_chars(32)
        box.append(title)

        if subtitle_text:
            subtitle = Gtk.Label(label=subtitle_text)
            subtitle.add_css_class("preview-main-subtitle")
            subtitle.set_justify(Gtk.Justification.CENTER)
            subtitle.set_wrap(True)
            subtitle.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
            subtitle.set_max_width_chars(36)
            subtitle.set_lines(3)
            subtitle.set_ellipsize(Pango.EllipsizeMode.END)
            box.append(subtitle)

        return box

    @staticmethod
    def _create_meta_grid():
        # Gtk.Grid with homogeneous columns for perfect 50/50 split
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(8)
        grid.set_column_homogeneous(True)
        grid.set_halign(Gtk.Align.FILL)
        grid.set_hexpand(True)
        grid.add_css_class("preview-meta-grid")
        return grid

    @staticmethod
    def _create_meta_card(key: str, value: str):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.add_css_class("preview-meta-card")
        card.set_hexpand(True)

        lbl_key = Gtk.Label(label=key)
        lbl_key.add_css_class("preview-meta-key")
        lbl_key.set_halign(Gtk.Align.START)

        lbl_val = Gtk.Label(label=value)
        lbl_val.add_css_class("preview-meta-val")
        lbl_val.set_halign(Gtk.Align.START)
        lbl_val.set_wrap(True)
        lbl_val.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        lbl_val.set_lines(2)
        lbl_val.set_ellipsize(Pango.EllipsizeMode.END)

        card.append(lbl_key)
        card.append(lbl_val)

        return card

    @staticmethod
    def _create_action_footer(actions: list):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_halign(Gtk.Align.FILL)
        box.set_hexpand(True)
        box.set_valign(Gtk.Align.END)
        box.set_margin_top(8)
        box.add_css_class("preview-action-box")

        for lbl, cb, destructive in actions:
            btn = Gtk.Button(label=lbl)
            btn.set_hexpand(True)
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
        raw_cats = result.preview_data.get("category") or result.preview_data.get("categories")
        if raw_cats:
            if isinstance(raw_cats, str):
                parts = [p.strip() for p in raw_cats.replace(",", ";").split(";") if p.strip()]
            else:
                parts = [str(p).strip() for p in raw_cats if str(p).strip()]

            ignored_tokens = {"gnome", "gtk", "qt", "x-gnome", "kde", "application", "x-kde"}
            filtered_parts = [p for p in parts if p.lower() not in ignored_tokens]

            translated_cats = []
            seen = set()
            for p in filtered_parts:
                k = APP_CAT_I18N.get(p.lower())
                tr = t(k) if k else p
                if tr and tr not in seen:
                    seen.add(tr)
                    translated_cats.append(tr)

            display_cat = ", ".join(translated_cats) if translated_cats else (filtered_parts[0] if filtered_parts else "")
            if display_cat:
                grid.attach(PreviewManager._create_meta_card(t("label_categories"), display_cat), col, 0, 1, 1)

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
        hero_box.append(PreviewManager._create_file_thumbnail(result, 128))
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
                is_ru = (get_current_language() == "ru")
                units = ["Б", "КБ", "МБ", "ГБ", "ТБ"] if is_ru else ["B", "KB", "MB", "GB", "TB"]
                for unit in units:
                    if bytes_size < 1024.0:
                        size = f"{bytes_size:.1f} {unit}"
                        break
                    bytes_size /= 1024.0
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                result.preview_data["size"] = size
                result.preview_data["mtime"] = mtime
            except OSError as e:
                logger.debug("File stat failed in preview: %s", e)

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
        lbl.set_lines(4)
        lbl.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
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

        raw_cat = result.preview_data.get("emoji_category", "")
        cat_key = EMOJI_CAT_KEYS.get(raw_cat)
        cat_label = t(cat_key) if cat_key else raw_cat
        content_box.append(PreviewManager._create_title_block(
            result.title,
            cat_label
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
    def _render_web(result: SearchResult) -> Gtk.Widget:
        root_box, content_box = PreviewManager._create_base_structure()
        data = result.preview_data or {}
        engine_name = data.get("engine", "Web")
        query = data.get("query", "")
        flag = data.get("flag", "")

        hero_box = PreviewManager._create_hero_container()
        hero_box.append(PreviewManager._create_icon(result.icon, 128))
        content_box.append(hero_box)

        title_text = result.title
        subtitle_text = result.subtitle or t("web_search_action_open")
        content_box.append(PreviewManager._create_title_block(title_text, subtitle_text))

        grid = PreviewManager._create_meta_grid()
        col = 0
        row = 0

        grid.attach(PreviewManager._create_meta_card(t("settings_web_search_engine"), engine_name), col, row, 1, 1)
        col += 1

        if flag:
            grid.attach(PreviewManager._create_meta_card(t("label_flag"), flag), col, row, 1, 1)
            col += 1
            if col > 1:
                col = 0
                row += 1

        if query:
            grid.attach(PreviewManager._create_meta_card(t("label_query"), query), col, row, 1, 1)

        content_box.append(grid)

        actions = []
        if result._action_execute:
            actions.append((t("web_search_in", engine=engine_name), result.execute, False))
        if result._action_copy:
            actions.append((t("action_copy"), result.copy_value, False))

        root_box.append(PreviewManager._create_action_footer(actions))
        return root_box

    @staticmethod
    def _render_basic(result: SearchResult) -> Gtk.Widget:
        root_box, content_box = PreviewManager._create_base_structure()
        hero_box = PreviewManager._create_hero_container()
        hero_box.append(PreviewManager._create_icon(result.icon, 128))
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
        is_ru = (get_current_language() == "ru")
        day_night_str = ("День ☀️" if is_day else "Ночь 🌙") if is_ru else ("Day ☀️" if is_day else "Night 🌙")
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
            set_clipboard_text(copy_text)

        def _copy_all_action():
            set_clipboard_text(full_copy_text)

        actions = [
            (t("action_copy"), _copy_val_action, False),
            (t("action_copy_all"), _copy_all_action, False)
        ]

        root_box.append(PreviewManager._create_action_footer(actions))
        return root_box

    @staticmethod
    def _get_temp_unit() -> str:
        if not hasattr(PreviewManager, "_cached_temp_unit") or PreviewManager._cached_temp_unit is None:
            try:
                from config_manager import ConfigManager
                PreviewManager._cached_temp_unit = ConfigManager().get("temperature_unit", "celsius")
            except Exception:
                PreviewManager._cached_temp_unit = "celsius"
        return PreviewManager._cached_temp_unit

    @staticmethod
    def _create_weather_metric_item(label: str, value: str) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_halign(Gtk.Align.START)

        lbl_title = Gtk.Label(label=label)
        lbl_title.set_halign(Gtk.Align.START)
        lbl_title.add_css_class("weather-bento-sublabel")
        box.append(lbl_title)

        lbl_val = Gtk.Label(label=value)
        lbl_val.set_halign(Gtk.Align.START)
        lbl_val.add_css_class("weather-bento-val-large")
        box.append(lbl_val)

        return box

    @staticmethod
    def _render_weather(result: SearchResult) -> Gtk.Widget:
        import subprocess

        from providers.weather import get_condition_text
        data = result.preview_data or {}

        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root_box.add_css_class("preview-panel")
        root_box.add_css_class("preview-panel-weather")
        root_box.set_vexpand(True)
        root_box.set_hexpand(True)

        scroll_overview = Gtk.ScrolledWindow()
        scroll_overview.add_css_class("weather-scrolled-window")
        scroll_overview.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_overview.set_vexpand(True)
        scroll_overview.set_propagate_natural_height(False)
        scroll_overview.set_propagate_natural_width(False)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_box.add_css_class("weather-content-pad")
        scroll_overview.set_child(content_box)

        lang = get_current_language()
        is_ru = (lang == 'ru')

        temp_unit = data.get("temp_unit") or PreviewManager._get_temp_unit()

        # 1. Header & Hero Section
        hero_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        hero_box.set_halign(Gtk.Align.CENTER)
        hero_box.add_css_class("weather-hero-box")

        # City Name
        city_name = data.get("city_name", result.title.split(":")[0] if ":" in result.title else result.title)
        if is_ru and data.get("name_ru"):
            city_name = data.get("name_ru")
        elif not is_ru and data.get("name_en"):
            city_name = data.get("name_en")
        lbl_city = Gtk.Label(label=city_name)
        lbl_city.add_css_class("weather-hero-city")
        hero_box.append(lbl_city)

        # Big Temperature with condition icon
        temp_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        temp_row.set_halign(Gtk.Align.CENTER)

        icon_path = data.get("icon_file") or result.icon
        if icon_path and os.path.exists(icon_path):
            weather_icon = Gtk.Image.new_from_file(icon_path)
            weather_icon.set_pixel_size(48)
            weather_icon.add_css_class("weather-card-condition-icon")
            temp_row.append(weather_icon)

        temp_val = data.get("temp", 24)
        disp_temp = convert_temp(temp_val, temp_unit)
        lbl_temp = Gtk.Label(label=f"{disp_temp}°")
        lbl_temp.add_css_class("weather-hero-temp")
        temp_row.append(lbl_temp)

        hero_box.append(temp_row)

        # Condition
        w_code = data.get("weather_code", 0)
        is_day = bool(data.get("is_day", 1))
        tod = data.get("time_of_day", "day")
        if data.get("condition_text"):
            cond_text = data.get("condition_text")
        elif tod == 'dusk' and w_code == 0:
            cond_text = "Ясно" if lang == "ru" else "Clear"
        else:
            cond_text = get_condition_text(w_code, lang=lang, is_day=is_day)
        lbl_cond = Gtk.Label(label=cond_text)
        lbl_cond.add_css_class("weather-hero-condition")
        hero_box.append(lbl_cond)

        # Extremes & Feels like
        t_min = data.get("temp_min", 9)
        t_max = data.get("temp_max", 25)
        disp_min = convert_temp(t_min, temp_unit)
        disp_max = convert_temp(t_max, temp_unit)

        feels_val = data.get("feels_like")
        feels_str = ""
        if feels_val is not None:
            disp_feels = convert_temp(feels_val, temp_unit)
            feels_str = f" • {t('weather_feels_like', temp=disp_feels)}" if lang == "ru" else f" • Feels like {disp_feels}°"

        extremes_text = f"{t('weather_high_low', high=disp_max, low=disp_min)}{feels_str}"
        lbl_extremes = Gtk.Label(label=extremes_text)
        lbl_extremes.add_css_class("weather-hero-extremes")
        hero_box.append(lbl_extremes)

        content_box.append(hero_box)

        # 2. Compact Essential Metrics Card (2x2 grid: Humidity, Wind, Precipitation, Pressure)
        metrics_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        metrics_card.add_css_class("weather-glass-card")
        metrics_card.set_margin_top(8)

        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(14)
        grid.set_column_homogeneous(True)

        # Humidity
        hum_val = data.get("humidity", 0)
        hum_lbl = "Влажность" if is_ru else "Humidity"
        grid.attach(PreviewManager._create_weather_metric_item(hum_lbl, f"{hum_val}%"), 0, 0, 1, 1)

        # Wind
        wind_val = data.get("wind_speed", 0)
        wind_unit = "м/с" if is_ru else "m/s"
        wind_lbl = "Ветер" if is_ru else "Wind"
        grid.attach(PreviewManager._create_weather_metric_item(wind_lbl, f"{round(wind_val, 1)} {wind_unit}"), 1, 0, 1, 1)

        # Precipitation
        precip_val = data.get("precipitation", 0.0)
        precip_lbl = "Осадки" if is_ru else "Precipitation"
        grid.attach(PreviewManager._create_weather_metric_item(precip_lbl, f"{precip_val:.1f} mm"), 0, 1, 1, 1)

        # Pressure
        press_mm = data.get("pressure_mm")
        if press_mm is not None:
            press_hpa = round(press_mm / 0.750062)
        else:
            press_hpa = round(data.get("pressure", 1013))
            press_mm = round(press_hpa * 0.750062)

        if is_ru:
            press_str = f"{press_mm} мм рт. ст."
            press_lbl = "Давление"
        else:
            press_str = f"{press_hpa} hPa"
            press_lbl = "Pressure"
        grid.attach(PreviewManager._create_weather_metric_item(press_lbl, press_str), 1, 1, 1, 1)

        metrics_card.append(grid)
        content_box.append(metrics_card)

        # 3. Echo Weather Standalone App CTA Box
        cta_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        cta_card.add_css_class("weather-glass-card")
        cta_card.set_margin_top(4)

        cta_title = Gtk.Label(label="Echo Weather" if not is_ru else "Приложение Echo Weather")
        cta_title.set_halign(Gtk.Align.START)
        cta_title.add_css_class("weather-card-header-title")
        cta_card.append(cta_title)

        cta_desc = Gtk.Label(
            label="Подробный почасовой анализ, графики и астрономия доступны в приложении" if is_ru
            else "Detailed hourly forecasts, interactive charts, and astronomy in Echo Weather"
        )
        cta_desc.set_halign(Gtk.Align.START)
        cta_desc.set_wrap(True)
        cta_desc.add_css_class("weather-summary-text")
        cta_card.append(cta_desc)

        btn_open_app = Gtk.Button(label="Открыть подробный прогноз ↗" if is_ru else "Open Detailed Forecast ↗")
        btn_open_app.add_css_class("suggested-action")
        btn_open_app.set_margin_top(6)

        def _on_open_app_clicked(_btn):
            launch_echo_weather(city_name)

        btn_open_app.connect("clicked", _on_open_app_clicked)
        cta_card.append(btn_open_app)

        content_box.append(cta_card)

        # 4. Action Footer
        actions = []
        if result._action_copy:
            copy_val = f"{city_name}: {disp_temp:+d}°, {cond_text} (↓ {disp_min}° ↑ {disp_max}°)"
            def _copy_forecast_action():
                set_clipboard_text(copy_val)
            actions.append((t("weather_copy_action"), _copy_forecast_action, False))

        def _launch_app_action():
            launch_echo_weather(city_name)
        actions.append(("Echo Weather", _launch_app_action, False))

        footer = PreviewManager._create_action_footer(actions)
        footer.add_css_class("weather-action-box")
        content_box.append(footer)

        root_box.append(scroll_overview)
        return root_box

