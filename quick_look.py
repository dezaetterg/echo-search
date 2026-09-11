import os
import time
import mimetypes
import threading
import subprocess
from pathlib import Path
from datetime import datetime

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk, GLib, Gio, Pango, GdkPixbuf

from i18n import t, get_current_language
from utils import format_shortcut_display

try:
    from pygments import lex
    from pygments.lexers import get_lexer_for_filename, TextLexer
    from pygments.token import Token
    PYGMENTS_AVAILABLE = True
except Exception:
    PYGMENTS_AVAILABLE = False

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".bmp", ".ico", ".tiff", ".avif"}
CODE_EXTENSIONS = {
    ".py", ".json", ".md", ".txt", ".sh", ".bash", ".zsh", ".js", ".ts", ".jsx", ".tsx",
    ".html", ".css", ".scss", ".xml", ".yaml", ".yml", ".toml", ".ini", ".conf", ".c",
    ".cpp", ".h", ".hpp", ".rs", ".go", ".java", ".kt", ".lua", ".sql", ".diff", ".patch"
}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".opus", ".wma"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv", ".wmv", ".m4v"}
PDF_EXTENSIONS = {".pdf"}
DOCUMENT_EXTENSIONS = {".docx", ".odt", ".epub", ".fb2", ".rtf", ".doc"}

class QuickLookWindow(Gtk.Window):
    def __init__(self, parent_window=None):
        super().__init__()
        self.parent_window = parent_window
        self.current_path = None
        self.current_result = None
        self._load_generation = 0
        self._opened_timestamp = 0
        self.current_media_file = None
        self.current_video_widget = None
        self._audio_slider_handler_id = None


        self._pdf_path = None
        self._pdf_gen = 0
        self._pdf_current_page = 1
        self._pdf_total_pages = 1
        self._pdf_picture = None
        self._pdf_page_label = None
        self._pdf_prev_btn = None
        self._pdf_next_btn = None
        self._pdf_scroll = None
        self._pdf_zoom = 1.0
        self._pdf_fit_mode = "width"
        self._pdf_aspect = 1.414
        self._pdf_cached_file = None
        self._last_scroll_w = 0
        self._pdf_zoom_label = None
        self._pdf_zoom_in_btn = None
        self._pdf_zoom_out_btn = None
        self._pdf_fit_btn = None
        self.maximize_btn = None
        self.save_btn = None
        self._text_editor_active = False
        self._text_path = None
        self._text_view = None
        self._text_buffer = None
        self._text_line_numbers_tv = None
        self._text_dirty = False
        self._text_dirty_badge = None
        self._text_stat_label = None
        self._text_cursor_label = None
        self._text_status_badge = None
        self._text_save_btn = None
        self._text_lexer = None
        self._text_rehighlight_source_id = None
        self._text_total_lines = 1
        self._current_content_w = 980
        self._current_content_h = 670
        
        self.set_title("Quick Look")
        self.set_decorated(False)
        self.set_resizable(True)
        self.set_default_size(840, 580)
        
        if parent_window:
            self.set_transient_for(parent_window)
            self.set_modal(False)
            
        self.add_css_class("quick-look-window")
        
        # Outer Card
        self.card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.card_box.add_css_class("quick-look-card")
        self.card_box.add_css_class("outer-border-box")
        self.set_child(self.card_box)
        
        # Header
        self._build_header()
        
        # Body (dynamic container)
        self.body_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.body_container.set_vexpand(True)
        self.body_container.set_hexpand(True)
        self.card_box.append(self.body_container)
        
        # Footer
        self._build_footer()
        
        # Key controller
        key_ctrl = Gtk.EventControllerKey.new()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)
        
        # Focus watcher
        
    def _build_header(self):
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.header_box.add_css_class("quick-look-header")
        
        self.header_icon = Gtk.Image()
        self.header_icon.set_pixel_size(28)
        self.header_box.append(self.header_icon)
        
        title_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_vbox.set_hexpand(True)
        
        self.title_label = Gtk.Label()
        self.title_label.add_css_class("quick-look-title")
        self.title_label.set_halign(Gtk.Align.START)
        self.title_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.title_label.set_max_width_chars(45)
        title_vbox.append(self.title_label)
        
        self.subtitle_label = Gtk.Label()
        self.subtitle_label.add_css_class("quick-look-subtitle")
        self.subtitle_label.set_halign(Gtk.Align.START)
        title_vbox.append(self.subtitle_label)
        
        self.header_box.append(title_vbox)
        
        # Badges box
        self.badges_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.header_box.append(self.badges_box)
        
        # Window controls (Maximize & Close)
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.maximize_btn = Gtk.Button()
        self.maximize_btn.add_css_class("quick-look-close-btn")
        self.maximize_btn.add_css_class("circular")
        self.maximize_btn.set_icon_name("view-fullscreen-symbolic")
        self.maximize_btn.set_tooltip_text("Развернуть / Восстановить (F)")
        self.maximize_btn.connect("clicked", lambda b: self._toggle_maximize())
        controls_box.append(self.maximize_btn)
        
        close_btn = Gtk.Button()
        close_btn.add_css_class("quick-look-close-btn")
        close_btn.add_css_class("circular")
        close_btn.set_icon_name("window-close-symbolic")
        close_btn.set_tooltip_text("Закрыть (Esc / Пробел)")
        close_btn.connect("clicked", lambda b: self.hide_preview())
        controls_box.append(close_btn)
        
        self.header_box.append(controls_box)
        self.card_box.append(self.header_box)

    def _toggle_maximize(self):
        if self.is_maximized():
            self.unmaximize()
            if hasattr(self, "maximize_btn") and self.maximize_btn:
                self.maximize_btn.set_icon_name("view-fullscreen-symbolic")
        else:
            self.maximize()
            if hasattr(self, "maximize_btn") and self.maximize_btn:
                self.maximize_btn.set_icon_name("view-restore-symbolic")
        if getattr(self, "_pdf_path", None):
            GLib.timeout_add(120, lambda: (self._update_pdf_page_size(), False)[1])
        
    def _build_footer(self):
        self.footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.footer_box.add_css_class("quick-look-footer")
        
        self.save_btn = Gtk.Button(label=f"💾 {t('action_save')} Ctrl+S")
        self.save_btn.add_css_class("quick-look-action-btn")
        self.save_btn.connect("clicked", lambda b: self._save_text_file())
        self.save_btn.set_visible(False)
        self.footer_box.append(self.save_btn)

        self.open_btn = Gtk.Button(label=f"{t("action_open")} ↵")
        self.open_btn.add_css_class("quick-look-action-btn")
        self.open_btn.add_css_class("primary-action")
        self.open_btn.connect("clicked", self._on_open_clicked)
        self.footer_box.append(self.open_btn)
        
        self.reveal_btn = Gtk.Button(label=f"{t("action_open_location")} ⇧↵")
        self.reveal_btn.add_css_class("quick-look-action-btn")
        self.reveal_btn.connect("clicked", self._on_reveal_clicked)
        self.footer_box.append(self.reveal_btn)
        
        self.terminal_btn = Gtk.Button(label=f"{t("action_open_terminal")} Ctrl+T")
        self.terminal_btn.add_css_class("quick-look-action-btn")
        self.terminal_btn.connect("clicked", self._on_terminal_clicked)
        self.terminal_btn.set_visible(False)
        self.footer_box.append(self.terminal_btn)
        
        self.copy_btn = Gtk.Button(label=f"{t("action_copy_path")} Ctrl+C")
        self.copy_btn.add_css_class("quick-look-action-btn")
        self.copy_btn.connect("clicked", self._on_copy_clicked)
        self.footer_box.append(self.copy_btn)
        
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        self.footer_box.append(spacer)
        
        self.hint_lbl = Gtk.Label(label=f"[Space / Esc] {t("action_close")}")
        self.hint_lbl.add_css_class("quick-look-hint")
        self.footer_box.append(self.hint_lbl)
        
        self.card_box.append(self.footer_box)

    def _clear_badges(self):
        while child := self.badges_box.get_first_child():
            self.badges_box.remove(child)

    def _add_badge(self, text: str):
        badge = Gtk.Label(label=text)
        badge.add_css_class("quick-look-badge")
        self.badges_box.append(badge)

    def _cleanup_media(self):
        if self.current_media_file:
            try:
                self.current_media_file.set_playing(False)
                self.current_media_file.clear()
            except Exception:
                pass
            self.current_media_file = None
            
        if self.current_video_widget:
            try:
                media_stream = self.current_video_widget.get_media_stream()
                if media_stream:
                    media_stream.set_playing(False)
            except Exception:
                pass
            self.current_video_widget = None

        if getattr(self, "_text_rehighlight_source_id", None):
            try:
                GLib.source_remove(self._text_rehighlight_source_id)
            except Exception:
                pass
            self._text_rehighlight_source_id = None
        self._text_editor_active = False
        self._text_path = None
        self._text_view = None
        self._text_buffer = None
        self._text_line_numbers_tv = None
        self._text_dirty = False
        self._text_dirty_badge = None
        self._text_stat_label = None
        self._text_cursor_label = None
        self._text_status_badge = None
        self._text_save_btn = None
        self._text_lexer = None
        if hasattr(self, "save_btn") and self.save_btn:
            self.save_btn.set_visible(False)

        self._pdf_path = None
        self._pdf_picture = None
        self._pdf_page_label = None
        self._pdf_prev_btn = None
        self._pdf_next_btn = None
        self._pdf_scroll = None
        self._pdf_zoom_label = None
        self._pdf_zoom_in_btn = None
        self._pdf_zoom_out_btn = None
        self._pdf_fit_btn = None
        self._pdf_zoom = 1.0
        self._pdf_fit_mode = "width"
        self._pdf_aspect = 1.414
        self._pdf_cached_file = None
        self._last_scroll_w = 0

    def preview_result(self, result) -> bool:
        if not result:
            return False
            
        self._cleanup_media()
        self.current_result = result
        path = None
        if result.preview_data and isinstance(result.preview_data, dict):
            path = result.preview_data.get("path")
        if not path and getattr(result, "id", None) and os.path.exists(result.id):
            path = result.id
            
        if not path or not os.path.exists(path):
            return False
            
        self.current_path = path
        self._opened_timestamp = time.time()
        self._load_generation += 1
        gen = self._load_generation
        
        cfg = getattr(self.parent_window, "config_manager", None)
        sc = cfg.get("quick_look_shortcut", "space") if cfg else "space"
        cur_lang = cfg.get("language", "auto") if cfg else "auto"
        if cur_lang == "auto":
            cur_lang = get_current_language()
        key_display = format_shortcut_display(sc, cur_lang)
        self.hint_lbl.set_text(f"[{key_display} / Esc] {t('action_close')}")

        filename = os.path.basename(path) or path
        is_directory = os.path.isdir(path)
        ext = "" if is_directory else os.path.splitext(path)[1].lower()
        self.title_label.set_label(filename)
        
        # Adaptive dimensions based on content category
        is_doc = (ext in PDF_EXTENSIONS or ext in DOCUMENT_EXTENSIONS or 
                  ext in CODE_EXTENSIONS or ext in (".txt", ".log", ".md", ".json", ".xml", ".yaml", ".yml"))
        if is_doc:
            target_w, target_h = 1040, 820
            content_w, content_h = 980, 670
        elif ext in IMAGE_EXTENSIONS or ext in VIDEO_EXTENSIONS:
            target_w, target_h = 920, 680
            content_w, content_h = 860, 530
        else:
            target_w, target_h = 820, 580
            content_w, content_h = 760, 430

        try:
            display = Gdk.Display.get_default()
            monitors = display.get_monitors()
            if monitors and monitors.get_n_items() > 0:
                mon = monitors.get_item(0)
                geom = mon.get_geometry()
                target_w = min(target_w, geom.width - 60)
                target_h = min(target_h, geom.height - 120)
                content_w = min(content_w, target_w - 50)
                content_h = min(content_h, target_h - 150)
        except Exception:
            pass

        self._current_content_w = content_w
        self._current_content_h = content_h
        if not self.is_maximized():
            self.set_default_size(target_w, target_h)
        
        # Determine MIME & Size
        if is_directory:
            mime = "inode/directory"
            self.terminal_btn.set_visible(True)
        else:
            guessed_mime, _ = mimetypes.guess_type(path)
            mime = guessed_mime or "application/octet-stream"
            self.terminal_btn.set_visible(False)
            
        try:
            stat = os.stat(path)
            size_bytes = stat.st_size
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if size_bytes < 1024.0:
                    formatted_size = f"{size_bytes:.1f} {unit}"
                    break
                size_bytes /= 1024.0
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
        except Exception:
            formatted_size = "Unknown size"
            mtime = ""
            
        if is_directory:
            self.subtitle_label.set_label(f"{path} • {mtime}")
        else:
            self.subtitle_label.set_label(f"{mime} • {formatted_size} • {mtime}")
            
        self._clear_badges()
        
        # Set icon
        if is_directory:
            self.header_icon.set_from_icon_name("folder")
        elif result.icon and os.path.isabs(result.icon) and os.path.exists(result.icon):
            self.header_icon.set_from_file(result.icon)
        else:
            self.header_icon.set_from_icon_name(result.icon or "text-x-generic")
            
        # Clear previous body
        while child := self.body_container.get_first_child():
            self.body_container.remove(child)
            
        try:
            if is_directory:
                self._render_folder_view(path, gen)
            elif ext in VIDEO_EXTENSIONS or mime.startswith("video/"):
                self._render_video_view(path, gen, ext, mime, formatted_size)
            elif ext in AUDIO_EXTENSIONS or mime.startswith("audio/"):
                self._render_audio_view(path, gen, ext, mime, formatted_size)
            elif ext in IMAGE_EXTENSIONS:
                self._render_image_view(path, gen, formatted_size)
            elif ext in PDF_EXTENSIONS or mime == "application/pdf":
                self._render_pdf_view(path, gen, formatted_size, mime, mtime)
            elif ext in DOCUMENT_EXTENSIONS:
                self._render_document_view(path, gen, ext, formatted_size, mime, mtime)
            elif ext in CODE_EXTENSIONS or mime.startswith("text/"):
                self._render_text_view(path, gen, ext)
            else:
                self._render_generic_view(path, gen, mime, formatted_size, mtime)
        except Exception as e:
            try:
                while child := self.body_container.get_first_child():
                    self.body_container.remove(child)
                self._render_generic_view(path, gen, mime, formatted_size, mtime)
            except Exception:
                pass
            
        self.present()
        return True

    def _render_folder_view(self, path: str, generation: int):
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        container.add_css_class("quick-look-folder-container")
        container.set_vexpand(True)
        container.set_hexpand(True)
        container.set_size_request(getattr(self, "_current_content_w", 760), getattr(self, "_current_content_h", 430))
        
        scroll = Gtk.ScrolledWindow()
        scroll.add_css_class("quick-look-folder-scroll")
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        
        items_listbox = Gtk.ListBox()
        items_listbox.add_css_class("quick-look-folder-listbox")
        items_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.set_child(items_listbox)
        container.append(scroll)
        self.body_container.append(container)
        
        self._add_badge(t("label_folder"))
        
        def _async_scan_folder():
            try:
                entries = []
                dir_count = 0
                file_count = 0
                with os.scandir(path) as it:
                    for entry in it:
                        is_dir = entry.is_dir(follow_symlinks=False)
                        if is_dir:
                            dir_count += 1
                        else:
                            file_count += 1
                        entries.append((is_dir, entry.name, entry.path))
                        if len(entries) >= 500:
                            break
                            
                # Sort: directories first, then alphabetical
                entries.sort(key=lambda x: (not x[0], x[1].lower()))
                top_entries = entries[:15]
                total_items = dir_count + file_count
                
                def _update_folder_ui():
                    if self._load_generation == generation and self.is_visible():
                        self._add_badge(f"{total_items} {t("label_items")}")
                        self._add_badge(f"{dir_count} {t("label_folders")}, {file_count} {t("label_files")}")
                        
                        if not top_entries:
                            empty_lbl = Gtk.Label(label=t("label_empty_folder"))
                            empty_lbl.add_css_class("quick-look-empty-folder")
                            empty_lbl.set_valign(Gtk.Align.CENTER)
                            empty_lbl.set_vexpand(True)
                            items_listbox.append(empty_lbl)
                            return False
                            
                        for is_d, name, item_path in top_entries:
                            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                            row.add_css_class("quick-look-folder-row")
                            
                            icon_img = Gtk.Image()
                            if is_d:
                                icon_img.set_from_icon_name("folder")
                            else:
                                ext = os.path.splitext(name)[1].lower()
                                if ext in IMAGE_EXTENSIONS:
                                    icon_img.set_from_icon_name("image-x-generic")
                                elif ext in CODE_EXTENSIONS:
                                    icon_img.set_from_icon_name("text-x-script")
                                elif ext in AUDIO_EXTENSIONS:
                                    icon_img.set_from_icon_name("audio-x-generic")
                                elif ext in VIDEO_EXTENSIONS:
                                    icon_img.set_from_icon_name("video-x-generic")
                                else:
                                    icon_img.set_from_icon_name("text-x-generic")
                            icon_img.set_pixel_size(18)
                            row.append(icon_img)
                            
                            name_lbl = Gtk.Label(label=name)
                            name_lbl.add_css_class("quick-look-folder-item-name")
                            name_lbl.set_halign(Gtk.Align.START)
                            name_lbl.set_ellipsize(Pango.EllipsizeMode.END)
                            name_lbl.set_hexpand(True)
                            row.append(name_lbl)
                            
                            try:
                                if is_d:
                                    size_str = "—"
                                else:
                                    sb = os.path.getsize(item_path)
                                    for u in ["B", "KB", "MB", "GB"]:
                                        if sb < 1024.0:
                                            size_str = f"{sb:.1f} {u}"
                                            break
                                        sb /= 1024.0
                            except Exception:
                                size_str = ""
                                
                            sz_lbl = Gtk.Label(label=size_str)
                            sz_lbl.add_css_class("quick-look-folder-item-size")
                            row.append(sz_lbl)
                            
                            items_listbox.append(row)
                    return False
                    
                GLib.idle_add(_update_folder_ui)
            except Exception:
                pass
                
        threading.Thread(target=_async_scan_folder, daemon=True).start()

    def _render_audio_view(self, path: str, generation: int, ext: str, mime: str, size_str: str):
        hero_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        hero_box.add_css_class("quick-look-audio-hero")
        hero_box.set_vexpand(True)
        hero_box.set_hexpand(True)
        hero_box.set_size_request(getattr(self, "_current_content_w", 760), getattr(self, "_current_content_h", 430))
        hero_box.set_valign(Gtk.Align.CENTER)
        
        disc_icon = Gtk.Image.new_from_icon_name("media-optical-audio-symbolic")
        disc_icon.set_pixel_size(90)
        disc_icon.add_css_class("quick-look-audio-disc")
        hero_box.append(disc_icon)
        
        audio_title = Gtk.Label(label=os.path.basename(path))
        audio_title.add_css_class("quick-look-audio-title")
        audio_title.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        audio_title.set_max_width_chars(50)
        hero_box.append(audio_title)
        
        # Audio controls box
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        controls_box.add_css_class("quick-look-audio-controls")
        
        play_btn = Gtk.Button()
        play_btn.add_css_class("quick-look-play-btn")
        play_btn.set_icon_name("media-playback-start-symbolic")
        controls_box.append(play_btn)
        
        time_elapsed_lbl = Gtk.Label(label="00:00")
        time_elapsed_lbl.add_css_class("quick-look-audio-time")
        controls_box.append(time_elapsed_lbl)
        
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        scale.set_hexpand(True)
        scale.set_draw_value(False)
        controls_box.append(scale)
        
        time_total_lbl = Gtk.Label(label="--:--")
        time_total_lbl.add_css_class("quick-look-audio-time")
        controls_box.append(time_total_lbl)
        
        hero_box.append(controls_box)
        self.body_container.append(hero_box)
        
        self._add_badge(ext.upper()[1:] if ext else "AUDIO")
        self._add_badge(size_str)
        
        # GtkMediaFile setup
        try:
            media_file = Gtk.MediaFile.new_for_filename(path)
            self.current_media_file = media_file
            
            def _format_time(microseconds):
                sec = int(microseconds / 1000000)
                m, s = divmod(sec, 60)
                return f"{m:02d}:{s:02d}"
                
            def _on_play_toggle(btn):
                if media_file.get_playing():
                    media_file.set_playing(False)
                    play_btn.set_icon_name("media-playback-start-symbolic")
                else:
                    media_file.set_playing(True)
                    play_btn.set_icon_name("media-playback-pause-symbolic")
                    
            play_btn.connect("clicked", _on_play_toggle)
            
            def _on_scale_change(slider):
                if media_file.get_duration() > 0:
                    target_time = int((slider.get_value() / 100.0) * media_file.get_duration())
                    media_file.seek(target_time)
                    
            scale.connect("value-changed", _on_scale_change)
            
            def _update_stream():
                if self._load_generation == generation and self.is_visible() and self.current_media_file == media_file:
                    dur = media_file.get_duration()
                    pos = media_file.get_timestamp()
                    if dur > 0:
                        time_total_lbl.set_label(_format_time(dur))
                        time_elapsed_lbl.set_label(_format_time(pos))
                        scale.handler_block_by_func(_on_scale_change)
                        scale.set_value((pos / dur) * 100.0)
                        scale.handler_unblock_by_func(_on_scale_change)
                    if media_file.get_ended():
                        play_btn.set_icon_name("media-playback-start-symbolic")
                    return True
                return False
                
            GLib.timeout_add(250, _update_stream)
        except Exception:
            pass

    def _render_video_view(self, path: str, generation: int, ext: str, mime: str, size_str: str):
        video_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        video_box.add_css_class("quick-look-video-container")
        video_box.set_vexpand(True)
        video_box.set_hexpand(True)
        video_box.set_size_request(getattr(self, "_current_content_w", 860), getattr(self, "_current_content_h", 530))
        
        try:
            video_widget = Gtk.Video.new_for_filename(path)
            video_widget.add_css_class("quick-look-video")
            video_widget.set_autoplay(False)
            video_widget.set_vexpand(True)
            video_widget.set_hexpand(True)
            self.current_video_widget = video_widget
            video_box.append(video_widget)
        except Exception:
            # Fallback to media hero
            self._render_media_view(path, generation, ext, mime, size_str)
            return
            
        self.body_container.append(video_box)
        self._add_badge(ext.upper()[1:] if ext else "VIDEO")
        self._add_badge(size_str)

    def _render_image_view(self, path: str, generation: int, size_str: str):
        img_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        img_box.add_css_class("quick-look-image-container")
        img_box.set_vexpand(True)
        img_box.set_hexpand(True)
        img_box.set_size_request(getattr(self, "_current_content_w", 860), getattr(self, "_current_content_h", 530))
        img_box.set_valign(Gtk.Align.CENTER)
        img_box.set_halign(Gtk.Align.CENTER)
        
        image_widget = Gtk.Picture()
        image_widget.set_can_shrink(True)
        image_widget.set_content_fit(Gtk.ContentFit.CONTAIN)
        image_widget.add_css_class("quick-look-image")
        img_box.append(image_widget)
        
        self.body_container.append(img_box)
        
        # Phase 0: Fast thumbnail if cached
        try:
            import hashlib
            uri = Path(path).as_uri()
            h = hashlib.md5(uri.encode("utf-8")).hexdigest()
            thumb_path = os.path.expanduser(f"~/.cache/thumbnails/large/{h}.png")
            if not os.path.exists(thumb_path):
                thumb_path = os.path.expanduser(f"~/.cache/thumbnails/normal/{h}.png")
            if os.path.exists(thumb_path):
                image_widget.set_filename(thumb_path)
        except Exception:
            pass
            
        # Phase 1: Async High-Res Decoding (constrained to viewport 1200x800)
        def _async_load():
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(path, 1200, 800)
                w = pixbuf.get_width()
                h = pixbuf.get_height()
                
                def _update_ui():
                    if self._load_generation == generation and self.is_visible():
                        image_widget.set_pixbuf(pixbuf)
                        self._add_badge(f"{w} × {h} px")
                    return False
                    
                GLib.idle_add(_update_ui)
            except Exception:
                pass
                
        threading.Thread(target=_async_load, daemon=True).start()

    def _render_pdf_view(self, path: str, generation: int, size_str: str, mime: str = "", mtime: str = ""):
        self._pdf_path = path
        self._pdf_gen = generation
        self._pdf_current_page = 1
        self._pdf_total_pages = 1
        self._pdf_zoom = 1.0
        self._pdf_fit_mode = "width"
        self._pdf_aspect = 1.414
        self._pdf_cached_file = None
        self._last_scroll_w = 0
        
        content_w = getattr(self, "_current_content_w", 980)
        content_h = getattr(self, "_current_content_h", 670)
        
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        container.add_css_class("quick-look-pdf-container")
        container.set_vexpand(True)
        container.set_hexpand(True)
        container.set_size_request(content_w, content_h)
        
        # Toolbar with page switcher & zoom controls
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.add_css_class("quick-look-pdf-toolbar")
        toolbar.set_halign(Gtk.Align.CENTER)
        toolbar.set_valign(Gtk.Align.CENTER)
        
        # Previous page
        prev_btn = Gtk.Button()
        prev_btn.set_icon_name("go-previous-symbolic")
        prev_btn.add_css_class("quick-look-page-btn")
        prev_btn.set_tooltip_text("Предыдущая страница (Left / Page Up)")
        prev_btn.set_sensitive(False)
        prev_btn.connect("clicked", lambda _: self._on_pdf_prev_page())
        toolbar.append(prev_btn)
        
        page_lbl = Gtk.Label(label="1 / 1")
        page_lbl.add_css_class("quick-look-page-label")
        toolbar.append(page_lbl)
        
        # Next page
        next_btn = Gtk.Button()
        next_btn.set_icon_name("go-next-symbolic")
        next_btn.add_css_class("quick-look-page-btn")
        next_btn.set_tooltip_text("Следующая страница (Right / Page Down)")
        next_btn.set_sensitive(False)
        next_btn.connect("clicked", lambda _: self._on_pdf_next_page())
        toolbar.append(next_btn)
        
        # Separator
        sep1 = Gtk.Box()
        sep1.add_css_class("quick-look-toolbar-sep")
        toolbar.append(sep1)
        
        # Zoom out
        zoom_out_btn = Gtk.Button()
        zoom_out_btn.set_icon_name("zoom-out-symbolic")
        zoom_out_btn.add_css_class("quick-look-page-btn")
        zoom_out_btn.set_tooltip_text("Уменьшить (-)")
        zoom_out_btn.connect("clicked", lambda _: self._pdf_zoom_out())
        toolbar.append(zoom_out_btn)
        
        # Zoom percentage reset
        zoom_lbl_btn = Gtk.Button(label="100%")
        zoom_lbl_btn.add_css_class("quick-look-page-btn")
        zoom_lbl_btn.add_css_class("quick-look-zoom-btn")
        zoom_lbl_btn.set_tooltip_text("Сбросить масштаб (0)")
        zoom_lbl_btn.connect("clicked", lambda _: self._pdf_zoom_reset())
        toolbar.append(zoom_lbl_btn)
        
        # Zoom in
        zoom_in_btn = Gtk.Button()
        zoom_in_btn.set_icon_name("zoom-in-symbolic")
        zoom_in_btn.add_css_class("quick-look-page-btn")
        zoom_in_btn.set_tooltip_text("Увеличить (+)")
        zoom_in_btn.connect("clicked", lambda _: self._pdf_zoom_in())
        toolbar.append(zoom_in_btn)
        
        # Separator
        sep2 = Gtk.Box()
        sep2.add_css_class("quick-look-toolbar-sep")
        toolbar.append(sep2)
        
        # Fit Width / Fit Page toggle
        fit_btn = Gtk.Button()
        fit_btn.set_icon_name("zoom-fit-best-symbolic")
        fit_btn.add_css_class("quick-look-page-btn")
        fit_btn.set_tooltip_text("По ширине / Вся страница (W)")
        fit_btn.connect("clicked", lambda _: self._pdf_toggle_fit())
        toolbar.append(fit_btn)
        
        container.append(toolbar)
        
        # ScrolledWindow with Page Picture
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        scroll.add_css_class("quick-look-pdf-scroll")
        
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        page_box.set_halign(Gtk.Align.CENTER)
        page_box.set_valign(Gtk.Align.START)
        page_box.set_hexpand(False)
        page_box.set_vexpand(False)
        page_box.set_margin_top(4)
        page_box.set_margin_bottom(16)
        
        picture = Gtk.Picture()
        picture.set_can_shrink(True)
        picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        picture.set_halign(Gtk.Align.CENTER)
        picture.set_valign(Gtk.Align.START)
        picture.set_hexpand(False)
        picture.set_vexpand(False)
        picture.add_css_class("quick-look-pdf-page")
        
        page_box.append(picture)
        scroll.set_child(page_box)
        container.append(scroll)
        
        self.body_container.append(container)
        
        self._pdf_picture = picture
        self._pdf_page_label = page_lbl
        self._pdf_prev_btn = prev_btn
        self._pdf_next_btn = next_btn
        self._pdf_scroll = scroll
        self._pdf_toolbar = toolbar
        self._pdf_zoom_label = zoom_lbl_btn
        self._pdf_zoom_in_btn = zoom_in_btn
        self._pdf_zoom_out_btn = zoom_out_btn
        self._pdf_fit_btn = fit_btn
        
        def _on_scroll_notify(sc, pspec):
            w = sc.get_allocated_width()
            if w > 400 and abs(w - getattr(self, "_last_scroll_w", 0)) > 30:
                self._last_scroll_w = w
                if getattr(self, "_pdf_fit_mode", "width") == "width":
                    self._update_pdf_page_size()
        scroll.connect("notify::allocated-width", _on_scroll_notify)
        
        self._add_badge("PDF")
        self._add_badge(size_str)
        
        def _async_init_pdf():
            import subprocess, re
            total_pages = 1
            try:
                res = subprocess.run(["pdfinfo", path], capture_output=True, text=True, timeout=2)
                if res.returncode == 0:
                    for line in res.stdout.splitlines():
                        if line.startswith("Pages:"):
                            total_pages = int(line.split(":", 1)[1].strip())
                            break
            except Exception:
                pass
                
            if total_pages <= 1:
                try:
                    with open(path, "rb") as f:
                        buf = f.read(1024 * 1024)
                        m = re.findall(rb"/Count\s+(\d+)", buf)
                        if m:
                            total_pages = max(int(x) for x in m)
                except Exception:
                    pass
                    
            def _apply_init():
                if self._load_generation == generation and self.is_visible() and getattr(self, "_pdf_path", None) == path:
                    self._pdf_total_pages = max(1, total_pages)
                    if total_pages <= 1:
                        prev_btn.set_visible(False)
                        page_lbl.set_visible(False)
                        next_btn.set_visible(False)
                        sep1.set_visible(False)
                    else:
                        prev_btn.set_visible(True)
                        page_lbl.set_visible(True)
                        next_btn.set_visible(True)
                        sep1.set_visible(True)
                    self._update_pdf_controls()
                    cur_lang = get_current_language()
                    pages_label = "стр." if cur_lang in ("ru", "kk", "uk", "be") else "pages"
                    self._add_badge(f"{total_pages} {pages_label}")
                    self._load_pdf_page(1)
                return False
                
            GLib.idle_add(_apply_init)
            
        threading.Thread(target=_async_init_pdf, daemon=True).start()

    def _get_base_width(self) -> int:
        if getattr(self, "_pdf_scroll", None):
            w = self._pdf_scroll.get_allocated_width()
            if w > 300:
                return max(360, min(1400, w - 80))
        return getattr(self, "_current_content_w", 980) - 80

    def _update_pdf_page_size(self):
        if not getattr(self, "_pdf_picture", None):
            return
            
        aspect = getattr(self, "_pdf_aspect", 1.414)
        base_w = self._get_base_width()
        zoom = getattr(self, "_pdf_zoom", 1.0)
        
        pw = max(180, int(base_w * zoom))
        ph = int(pw * aspect)
        
        self._pdf_picture.set_size_request(pw, ph)
        self._pdf_picture.set_can_shrink(True)
        self._pdf_picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        
        if getattr(self, "_pdf_zoom_label", None):
            pct = int(zoom * 100)
            self._pdf_zoom_label.set_label(f"{pct}%")

    def _pdf_zoom_in(self):
        self._pdf_fit_mode = "custom"
        self._pdf_zoom = min(3.0, round(getattr(self, "_pdf_zoom", 1.0) + 0.15, 2))
        self._update_pdf_page_size()

    def _pdf_zoom_out(self):
        self._pdf_fit_mode = "custom"
        self._pdf_zoom = max(0.25, round(getattr(self, "_pdf_zoom", 1.0) - 0.15, 2))
        self._update_pdf_page_size()

    def _pdf_zoom_reset(self):
        self._pdf_fit_mode = "width"
        self._pdf_zoom = 1.0
        self._update_pdf_page_size()

    def _pdf_toggle_fit(self):
        if not getattr(self, "_pdf_picture", None):
            return
        if getattr(self, "_pdf_fit_mode", "width") == "width":
            self._pdf_fit_mode = "page"
            aspect = getattr(self, "_pdf_aspect", 1.414)
            alloc_h = self._pdf_scroll.get_allocated_height() if self._pdf_scroll else 650
            target_h = max(350, alloc_h - 40)
            target_w = int(target_h / aspect)
            base_w = self._get_base_width()
            self._pdf_zoom = max(0.3, round(target_w / base_w, 2))
        else:
            self._pdf_fit_mode = "width"
            self._pdf_zoom = 1.0
        self._update_pdf_page_size()

    def _update_pdf_controls(self):
        if not getattr(self, "_pdf_page_label", None):
            return
        cur = getattr(self, "_pdf_current_page", 1)
        total = getattr(self, "_pdf_total_pages", 1)
        cur_lang = get_current_language()
        prefix = "Стр." if cur_lang in ("ru", "kk", "uk", "be") else "Page"
        self._pdf_page_label.set_text(f"{prefix} {cur} / {total}")
        if getattr(self, "_pdf_prev_btn", None):
            self._pdf_prev_btn.set_sensitive(cur > 1)
        if getattr(self, "_pdf_next_btn", None):
            self._pdf_next_btn.set_sensitive(cur < total)

    def _on_pdf_prev_page(self):
        if not getattr(self, "_pdf_path", None) or self._pdf_current_page <= 1:
            return False
        self._pdf_current_page -= 1
        self._load_pdf_page(self._pdf_current_page)
        return True

    def _on_pdf_next_page(self):
        if not getattr(self, "_pdf_path", None) or self._pdf_current_page >= getattr(self, "_pdf_total_pages", 1):
            return False
        self._pdf_current_page += 1
        self._load_pdf_page(self._pdf_current_page)
        return True

    def _load_pdf_page(self, page_num: int):
        path = getattr(self, "_pdf_path", None)
        gen = getattr(self, "_pdf_gen", 0)
        if not path:
            return
        self._update_pdf_controls()
        
        def _async_worker():
            import hashlib, subprocess, tempfile, glob
            try:
                cache_dir = os.path.join(tempfile.gettempdir(), "echo_quicklook_pdf")
                os.makedirs(cache_dir, exist_ok=True)
                
                mtime = os.path.getmtime(path)
                h = hashlib.md5(f"{path}_{mtime}_{page_num}".encode("utf-8")).hexdigest()
                cached_png = os.path.join(cache_dir, f"{h}.png")
                
                if not os.path.exists(cached_png):
                    out_prefix = os.path.join(cache_dir, f"tmp_{h}")
                    cmd = ["pdftoppm", "-png", "-r", "150", "-f", str(page_num), "-l", str(page_num), path, out_prefix]
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                    matched = glob.glob(f"{out_prefix}*.png")
                    if matched:
                        os.replace(matched[0], cached_png)
                        
                if os.path.exists(cached_png):
                    aspect = 1.414
                    try:
                        from gi.repository import GdkPixbuf
                        info, img_w, img_h = GdkPixbuf.Pixbuf.get_file_info(cached_png)
                        if info and img_w > 0:
                            aspect = img_h / img_w
                    except Exception:
                        pass
                        
                    def _update_ui():
                        if (self._load_generation == gen and self.is_visible() and 
                                getattr(self, "_pdf_path", None) == path and 
                                getattr(self, "_pdf_current_page", 1) == page_num):
                            self._pdf_aspect = aspect
                            self._pdf_cached_file = cached_png
                            self._pdf_picture.set_filename(cached_png)
                            self._update_pdf_page_size()
                            if self._pdf_scroll:
                                vadj = self._pdf_scroll.get_vadjustment()
                                if vadj:
                                    vadj.set_value(0)
                        return False
                    GLib.idle_add(_update_ui)
            except Exception:
                pass
                
        threading.Thread(target=_async_worker, daemon=True).start()

    def _render_document_view(self, path: str, generation: int, ext: str, size_str: str, mime: str = "", mtime: str = ""):
        scroll = Gtk.ScrolledWindow()
        scroll.add_css_class("quick-look-doc-scroll")
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        content_w = getattr(self, "_current_content_w", 980)
        content_h = getattr(self, "_current_content_h", 670)
        scroll.set_size_request(content_w, content_h)
        
        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_cursor_visible(False)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        text_view.add_css_class("quick-look-doc-view")
        scroll.set_child(text_view)
        
        self.body_container.append(scroll)
        self._add_badge(ext.upper()[1:] if ext else "DOC")
        self._add_badge(size_str)
        
        def _async_load_doc():
            content = None
            try:
                if ext == ".docx":
                    import zipfile, xml.etree.ElementTree as ET
                    with zipfile.ZipFile(path) as z:
                        xml_content = z.read("word/document.xml")
                        tree = ET.fromstring(xml_content)
                        paragraphs = []
                        for p in tree.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                            texts = [node.text for node in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t") if node.text]
                            if texts:
                                paragraphs.append("".join(texts))
                        content = "\n\n".join(paragraphs)
                elif ext == ".odt":
                    import zipfile, xml.etree.ElementTree as ET
                    with zipfile.ZipFile(path) as z:
                        xml_content = z.read("content.xml")
                        tree = ET.fromstring(xml_content)
                        paragraphs = []
                        for p in tree.iter("{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p"):
                            text = "".join(p.itertext())
                            if text:
                                paragraphs.append(text)
                        content = "\n\n".join(paragraphs)
                elif ext == ".rtf":
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        raw = f.read(50000)
                        import re
                        content = re.sub(r"\\[a-z0-9\-]+", " ", raw)
                        content = re.sub(r"[{}]", "", content)
                        content = re.sub(r"\s+", " ", content).strip()
                elif ext in (".epub", ".fb2"):
                    if ext == ".fb2":
                        import xml.etree.ElementTree as ET
                        tree = ET.parse(path)
                        content = "\n\n".join(p.text for p in tree.iter() if p.tag.endswith("p") and p.text)
                    elif ext == ".epub":
                        import zipfile, re
                        with zipfile.ZipFile(path) as z:
                            html_files = [n for n in z.namelist() if n.endswith((".html", ".xhtml"))]
                            texts = []
                            for hf in html_files[:10]:
                                html_text = z.read(hf).decode("utf-8", errors="ignore")
                                clean_text = re.sub(r"<[^>]+>", " ", html_text)
                                clean_text = re.sub(r"\s+", " ", clean_text).strip()
                                if clean_text:
                                    texts.append(clean_text)
                            content = "\n\n".join(texts)
            except Exception:
                pass
                
            if not content:
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        content = "".join([f.readline() for _ in range(250)])
                except Exception:
                    pass
                    
            def _update_ui():
                if self._load_generation == generation and self.is_visible():
                    buffer = text_view.get_buffer()
                    if content and content.strip():
                        buffer.set_text(content)
                        lines = content.count("\n") + 1
                        self._add_badge(f"{lines} {t('label_lines')}")
                    else:
                        cur_lang = get_current_language()
                        no_preview_text = "Предпросмотр содержимого недоступен" if cur_lang in ("ru", "kk", "uk", "be") else "Content preview unavailable"
                        buffer.set_text(no_preview_text)
                return False
                
            GLib.idle_add(_update_ui)
            
        threading.Thread(target=_async_load_doc, daemon=True).start()

    def _init_syntax_tags(self, buffer):
        tags = {
            "tok_kw": {"foreground": "#ff7b72", "weight": Pango.Weight.BOLD},
            "tok_str": {"foreground": "#a5d6ff"},
            "tok_comment": {"foreground": "#8b949e", "style": Pango.Style.ITALIC},
            "tok_fn": {"foreground": "#d2a8ff", "weight": Pango.Weight.BOLD},
            "tok_num": {"foreground": "#79c0ff"},
            "tok_op": {"foreground": "#ff7b72"},
            "tok_builtin": {"foreground": "#ffa657"},
            "tok_var": {"foreground": "#7ee787"},
            "tok_type": {"foreground": "#e3b341", "weight": Pango.Weight.BOLD},
            "tok_tag": {"foreground": "#7ee787"},
        }
        table = buffer.get_tag_table()
        for name, props in tags.items():
            if not table.lookup(name):
                buffer.create_tag(name, **props)

    def _apply_syntax_highlight(self, buffer, content: str, lexer):
        if not PYGMENTS_AVAILABLE or not content or not lexer:
            return
        if len(content) > 300_000:
            return
        try:
            buffer.remove_all_tags(buffer.get_start_iter(), buffer.get_end_iter())
            tokens = list(lex(content, lexer))
            iter_cur = buffer.get_start_iter()
            
            for ttype, val in tokens:
                length = len(val)
                if length == 0:
                    continue
                tag_name = None
                if ttype in Token.Keyword or ttype in Token.Operator.Word:
                    tag_name = "tok_kw"
                elif ttype in Token.String:
                    tag_name = "tok_str"
                elif ttype in Token.Comment:
                    tag_name = "tok_comment"
                elif ttype in (Token.Name.Function, Token.Name.Class, Token.Name.Decorator):
                    tag_name = "tok_fn"
                elif ttype in Token.Number:
                    tag_name = "tok_num"
                elif ttype in Token.Operator:
                    tag_name = "tok_op"
                elif ttype in Token.Name.Builtin:
                    tag_name = "tok_builtin"
                elif ttype in Token.Name.Variable or ttype in Token.Name.Attribute:
                    tag_name = "tok_var"
                elif ttype in Token.Name.Constant or ttype in Token.Name.Entity or ttype in Token.Keyword.Type:
                    tag_name = "tok_type"
                elif ttype in Token.Name.Tag:
                    tag_name = "tok_tag"

                end_iter = iter_cur.copy()
                end_iter.forward_chars(length)
                if tag_name:
                    buffer.apply_tag_by_name(tag_name, iter_cur, end_iter)
                iter_cur = end_iter
        except Exception:
            pass

    def _update_line_numbers(self, total_lines: int):
        if not getattr(self, "_text_line_numbers_tv", None):
            return
        buf = self._text_line_numbers_tv.get_buffer()
        max_display = min(total_lines, 5000)
        nums = chr(10).join(str(i) for i in range(1, max_display + 1))
        buf.set_text(nums)

    def _update_editor_status(self, saved=False):
        dirty = getattr(self, "_text_dirty", False)
        
        if getattr(self, "save_btn", None):
            if dirty:
                self.save_btn.set_label(f"💾 {t('action_save')} Ctrl+S")
                self.save_btn.add_css_class("primary-action")
            elif saved:
                self.save_btn.set_label(f"✓ {t('label_saved')}")
                self.save_btn.remove_css_class("primary-action")
            else:
                self.save_btn.set_label(f"💾 {t('action_save')} Ctrl+S")
                self.save_btn.remove_css_class("primary-action")
                
        if getattr(self, "_text_save_btn", None):
            if dirty:
                self._text_save_btn.add_css_class("dirty")
                self._text_save_btn.set_label(f"💾 {t('action_save')}")
            elif saved:
                self._text_save_btn.remove_css_class("dirty")
                self._text_save_btn.set_label(f"✓ {t('label_saved')}")
            else:
                self._text_save_btn.remove_css_class("dirty")
                self._text_save_btn.set_label(f"💾 {t('action_save')}")
                
        if getattr(self, "_text_status_badge", None):
            if dirty:
                self._text_status_badge.set_label(f"● {t('label_unsaved')}")
                self._text_status_badge.remove_css_class("quick-look-editor-saved-badge")
                self._text_status_badge.add_css_class("quick-look-editor-dirty-badge")
                self._text_status_badge.set_visible(True)
            elif saved:
                self._text_status_badge.set_label(f"✓ {t('label_saved')}")
                self._text_status_badge.remove_css_class("quick-look-editor-dirty-badge")
                self._text_status_badge.add_css_class("quick-look-editor-saved-badge")
                self._text_status_badge.set_visible(True)
            else:
                self._text_status_badge.set_visible(False)

    def _on_text_buffer_changed(self, buffer):
        if not getattr(self, "_text_editor_active", False):
            return
        if not getattr(self, "_text_dirty", False):
            self._text_dirty = True
            self._update_editor_status()
            
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        curr_lines = text.count(chr(10)) + 1
        if curr_lines != getattr(self, "_text_total_lines", 0):
            self._text_total_lines = curr_lines
            self._update_line_numbers(curr_lines)
            if getattr(self, "_text_stat_label", None):
                self._text_stat_label.set_label(f"{curr_lines} {t('label_lines')}")
                
        if getattr(self, "_text_rehighlight_source_id", None):
            try:
                GLib.source_remove(self._text_rehighlight_source_id)
            except Exception:
                pass
            self._text_rehighlight_source_id = None
            
        if getattr(self, "_text_lexer", None):
            def _rehighlight_worker():
                self._text_rehighlight_source_id = None
                if getattr(self, "_text_editor_active", False) and self._text_buffer == buffer:
                    txt = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
                    self._apply_syntax_highlight(buffer, txt, self._text_lexer)
                return False
            self._text_rehighlight_source_id = GLib.timeout_add(350, _rehighlight_worker)

    def _on_text_mark_set(self, buffer, location, mark):
        if mark.get_name() == "insert" and getattr(self, "_text_cursor_label", None):
            line = location.get_line() + 1
            col = location.get_line_offset() + 1
            self._text_cursor_label.set_label(f"Ln {line}, Col {col}")

    def _save_text_file(self):
        if not getattr(self, "_text_editor_active", False) or not getattr(self, "_text_path", None):
            return
        if not getattr(self, "_text_buffer", None):
            return
            
        buf = self._text_buffer
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        path = self._text_path
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self._text_dirty = False
            self._update_editor_status(saved=True)
            
            try:
                stat = os.stat(path)
                size_bytes = stat.st_size
                for unit in ["B", "KB", "MB", "GB", "TB"]:
                    if size_bytes < 1024.0:
                        formatted_size = f"{size_bytes:.1f} {unit}"
                        break
                    size_bytes /= 1024.0
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
                guessed_mime, _ = mimetypes.guess_type(path)
                mime = guessed_mime or "text/plain"
                self.subtitle_label.set_label(f"{mime} • {formatted_size} • {mtime}")
            except Exception:
                pass
                
            def _reset_saved_badge():
                if not getattr(self, "_text_dirty", False) and getattr(self, "_text_status_badge", None):
                    self._text_status_badge.set_visible(False)
                return False
            GLib.timeout_add(2500, _reset_saved_badge)
                
        except Exception as e:
            if getattr(self, "_text_status_badge", None):
                self._text_status_badge.set_label(f"Ошибка: {str(e)[:25]}")
                self._text_status_badge.remove_css_class("quick-look-editor-saved-badge")
                self._text_status_badge.add_css_class("quick-look-editor-dirty-badge")
                self._text_status_badge.set_visible(True)

    def _render_text_view(self, path: str, generation: int, ext: str):
        self._text_editor_active = True
        self._text_path = path
        self._text_dirty = False
        self._text_total_lines = 1
        
        content_w = getattr(self, "_current_content_w", 980)
        content_h = getattr(self, "_current_content_h", 670)
        
        editor_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        editor_card.add_css_class("quick-look-editor-card")
        editor_card.set_vexpand(True)
        editor_card.set_hexpand(True)
        editor_card.set_size_request(content_w, content_h)
        
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toolbar.add_css_class("quick-look-editor-toolbar")
        
        try:
            lexer = get_lexer_for_filename(path, "") if PYGMENTS_AVAILABLE else None
            lexer_name = lexer.name if lexer else (ext.upper()[1:] if ext else "Text")
        except Exception:
            lexer = TextLexer() if PYGMENTS_AVAILABLE else None
            lexer_name = ext.upper()[1:] if ext else "Text"
            
        self._text_lexer = lexer
        
        lang_badge = Gtk.Label(label=lexer_name)
        lang_badge.add_css_class("quick-look-badge")
        toolbar.append(lang_badge)
        
        self._text_stat_label = Gtk.Label(label=f"1 {t('label_lines')}")
        self._text_stat_label.add_css_class("quick-look-editor-stat")
        toolbar.append(self._text_stat_label)
        
        self._text_cursor_label = Gtk.Label(label="Ln 1, Col 1")
        self._text_cursor_label.add_css_class("quick-look-editor-stat")
        toolbar.append(self._text_cursor_label)
        
        enc_lbl = Gtk.Label(label="UTF-8")
        enc_lbl.add_css_class("quick-look-editor-stat")
        toolbar.append(enc_lbl)
        
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        toolbar.append(spacer)
        
        self._text_status_badge = Gtk.Label(label="")
        self._text_status_badge.set_visible(False)
        toolbar.append(self._text_status_badge)
        
        self._text_save_btn = Gtk.Button(label=f"💾 {t('action_save')}")
        self._text_save_btn.add_css_class("quick-look-save-btn")
        self._text_save_btn.set_tooltip_text(f"{t('action_save')} (Ctrl+S)")
        self._text_save_btn.connect("clicked", lambda b: self._save_text_file())
        toolbar.append(self._text_save_btn)
        
        editor_card.append(toolbar)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        content_box.set_vexpand(True)
        content_box.set_hexpand(True)
        
        lines_tv = Gtk.TextView()
        lines_tv.set_editable(False)
        lines_tv.set_can_focus(False)
        lines_tv.set_monospace(True)
        lines_tv.add_css_class("quick-look-line-numbers")
        self._text_line_numbers_tv = lines_tv
        content_box.append(lines_tv)
        
        scroll = Gtk.ScrolledWindow()
        scroll.add_css_class("quick-look-text-scroll")
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        
        text_view = Gtk.TextView()
        text_view.set_editable(True)
        text_view.set_cursor_visible(True)
        text_view.set_monospace(True)
        text_view.set_accepts_tab(True)
        text_view.set_wrap_mode(Gtk.WrapMode.NONE)
        text_view.add_css_class("quick-look-code-view")
        scroll.set_child(text_view)
        content_box.append(scroll)
        
        lines_tv.set_vadjustment(scroll.get_vadjustment())
        
        editor_card.append(content_box)
        self.body_container.append(editor_card)
        
        self._text_view = text_view
        buffer = text_view.get_buffer()
        self._text_buffer = buffer
        self._init_syntax_tags(buffer)
        
        if getattr(self, "save_btn", None):
            self.save_btn.set_visible(True)
            self._update_editor_status()
            
        def _async_read_text():
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content_str = f.read(5 * 1024 * 1024)
                total_lines = content_str.count(chr(10)) + 1
                
                def _update_ui():
                    if self._load_generation == generation and self.is_visible() and getattr(self, "_text_path", None) == path:
                        buffer.set_text(content_str)
                        self._text_dirty = False
                        self._text_total_lines = total_lines
                        self._update_line_numbers(total_lines)
                        self._apply_syntax_highlight(buffer, content_str, lexer)
                        
                        if getattr(self, "_text_stat_label", None):
                            self._text_stat_label.set_label(f"{total_lines} {t('label_lines')}")
                        self._add_badge(lexer_name)
                        self._add_badge(f"{total_lines} {t('label_lines')}")
                        
                        buffer.connect("changed", self._on_text_buffer_changed)
                        buffer.connect("mark-set", self._on_text_mark_set)
                        self._update_editor_status()
                    return False
                    
                GLib.idle_add(_update_ui)
            except Exception:
                pass
                
        threading.Thread(target=_async_read_text, daemon=True).start()

    def _render_generic_view(self, path: str, generation: int, mime: str, size_str: str, mtime: str):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.add_css_class("quick-look-generic-box")
        box.set_vexpand(True)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        box.set_size_request(getattr(self, "_current_content_w", 760), getattr(self, "_current_content_h", 430))
        
        icon = Gtk.Image.new_from_icon_name("package-x-generic")
        icon.set_pixel_size(96)
        box.append(icon)
        
        path_lbl = Gtk.Label(label=path)
        path_lbl.add_css_class("quick-look-path-label")
        path_lbl.set_wrap(True)
        path_lbl.set_max_width_chars(60)
        box.append(path_lbl)
        
        self._add_badge(size_str)
        self._add_badge(mtime)
        
        self.body_container.append(box)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        focus = self.get_focus()
        is_editor_focused = isinstance(focus, Gtk.TextView) and focus.get_editable()
        
        # Save shortcut (Ctrl+S / Ctrl+Ы)
        if (keyval in (Gdk.KEY_s, Gdk.KEY_S, Gdk.KEY_Cyrillic_yeru, Gdk.KEY_Cyrillic_YERU)) and (state & Gdk.ModifierType.CONTROL_MASK):
            if getattr(self, "_text_editor_active", False):
                self._save_text_file()
                return True
                
        # If text editor is focused, do not let typing space close preview
        if is_editor_focused:
            if keyval == Gdk.KEY_Escape:
                self.hide_preview()
                return True
            return False

        if keyval == Gdk.KEY_space:
            if time.time() - getattr(self, "_opened_timestamp", 0) < 0.2:
                return True
            self.hide_preview()
            return True
            
        elif keyval == Gdk.KEY_Escape:
            self.hide_preview()
            return True
            
        elif keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            if state & Gdk.ModifierType.SHIFT_MASK:
                self._on_reveal_clicked(None)
            else:
                self._on_open_clicked(None)
            return True
            
        elif (keyval in (Gdk.KEY_c, Gdk.KEY_C, Gdk.KEY_Cyrillic_es, Gdk.KEY_Cyrillic_ES)) and (state & Gdk.ModifierType.CONTROL_MASK):
            self._on_copy_clicked(None)
            return True
            
        elif (keyval in (Gdk.KEY_t, Gdk.KEY_T, Gdk.KEY_Cyrillic_ie, Gdk.KEY_Cyrillic_IE)) and (state & Gdk.ModifierType.CONTROL_MASK):
            self._on_terminal_clicked(None)
            return True
            
        elif keyval in (Gdk.KEY_Left, Gdk.KEY_Page_Up):
            if getattr(self, "_pdf_path", None):
                if self._on_pdf_prev_page():
                    return True

        elif keyval in (Gdk.KEY_Right, Gdk.KEY_Page_Down):
            if getattr(self, "_pdf_path", None):
                if self._on_pdf_next_page():
                    return True

        elif keyval in (Gdk.KEY_f, Gdk.KEY_F, Gdk.KEY_F11, Gdk.KEY_Cyrillic_a, Gdk.KEY_Cyrillic_A):
            self._toggle_maximize()
            return True

        elif keyval in (Gdk.KEY_plus, Gdk.KEY_equal, Gdk.KEY_KP_Add):
            if getattr(self, "_pdf_path", None):
                self._pdf_zoom_in()
                return True

        elif keyval in (Gdk.KEY_minus, Gdk.KEY_underscore, Gdk.KEY_KP_Subtract):
            if getattr(self, "_pdf_path", None):
                self._pdf_zoom_out()
                return True

        elif keyval in (Gdk.KEY_0, Gdk.KEY_KP_0):
            if getattr(self, "_pdf_path", None):
                self._pdf_zoom_reset()
                return True

        elif keyval in (Gdk.KEY_w, Gdk.KEY_W, Gdk.KEY_Cyrillic_tse, Gdk.KEY_Cyrillic_TSE):
            if getattr(self, "_pdf_path", None):
                self._pdf_toggle_fit()
                return True

        elif keyval in (Gdk.KEY_Up, Gdk.KEY_Down):
            # Forward arrow keys to parent mode to navigate to next file
            if self.parent_window and hasattr(self.parent_window, "mode_manager"):
                self.parent_window.mode_manager.on_key_pressed(keyval, state)
                mode = self.parent_window.mode_manager.get_active_mode()
                if hasattr(mode, "current_results") and hasattr(mode, "selected_index"):
                    idx = mode.selected_index
                    if 0 <= idx < len(mode.current_results):
                        self.preview_result(mode.current_results[idx])
                elif hasattr(mode, "suggestions_flowbox"):
                    sel = mode.suggestions_flowbox.get_selected_children() or mode.recents_flowbox.get_selected_children()
                    if sel and getattr(sel[0], "result", None):
                        self.preview_result(sel[0].result)
            return True
            
        return False



    def _on_open_clicked(self, btn):
        if self.current_result:
            self.current_result.execute()
        elif self.current_path:
            subprocess.Popen(["xdg-open", self.current_path], start_new_session=True)
        self.hide_preview()
        if self.parent_window:
            self.parent_window.hide()

    def _on_reveal_clicked(self, btn):
        if self.current_result:
            self.current_result.open_location()
        elif self.current_path:
            target = self.current_path if os.path.isdir(self.current_path) else os.path.dirname(self.current_path)
            subprocess.Popen(["xdg-open", target], start_new_session=True)
        self.hide_preview()
        if self.parent_window:
            self.parent_window.hide()

    def _on_terminal_clicked(self, btn):
        if self.current_path:
            target_dir = self.current_path if os.path.isdir(self.current_path) else os.path.dirname(self.current_path)
            terminals = ["x-terminal-emulator", "gnome-terminal", "kitty", "alacritty", "foot", "konsole", "xfce4-terminal"]
            for term in terminals:
                if subprocess.call(["which", term], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                    subprocess.Popen([term, "--working-directory", target_dir], start_new_session=True)
                    break
        self.hide_preview()
        if self.parent_window:
            self.parent_window.hide()

    def _on_copy_clicked(self, btn):
        if self.current_path:
            display = Gdk.Display.get_default()
            if display:
                display.get_clipboard().set(self.current_path)
        self.hide_preview()

    def hide_preview(self):
        self._cleanup_media()
        if self.is_maximized():
            self.unmaximize()
            if hasattr(self, "maximize_btn") and self.maximize_btn:
                self.maximize_btn.set_icon_name("view-fullscreen-symbolic")
        self.hide()
        self._load_generation += 1
        if self.parent_window and hasattr(self.parent_window, "entry"):
            self.parent_window.entry.grab_focus()
