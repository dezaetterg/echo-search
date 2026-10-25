import concurrent.futures

from logger import get_logger

logger = get_logger("search")
import threading

from providers import (
    AppProvider,
    CalculatorProvider,
    ClipboardProvider,
    CommandProvider,
    CurrencyProvider,
    EmojiProvider,
    FileProvider,
    HistoryManager,
    SearchResult,
    TimezoneProvider,
    UnitProvider,
    WeatherProvider,
    WebSearchProvider,
    parse_search_flag,
)

INSTANT_CATEGORIES = {"Math", "Units", "Currency", "Time", "Weather", "Commands"}


def get_result_category_group(result: SearchResult) -> str:
    """Classifies a search result into one of the canonical block categories."""
    cat = getattr(result, "category", "") or ""
    prov = getattr(result, "provider", "") or ""

    if cat in INSTANT_CATEGORIES:
        return "instant"
    if cat in ("Apps", "Settings") or prov == "AppProvider":
        return "apps"
    if cat == "Files" or prov == "FileProvider":
        return "files"
    if cat == "Clipboard" or prov == "ClipboardProvider":
        return "clipboard"
    if cat == "Emoji" or prov == "EmojiProvider":
        return "emoji"
    if cat == "Web" or prov == "WebSearchProvider":
        return "web"
    return "apps"


class SearchEngine:
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.history = HistoryManager(config_manager)

        self.calculator = CalculatorProvider(self.history)
        self.units = UnitProvider(self.history)
        self.commands = CommandProvider(self.history)
        self.timezone = TimezoneProvider(self.history)
        self.currency = CurrencyProvider(self.history)
        self.apps = AppProvider(self.history)
        self.files = FileProvider(self.history)
        self.clipboard = ClipboardProvider(self.history)
        self.emoji = EmojiProvider(self.history)
        self.weather = WeatherProvider(self.history, config_manager)
        self.web = WebSearchProvider(config_manager=config_manager, history_manager=self.history)

        self.providers = [
            self.calculator,
            self.units,
            self.currency,
            self.timezone,
            self.weather,
            self.commands,
            self.apps,
            self.clipboard,
            self.emoji,
            self.files,
            self.web
        ]

        self._provider_map = {
            "Apps": [self.apps],
            "Settings": [self.apps],
            "Files": [self.files],
            "Clipboard": [self.clipboard],
            "Emoji": [self.emoji],
            "Math": [self.calculator, self.units, self.currency],
            "Units": [self.units, self.currency],
            "Currency": [self.currency],
            "Commands": [self.commands],
            "Time": [self.timezone],
            "Weather": [self.weather],
            "Web": [self.web]
        }

        self._current_search_id = 0
        self._lock = threading.Lock()
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=4,
            thread_name_prefix="echo_search_worker"
        )

    def reload_providers(self):
        for provider in self.providers:
            if hasattr(provider, "reload_apps"):
                provider.reload_apps()

    def get_all_apps(self) -> list[SearchResult]:
        return self.apps.search("", limit=100, category_filter="Apps")

    def get_clipboard_history(self) -> list[SearchResult]:
        return self.clipboard.search("", limit=100, category_filter="Clipboard")

    def get_recent_files(self) -> list[SearchResult]:
        if hasattr(self.files, "get_recent_files"):
            return self.files.get_recent_files(limit=30)
        return self.files.search("", limit=20, category_filter="Files")

    def get_all_emojis(self) -> list[SearchResult]:
        return self.emoji.search("", limit=4000, category_filter="Emoji")

    def search_async(self, query: str, limit: int = 20, category_filter: str = None, callback = None):
        with self._lock:
            self._current_search_id += 1
            search_id = self._current_search_id

        def _search_worker():
            if self._current_search_id != search_id:
                return

            results = []

            clean_q = (query or "").strip()

            # 1. Если выбран конкретный режим/категория - опрашиваем только целевого провайдера (даже при пустой строке)
            if category_filter and category_filter not in (None, "All"):
                target_providers = self._provider_map.get(category_filter)
                if target_providers:
                    for p in target_providers:
                        if self._current_search_id != search_id:
                            return
                        try:
                            results.extend(p.search(clean_q, limit, category_filter))
                        except Exception as e:
                            logger.warning(f"Error in {p.__class__.__name__}: {e}")
                else:
                    for p in self.providers:
                        if self._current_search_id != search_id:
                            return
                        try:
                            results.extend(p.search(clean_q, limit, category_filter))
                        except Exception as e:
                            logger.warning(f"Provider {p.__class__.__name__} error: {e}")

            # 2. Если пустой запрос в глобальном режиме (All/None) - отдаем недавние приложения
            elif not clean_q:
                recent_when_empty = self.config_manager.get("recent_when_empty") if self.config_manager else True
                if recent_when_empty:
                    results.extend(self.apps.search("", limit, category_filter))

            # 3. Быстрые флаги веб-поиска (-g, -ya, -ddg, etc.)
            elif parse_search_flag(clean_q):
                web_results = self.web.search(clean_q, limit, category_filter)
                if web_results:
                    if self._current_search_id == search_id and callback:
                        from gi.repository import GLib
                        GLib.idle_add(callback, web_results, search_id)
                    return

            # 4. Глобальный поиск по всем провайдерам
            else:
                for p in self.providers:
                    if self._current_search_id != search_id:
                        return
                    try:
                        provider_results = p.search(clean_q, limit, category_filter)
                        if provider_results:
                            results.extend(provider_results)
                    except Exception as e:
                        logger.warning(f"Provider {p.__class__.__name__} error: {e}")

            if self._current_search_id != search_id:
                return

            results = self.group_and_sort_results(
                results,
                limit=limit,
                is_global=(category_filter in (None, "All"))
            )

            try:
                from gi.repository import GLib
                if self._current_search_id == search_id and callback:
                    GLib.idle_add(callback, results, search_id)
            except Exception as e:
                logger.debug(f"GLib callback dispatch error: {e}")

        self._executor.submit(_search_worker)

    def group_and_sort_results(self, results: list[SearchResult], limit: int = 20, is_global: bool = True) -> list[SearchResult]:
        """Groups and sorts search results according to category order and score."""
        if not results:
            return []

        group_enabled = True
        category_order = ["instant", "apps", "files", "clipboard", "emoji", "web"]
        max_per_cat = 5

        if self.config_manager:
            group_enabled = self.config_manager.get("group_results_by_category", True)
            custom_order = self.config_manager.get("results_category_order", category_order)
            if isinstance(custom_order, list) and custom_order:
                category_order = [str(c).lower() for c in custom_order]
            max_per_cat = self.config_manager.get("max_results_per_category", 5)

        if not group_enabled or not is_global:
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]

        # Group results into buckets
        buckets: dict[str, list[SearchResult]] = {}
        for r in results:
            grp = get_result_category_group(r)
            if grp not in buckets:
                buckets[grp] = []
            buckets[grp].append(r)

        # Sort within each bucket by score descending
        for grp in buckets:
            buckets[grp].sort(key=lambda x: x.score, reverse=True)

        # If only a single category matched, allow it to use the full limit
        if len(buckets) == 1:
            only_grp = next(iter(buckets))
            return buckets[only_grp][:limit]

        ordered_results: list[SearchResult] = []
        seen_groups = set()
        for grp in category_order:
            seen_groups.add(grp)
            if grp in buckets and buckets[grp]:
                cat_limit = 3 if grp == "instant" else max_per_cat
                ordered_results.extend(buckets[grp][:cat_limit])

        # Any extra categories not explicitly in category_order
        for grp, items in buckets.items():
            if grp not in seen_groups and items:
                ordered_results.extend(items[:max_per_cat])

        return ordered_results[:limit]

    def record_launch(self, app_id: str, query: str = ""):
        self.history.record_launch(app_id, query)
