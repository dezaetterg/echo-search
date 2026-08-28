import concurrent.futures
import threading

from providers import (
    HistoryManager, 
    AppProvider, 
    CalculatorProvider, 
    UnitProvider, 
    CommandProvider,
    FileProvider,
    ClipboardProvider,
    EmojiProvider,
    SearchResult
)

class SearchEngine:
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.history = HistoryManager(config_manager)
        
        self.calculator = CalculatorProvider(self.history)
        self.units = UnitProvider(self.history)
        self.commands = CommandProvider(self.history)
        self.apps = AppProvider(self.history)
        self.files = FileProvider(self.history)
        self.clipboard = ClipboardProvider(self.history)
        self.emoji = EmojiProvider(self.history)
        
        self.providers = [
            self.calculator,
            self.units,
            self.commands,
            self.apps,
            self.files,
            self.clipboard,
            self.emoji
        ]
        
        self._provider_map = {
            "Apps": [self.apps],
            "Settings": [self.apps],
            "Files": [self.files],
            "Clipboard": [self.clipboard],
            "Emoji": [self.emoji],
            "Math": [self.calculator, self.units],
            "Units": [self.units],
            "Commands": [self.commands]
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

            # 1. Если пустой запрос и фильтр не стоит, отдаем недавние приложения
            if not query and category_filter in (None, "All"):
                recent_when_empty = self.config_manager.get("recent_when_empty") if self.config_manager else True
                if recent_when_empty:
                    results.extend(self.apps.search(query, limit, category_filter))
            
            # 2. Если выбран конкретный режим/категория - опрашиваем только целевого провайдера
            elif category_filter and category_filter in self._provider_map:
                target_providers = self._provider_map[category_filter]
                for p in target_providers:
                    if self._current_search_id != search_id:
                        return
                    try:
                        results.extend(p.search(query, limit, category_filter))
                    except Exception as e:
                        print(f"Error in {p.__class__.__name__}: {e}")
            
            # 3. Глобальный поиск - последовательный опрос без вложенного deadlock пула потоков
            else:
                for p in self.providers:
                    if self._current_search_id != search_id:
                        return
                    try:
                        provider_results = p.search(query, limit, category_filter)
                        if provider_results:
                            results.extend(provider_results)
                    except Exception as e:
                        print(f"Provider {p.__class__.__name__} error: {e}")

            if self._current_search_id != search_id:
                return

            # Сортировка результатов по релевантности
            results.sort(key=lambda x: x.score, reverse=True)

            try:
                from gi.repository import GLib
                if self._current_search_id == search_id and callback:
                    GLib.idle_add(callback, results[:limit], search_id)
            except Exception:
                pass

        self._executor.submit(_search_worker)

    def record_launch(self, app_id: str, query: str = ""):
        self.history.record_launch(app_id, query)
