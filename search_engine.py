import concurrent.futures
import threading
import uuid
from rapidfuzz import fuzz

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
        self.providers = [
            CalculatorProvider(self.history),
            UnitProvider(self.history),
            CommandProvider(self.history),
            AppProvider(self.history),
            FileProvider(self.history),
            ClipboardProvider(self.history),
            EmojiProvider(self.history)
        ]
        self._current_search_id = None
        self._lock = threading.Lock()
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=8,
            thread_name_prefix="echo_search_worker"
        )

    def _run_provider(self, provider, query, limit, category_filter, search_id):
        # Если поиск отменен до начала, выходим
        if self._current_search_id != search_id:
            return []

        try:
            results = provider.search(query, limit, category_filter)
            # Если отменен во время работы
            if self._current_search_id != search_id:
                return []
            return results
        except Exception as e:
            print(f"Error in {provider.__class__.__name__}: {e}")
            return []

    def reload_providers(self):
        for provider in self.providers:
            if hasattr(provider, "reload_apps"):
                provider.reload_apps()

    def get_all_apps(self) -> list[SearchResult]:
        for provider in self.providers:
            if isinstance(provider, AppProvider):
                return provider.search("", limit=100, category_filter="Apps")
        return []

    def get_clipboard_history(self) -> list[SearchResult]:
        for provider in self.providers:
            if isinstance(provider, ClipboardProvider):
                return provider.search("", limit=100, category_filter="Clipboard")
        return []

    def get_recent_files(self) -> list[SearchResult]:
        for provider in self.providers:
            if isinstance(provider, FileProvider):
                if hasattr(provider, "get_recent_files"):
                    return provider.get_recent_files(limit=30)
                return provider.search("", limit=20, category_filter="Files")
        return []

    def get_all_emojis(self) -> list[SearchResult]:
        for provider in self.providers:
            if isinstance(provider, EmojiProvider):
                return provider.search("", limit=4000, category_filter="Emoji")
        return []

    def search_async(self, query: str, limit: int, category_filter: str, callback):
        with self._lock:
            search_id = str(uuid.uuid4())
            self._current_search_id = search_id

        def _search():
            results = []

            # Если пустой запрос и фильтр не стоит, собираем недавние/частые через AppProvider
            if not query and category_filter in (None, "All"):
                recent_when_empty = self.config_manager.get("recent_when_empty") if self.config_manager else True
                if recent_when_empty:
                    app_prov = next((p for p in self.providers if isinstance(p, AppProvider)), None)
                    if app_prov:
                        results.extend(app_prov.search(query, limit, category_filter))
            else:
                # Параллельный опрос всех провайдеров через постоянный переиспользуемый пул потоков
                providers_to_run = self.providers
                futures = [
                    self._executor.submit(self._run_provider, p, query, limit, category_filter, search_id) 
                    for p in providers_to_run
                ]
                for future in concurrent.futures.as_completed(futures):
                    if self._current_search_id != search_id:
                        return
                    try:
                        results.extend(future.result())
                    except Exception as e:
                        print(f"Provider future error: {e}")

            if self._current_search_id != search_id:
                return

            # Финальная глобальная сортировка всех результатов по score
            results.sort(key=lambda x: x.score, reverse=True)

            # Возвращаем в callback через UI поток, только если этот поиск еще актуален
            try:
                import gi
                from gi.repository import GLib
                if self._current_search_id == search_id:
                    GLib.idle_add(callback, results[:limit], search_id)
            except Exception:
                pass

        threading.Thread(target=_search, daemon=True).start()

    def record_launch(self, app_id: str, query: str = ""):
        self.history.record_launch(app_id, query)
