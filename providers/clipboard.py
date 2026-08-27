import datetime
from .base import BaseProvider, SearchResult

try:
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk, Gdk, GLib, Pango
except (ValueError, ImportError):
    pass

# Standard Linux desktop privacy hints used by password managers (KeePassXC, 1Password, Bitwarden, GNOME Secrets)
PASSWORD_MANAGER_MIME_HINTS = {
    "x-kde-passwordmanagerhint",
    "application/x-keepassxc-password",
    "application/x-secret",
    "application/x-credential",
    "application/x-password",
    "text/x-moz-url-priv",
    "org.keepassxc.password"
}

class ClipboardProvider(BaseProvider):
    def __init__(self, history_manager):
        super().__init__(history_manager)
        self.history = []  # List of dicts: {"text": str, "time": datetime}
        self.on_new_item = None

        try:
            display = Gdk.Display.get_default()
            if display:
                self.clipboard = display.get_clipboard()
                self.clipboard.connect("changed", self._on_clipboard_changed)
                self._check_and_read(self.clipboard)
        except Exception as e:
            print(f"Warning: Could not initialize ClipboardProvider: {e}")

    def _is_secret_clipboard(self, clipboard) -> bool:
        """Checks whether the clipboard contains sensitive password manager hints."""
        try:
            formats = clipboard.get_formats()
            if formats:
                mimes = formats.get_mime_types() or []
                for mime in mimes:
                    mime_lower = mime.lower()
                    for hint in PASSWORD_MANAGER_MIME_HINTS:
                        if hint in mime_lower:
                            return True
        except Exception:
            pass
        return False

    def _check_and_read(self, clipboard):
        if self._is_secret_clipboard(clipboard):
            return
        clipboard.read_text_async(None, self._on_text_read)

    def _on_clipboard_changed(self, clipboard):
        self._check_and_read(clipboard)

    def _on_text_read(self, clipboard, result):
        try:
            # Double-check privacy flags before finalizing
            if self._is_secret_clipboard(clipboard):
                return

            text = clipboard.read_text_finish(result)
            if text and text.strip():
                text = text.strip()
                # Memory guard: limit massive raw clipboard texts (e.g. 50MB dumps) to 32KB
                max_len = 32768
                if len(text) > max_len:
                    text = text[:max_len] + "\n... [Обрезано для оптимизации памяти]"

                # Remove if exists to move to top
                self.history = [item for item in self.history if item["text"] != text]

                item = {
                    "text": text,
                    "time": datetime.datetime.now()
                }
                self.history.insert(0, item)

                if len(self.history) > 50:
                    self.history = self.history[:50]

                if self.on_new_item:
                    import gi
                    from gi.repository import GLib
                    res = self._create_result(item, 0)
                    GLib.idle_add(self.on_new_item, res)
        except Exception:
            pass

    def _create_result(self, item: dict, index: int) -> SearchResult:
        text = item["text"]
        lines = text.split("\n")
        title = "\n".join(lines[:3])

        def _copy_callback():
            try:
                display = Gdk.Display.get_default()
                if display:
                    display.get_clipboard().set(text)
            except Exception:
                pass

        def _delete_callback():
            try:
                if item in self.history:
                    self.history.remove(item)
            except Exception:
                pass

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

        q = query.lower().strip()
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
