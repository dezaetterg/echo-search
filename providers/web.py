import os
import json
import sqlite3
import subprocess
import urllib.parse
import re
from pathlib import Path
from .base import BaseProvider, SearchResult
from i18n import t

try:
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gdk, Gio
except (ValueError, ImportError):
    pass

BANGS = {
    "!g": ("Google", "https://www.google.com/search?q={q}", "web-browser"),
    "!yt": ("YouTube", "https://www.youtube.com/results?search_query={q}", "video-x-generic"),
    "!gh": ("GitHub", "https://github.com/search?q={q}", "application-x-executable"),
    "!w": ("Wikipedia", "https://en.wikipedia.org/wiki/Special:Search?search={q}", "accessories-dictionary"),
    "!ddg": ("DuckDuckGo", "https://duckduckgo.com/?q={q}", "web-browser"),
    "!ya": ("Yandex", "https://yandex.ru/search/?text={q}", "web-browser"),
    "!ai": ("ChatGPT", "https://chat.openai.com/?q={q}", "system-search"),
    "!gpt": ("ChatGPT", "https://chat.openai.com/?q={q}", "system-search"),
    "!rd": ("Reddit", "https://www.reddit.com/search/?q={q}", "web-browser"),
    "!tr": ("Google Translate", "https://translate.google.com/?text={q}", "accessories-dictionary"),
    "!maps": ("Google Maps", "https://www.google.com/maps/search/{q}", "applications-accessories")
}

URL_REGEX = re.compile(
    r"^(https?://)?(www\.)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(/[^\s]*)?$",
    re.IGNORECASE
)

class WebProvider(BaseProvider):
    def __init__(self, history_manager):
        super().__init__(history_manager)
        self.bookmarks = []
        self._load_bookmarks()

    def _load_bookmarks(self):
        bookmarks = []
        # 1. Chromium / Chrome / Brave / Edge Bookmarks
        chromium_paths = [
            os.path.expanduser("~/.config/chromium/Default/Bookmarks"),
            os.path.expanduser("~/.config/google-chrome/Default/Bookmarks"),
            os.path.expanduser("~/.config/BraveSoftware/Brave-Browser/Default/Bookmarks"),
            os.path.expanduser("~/.config/microsoft-edge/Default/Bookmarks"),
            os.path.expanduser("~/.config/vivaldi/Default/Bookmarks")
        ]
        for path in chromium_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._extract_chromium_bookmarks(data.get("roots", {}), bookmarks)
                except Exception:
                    pass

        # 2. Firefox Bookmarks
        ff_base = os.path.expanduser("~/.mozilla/firefox")
        if os.path.exists(ff_base):
            try:
                for root, dirs, files in os.walk(ff_base):
                    if "places.sqlite" in files:
                        sqlite_path = os.path.join(root, "places.sqlite")
                        self._extract_firefox_bookmarks(sqlite_path, bookmarks)
            except Exception:
                pass

        self.bookmarks = bookmarks

    def _extract_chromium_bookmarks(self, node, bookmarks):
        if isinstance(node, dict):
            if node.get("type") == "url" and node.get("url") and node.get("name"):
                bookmarks.append({
                    "title": node["name"],
                    "url": node["url"],
                    "title_lower": node["name"].lower()
                })
            for v in node.values():
                if isinstance(v, (dict, list)):
                    self._extract_chromium_bookmarks(v, bookmarks)
        elif isinstance(node, list):
            for item in node:
                self._extract_chromium_bookmarks(item, bookmarks)

    def _extract_firefox_bookmarks(self, sqlite_path, bookmarks):
        try:
            uri = f"file:{sqlite_path}?immutable=1"
            conn = sqlite3.connect(uri, uri=True, timeout=1.0)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.title, p.url 
                FROM moz_bookmarks b
                JOIN moz_places p ON b.fk = p.id
                WHERE b.title IS NOT NULL AND p.url NOT LIKE "place:%"
                LIMIT 500
            """)
            for title, url in cursor.fetchall():
                if title and url:
                    bookmarks.append({
                        "title": title,
                        "url": url,
                        "title_lower": title.lower()
                    })
            conn.close()
        except Exception:
            pass

    def _open_url(self, url: str):
        try:
            subprocess.Popen(["xdg-open", url], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            try:
                Gio.AppInfo.launch_default_for_uri(url, None)
            except Exception as e:
                print(f"Error opening URL {url}: {e}")

    def _create_result(self, title: str, subtitle: str, url: str, icon: str, score: float, category: str = "Web") -> SearchResult:
        def _exec():
            self._open_url(url)

        def _copy():
            try:
                display = Gdk.Display.get_default()
                if display:
                    display.get_clipboard().set(url)
            except Exception:
                pass

        return SearchResult(
            id=f"web_{url}",
            title=title,
            subtitle=subtitle,
            icon=icon,
            score=score,
            category=category,
            provider="WebProvider",
            preview_data={"url": url, "query": title},
            action_execute=_exec,
            action_copy=_copy
        )

    def search(self, query: str, limit: int = 10, category_filter: str = None) -> list[SearchResult]:
        if category_filter not in (None, "All", "Web", "Bookmarks"):
            return []

        q = query.strip()
        if not q:
            return []

        results = []

        # 1. Search Bangs (!g, !yt, !gh, etc.)
        for bang, (service_name, template, icon) in BANGS.items():
            if q.startswith(bang + " ") or q == bang:
                sub_query = q[len(bang):].strip()
                if not sub_query:
                    results.append(self._create_result(
                        title=f"{service_name}",
                        subtitle=f"Type a query to search on {service_name}",
                        url=template.replace("{q}", ""),
                        icon=icon,
                        score=110
                    ))
                else:
                    encoded = urllib.parse.quote_plus(sub_query)
                    target_url = template.replace("{q}", encoded)
                    results.append(self._create_result(
                        title=f"{service_name}: {sub_query}",
                        subtitle=target_url,
                        url=target_url,
                        icon=icon,
                        score=120
                    ))
                return results

        # 2. Direct URL Detection
        if URL_REGEX.match(q):
            target_url = q if q.startswith(("http://", "https://")) else f"https://{q}"
            results.append(self._create_result(
                title=f"Open {q}",
                subtitle=target_url,
                url=target_url,
                icon="web-browser",
                score=105
            ))

        # 3. Browser Bookmarks Search
        q_lower = q.lower()
        for bm in self.bookmarks:
            score = 0
            t_lower = bm["title_lower"]
            url = bm["url"]

            if q_lower == t_lower:
                score = 100
            elif t_lower.startswith(q_lower):
                score = 90
            elif q_lower in t_lower:
                score = 80
            elif q_lower in url.lower():
                score = 70

            if score > 0:
                results.append(self._create_result(
                    title=bm["title"],
                    subtitle=url,
                    url=url,
                    icon="user-bookmarks",
                    score=score,
                    category="Bookmarks"
                ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
