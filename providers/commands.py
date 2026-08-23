import os
from .base import BaseProvider, SearchResult

class CommandProvider(BaseProvider):
    def __init__(self, history_manager):
        super().__init__(history_manager)
        self.commands = [
            {"id": "cmd_shutdown", "name": "Выключить", "desc": "Выключить компьютер", "icon": "system-shutdown", "cmd": "systemctl poweroff", "keywords": ["выключить", "poweroff", "shutdown", "halt"]},
            {"id": "cmd_reboot", "name": "Перезагрузить", "desc": "Перезагрузить", "icon": "system-reboot", "cmd": "systemctl reboot", "keywords": ["перезагрузить", "рестарт", "reboot", "restart"]},
            {"id": "cmd_suspend", "name": "Спящий режим", "desc": "Спящий режим", "icon": "system-suspend", "cmd": "systemctl suspend", "keywords": ["сон", "спящий", "sleep", "suspend"]},
            {"id": "cmd_logout", "name": "Выйти из системы", "desc": "Выйти из системы", "icon": "system-log-out", "cmd": "gnome-session-quit --logout --no-prompt", "keywords": ["выйти", "logout", "log out"]},
            {"id": "cmd_lock", "name": "Заблокировать экран", "desc": "Заблокировать экран", "icon": "system-lock-screen", "cmd": "loginctl lock-session", "keywords": ["блок", "заблокировать", "lock", "screen"]},
        ]

    def _create_result(self, cmd_data: dict, score: float) -> SearchResult:
        def _exec_callback():
            os.system(f"{cmd_data['cmd']} &")
            
        def _copy_callback():
            try:
                import gi
                gi.require_version('Gtk', '4.0')
                from gi.repository import Gdk
                clipboard = Gdk.Display.get_default().get_clipboard()
                clipboard.set(cmd_data['cmd'])
            except: pass

        return SearchResult(
            id=cmd_data['id'],
            title=cmd_data['name'],
            subtitle=cmd_data['desc'],
            icon=cmd_data['icon'],
            score=score,
            category="Commands",
            provider="CommandProvider",
            preview_data={"cmd": cmd_data['cmd']},
            action_execute=_exec_callback,
            action_copy=_copy_callback
        )

    def search(self, query: str, limit: int = 10, category_filter: str = None) -> list[SearchResult]:
        if category_filter not in (None, "All"):
            return []
            
        if not query:
            return []

        results = []
        q = query.lower()
        
        for cmd in self.commands:
            score = 0
            if q == cmd["name"].lower(): score = 100
            elif cmd["name"].lower().startswith(q): score = 90
            else:
                for kw in cmd["keywords"]:
                    if q == kw: score = max(score, 95)
                    elif kw.startswith(q): score = max(score, 85)
            
            if score > 0:
                results.append(self._create_result(cmd, score))
                
        results.sort(key=lambda x: x.score, reverse=True)
        return results
