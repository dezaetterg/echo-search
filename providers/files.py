import os
import urllib.parse
import mimetypes
import threading
import subprocess
from datetime import datetime
from .base import BaseProvider, SearchResult

try:
    import gi
    gi.require_version("Tracker", "3.0")
    gi.require_version("Gtk", "4.0")
    from gi.repository import Tracker, Gio, Gtk, Gdk, GObject
except (ValueError, ImportError):
    Tracker = None

RU_TO_EN = str.maketrans(
    "йцукенгшщзхъфывапролджэячсмитьбюё",
    "qwertyuiop[]asdfghjkl;'zxcvbnm,.~"
)
EN_TO_RU = str.maketrans(
    "qwertyuiop[]asdfghjkl;'zxcvbnm,.~",
    "йцукенгшщзхъфывапролджэячсмитьбюё"
)

def escape_sparql(text: str) -> str:
    """Sanitizes input strings for SPARQL query filters"""
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ")

class FileProvider(BaseProvider):
    def __init__(self, history_manager):
        super().__init__(history_manager)
        self.conn = None
        self.tracker_broken = False
        self.local_cache = []
        self.is_building_cache = False

        self._init_tracker()
        self._build_cache_async()

    def _init_tracker(self):
        if Tracker:
            try:
                self.conn = Tracker.SparqlConnection.bus_new("org.freedesktop.Tracker3.Miner.Files", None, None)
                self.tracker_broken = False
            except Exception as e:
                print(f"Tracker3 connection failed: {e}")
                self.conn = None
                self.tracker_broken = True

    def _build_cache_async(self):
        if self.is_building_cache:
            return
        self.is_building_cache = True

        def _worker():
            try:
                home = os.path.expanduser("~")
                temp_cache = []
                # Scan key user directories first
                target_dirs = [
                    os.path.join(home, "Desktop"),
                    os.path.join(home, "Documents"),
                    os.path.join(home, "Downloads"),
                    os.path.join(home, "Pictures"),
                    os.path.join(home, "Videos"),
                    os.path.join(home, "Music")
                ]
                
                for base_dir in target_dirs:
                    if not os.path.exists(base_dir):
                        continue
                    for root, dirs, files in os.walk(base_dir):
                        dirs[:] = [d for d in dirs if not d.startswith(".")]
                        if root.count(os.sep) - home.count(os.sep) > 4:
                            continue
                        for name in files:
                            if name.startswith("."):
                                continue
                            temp_cache.append({
                                "name": name,
                                "name_lower": name.lower(),
                                "path": os.path.join(root, name)
                            })

                self.local_cache = temp_cache
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

    def _get_icon_for_mime(self, mime: str, path: str) -> str:
        if not mime or mime in ("unknown", "file"):
            guessed_mime, _ = mimetypes.guess_type(path)
            mime = guessed_mime or "unknown"

        try:
            import hashlib
            uri = f"file://{urllib.parse.quote(path)}"
            hash_str = hashlib.md5(uri.encode("utf-8")).hexdigest()

            thumb_normal = os.path.expanduser(f"~/.cache/thumbnails/normal/{hash_str}.png")
            thumb_large = os.path.expanduser(f"~/.cache/thumbnails/large/{hash_str}.png")

            if os.path.exists(thumb_large):
                return thumb_large
            if os.path.exists(thumb_normal):
                return thumb_normal
        except Exception:
            pass

        if "image" in mime:
            return path
        if "video" in mime:
            return "video-x-generic"
        if "audio" in mime:
            return "audio-x-generic"
        if "text" in mime:
            return "text-x-generic"
        if "pdf" in mime:
            return "application-pdf"
        if os.path.isdir(path):
            return "folder"
        return "text-x-generic"

    def _create_result(self, path: str, name: str, mime_type: str, score: float) -> SearchResult:
        if not mime_type or mime_type in ("unknown", "file"):
            guessed_mime, _ = mimetypes.guess_type(path)
            mime_type = guessed_mime or "unknown"

        def _exec_callback():
            try:
                import gi
                from gi.repository import Gio
                Gio.AppInfo.launch_default_for_uri(f"file://{path}", None)
            except Exception:
                subprocess.Popen(["xdg-open", path], start_new_session=True)

        def _loc_callback():
            try:
                import gi
                from gi.repository import Gio
                dir_path = os.path.dirname(path)
                Gio.AppInfo.launch_default_for_uri(f"file://{dir_path}", None)
            except Exception:
                subprocess.Popen(["xdg-open", os.path.dirname(path)], start_new_session=True)

        def _copy_callback():
            try:
                import gi
                gi.require_version("Gtk", "4.0")
                from gi.repository import Gdk, Gio, GObject
                display = Gdk.Display.get_default()
                if not display:
                    return
                clipboard = display.get_clipboard()

                if "image" in mime_type:
                    try:
                        tex = Gdk.Texture.new_from_filename(path)
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
            subtitle=mime_type,
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

    def search(self, query: str, limit: int = 10, category_filter: str = None) -> list[SearchResult]:
        if category_filter not in (None, "All", "Files"):
            return []

        if not query:
            results = []
            try:
                import gi
                gi.require_version("Gtk", "4.0")
                from gi.repository import Gtk
                recent_mgr = Gtk.RecentManager.get_default()
                items = recent_mgr.get_items()
                items.sort(key=lambda x: x.get_modified(), reverse=True)

                for item in items[:limit]:
                    uri = item.get_uri()
                    if uri.startswith("file://"):
                        path = urllib.parse.unquote(uri.replace("file://", ""))
                        if os.path.exists(path):
                            mime_type = item.get_mime_type()
                            results.append(self._create_result(path, item.get_display_name(), mime_type, 100))
            except Exception as e:
                print(f"RecentManager error: {e}")

            return results

        if len(query) < 2:
            return []

        if self.tracker_broken:
            self._init_tracker()

        q_orig = query.lower().strip()
        q_en = q_orig.translate(RU_TO_EN)
        q_ru = q_orig.translate(EN_TO_RU)
        queries = list(dict.fromkeys([q_orig, q_en, q_ru]))

        results = []
        seen_paths = set()

        # 1. Search via GNOME Tracker 3 SPARQL with safe escaping
        if self.conn and not self.tracker_broken:
            try:
                # Build safe multi-term contains filters
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
                    if path in seen_paths:
                        continue
                    seen_paths.add(path)

                    name = cursor.get_string(1)[0] or os.path.basename(path)
                    mime = cursor.get_string(2)[0] or "unknown"

                    score = 60
                    name_lower = name.lower()
                    if any(q == name_lower for q in queries):
                        score += 25
                    elif any(name_lower.startswith(q) for q in queries):
                        score += 15
                    score += self.history_manager.get_score_bonus(path, q_orig)

                    results.append(self._create_result(path, name, mime, score))

                if results:
                    results.sort(key=lambda x: x.score, reverse=True)
                    return results[:limit]

            except Exception as e:
                print(f"Tracker3 query error: {e}")
                self.tracker_broken = True
                self.conn = None

        # 2. FALLBACK: In-memory local file cache
        if not self.local_cache and not self.is_building_cache:
            self._build_cache_async()

        for item in self.local_cache:
            item_path = item["path"]
            if item_path in seen_paths:
                continue
            item_name = item["name"]
            item_name_lower = item_name.lower()

            matched = any(q in item_name_lower for q in queries)
            if matched:
                seen_paths.add(item_path)
                score = 50
                if any(item_name_lower == q for q in queries):
                    score += 25
                elif any(item_name_lower.startswith(q) for q in queries):
                    score += 15
                results.append(self._create_result(item_path, item_name, "file", score))
                if len(results) >= limit:
                    break

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

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
                print(f"Tracker3 recent files error: {e}")
                self.tracker_broken = True
                self.conn = None

        # Fallback to Gtk.RecentManager
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            from gi.repository import Gtk
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
        except Exception as e:
            print(f"Fallback recent files error: {e}")

        return results
