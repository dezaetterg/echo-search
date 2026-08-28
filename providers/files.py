import functools
from pathlib import Path
import os
import urllib.parse
import mimetypes
import threading
import subprocess
import time
from datetime import datetime
from .base import BaseProvider, SearchResult

try:
    import gi
    gi.require_version("GLib", "2.0")
    gi.require_version("Gtk", "4.0")
    from gi.repository import GLib, Gio, Gtk, Gdk, GObject
except (ValueError, ImportError):
    pass

try:
    gi.require_version("Tracker", "3.0")
    from gi.repository import Tracker
except (ValueError, ImportError):
    Tracker = None

RU_TO_EN = str.maketrans(
    "йцукенгшщзхъфывапролджэячсмитьбюё",
    "qwertyuiop[]asdfghjkl;\x27zxcvbnm,.~"
)
EN_TO_RU = str.maketrans(
    "qwertyuiop[]asdfghjkl;\x27zxcvbnm,.~",
    "йцукенгшщзхъфывапролджэячсмитьбюё"
)

# Common directory blacklists to avoid wasting CPU/RAM on build artifacts, runtimes, and caches
IGNORE_DIRS = {
    ".git", ".cache", ".local", ".cargo", ".rustup", ".npm", ".nvm",
    "node_modules", "venv", ".venv", "env", "__pycache__", "target", "build",
    "dist", ".gemini", ".vscode", ".idea", ".mozilla", ".thunderbird", ".var",
    ".wine", ".steam", ".flatpak", "flatpak", ".gradle", ".m2", ".dart_tool",
    ".android", ".composer", "vendor"
}

# Fast extension to MIME and category lookup table
EXT_MAP = {
    # PDF
    ".pdf": ("application/pdf", "PDF"),
    ".djvu": ("image/vnd.djvu", "Documents"),
    ".epub": ("application/epub+zip", "Documents"),
    ".mobi": ("application/x-mobipocket-ebook", "Documents"),
    ".fb2": ("application/x-fictionbook+xml", "Documents"),
    # Documents
    ".doc": ("application/msword", "Documents"),
    ".docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "Documents"),
    ".odt": ("application/vnd.oasis.opendocument.text", "Documents"),
    ".rtf": ("application/rtf", "Documents"),
    ".txt": ("text/plain", "Documents"),
    ".md": ("text/markdown", "Documents"),
    ".markdown": ("text/markdown", "Documents"),
    ".rst": ("text/x-rst", "Documents"),
    ".tex": ("application/x-tex", "Documents"),
    ".xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "Documents"),
    ".xls": ("application/vnd.ms-excel", "Documents"),
    ".ods": ("application/vnd.oasis.opendocument.spreadsheet", "Documents"),
    ".csv": ("text/csv", "Documents"),
    ".tsv": ("text/tab-separated-values", "Documents"),
    ".pptx": ("application/vnd.openxmlformats-officedocument.presentationml.presentation", "Documents"),
    ".ppt": ("application/vnd.ms-powerpoint", "Documents"),
    ".odp": ("application/vnd.oasis.opendocument.presentation", "Documents"),
    # Images
    ".png": ("image/png", "Images"),
    ".jpg": ("image/jpeg", "Images"),
    ".jpeg": ("image/jpeg", "Images"),
    ".webp": ("image/webp", "Images"),
    ".svg": ("image/svg+xml", "Images"),
    ".gif": ("image/gif", "Images"),
    ".bmp": ("image/bmp", "Images"),
    ".ico": ("image/x-icon", "Images"),
    ".tiff": ("image/tiff", "Images"),
    ".tif": ("image/tiff", "Images"),
    ".avif": ("image/avif", "Images"),
    ".heic": ("image/heic", "Images"),
    ".heif": ("image/heif", "Images"),
    ".raw": ("image/x-raw", "Images"),
    ".cr2": ("image/x-canon-cr2", "Images"),
    ".nef": ("image/x-nikon-nef", "Images"),
    ".dng": ("image/x-adobe-dng", "Images"),
    # Audio
    ".mp3": ("audio/mpeg", "Audio"),
    ".wav": ("audio/wav", "Audio"),
    ".flac": ("audio/flac", "Audio"),
    ".ogg": ("audio/ogg", "Audio"),
    ".m4a": ("audio/mp4", "Audio"),
    ".aac": ("audio/aac", "Audio"),
    ".opus": ("audio/opus", "Audio"),
    ".wma": ("audio/x-ms-wma", "Audio"),
    ".mid": ("audio/midi", "Audio"),
    ".midi": ("audio/midi", "Audio"),
    # Video
    ".mp4": ("video/mp4", "Videos"),
    ".mkv": ("video/x-matroska", "Videos"),
    ".webm": ("video/webm", "Videos"),
    ".avi": ("video/x-msvideo", "Videos"),
    ".mov": ("video/quicktime", "Videos"),
    ".wmv": ("video/x-ms-wmv", "Videos"),
    ".flv": ("video/x-flv", "Videos"),
    ".m4v": ("video/x-m4v", "Videos"),
    ".ts": ("video/mp2t", "Videos"),
    # Archives
    ".zip": ("application/zip", "Archives"),
    ".rar": ("application/vnd.rar", "Archives"),
    ".7z": ("application/x-7z-compressed", "Archives"),
    ".tar": ("application/x-tar", "Archives"),
    ".gz": ("application/gzip", "Archives"),
    ".tgz": ("application/gzip", "Archives"),
    ".bz2": ("application/x-bzip2", "Archives"),
    ".xz": ("application/x-xz", "Archives"),
    ".zst": ("application/zstd", "Archives"),
    ".iso": ("application/x-cd-image", "Archives"),
    ".deb": ("application/vnd.debian.binary-package", "Archives"),
    ".rpm": ("application/x-rpm", "Archives"),
    ".appimage": ("application/x-executable", "Archives"),
}

def escape_sparql(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ")

class FileProvider(BaseProvider):
    def __init__(self, history_manager):
        super().__init__(history_manager)
        self.conn = None
        self.tracker_broken = False
        self.local_cache = []
        self.category_buckets = {
            "All": [],
            "PDF": [],
            "Documents": [],
            "Images": [],
            "Videos": [],
            "Audio": [],
            "Folders": [],
            "Archives": []
        }
        self.is_building_cache = False
        self.last_cache_time = 0

        self._init_tracker()
        self._build_cache_async()

    def _init_tracker(self):
        if Tracker:
            try:
                self.conn = Tracker.SparqlConnection.bus_new("org.freedesktop.Tracker3.Miner.Files", None, None)
                self.tracker_broken = False
            except Exception as e:
                self.conn = None
                self.tracker_broken = True
        else:
            self.tracker_broken = True

    def _get_target_directories(self) -> list[str]:
        home = os.path.expanduser("~")
        target_dirs = set()

        # 1. Native XDG directory lookup (supports all languages / distros)
        try:
            for attr in ["DIRECTORY_DOCUMENTS", "DIRECTORY_DOWNLOAD", "DIRECTORY_PICTURES",
                         "DIRECTORY_VIDEOS", "DIRECTORY_MUSIC", "DIRECTORY_DESKTOP",
                         "DIRECTORY_TEMPLATES", "DIRECTORY_PUBLIC_SHARE"]:
                dir_enum = getattr(GLib.UserDirectory, attr, None)
                if dir_enum is not None:
                    resolved = GLib.get_user_special_dir(dir_enum)
                    if resolved and os.path.exists(resolved):
                        target_dirs.add(resolved)
        except Exception:
            pass

        # 2. Add standard English and Russian fallbacks if not caught by XDG
        fallbacks = [
            "Desktop", "Documents", "Downloads", "Pictures", "Videos", "Music",
            "Рабочий стол", "Документы", "Загрузки", "Изображения", "Видео", "Музыка"
        ]
        for name in fallbacks:
            p = os.path.join(home, name)
            if os.path.exists(p):
                target_dirs.add(p)

        # 3. Add any top-level user directories in ~ (e.g. ~/Projects, ~/Books, ~/pdf, ~/Cloud)
        try:
            for entry in os.scandir(home):
                if entry.is_dir(follow_symlinks=False):
                    if not entry.name.startswith(".") and entry.name not in IGNORE_DIRS:
                        target_dirs.add(entry.path)
        except Exception:
            pass

        return sorted(list(target_dirs))

    def _build_cache_async(self):
        if self.is_building_cache:
            return
        self.is_building_cache = True

        def _worker():
            try:
                target_dirs = self._get_target_directories()
                temp_cache = []
                buckets = {
                    "All": [],
                    "PDF": [],
                    "Documents": [],
                    "Images": [],
                    "Videos": [],
                    "Audio": [],
                    "Folders": [],
                    "Archives": []
                }

                def _scan_folder(folder_path, depth=0, max_depth=8):
                    if depth > max_depth:
                        return
                    try:
                        with os.scandir(folder_path) as it:
                            for entry in it:
                                if entry.name.startswith(".") or entry.name in IGNORE_DIRS:
                                    continue
                                try:
                                    name = entry.name
                                    name_lower = name.lower()
                                    path = entry.path

                                    if entry.is_dir(follow_symlinks=False):
                                        st = entry.stat(follow_symlinks=False)
                                        item = {
                                            "name": name,
                                            "name_lower": name_lower,
                                            "path": path,
                                            "mime": "inode/directory",
                                            "category": "Folders",
                                            "size": 0,
                                            "mtime": st.st_mtime,
                                            "is_dir": True
                                        }
                                        temp_cache.append(item)
                                        buckets["Folders"].append(item)
                                        buckets["All"].append(item)
                                        _scan_folder(path, depth + 1, max_depth)

                                    elif entry.is_file(follow_symlinks=False):
                                        ext = os.path.splitext(name)[1].lower()
                                        mime = "application/octet-stream"
                                        category = "Documents"

                                        if ext in EXT_MAP:
                                            mime, category = EXT_MAP[ext]
                                        else:
                                            guessed, _ = mimetypes.guess_type(name)
                                            if guessed:
                                                mime = guessed
                                                if mime.startswith("image/"):
                                                    category = "Images"
                                                elif mime.startswith("video/"):
                                                    category = "Videos"
                                                elif mime.startswith("audio/"):
                                                    category = "Audio"
                                                elif mime == "application/pdf":
                                                    category = "PDF"
                                                elif any(a in mime for a in ["zip", "tar", "rar", "7z", "compressed"]):
                                                    category = "Archives"

                                        st = entry.stat(follow_symlinks=False)
                                        item = {
                                            "name": name,
                                            "name_lower": name_lower,
                                            "path": path,
                                            "mime": mime,
                                            "category": category,
                                            "size": st.st_size,
                                            "mtime": st.st_mtime,
                                            "is_dir": False
                                        }
                                        temp_cache.append(item)
                                        buckets["All"].append(item)
                                        if category in buckets:
                                            buckets[category].append(item)
                                        if category == "PDF":
                                            buckets["Documents"].append(item) # PDF is also a document

                                except (PermissionError, OSError):
                                    continue
                    except (PermissionError, OSError):
                        pass

                for base_dir in target_dirs:
                    _scan_folder(base_dir, depth=0, max_depth=8)

                # Sort each bucket by mtime DESC so recent files always appear first
                for k in buckets:
                    buckets[k].sort(key=lambda x: x["mtime"], reverse=True)

                self.local_cache = temp_cache
                self.category_buckets = buckets
                self.last_cache_time = time.time()

            except Exception as e:
                print(f"Error building local cache: {e}")
            finally:
                self.is_building_cache = False

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    @functools.lru_cache(maxsize=1024)
    def _get_icon_for_mime(self, mime: str, path: str) -> str:
        if not mime or mime in ("unknown", "file"):
            guessed_mime, _ = mimetypes.guess_type(path)
            mime = guessed_mime or "unknown"

        try:
            import hashlib
            uri = Path(path).as_uri()
            hash_str = hashlib.md5(uri.encode("utf-8")).hexdigest()

            thumb_xlarge = os.path.expanduser(f"~/.cache/thumbnails/x-large/{hash_str}.png")
            if os.path.exists(thumb_xlarge):
                return thumb_xlarge

            thumb_large = os.path.expanduser(f"~/.cache/thumbnails/large/{hash_str}.png")
            if os.path.exists(thumb_large):
                return thumb_large

            thumb_normal = os.path.expanduser(f"~/.cache/thumbnails/normal/{hash_str}.png")
            if os.path.exists(thumb_normal):
                return thumb_normal
        except Exception:
            pass

        if mime.startswith("image/"):
            return "image-x-generic"
        elif mime.startswith("video/"):
            return "video-x-generic"
        elif mime.startswith("audio/"):
            return "audio-x-generic"
        elif "pdf" in mime:
            return "application-pdf"
        elif "zip" in mime or "tar" in mime or "compressed" in mime or "rar" in mime:
            return "package-x-generic"
        elif "text/" in mime or "document" in mime:
            return "text-x-generic"
        elif "directory" in mime or os.path.isdir(path):
            return "folder"
        return "text-x-generic"

    def _create_result(self, path: str, name: str, mime_type: str, score: float) -> SearchResult:
        def _exec_callback():
            try:
                subprocess.Popen(["xdg-open", path], start_new_session=True)
            except Exception as e:
                print(f"Failed to open file {path}: {e}")

        def _loc_callback():
            try:
                parent_dir = os.path.dirname(path)
                subprocess.Popen(["xdg-open", parent_dir], start_new_session=True)
            except Exception as e:
                print(f"Failed to open file location {path}: {e}")

        def _copy_callback():
            try:
                display = Gdk.Display.get_default()
                clipboard = display.get_clipboard()

                if mime_type.startswith("image/") and os.path.exists(path):
                    try:
                        gfile = Gio.File.new_for_path(path)
                        tex = Gdk.Texture.new_from_file(gfile)
                        val = GObject.Value(Gdk.Texture.__gtype__, tex)
                        clipboard.set(val)
                        return
                    except Exception:
                        pass

                gfile = Gio.File.new_for_path(path)
                flist = Gdk.FileList.new_from_list([gfile])
                val = GObject.Value(Gdk.FileList.__gtype__, flist)
                clipboard.set(val)
            except Exception as e:
                print(f"Clipboard file copy error: {e}")

        return SearchResult(
            id=f"file_{path}",
            title=name,
            subtitle=mime_type if mime_type != "unknown" else os.path.dirname(path),
            icon=self._get_icon_for_mime(mime_type, path),
            score=score,
            category="Files",
            provider="FileProvider",
            preview_data={
                "type": "file",
                "path": path,
                "mime": mime_type
            },
            action_execute=_exec_callback,
            action_open_location=_loc_callback,
            action_copy=_copy_callback
        )

    def get_files_by_category(self, category: str = "All", limit: int = 40) -> list[SearchResult]:
        if not self.local_cache and not self.is_building_cache:
            self._build_cache_async()

        # Normalize category
        cat_key = category
        if cat_key not in self.category_buckets:
            cat_key = "All"

        items = self.category_buckets.get(cat_key, [])
        if not items and cat_key != "All":
            items = [item for item in self.local_cache if item.get("category") == cat_key]

        results = []
        for item in items[:limit]:
            results.append(self._create_result(item["path"], item["name"], item["mime"], 50))
        return results

    def get_recent_files(self, limit: int = 30) -> list[SearchResult]:
        if self.tracker_broken:
            self._init_tracker()

        results = []
        seen = set()

        if self.conn and not self.tracker_broken:
            try:
                sparql = f"""
                SELECT nie:url(?urn) nfo:fileName(?urn) nie:mimeType(?urn)
                WHERE {{
                    ?urn a nfo:FileDataObject .
                    FILTER ( STRSTARTS(nie:url(?urn), "file://") )
                }}
                ORDER BY DESC(nfo:fileLastModified(?urn))
                LIMIT {limit}
                """
                cursor = self.conn.query(sparql, None)
                while cursor.next():
                    url = cursor.get_string(0)[0]
                    if not url:
                        continue
                    path = urllib.parse.unquote(url.replace("file://", ""))
                    if path in seen or not os.path.exists(path):
                        continue
                    seen.add(path)
                    name = cursor.get_string(1)[0] or os.path.basename(path)
                    mime = cursor.get_string(2)[0] or "unknown"
                    results.append(self._create_result(path, name, mime, 50))
                if results:
                    return results
            except Exception as e:
                self.tracker_broken = True
                self.conn = None

        # Fallback to Gtk.RecentManager
        try:
            rm = Gtk.RecentManager.get_default()
            for item in rm.get_items()[:limit * 2]:
                url = item.get_uri()
                if url.startswith("file://"):
                    path = urllib.parse.unquote(url.replace("file://", ""))
                    if path in seen or not os.path.exists(path):
                        continue
                    seen.add(path)
                    name = item.get_display_name() or os.path.basename(path)
                    mime = item.get_mime_type() or "unknown"
                    results.append(self._create_result(path, name, mime, 50))
                    if len(results) >= limit:
                        break
        except Exception:
            pass

        # If recent files are still sparse, fill from local cache sorted by modification time
        if len(results) < limit and self.local_cache:
            for item in self.local_cache:
                p = item["path"]
                if p not in seen:
                    seen.add(p)
                    results.append(self._create_result(p, item["name"], item["mime"], 40))
                    if len(results) >= limit:
                        break

        return results

    def search(self, query: str, limit: int = 15, category_filter: str = None) -> list[SearchResult]:
        if category_filter not in (None, "All", "Files"):
            return []

        if not query:
            return self.get_recent_files(limit=limit)

        if len(query) < 2:
            return []

        q_orig = query.lower().strip()
        q_en = q_orig.translate(RU_TO_EN)
        q_ru = q_orig.translate(EN_TO_RU)
        queries = list(dict.fromkeys([q_orig, q_en, q_ru]))

        results = []
        seen_paths = set()

        # 1. Search via GNOME Tracker 3 SPARQL if available
        if self.conn and not self.tracker_broken:
            try:
                filter_clauses = [f'CONTAINS(LCASE(?name), "{escape_sparql(q)}")' for q in queries]
                or_filter = " || ".join(filter_clauses)
                
                sparql = f"""
                SELECT nie:url(?info) nfo:fileName(?info) nie:mimeType(?info)
                WHERE {{
                    ?info a nfo:FileDataObject ;
                          nfo:fileName ?name .
                    FILTER({or_filter})
                }}
                LIMIT {limit * 2}
                """

                cursor = self.conn.query(sparql, None)
                while cursor.next():
                    url = cursor.get_string(0)[0]
                    if not url:
                        continue

                    path = urllib.parse.unquote(url.replace("file://", ""))
                    if path in seen_paths or not os.path.exists(path):
                        continue
                    seen_paths.add(path)

                    name = cursor.get_string(1)[0] or os.path.basename(path)
                    mime = cursor.get_string(2)[0] or "unknown"

                    score = 60
                    name_lower = name.lower()
                    if any(q == name_lower for q in queries):
                        score += 30
                    elif any(name_lower.startswith(q) for q in queries):
                        score += 20
                    score += self.history_manager.get_score_bonus(path, q_orig)

                    results.append(self._create_result(path, name, mime, score))

            except Exception as e:
                self.tracker_broken = True
                self.conn = None

        # 2. Local high-speed in-memory cache lookup
        if not self.local_cache and not self.is_building_cache:
            self._build_cache_async()

        now = time.time()
        for item in self.local_cache:
            item_path = item["path"]
            if item_path in seen_paths:
                continue
            item_name = item["name"]
            item_name_lower = item["name_lower"]

            matched = False
            score = 0
            for q in queries:
                if item_name_lower == q:
                    score = 95
                    matched = True
                    break
                elif item_name_lower.startswith(q):
                    score = 80
                    matched = True
                    break
                elif f" {q}" in item_name_lower or f"_{q}" in item_name_lower or f"-{q}" in item_name_lower:
                    score = 70
                    matched = True
                    break
                elif q in item_name_lower:
                    score = 55
                    matched = True
                    break

            if matched:
                seen_paths.add(item_path)
                # Recency bonus
                mtime = item.get("mtime", 0)
                if now - mtime < 7 * 86400:
                    score += 15
                elif now - mtime < 30 * 86400:
                    score += 8

                score += self.history_manager.get_score_bonus(item_path, q_orig)
                results.append(self._create_result(item_path, item_name, item["mime"], score))
                if len(results) >= limit * 3:
                    break

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def get_quick_folders(self) -> list[dict]:
        if not self.local_cache and not self.is_building_cache:
            self._build_cache_async()

        PLACES = [
            ("DIRECTORY_DOWNLOAD", "folder-download", "Загрузки", "Downloads"),
            ("DIRECTORY_DOCUMENTS", "folder-documents", "Документы", "Documents"),
            ("DIRECTORY_PICTURES", "folder-pictures", "Изображения", "Pictures"),
            ("DIRECTORY_DESKTOP", "user-desktop", "Рабочий стол", "Desktop"),
            ("DIRECTORY_VIDEOS", "folder-videos", "Видео", "Videos"),
            ("DIRECTORY_MUSIC", "folder-music", "Музыка", "Music"),
        ]

        folders = []
        home = os.path.expanduser("~")
        for attr, icon, ru_name, en_name in PLACES:
            dir_enum = getattr(GLib.UserDirectory, attr, None)
            path = None
            if dir_enum is not None:
                path = GLib.get_user_special_dir(dir_enum)
            if not path or not os.path.exists(path):
                for fallback in (ru_name, en_name):
                    p = os.path.join(home, fallback)
                    if os.path.exists(p):
                        path = p
                        break
            if path and os.path.exists(path):
                name = os.path.basename(path)
                cnt = sum(1 for item in self.local_cache if item["path"].startswith(path) and not item.get("is_dir", False))
                folders.append({
                    "name": name,
                    "path": path,
                    "icon": icon,
                    "count": cnt
                })
        return folders

    def get_files_in_folder(self, folder_path: str, limit: int = 40) -> list[SearchResult]:
        if not self.local_cache and not self.is_building_cache:
            self._build_cache_async()

        matched = [
            item for item in self.local_cache
            if item["path"].startswith(folder_path) and item["path"] != folder_path and not item.get("is_dir", False)
        ]
        matched.sort(key=lambda x: x.get("mtime", 0), reverse=True)

        results = []
        for item in matched[:limit]:
            results.append(self._create_result(item["path"], item["name"], item["mime"], 50))
        return results
