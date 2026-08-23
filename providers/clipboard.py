import datetime
from .base import BaseProvider, SearchResult

try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk, GLib, Pango
except ValueError:
    pass

class ClipboardProvider(BaseProvider):
    def __init__(self, history_manager):
        super().__init__(history_manager)
        self.history = [] # List of dicts: {"text": str, "time": datetime}
        self.on_new_item = None
        
        try:
            self.clipboard = Gdk.Display.get_default().get_clipboard()
            self.clipboard.connect("changed", self._on_clipboard_changed)
            self.clipboard.read_text_async(None, self._on_text_read)
        except Exception:
            pass

    def _on_clipboard_changed(self, clipboard):
        clipboard.read_text_async(None, self._on_text_read)

    def _on_text_read(self, clipboard, result):
        try:
            text = clipboard.read_text_finish(result)
            if text and text.strip():
                text = text.strip()
                # Remove if exists to move to top
                self.history = [item for item in self.history if item["text"] != text]
                
                item = {
                    "text": text,
                    "time": datetime.datetime.now()
                }
                self.history.insert(0, item)
                
                if len(self.history) > 100:
                    self.history = self.history[:100]
                    
                if self.on_new_item:
                    import gi
                    from gi.repository import GLib
                    # We pass the SearchResult representation
                    res = self._create_result(item, 0)
                    GLib.idle_add(self.on_new_item, res)
        except Exception:
            pass

    def _create_result(self, item: dict, index: int) -> SearchResult:
        text = item["text"]
        
        lines = text.split('\n')
        # We will show up to 3 lines. The mode will handle Ellipsize
        title = '\n'.join(lines[:3])
            
        def _copy_callback():
            try:
                self.clipboard.set(text)
            except: pass
            
        def _delete_callback():
            try:
                if item in self.history:
                    self.history.remove(item)
            except: pass

        time_str = item["time"].strftime("%H:%M:%S")

        return SearchResult(
            id=f"clip_{index}",
            title=title,
            subtitle=time_str,
            icon="edit-paste",
            score=100 - index,
            category="Clipboard",
            provider="ClipboardProvider",
            preview_data={
                "full_text": text,
                "lines_count": len(lines),
                "chars_count": len(text),
                "copy_time": time_str
            },
            action_execute=_copy_callback,
            action_copy=_copy_callback,
            action_delete=_delete_callback
        )

    def search(self, query: str, limit: int = 10, category_filter: str = None) -> list[SearchResult]:
        if category_filter not in (None, "All", "Clipboard"):
            return []
            
        q = query.lower()
        if category_filter == "Clipboard" and not q:
            return [self._create_result(item, i) for i, item in enumerate(self.history[:limit])]
            
        if not q:
            return []
            
        if q in ("clip", "clipboard", "буфер"):
            return [self._create_result(item, i) for i, item in enumerate(self.history[:limit])]
            
        results = []
        for i, item in enumerate(self.history):
            if q in item["text"].lower():
                results.append(self._create_result(item, i))
                
        return results[:limit]
