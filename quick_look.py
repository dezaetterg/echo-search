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

from i18n import t

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".bmp", ".ico", ".tiff", ".avif"}
CODE_EXTENSIONS = {
    ".py", ".json", ".md", ".txt", ".sh", ".bash", ".zsh", ".js", ".ts", ".jsx", ".tsx",
    ".html", ".css", ".scss", ".xml", ".yaml", ".yml", ".toml", ".ini", ".conf", ".c",
    ".cpp", ".h", ".hpp", ".rs", ".go", ".java", ".kt", ".lua", ".sql", ".diff", ".patch"
}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".opus", ".wma"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv", ".wmv", ".m4v"}

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
        
        self.set_title("Quick Look")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(780, 560)
        
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
        self.connect("notify::is-active", self._on_is_active_changed)
        
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
        
        # Close button
        close_btn = Gtk.Button()
        close_btn.add_css_class("quick-look-close-btn")
        close_btn.set_icon_name("window-close-symbolic")
        close_btn.connect("clicked", lambda b: self.hide_preview())
        self.header_box.append(close_btn)
        
        self.card_box.append(self.header_box)
        
    def _build_footer(self):
        self.footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.footer_box.add_css_class("quick-look-footer")
        
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
        
        hint_lbl = Gtk.Label(label=f"[Space / Esc] {t("action_close")}")
        hint_lbl.add_css_class("quick-look-hint")
        self.footer_box.append(hint_lbl)
        
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
        
        filename = os.path.basename(path) or path
        is_directory = os.path.isdir(path)
        ext = "" if is_directory else os.path.splitext(path)[1].lower()
        self.title_label.set_label(filename)
        
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
            
        if is_directory:
            self._render_folder_view(path, gen)
        elif ext in VIDEO_EXTENSIONS or mime.startswith("video/"):
            self._render_video_view(path, gen, ext, mime, formatted_size)
        elif ext in AUDIO_EXTENSIONS or mime.startswith("audio/"):
            self._render_audio_view(path, gen, ext, mime, formatted_size)
        elif ext in IMAGE_EXTENSIONS:
            self._render_image_view(path, gen, formatted_size)
        elif ext in CODE_EXTENSIONS or mime.startswith("text/"):
            self._render_text_view(path, gen, ext)
        else:
            self._render_generic_view(path, gen, mime, formatted_size, mtime)
            
        self.present()
        return True

    def _render_folder_view(self, path: str, generation: int):
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        container.add_css_class("quick-look-folder-container")
        container.set_vexpand(True)
        container.set_hexpand(True)
        container.set_size_request(740, 380)
        
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
        hero_box.set_size_request(740, 380)
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
        video_box.set_size_request(740, 380)
        
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
        img_box.set_size_request(740, 380)
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

    def _render_text_view(self, path: str, generation: int, ext: str):
        scroll = Gtk.ScrolledWindow()
        scroll.add_css_class("quick-look-text-scroll")
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        scroll.set_size_request(740, 380)
        
        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_cursor_visible(False)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        text_view.set_monospace(True)
        text_view.add_css_class("quick-look-code-view")
        scroll.set_child(text_view)
        
        self.body_container.append(scroll)
        
        def _async_read_text():
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    lines = [f.readline() for _ in range(350)]
                content = "".join(lines)
                total_lines = len(lines)
                
                def _update_text():
                    if self._load_generation == generation and self.is_visible():
                        buffer = text_view.get_buffer()
                        buffer.set_text(content)
                        self._add_badge(f"{ext.upper()[1:] if ext else "TXT"}")
                        self._add_badge(f"{total_lines} {t("label_lines")}")
                    return False
                    
                GLib.idle_add(_update_text)
            except Exception:
                pass
                
        threading.Thread(target=_async_read_text, daemon=True).start()

    def _render_generic_view(self, path: str, generation: int, mime: str, size_str: str, mtime: str):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.add_css_class("quick-look-generic-box")
        box.set_vexpand(True)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        box.set_size_request(740, 380)
        
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

    def _on_is_active_changed(self, window, param):
        try:
            if not self.is_active() and self.is_visible():
                def _check_focus():
                    if self.is_visible() and not self.is_active():
                        if not (self.parent_window and self.parent_window.is_active()):
                            self.hide_preview()
                            if self.parent_window:
                                self.parent_window.hide()
                    return False
                GLib.timeout_add(150, _check_focus)
        except Exception:
            pass

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
        self.hide()
        self._load_generation += 1
        if self.parent_window and hasattr(self.parent_window, "entry"):
            self.parent_window.entry.grab_focus()
