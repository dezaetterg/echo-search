import os
from .base import BaseProvider, SearchResult
from i18n import t

class CommandProvider(BaseProvider):
    def __init__(self, history_manager):
        super().__init__(history_manager)
        self.commands_def = [
            {
                "id": "cmd_shutdown",
                "name_key": "cmd_shutdown_name",
                "desc_key": "cmd_shutdown_desc",
                "icon": "system-shutdown",
                "cmd": "systemctl poweroff",
                "keywords": ["shutdown", "poweroff", "turn off", "halt", "выключить", "выключение", "питание"]
            },
            {
                "id": "cmd_reboot",
                "name_key": "cmd_reboot_name",
                "desc_key": "cmd_reboot_desc",
                "icon": "system-reboot",
                "cmd": "systemctl reboot",
                "keywords": ["reboot", "restart", "reset", "перезагрузить", "перезагрузка", "рестарт"]
            },
            {
                "id": "cmd_suspend",
                "name_key": "cmd_suspend_name",
                "desc_key": "cmd_suspend_desc",
                "icon": "system-suspend",
                "cmd": "systemctl suspend",
                "keywords": ["sleep", "suspend", "hibernate", "сон", "спящий", "спящий режим", "пауза"]
            },
            {
                "id": "cmd_logout",
                "name_key": "cmd_logout_name",
                "desc_key": "cmd_logout_desc",
                "icon": "system-log-out",
                "cmd": "loginctl terminate-session self 2>/dev/null || gnome-session-quit --logout --no-prompt 2>/dev/null || cinnamon-session-quit --logout --no-prompt 2>/dev/null || qdbus org.kde.ksmserver /KSMServer logout 0 0 0 2>/dev/null",
                "keywords": ["logout", "log out", "sign out", "exit", "выйти", "выход", "выйти из системы", "завершить сеанс"]
            },
            {
                "id": "cmd_lock",
                "name_key": "cmd_lock_name",
                "desc_key": "cmd_lock_desc",
                "icon": "system-lock-screen",
                "cmd": "loginctl lock-session 2>/dev/null || gnome-screensaver-command -l 2>/dev/null || cinnamon-screensaver-command -l 2>/dev/null || qdbus org.freedesktop.ScreenSaver /ScreenSaver Lock 2>/dev/null",
                "keywords": ["lock", "lock screen", "screen lock", "блок", "заблокировать", "заблокировать экран", "экран"]
            },
        ]

    def _create_result(self, cmd_data: dict, score: float) -> SearchResult:
        name = t(cmd_data["name_key"])
        desc = t(cmd_data["desc_key"])
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
            title=name,
            subtitle=desc,
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
        q = query.lower().strip()
        
        for cmd in self.commands_def:
            name = t(cmd["name_key"]).lower()
            score = 0
            if q == name: score = 100
            elif name.startswith(q): score = 90
            elif q in name: score = 80
            else:
                for kw in cmd["keywords"]:
                    if q == kw: score = max(score, 95)
                    elif kw.startswith(q): score = max(score, 85)
                    elif q in kw: score = max(score, 75)
            
            if score > 0:
                results.append(self._create_result(cmd, score))
                
        results.sort(key=lambda x: x.score, reverse=True)
        return results
