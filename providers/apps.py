import os
import configparser
import shlex
import subprocess
from pathlib import Path
from rapidfuzz import fuzz

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Gdk", "4.0")
    from gi.repository import Gio, GLib, Gdk
except (ValueError, ImportError):
    pass

from .base import BaseProvider, SearchResult
from i18n import t, i18n

CATEGORY_KEYS = {
    "Settings": "provider_cat_settings",
    "System": "provider_cat_system",
    "Utility": "provider_cat_utility",
    "Network": "provider_cat_network",
    "AudioVideo": "provider_cat_multimedia",
    "Game": "provider_cat_game",
    "Graphics": "provider_cat_graphics",
    "Development": "provider_cat_dev",
    "Office": "provider_cat_office"
}

RU_TO_EN = str.maketrans(
    "йцукенгшщзхъфывапролджэячсмитьбюё",
    "qwertyuiop[]asdfghjkl;'zxcvbnm,.~"
)
EN_TO_RU = str.maketrans(
    "qwertyuiop[]asdfghjkl;'zxcvbnm,.~",
    "йцукенгшщзхъфывапролджэячсмитьбюё"
)
RU_PHONETIC = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya"
}

class DesktopApp:
    def __init__(self, path: str):
        self.path = path
        self.name = ""
        self.name_en = ""
        self.generic_name = ""
        self.exec_cmd = ""
        self.icon = ""
        self.categories = ""
        self.keywords = ""
        self.keywords_loc = ""
        self.keywords_ru = ""
        self.description = ""
        self.developer = "System"
        self.no_display = False
        
        # Pre-calculated in-memory search tokens for 0ms lookup
        self.app_names = []
        self.cached_searchable_text = ""
        self._parse()

    def _parse(self):
        try:
            config = configparser.ConfigParser(interpolation=None)
            config.read(self.path, encoding="utf-8")
            if "Desktop Entry" in config:
                entry = config["Desktop Entry"]

                is_no_display = entry.get("NoDisplay", "false").lower() == "true"
                categories = entry.get("Categories", "")
                exec_cmd = entry.get("Exec", "")

                if is_no_display and "Settings" not in categories and "gnome-control-center" not in exec_cmd:
                    self.no_display = True
                    return

                if entry.get("Type", "") != "Application":
                    self.no_display = True
                    return

                lang = i18n.get_language()
                if lang and lang != "en":
                    self.name = entry.get(f"Name[{lang}]", entry.get("Name", os.path.basename(self.path)))
                    self.generic_name = entry.get(f"GenericName[{lang}]", entry.get("GenericName", ""))
                    self.description = entry.get(f"Comment[{lang}]", entry.get("Comment", ""))
                    self.keywords_loc = entry.get(f"Keywords[{lang}]", "")
                else:
                    self.name = entry.get("Name", os.path.basename(self.path))
                    self.generic_name = entry.get("GenericName", "")
                    self.description = entry.get("Comment", "")
                    self.keywords_loc = ""

                self.name_en = entry.get("Name", os.path.basename(self.path))
                self.exec_cmd = entry.get("Exec", "")
                self.icon = entry.get("Icon", "application-x-executable")
                self.categories = entry.get("Categories", "")
                self.keywords = entry.get("Keywords", "")
                self.keywords_ru = entry.get("Keywords[ru]", "")

                vendor = entry.get("Vendor", "")
                if vendor:
                    self.developer = vendor
                elif "org.gnome" in self.path:
                    self.developer = "GNOME"
                elif "org.kde" in self.path:
                    self.developer = "KDE"
                elif "flatpak" in self.path:
                    self.developer = "Flatpak App"

                if self.exec_cmd:
                    self.exec_cmd = " ".join([part for part in self.exec_cmd.split() if not part.startswith("%")])

                # Precompute search tokens
                names_set = {self.name.lower()}
                if self.name_en:
                    names_set.add(self.name_en.lower())
                self.app_names = list(names_set)
                self.cached_searchable_text = f"{self.name} {self.name_en} {self.categories} {self.keywords} {self.keywords_loc} {self.keywords_ru}".lower()

        except Exception:
            self.no_display = True

    @property
    def searchable_text(self):
        return self.cached_searchable_text

    @property
    def display_description(self):
        if self.generic_name:
            return self.generic_name
        for cat, key in CATEGORY_KEYS.items():
            if cat in self.categories:
                return t(key)
        return t("provider_app_desc")


class AppProvider(BaseProvider):
    def __init__(self, history_manager):
        super().__init__(history_manager)
        self.apps = []
        self._monitors = []
        self._reload_timer_id = None
        self._load_apps()
        self._setup_file_monitors()

    def _load_apps(self):
        apps = []
        app_dirs = [
            "/usr/share/applications",
            os.path.expanduser("~/.local/share/applications"),
            "/var/lib/flatpak/exports/share/applications",
            os.path.expanduser("~/.local/share/flatpak/exports/share/applications"),
            "/var/lib/snapd/desktop/applications",
            "/snap/current/usr/share/applications"
        ]
        seen_execs = set()
        for d in app_dirs:
            p = Path(d)
            if not p.exists():
                continue
            try:
                for f in p.rglob("*.desktop"):
                    app = DesktopApp(str(f))
                    if not app.no_display and app.name and app.exec_cmd:
                        if app.exec_cmd not in seen_execs:
                            apps.append(app)
                            seen_execs.add(app.exec_cmd)
            except Exception as e:
                print(f"Error scanning app dir {d}: {e}")
        self.apps = apps

    def _setup_file_monitors(self):
        try:
            import gi
            from gi.repository import Gio
            watch_dirs = [
                "/usr/share/applications",
                os.path.expanduser("~/.local/share/applications"),
                "/var/lib/flatpak/exports/share/applications",
                os.path.expanduser("~/.local/share/flatpak/exports/share/applications")
            ]
            for d in watch_dirs:
                if os.path.exists(d):
                    gfile = Gio.File.new_for_path(d)
                    monitor = gfile.monitor_directory(Gio.FileMonitorFlags.NONE, None)
                    monitor.connect("changed", self._on_dir_changed)
                    self._monitors.append(monitor)
        except Exception as e:
            print(f"Warning: Could not setup AppProvider file monitors: {e}")

    def _on_dir_changed(self, monitor, file, other_file, event_type):
        # Debounce reloading to avoid multi-reloads when several desktop files are written
        try:
            import gi
            from gi.repository import GLib
            if self._reload_timer_id is not None:
                GLib.source_remove(self._reload_timer_id)
            self._reload_timer_id = GLib.timeout_add(500, self._debounced_reload)
        except Exception:
            self._load_apps()

    def _debounced_reload(self):
        self._reload_timer_id = None
        self._load_apps()
        return False

    def reload_apps(self):
        self._load_apps()

    def _create_result(self, app_data: DesktopApp, score: float) -> SearchResult:
        def _exec_callback():
            # 1. Native Gio DesktopAppInfo launch (preferred, securely handles environment & dbus activation)
            try:
                import gi
                from gi.repository import Gio
                app_info = Gio.DesktopAppInfo.new_from_filename(app_data.path)
                if app_info:
                    app_info.launch_uris([], None)
                    return
            except Exception:
                pass

            # 2. Secure subprocess spawn without shell=True
            if app_data.exec_cmd:
                try:
                    args = shlex.split(app_data.exec_cmd)
                    subprocess.Popen(
                        args,
                        start_new_session=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                except Exception as e:
                    print(f"Error launching application {app_data.name}: {e}")

        def _loc_callback():
            path = os.path.dirname(app_data.path)
            try:
                import gi
                from gi.repository import Gio
                Gio.AppInfo.launch_default_for_uri(f"file://{path}", None)
            except Exception:
                subprocess.Popen(["xdg-open", path], start_new_session=True)

        def _copy_callback():
            try:
                import gi
                gi.require_version("Gtk", "4.0")
                from gi.repository import Gdk
                display = Gdk.Display.get_default()
                if display:
                    clipboard = display.get_clipboard()
                    clipboard.set(app_data.path)
            except Exception:
                pass

        return SearchResult(
            id=app_data.path,
            title=app_data.name,
            subtitle=app_data.display_description,
            icon=app_data.icon,
            score=score,
            category="Apps" if "Settings" not in app_data.categories else "Settings",
            provider="AppProvider",
            preview_data={
                "type": "app",
                "path": app_data.path,
                "exec_cmd": app_data.exec_cmd,
                "generic_name": app_data.generic_name,
                "categories": app_data.categories,
                "description": app_data.description,
                "developer": app_data.developer
            },
            action_execute=_exec_callback,
            action_open_location=_loc_callback,
            action_copy=_copy_callback
        )

    def search(self, query: str, limit: int = 10, category_filter: str = None) -> list[SearchResult]:
        if category_filter not in (None, "All", "Apps", "Settings"):
            return []

        query = query.lower().strip()
        query_en = query.translate(RU_TO_EN)
        query_ru = query.translate(EN_TO_RU)
        query_phonetic = "".join(RU_PHONETIC.get(c, c) for c in query)

        candidates = self.apps
        if category_filter == "Apps":
            candidates = [a for a in candidates if "Settings" not in a.categories]
        elif category_filter == "Settings":
            candidates = [a for a in candidates if "Settings" in a.categories]

        if not query:
            if category_filter in ("Apps", "Settings"):
                all_sorted = sorted(candidates, key=lambda x: x.name.lower())
                return [self._create_result(app, 0) for app in all_sorted]
            else:
                recent_ids = self.history_manager.get_recent_apps(limit)
                recent_apps = []
                for app_id in recent_ids:
                    app = next((a for a in candidates if a.path == app_id), None)
                    if app:
                        recent_apps.append(self._create_result(app, 100))
                return recent_apps

        app_results = []
        queries = [query, query_en, query_ru, query_phonetic]

        for app in candidates:
            app_names = app.app_names
            app_text = app.searchable_text

            score = 0
            for q in queries:
                if q == "стим" and "steam" in app_names:
                    score = max(score, 100)

                for n in app_names:
                    if n == q:
                        score = max(score, 100)
                    elif n.startswith(q):
                        score = max(score, 90)
                    elif f" {q}" in n or f"-{q}" in n:
                        score = max(score, 85)
                    elif q in n:
                        score = max(score, 75)

            if score == 0 and any(q in app_text for q in queries):
                score = 65

            if score == 0:
                for q in queries:
                    for n in app_names:
                        fuzz_score = fuzz.WRatio(q, n)
                        if fuzz_score > 75:
                            score = max(score, fuzz_score * 0.85)

            best_score = score

            if best_score >= 65:
                usage_bonus = self.history_manager.get_score_bonus(app.path, query)
                app_results.append(self._create_result(app, best_score + usage_bonus))

        app_results.sort(key=lambda x: x.score, reverse=True)
        return app_results[:limit]
