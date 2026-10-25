import os
import subprocess

from i18n import t
from logger import get_logger
from utils import set_clipboard_text

from .base import BaseProvider, SearchResult

logger = get_logger("commands")


def _exec_toggle_bluetooth():
    try:
        out = subprocess.check_output(["bluetoothctl", "show"], text=True, stderr=subprocess.DEVNULL)
        new_state = "off" if "Powered: yes" in out else "on"
        subprocess.Popen(["bluetoothctl", "power", new_state], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        logger.error("Error toggling bluetooth: %s", e)


def _exec_toggle_wifi():
    try:
        out = subprocess.check_output(["nmcli", "radio", "wifi"], text=True, stderr=subprocess.DEVNULL).strip()
        new_state = "off" if out == "enabled" else "on"
        subprocess.Popen(["nmcli", "radio", "wifi", new_state], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        logger.error("Error toggling wifi: %s", e)


def _exec_toggle_mute():
    try:
        res = subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode != 0:
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        logger.error("Error toggling mute: %s", e)


def _exec_toggle_theme():
    # 1. Cinnamon (Linux Mint)
    try:
        cur_theme = subprocess.check_output(["gsettings", "get", "org.cinnamon.desktop.interface", "gtk-theme"], text=True, stderr=subprocess.DEVNULL).strip().strip("\x27\"")
        if cur_theme:
            if "Dark" in cur_theme:
                new_theme = cur_theme.replace("-Dark", "").replace("Dark", "")
            else:
                new_theme = f"{cur_theme}-Dark"
            subprocess.Popen(["gsettings", "set", "org.cinnamon.desktop.interface", "gtk-theme", f"'{new_theme}'"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                cur_cin = subprocess.check_output(["gsettings", "get", "org.cinnamon.theme", "name"], text=True, stderr=subprocess.DEVNULL).strip().strip("\x27\"")
                if "Dark" in cur_cin:
                    new_cin = cur_cin.replace("-Dark", "").replace("Dark", "")
                else:
                    new_cin = f"{cur_cin}-Dark"
                subprocess.Popen(["gsettings", "set", "org.cinnamon.theme", "name", f"'{new_cin}'"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                logger.debug("Cinnamon theme name toggle skipped: %s", e)
            return
    except Exception as e:
        logger.debug("Cinnamon desktop interface check skipped: %s", e)

    # 2. GNOME / Freedesktop standard color-scheme
    try:
        out = subprocess.check_output(["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"], text=True, stderr=subprocess.DEVNULL).strip()
        new_scheme = "'default'" if "prefer-dark" in out else "'prefer-dark'"
        subprocess.Popen(["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", new_scheme], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    except Exception as e:
        logger.debug("GNOME color-scheme toggle skipped: %s", e)

    # 3. KDE Plasma
    try:
        cur_kde = ""
        for kread in ("kreadconfig6", "kreadconfig5"):
            try:
                cur_kde = subprocess.check_output([kread, "--group", "General", "--key", "ColorScheme"], text=True, stderr=subprocess.DEVNULL).strip()
                if cur_kde:
                    break
            except Exception as e:
                logger.debug("KDE read config (%s) skipped: %s", kread, e)
                continue
        new_kde = "BreezeLight" if "Dark" in cur_kde else "BreezeDark"
        subprocess.Popen(["plasma-apply-colorscheme", new_kde], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    except Exception as e:
        logger.error("Error toggling theme: %s", e)


def _exec_toggle_night_light():
    # 1. Cinnamon (Linux Mint)
    try:
        out = subprocess.check_output(["gsettings", "get", "org.cinnamon.settings-daemon.plugins.color", "night-light-enabled"], text=True, stderr=subprocess.DEVNULL).strip()
        new_state = "false" if "true" in out else "true"
        subprocess.Popen(["gsettings", "set", "org.cinnamon.settings-daemon.plugins.color", "night-light-enabled", new_state], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    except Exception as e:
        logger.debug("Cinnamon night-light toggle skipped: %s", e)

    # 2. GNOME
    try:
        out = subprocess.check_output(["gsettings", "get", "org.gnome.settings-daemon.plugins.color", "night-light-enabled"], text=True, stderr=subprocess.DEVNULL).strip()
        new_state = "false" if "true" in out else "true"
        subprocess.Popen(["gsettings", "set", "org.gnome.settings-daemon.plugins.color", "night-light-enabled", new_state], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    except Exception as e:
        logger.debug("GNOME night-light toggle skipped: %s", e)

    # 3. KDE Plasma
    try:
        for qdbus_bin in ("qdbus6", "qdbus"):
            try:
                res = subprocess.run([qdbus_bin, "org.kde.KWin", "/ColorCorrect", "org.kde.kwin.ColorCorrect.nightColorActive"], text=True, capture_output=True)
                if res.returncode == 0:
                    new_val = "false" if "true" in res.stdout.lower() else "true"
                    subprocess.Popen([qdbus_bin, "org.kde.KWin", "/ColorCorrect", "org.kde.kwin.ColorCorrect.setNightColorActive", new_val], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
            except Exception as e:
                logger.debug("KDE qdbus (%s) night-light check skipped: %s", qdbus_bin, e)
                continue
    except Exception as e:
        logger.debug("KDE night-light check skipped: %s", e)

    # 4. Wayland standalone compositors (Hyprland / Sway) using wlsunset / gammastep
    try:
        if subprocess.run(["pkill", "-0", "wlsunset"], stderr=subprocess.DEVNULL).returncode == 0:
            subprocess.Popen(["pkill", "wlsunset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        if subprocess.run(["pkill", "-0", "gammastep"], stderr=subprocess.DEVNULL).returncode == 0:
            subprocess.Popen(["pkill", "gammastep"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        if subprocess.run(["which", "wlsunset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            subprocess.Popen(["wlsunset", "-t", "4000"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        if subprocess.run(["which", "gammastep"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            subprocess.Popen(["gammastep", "-O", "4000"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
    except Exception as e:
        logger.error("Error toggling night light: %s", e)


class CommandProvider(BaseProvider):
    def __init__(self, history_manager):
        super().__init__(history_manager)
        self.commands_def = [
            # System power commands
            {
                "id": "cmd_shutdown",
                "name_key": "cmd_shutdown_name",
                "desc_key": "cmd_shutdown_desc",
                "icon": "system-shutdown-symbolic",
                "cmd": "systemctl poweroff 2>/dev/null || loginctl poweroff 2>/dev/null || poweroff 2>/dev/null || shutdown -h now",
                "keywords": ["shutdown", "poweroff", "turn off", "halt", "выключить", "выключение", "питание", "вырубить"]
            },
            {
                "id": "cmd_reboot",
                "name_key": "cmd_reboot_name",
                "desc_key": "cmd_reboot_desc",
                "icon": "system-reboot-symbolic",
                "cmd": "systemctl reboot 2>/dev/null || loginctl reboot 2>/dev/null || reboot",
                "keywords": ["reboot", "restart", "reset", "перезагрузить", "перезагрузка", "рестарт"]
            },
            {
                "id": "cmd_suspend",
                "name_key": "cmd_suspend_name",
                "desc_key": "cmd_suspend_desc",
                "icon": "system-suspend-symbolic",
                "cmd": "systemctl suspend 2>/dev/null || loginctl suspend 2>/dev/null || zzz 2>/dev/null",
                "keywords": ["sleep", "suspend", "hibernate", "сон", "спящий", "спящий режим", "пауза"]
            },
            {
                "id": "cmd_logout",
                "name_key": "cmd_logout_name",
                "desc_key": "cmd_logout_desc",
                "icon": "system-log-out-symbolic",
                "cmd": "loginctl terminate-session self 2>/dev/null || gnome-session-quit --logout --no-prompt 2>/dev/null || cinnamon-session-quit --logout --no-prompt 2>/dev/null || qdbus org.kde.ksmserver /KSMServer logout 0 0 0 2>/dev/null",
                "keywords": ["logout", "log out", "sign out", "exit", "выйти", "выход", "выйти из системы", "завершить сеанс"]
            },
            {
                "id": "cmd_lock",
                "name_key": "cmd_lock_name",
                "desc_key": "cmd_lock_desc",
                "icon": "system-lock-screen-symbolic",
                "cmd": "loginctl lock-session 2>/dev/null || gnome-screensaver-command -l 2>/dev/null || cinnamon-screensaver-command -l 2>/dev/null || qdbus org.freedesktop.ScreenSaver /ScreenSaver Lock 2>/dev/null",
                "keywords": ["lock", "lock screen", "screen lock", "блок", "заблокировать", "заблокировать экран", "экран"]
            },

            # Bluetooth toggles
            {
                "id": "cmd_bluetooth_toggle",
                "name_key": "cmd_bluetooth_toggle_name",
                "desc_key": "cmd_bluetooth_toggle_desc",
                "icon": "bluetooth-active-symbolic",
                "action": _exec_toggle_bluetooth,
                "cmd_str": "bluetoothctl power toggle",
                "keywords": ["bluetooth", "bt", "блютуз", "синезуб", "bluetooth toggle", "переключить блютуз", "переключить bluetooth"]
            },
            {
                "id": "cmd_bluetooth_on",
                "name_key": "cmd_bluetooth_on_name",
                "desc_key": "cmd_bluetooth_on_desc",
                "icon": "bluetooth-active-symbolic",
                "cmd": "bluetoothctl power on",
                "keywords": ["bluetooth on", "включить блютуз", "включить bluetooth", "enable bluetooth", "turn on bluetooth", "блютуз вкл"]
            },
            {
                "id": "cmd_bluetooth_off",
                "name_key": "cmd_bluetooth_off_name",
                "desc_key": "cmd_bluetooth_off_desc",
                "icon": "bluetooth-disabled-symbolic",
                "cmd": "bluetoothctl power off",
                "keywords": ["bluetooth off", "выключить блютуз", "выключить bluetooth", "disable bluetooth", "turn off bluetooth", "блютуз выкл"]
            },

            # Wi-Fi toggles
            {
                "id": "cmd_wifi_toggle",
                "name_key": "cmd_wifi_toggle_name",
                "desc_key": "cmd_wifi_toggle_desc",
                "icon": "network-wireless-symbolic",
                "action": _exec_toggle_wifi,
                "cmd_str": "nmcli radio wifi toggle",
                "keywords": ["wifi", "wi-fi", "вайфай", "вай фай", "wifi toggle", "интернет", "сеть", "переключить вайфай", "переключить wifi"]
            },
            {
                "id": "cmd_wifi_on",
                "name_key": "cmd_wifi_on_name",
                "desc_key": "cmd_wifi_on_desc",
                "icon": "network-wireless-symbolic",
                "cmd": "nmcli radio wifi on",
                "keywords": ["wifi on", "wi-fi on", "включить вайфай", "включить wifi", "enable wifi", "turn on wifi", "вайфай вкл"]
            },
            {
                "id": "cmd_wifi_off",
                "name_key": "cmd_wifi_off_name",
                "desc_key": "cmd_wifi_off_desc",
                "icon": "network-wireless-offline-symbolic",
                "cmd": "nmcli radio wifi off",
                "keywords": ["wifi off", "wi-fi off", "выключить вайфай", "выключить wifi", "disable wifi", "turn off wifi", "вайфай выкл"]
            },

            # Sound / Mute toggles
            {
                "id": "cmd_mute_toggle",
                "name_key": "cmd_mute_toggle_name",
                "desc_key": "cmd_mute_toggle_desc",
                "icon": "audio-volume-muted-symbolic",
                "action": _exec_toggle_mute,
                "cmd_str": "wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle",
                "keywords": ["mute", "unmute", "звук", "без звука", "громкость", "audio", "sound", "volume", "переключить звук", "заглушить", "выключить звук"]
            },
            {
                "id": "cmd_mute_on",
                "name_key": "cmd_mute_on_name",
                "desc_key": "cmd_mute_on_desc",
                "icon": "audio-volume-muted-symbolic",
                "cmd": "wpctl set-mute @DEFAULT_AUDIO_SINK@ 1 2>/dev/null || pactl set-sink-mute @DEFAULT_SINK@ 1 2>/dev/null",
                "keywords": ["mute on", "выключить звук", "отключить звук", "тишина", "silence", "mute audio", "звук выкл"]
            },
            {
                "id": "cmd_mute_off",
                "name_key": "cmd_mute_off_name",
                "desc_key": "cmd_mute_off_desc",
                "icon": "audio-volume-high-symbolic",
                "cmd": "wpctl set-mute @DEFAULT_AUDIO_SINK@ 0 2>/dev/null || pactl set-sink-mute @DEFAULT_SINK@ 0 2>/dev/null",
                "keywords": ["unmute", "включить звук", "звук вкл", "unmute audio", "восстановить звук"]
            },

            # Theme Dark / Light toggles
            {
                "id": "cmd_theme_toggle",
                "name_key": "cmd_theme_toggle_name",
                "desc_key": "cmd_theme_toggle_desc",
                "icon": "preferences-desktop-theme-symbolic",
                "action": _exec_toggle_theme,
                "cmd_str": "toggle dark/light theme",
                "keywords": ["тема", "переключить тему", "сменить тему", "theme", "dark mode", "light mode", "темная тема", "светлая тема", "toggle theme"]
            },
            {
                "id": "cmd_theme_dark",
                "name_key": "cmd_theme_dark_name",
                "desc_key": "cmd_theme_dark_desc",
                "icon": "weather-clear-night-symbolic",
                "cmd": "gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark' 2>/dev/null || plasma-apply-colorscheme BreezeDark 2>/dev/null",
                "keywords": ["dark theme", "темная тема", "тёмная тема", "ночная тема", "dark mode", "включить темную тему"]
            },
            {
                "id": "cmd_theme_light",
                "name_key": "cmd_theme_light_name",
                "desc_key": "cmd_theme_light_desc",
                "icon": "weather-clear-symbolic",
                "cmd": "gsettings set org.gnome.desktop.interface color-scheme 'default' 2>/dev/null || plasma-apply-colorscheme BreezeLight 2>/dev/null",
                "keywords": ["light theme", "светлая тема", "дневная тема", "light mode", "включить светлую тему"]
            },

            # Night Light toggles
            {
                "id": "cmd_night_light_toggle",
                "name_key": "cmd_night_light_toggle_name",
                "desc_key": "cmd_night_light_toggle_desc",
                "icon": "night-light-symbolic",
                "action": _exec_toggle_night_light,
                "cmd_str": "toggle night light",
                "keywords": ["night light", "ночной свет", "ночной режим", "переключить ночной свет", "защита глаз", "синий свет", "night mode", "теплый свет"]
            },
            {
                "id": "cmd_night_light_on",
                "name_key": "cmd_night_light_on_name",
                "desc_key": "cmd_night_light_on_desc",
                "icon": "night-light-symbolic",
                "cmd": "gsettings set org.gnome.settings-daemon.plugins.color night-light-enabled true 2>/dev/null",
                "keywords": ["night light on", "включить ночной свет", "включить ночной режим", "enable night light", "теплые цвета"]
            },
            {
                "id": "cmd_night_light_off",
                "name_key": "cmd_night_light_off_name",
                "desc_key": "cmd_night_light_off_desc",
                "icon": "night-light-symbolic",
                "cmd": "gsettings set org.gnome.settings-daemon.plugins.color night-light-enabled false 2>/dev/null",
                "keywords": ["night light off", "выключить ночной свет", "выключить ночной режим", "disable night light"]
            },
        ]

    def _create_result(self, cmd_data: dict, score: float) -> SearchResult:
        name = t(cmd_data["name_key"])
        desc = t(cmd_data["desc_key"])
        cmd_str = cmd_data.get("cmd", cmd_data.get("cmd_str", name))

        def _exec_callback():
            try:
                if callable(cmd_data.get("action")):
                    cmd_data["action"]()
                elif "cmd" in cmd_data:
                    subprocess.Popen(
                        cmd_data["cmd"],
                        shell=True,
                        start_new_session=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
            except Exception as e:
                logger.error("Error executing command %s: %s", cmd_data.get("id"), e)

        def _copy_callback():
            set_clipboard_text(cmd_str)

        return SearchResult(
            id=cmd_data["id"],
            title=name,
            subtitle=desc,
            icon=cmd_data["icon"],
            score=score,
            category="Commands",
            provider="CommandProvider",
            preview_data={"cmd": cmd_str},
            action_execute=_exec_callback,
            action_copy=_copy_callback
        )

    def search(self, query: str, limit: int = 10, category_filter: str = None) -> list[SearchResult]:
        if category_filter not in (None, "All", "Commands"):
            return []

        if not query:
            return []

        results = []
        q = query.lower().strip()
        q_words = [w for w in q.split() if len(w) > 0]

        for cmd in self.commands_def:
            name = t(cmd["name_key"]).lower()
            score = 0
            if q == name:
                score = max(score, 110)
            elif name.startswith(q):
                score = max(score, 95)
            elif q in name:
                score = max(score, 85)

            for kw in cmd.get("keywords", []):
                kw_lower = kw.lower()
                if q == kw_lower:
                    score = max(score, 105)
                elif kw_lower.startswith(q):
                    score = max(score, 92)
                elif q in kw_lower:
                    score = max(score, 82)
                elif q_words and all(w in kw_lower or w in name for w in q_words):
                    score = max(score, 88)

            if score > 0:
                results.append(self._create_result(cmd, score))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
