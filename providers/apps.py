import os
import configparser
from pathlib import Path
from rapidfuzz import fuzz

from .base import BaseProvider, SearchResult
from i18n import t, i18n

CATEGORY_KEYS = {
    'Settings': 'provider_cat_settings',
    'System': 'provider_cat_system',
    'Utility': 'provider_cat_utility',
    'Network': 'provider_cat_network',
    'AudioVideo': 'provider_cat_multimedia',
    'Game': 'provider_cat_game',
    'Graphics': 'provider_cat_graphics',
    'Development': 'provider_cat_dev',
    'Office': 'provider_cat_office'
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
        self._parse()

    def _parse(self):
        try:
            config = configparser.ConfigParser(interpolation=None)
            config.read(self.path, encoding='utf-8')
            if 'Desktop Entry' in config:
                entry = config['Desktop Entry']
                
                is_no_display = entry.get('NoDisplay', 'false').lower() == 'true'
                categories = entry.get('Categories', '')
                exec_cmd = entry.get('Exec', '')
                
                if is_no_display and 'Settings' not in categories and 'gnome-control-center' not in exec_cmd:
                    self.no_display = True
                    return
                
                if entry.get('Type', '') != 'Application':
                    self.no_display = True
                    return

                lang = i18n.get_language()
                if lang and lang != 'en':
                    self.name = entry.get(f'Name[{lang}]', entry.get('Name', os.path.basename(self.path)))
                    self.generic_name = entry.get(f'GenericName[{lang}]', entry.get('GenericName', ''))
                    self.description = entry.get(f'Comment[{lang}]', entry.get('Comment', ''))
                    self.keywords_loc = entry.get(f'Keywords[{lang}]', '')
                else:
                    self.name = entry.get('Name', os.path.basename(self.path))
                    self.generic_name = entry.get('GenericName', '')
                    self.description = entry.get('Comment', '')
                    self.keywords_loc = ''

                self.name_en = entry.get('Name', os.path.basename(self.path))
                self.exec_cmd = entry.get('Exec', '')
                self.icon = entry.get('Icon', 'application-x-executable')
                self.categories = entry.get('Categories', '')
                self.keywords = entry.get('Keywords', '')
                self.keywords_ru = entry.get('Keywords[ru]', '')
                
                vendor = entry.get('Vendor', '')
                if vendor:
                    self.developer = vendor
                elif 'org.gnome' in self.path:
                    self.developer = "GNOME"
                elif 'org.kde' in self.path:
                    self.developer = "KDE"
                elif 'flatpak' in self.path:
                    self.developer = "Flatpak App"
                
                if self.exec_cmd:
                    self.exec_cmd = " ".join([part for part in self.exec_cmd.split() if not part.startswith('%')])
        except Exception:
            self.no_display = True

    @property
    def searchable_text(self):
        return f"{self.name} {self.name_en} {self.categories} {self.keywords} {self.keywords_loc} {self.keywords_ru}".lower()

    @property
    def display_description(self):
        if self.generic_name: return self.generic_name
        for cat, key in CATEGORY_KEYS.items():
            if cat in self.categories:
                return t(key)
        return t("provider_app_desc")

RU_TO_EN = str.maketrans(
    "йцукенгшщзхъфывапролджэячсмитьбюё",
    "qwertyuiop[]asdfghjkl;'zxcvbnm,.~"
)
EN_TO_RU = str.maketrans(
    "qwertyuiop[]asdfghjkl;'zxcvbnm,.~",
    "йцукенгшщзхъфывапролджэячсмитьбюё"
)
RU_PHONETIC = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}

class AppProvider(BaseProvider):
    def __init__(self, history_manager):
        super().__init__(history_manager)
        self.apps = []
        self._load_apps()

    def _load_apps(self):
        self.apps = []
        app_dirs = [
            "/usr/share/applications",
            os.path.expanduser("~/.local/share/applications"),
            "/var/lib/flatpak/exports/share/applications",
            os.path.expanduser("~/.local/share/flatpak/exports/share/applications")
        ]
        seen_execs = set()
        for d in app_dirs:
            p = Path(d)
            if not p.exists(): continue
            for f in p.rglob("*.desktop"):
                app = DesktopApp(str(f))
                if not app.no_display and app.name and app.exec_cmd:
                    if app.exec_cmd not in seen_execs:
                        self.apps.append(app)
                        seen_execs.add(app.exec_cmd)

    def reload_apps(self):
        self._load_apps()

    def _create_result(self, app_data: DesktopApp, score: float) -> SearchResult:
        def _exec_callback():
            if app_data.exec_cmd: os.system(f"{app_data.exec_cmd} &")
            
        def _loc_callback():
            path = os.path.dirname(app_data.path)
            os.system(f"xdg-open '{path}' &")
            
        def _copy_callback():
            try:
                import gi
                gi.require_version('Gtk', '4.0')
                from gi.repository import Gdk
                clipboard = Gdk.Display.get_default().get_clipboard()
                clipboard.set(app_data.path)
            except: pass

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
                # Возвращаем все элементы (Launchpad Mode)
                all_sorted = sorted(candidates, key=lambda x: x.name.lower())
                return [self._create_result(app, 0) for app in all_sorted]
            else:
                # В стандартном поиске возвращаем только недавние
                recent_ids = self.history_manager.get_recent_apps(limit)
                recent_apps = []
                for app_id in recent_ids:
                    app = next((a for a in candidates if a.path == app_id), None)
                    if app:
                        recent_apps.append(self._create_result(app, 100))
                return recent_apps

        app_results = []
        for app in candidates:
            best_score = 0
            app_names = [app.name.lower()]
            if app.name_en and app.name_en.lower() not in app_names:
                app_names.append(app.name_en.lower())
            app_text = app.searchable_text
            
            score = 0
            for q in [query, query_en, query_ru, query_phonetic]:
                if q == "стим" and "steam" in app_names:
                    score = max(score, 100)
                    
                for n in app_names:
                    if n == q: score = max(score, 100)
                    elif n.startswith(q): score = max(score, 90)
                    elif f" {q}" in n or f"-{q}" in n: score = max(score, 85)
                    elif q in n: score = max(score, 75)
            
            if score == 0 and any(q in app_text for q in [query, query_en, query_ru, query_phonetic]):
                score = 65
                
            if score == 0:
                for q in [query, query_en, query_ru, query_phonetic]:
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
