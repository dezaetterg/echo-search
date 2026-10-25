import json
import os
import shutil
import subprocess
from pathlib import Path

from i18n import i18n
from logger import get_logger

logger = get_logger("config")

def _detect_system_theme() -> str:
    """Universal cross-DE / cross-distro dark/light theme detector (Cinnamon, GNOME, KDE, XFCE, etc.)."""
    # 1. FreeDesktop Portal (Universal across all modern DEs including Wayland)
    try:
        import gi
        gi.require_version('Gio', '2.0')
        from gi.repository import Gio, GLib
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        proxy = Gio.DBusProxy.new_sync(
            bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.freedesktop.portal.Desktop",
            "/org/freedesktop/portal/desktop",
            "org.freedesktop.portal.Settings",
            None
        )
        res = proxy.call_sync(
            "Read",
            GLib.Variant("(ss)", ("org.freedesktop.appearance", "color-scheme")),
            Gio.DBusCallFlags.NONE,
            500,
            None
        )
        if res:
            val = res.get_child_value(0).get_variant().get_variant().get_uint32()
            if val == 1:
                return "dark"
            elif val == 2:
                return "light"
    except Exception as e:
        logger.debug("Portal theme detection unavailable: %s", e)

    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    has_gsettings = shutil.which("gsettings") is not None

    def _check_kde() -> str | None:
        try:
            kdeglobals = Path(os.path.expanduser("~/.config/kdeglobals"))
            if kdeglobals.exists():
                content = kdeglobals.read_text(encoding="utf-8", errors="ignore").lower()
                if "colorcheme=breezedark" in content or "dark" in content:
                    return "dark"
                elif "colorcheme=breeze" in content or "light" in content:
                    return "light"
        except Exception as e:
            logger.debug("KDE theme detection error: %s", e)
        return None

    def _check_xfce() -> str | None:
        if shutil.which("xfconf-query"):
            try:
                res = subprocess.run(
                    ["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName"],
                    capture_output=True, text=True, timeout=1
                )
                if res.returncode == 0:
                    val = res.stdout.strip().lower()
                    if "dark" in val:
                        return "dark"
                    elif val:
                        return "light"
            except Exception as e:
                logger.debug("XFCE theme detection error: %s", e)
        return None

    def _check_cinnamon() -> str | None:
        if not has_gsettings:
            return None
        for schema, key in (
            ("org.cinnamon.desktop.interface", "gtk-theme"),
            ("org.cinnamon.theme", "name"),
        ):
            try:
                res = subprocess.run(
                    ["gsettings", "get", schema, key],
                    capture_output=True, text=True, timeout=1
                )
                if res.returncode == 0:
                    val = res.stdout.strip().strip("'").lower()
                    if "dark" in val:
                        return "dark"
                    elif val:
                        return "light"
            except Exception as e:
                logger.debug("Cinnamon theme detection error (%s %s): %s", schema, key, e)
        return None

    def _check_gnome() -> str | None:
        if not has_gsettings:
            return None
        try:
            res = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True, text=True, timeout=1
            )
            if res.returncode == 0:
                val = res.stdout.strip().strip("'").lower()
                if "dark" in val:
                    return "dark"
                elif "light" in val or "default" in val:
                    return "light"
        except Exception as e:
            logger.debug("GNOME theme detection error: %s", e)
        return None

    # Targeted desktop check
    if "kde" in desktop:
        theme = _check_kde()
        if theme:
            return theme
    elif "xfce" in desktop:
        theme = _check_xfce()
        if theme:
            return theme
    elif "cinnamon" in desktop:
        theme = _check_cinnamon() or _check_gnome()
        if theme:
            return theme
    elif any(d in desktop for d in ("gnome", "ubuntu", "unity", "pantheon")):
        theme = _check_gnome()
        if theme:
            return theme

    # General fallback
    theme = _check_gnome() or _check_cinnamon() or _check_kde() or _check_xfce()
    if theme:
        return theme

    return "dark"

class ConfigManager:
    def __init__(self, config_dir=None):
        if config_dir:
            self.config_dir = Path(config_dir)
            self._is_custom_dir = True
        else:
            self.config_dir = Path(os.path.expanduser("~/.config/echo-search"))
            self._is_custom_dir = False
        self.config_file = self.config_dir / "config.json"

        system_theme = _detect_system_theme()
        self.defaults = {
            "theme": system_theme,
            "language": "auto",
            "blur": True,
            "transparency": 0.15,
            "preview_enabled": True,
            "preview_width": 420,
            "results_limit": 20,
            "animations": True,
            "animation_speed": 100,
            "unfold_animation": "instant_dynamic",
            "launch_at_login": False,
            "launch_shortcut": "<Super>Space",
            "quick_look_shortcut": "space",

            "applications": True,
            "files": True,
            "clipboard": True,
            "emoji": True,
            "calculator": True,
            "commands": True,
            "timezone": True,
            "weather": True,
            "weather_default_city": "Новокузнецк",
            "temperature_unit": "celsius",
            "settings": True,

            "icon_theme": "dark",
            "recent_when_empty": True,
            "search_history": True,
            "web_search_engine": "google",
            "web_search_custom_url": "",
            "web_search_flags": True,
            "highlight_matches": True,
            "show_action_bar": True,
            "show_alt_badges": True,
            "group_results_by_category": True,
            "results_category_order": ["instant", "apps", "files", "clipboard", "emoji", "web"],
            "max_results_per_category": 5
        }

        self.config = {}
        self.load()

    def load(self):
        self.config = self.defaults.copy()
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    user_config = json.load(f)
                    for key, val in user_config.items():
                        if key in self.defaults:
                            expected_type = type(self.defaults[key])
                            if isinstance(val, expected_type):
                                self.config[key] = val
                            # Special case: float to int (e.g. 20.0 to 20)
                            elif expected_type == int and isinstance(val, float):
                                self.config[key] = int(val)
                            # Special case: int to float (e.g. 1 to 1.0)
                            elif expected_type == float and isinstance(val, int):
                                self.config[key] = float(val)

                    # Backwards compatibility with legacy configuration schema
                    if self.config.get("theme") == "silver":
                        self.config["theme"] = "dark_glass"

                    if "results_category_order" in self.config:
                        val = self.config["results_category_order"]
                        if not isinstance(val, list) or not val:
                            self.config["results_category_order"] = list(self.defaults["results_category_order"])

                    if "enabled_modes" in user_config:
                        modes = user_config["enabled_modes"]
                        self.config["applications"] = "Apps" in modes
                        self.config["files"] = "Files" in modes
                        self.config["clipboard"] = "Clipboard" in modes
                        self.config["emoji"] = "Emoji" in modes
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        else:
            self.save()

        i18n.set_language(self.config.get("language", "auto"))
        if not self._is_custom_dir:
            self._sync_autostart(self.get("launch_at_login"))
            self._sync_desktop_hotkey(self.get("launch_shortcut", "<Super>Space"))
            self.apply_icon_theme(self.get("icon_theme", "dark"))

    def save(self):
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            # Ensure enabled_modes is explicitly written to config file
            self.config["enabled_modes"] = self.get("enabled_modes")
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get(self, key, default=None):
        if key == "enabled_modes":
            modes = []
            if self.config.get("applications", True): modes.append("Apps")
            if self.config.get("files", True): modes.append("Files")
            if self.config.get("clipboard", True): modes.append("Clipboard")
            if self.config.get("emoji", True): modes.append("Emoji")
            if self.config.get("settings", True): modes.append("Settings")
            return modes
        val = self.config.get(key)
        if val is not None:
            return val
        if default is not None:
            return default
        return self.defaults.get(key)

    def apply_to_engine(self, engine):
        if not hasattr(self, '_all_providers_cache') or not self._all_providers_cache:
            self._all_providers_cache = engine.providers.copy()

        active = []
        for p in self._all_providers_cache:
            name = p.__class__.__name__
            if name == "AppProvider" and (self.get("applications") or self.get("settings")):
                active.append(p)
            elif name == "FileProvider" and self.get("files"):
                active.append(p)
            elif name == "ClipboardProvider" and self.get("clipboard"):
                active.append(p)
            elif name == "EmojiProvider" and self.get("emoji"):
                active.append(p)
            elif name == "CalculatorProvider" and self.get("calculator"):
                active.append(p)
            elif name == "CommandProvider" and self.get("commands"):
                active.append(p)
            elif name == "UnitProvider" and self.get("calculator"):
                active.append(p)
            elif name == "CurrencyProvider" and self.get("calculator"):
                active.append(p)
            elif name == "TimezoneProvider" and self.get("timezone", True):
                active.append(p)
            elif name == "WeatherProvider" and self.get("weather", True):
                active.append(p)

        engine.providers = active

    def set(self, key, value):
        self.config[key] = value
        self.save()
        if key == "language":
            i18n.set_language(value)
        elif key == "icon_theme":
            self.apply_icon_theme(value)
        elif not self._is_custom_dir:
            if key in ("launch_shortcut", "hotkey"):
                self._sync_desktop_hotkey(value)
            elif key == "launch_at_login":
                self._sync_autostart(value)

    def _sync_autostart(self, enabled: bool):
        autostart_dir = Path(os.path.expanduser("~/.config/autostart"))
        desktop_file = autostart_dir / "com.echo.search.desktop"

        if enabled:
            autostart_dir.mkdir(parents=True, exist_ok=True)
            content = """[Desktop Entry]
Type=Application
Name=Echo
GenericName=Spotlight Search Launcher
Comment=Modern Liquid Glass Spotlight launcher
Exec=echo-search
Icon=com.echo.search
Terminal=false
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
            try:
                with open(desktop_file, "w") as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Error enabling autostart: {e}")
        else:
            if desktop_file.exists():
                try:
                    desktop_file.unlink()
                except Exception as e:
                    logger.error(f"Error disabling autostart: {e}")

    def _sync_desktop_hotkey(self, hotkey_str):
        import ast
        import re
        import subprocess

        EN_TO_RU = {
            'q': 'Cyrillic_shorti', 'w': 'Cyrillic_tse', 'e': 'Cyrillic_u', 'r': 'Cyrillic_ka', 't': 'Cyrillic_ie',
            'y': 'Cyrillic_en', 'u': 'Cyrillic_ge', 'i': 'Cyrillic_sha', 'o': 'Cyrillic_shcha', 'p': 'Cyrillic_ze',
            'a': 'Cyrillic_ef', 's': 'Cyrillic_yeru', 'd': 'Cyrillic_ve', 'f': 'Cyrillic_a', 'g': 'Cyrillic_pe',
            'h': 'Cyrillic_er', 'j': 'Cyrillic_o', 'k': 'Cyrillic_el', 'l': 'Cyrillic_de',
            'z': 'Cyrillic_ya', 'x': 'Cyrillic_che', 'c': 'Cyrillic_es', 'v': 'Cyrillic_em', 'b': 'Cyrillic_i',
            'n': 'Cyrillic_te', 'm': 'Cyrillic_softsign', 'bracketleft': 'Cyrillic_ha', 'bracketright': 'Cyrillic_hardsign',
            'semicolon': 'Cyrillic_zhe', 'apostrophe': 'Cyrillic_e', 'comma': 'Cyrillic_be', 'period': 'Cyrillic_yu',
            'grave': 'Cyrillic_io'
        }

        # Calculate companion Cyrillic binding for multi-layout support
        ru_binding = None
        m = re.search(r'^(<.*>)(.*)$', hotkey_str)
        if m:
            mods, key = m.group(1), m.group(2).lower()
            if key in EN_TO_RU:
                ru_binding = f"{mods}{EN_TO_RU[key]}"

        # 1. GNOME / Budgie / Unity
        try:
            MEDIA_KEYS = 'org.gnome.settings-daemon.plugins.media-keys'
            CUSTOM_SCHEMA = 'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding'
            res = subprocess.run(['gsettings', 'get', MEDIA_KEYS, 'custom-keybindings'], capture_output=True, text=True)
            if res.returncode == 0:
                raw = res.stdout.strip().replace('@as', '').strip()
                current_paths = ast.literal_eval(raw) if '[' in raw else []

                primary_slot = None
                for path in current_paths:
                    n = subprocess.run(['gsettings', 'get', f'{CUSTOM_SCHEMA}:{path}', 'name'], capture_output=True, text=True)
                    if n.stdout.strip().strip("'") == 'Echo Search':
                        primary_slot = path
                        break

                if not primary_slot:
                    for i in range(16):
                        candidate = f'/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom{i}/'
                        if candidate not in current_paths:
                            primary_slot = candidate
                            current_paths.append(candidate)
                            break

                if primary_slot:
                    subprocess.run(['gsettings', 'set', f'{CUSTOM_SCHEMA}:{primary_slot}', 'name', 'Echo Search'])
                    subprocess.run(['gsettings', 'set', f'{CUSTOM_SCHEMA}:{primary_slot}', 'command', 'echo-search'])
                    subprocess.run(['gsettings', 'set', f'{CUSTOM_SCHEMA}:{primary_slot}', 'binding', hotkey_str])

                # RU companion slot for layout independence
                ru_slot = None
                for path in current_paths:
                    n = subprocess.run(['gsettings', 'get', f'{CUSTOM_SCHEMA}:{path}', 'name'], capture_output=True, text=True)
                    if n.stdout.strip().strip("'") == 'Echo Search (RU)':
                        ru_slot = path
                        break

                if ru_binding:
                    if not ru_slot:
                        for i in range(16):
                            candidate = f'/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom{i}/'
                            if candidate not in current_paths:
                                ru_slot = candidate
                                current_paths.append(candidate)
                                break
                    if ru_slot:
                        subprocess.run(['gsettings', 'set', f'{CUSTOM_SCHEMA}:{ru_slot}', 'name', 'Echo Search (RU)'])
                        subprocess.run(['gsettings', 'set', f'{CUSTOM_SCHEMA}:{ru_slot}', 'command', 'echo-search'])
                        subprocess.run(['gsettings', 'set', f'{CUSTOM_SCHEMA}:{ru_slot}', 'binding', ru_binding])
                else:
                    if ru_slot and ru_slot in current_paths:
                        subprocess.run(['gsettings', 'reset-recursively', f'{CUSTOM_SCHEMA}:{ru_slot}'])
                        current_paths.remove(ru_slot)

                subprocess.run(['gsettings', 'set', MEDIA_KEYS, 'custom-keybindings', str(current_paths)])
        except Exception as e:
            logger.warning(f'Error syncing GNOME hotkey: {e}')

        # 2. Cinnamon (Linux Mint) - Supports multiple bindings per slot natively
        try:
            if "<super>space" in hotkey_str.lower():
                # Clear switch-input-source so Super+Space is not intercepted, preserving XKB Alt+Shift
                subprocess.run(['gsettings', 'set', 'org.cinnamon.desktop.keybindings.wm', 'switch-input-source', "['']"], capture_output=True)
                subprocess.run(['gsettings', 'set', 'org.cinnamon.desktop.keybindings.wm', 'switch-input-source-backward', "['']"], capture_output=True)
                subprocess.run(['gsettings', 'set', 'org.cinnamon.desktop.keybindings.wm', 'switch-to-workspace-left', "['']"], capture_output=True)
                subprocess.run(['gsettings', 'set', 'org.cinnamon.desktop.keybindings.wm', 'switch-to-workspace-down', "['']"], capture_output=True)
            CINNAMON_MAIN = 'org.cinnamon.desktop.keybindings'
            CINNAMON_CUSTOM = 'org.cinnamon.desktop.keybindings.custom-keybinding'
            res = subprocess.run(['gsettings', 'get', CINNAMON_MAIN, 'custom-list'], capture_output=True, text=True)
            if res.returncode == 0:
                raw = res.stdout.strip().replace('@as', '').strip()
                slots = ast.literal_eval(raw) if '[' in raw else []
                found_slot = None
                for slot in slots:
                    path = f'/org/cinnamon/desktop/keybindings/custom-keybindings/{slot}/'
                    n = subprocess.run(['gsettings', 'get', f'{CINNAMON_CUSTOM}:{path}', 'name'], capture_output=True, text=True)
                    if 'Echo' in n.stdout:
                        found_slot = slot
                        break
                if not found_slot:
                    for i in range(16):
                        candidate = f'custom{i}'
                        if candidate not in slots:
                            found_slot = candidate
                            slots.append(candidate)
                            break

                if found_slot:
                    path = f'/org/cinnamon/desktop/keybindings/custom-keybindings/{found_slot}/'
                    cinnamon_bindings = [hotkey_str]
                    if ru_binding:
                        cinnamon_bindings.append(ru_binding)
                    subprocess.run(['gsettings', 'set', f'{CINNAMON_CUSTOM}:{path}', 'name', 'Echo Search'])
                    subprocess.run(['gsettings', 'set', f'{CINNAMON_CUSTOM}:{path}', 'command', 'echo-search'])
                    subprocess.run(['gsettings', 'set', f'{CINNAMON_CUSTOM}:{path}', 'binding', str(cinnamon_bindings)])
                    # Pulse custom-list so Cinnamon daemon reloads hotkeys immediately
                    subprocess.run(['gsettings', 'set', CINNAMON_MAIN, 'custom-list', "['__dummy__']"], capture_output=True)
                    subprocess.run(['gsettings', 'set', CINNAMON_MAIN, 'custom-list', str(slots)], capture_output=True)
        except Exception as e:
            logger.warning(f'Error syncing Cinnamon hotkey: {e}')

        # 3. XFCE
        try:
            subprocess.run(['xfconf-query', '-c', 'xfce4-keyboard-shortcuts', '-p', f'/commands/custom/{hotkey_str}', '-n', '-t', 'string', '-s', 'echo-search'], capture_output=True)
            if ru_binding:
                subprocess.run(['xfconf-query', '-c', 'xfce4-keyboard-shortcuts', '-p', f'/commands/custom/{ru_binding}', '-n', '-t', 'string', '-s', 'echo-search'], capture_output=True)
        except Exception as e:
            logger.debug(f'XFCE hotkey sync error: {e}')

        # 4. KDE Plasma
        try:
            kde_tool = 'kwriteconfig6' if subprocess.run(['which', 'kwriteconfig6'], capture_output=True).returncode == 0 else 'kwriteconfig5'
            kde_hotkey = hotkey_str.replace('<Super>', 'Meta+').replace('<Ctrl>', 'Ctrl+').replace('<Alt>', 'Alt+').replace('<Shift>', 'Shift+')
            subprocess.run([kde_tool, '--file', 'kglobalshortcutsrc', '--group', 'com.echo.search.desktop', '--key', '_launch', f'{kde_hotkey},none,Echo'], capture_output=True)
        except Exception as e:
            logger.debug(f'KDE hotkey sync error: {e}')

    def apply_icon_theme(self, theme_name: str | None = None) -> bool:
        """Apply the selected application icon theme (dark, light, aura)."""
        theme = (theme_name or self.get("icon_theme", "dark")).lower()
        if theme not in ("dark", "light", "aura"):
            theme = "dark"

        candidate_dirs = [
            Path(__file__).parent / "assets" / "icons" / "themes" / theme,
            Path("/usr/lib/echo-search/assets/icons/themes") / theme,
            Path("/usr/share/echo-search/assets/icons/themes") / theme,
            Path(os.path.expanduser("~/.local/share/icons/echo-search/themes")) / theme,
            Path(os.path.expanduser("~/.local/share/echo-search/assets/icons/themes")) / theme,
        ]
        theme_dir = None
        for d in candidate_dirs:
            if d.exists():
                theme_dir = d
                break
        if not theme_dir:
            logger.debug("Icon theme directory for '%s' not found", theme)
            return False

        user_icons = Path(os.path.expanduser("~/.local/share/icons/hicolor"))
        sizes = [48, 64, 128, 256, 512]
        try:
            for s in sizes:
                src_png = theme_dir / f"{s}x{s}" / "apps" / "com.echo.search.png"
                if src_png.exists():
                    dst_png = user_icons / f"{s}x{s}" / "apps" / "com.echo.search.png"
                    dst_png.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_png, dst_png)

            scalable_dir = user_icons / "scalable" / "apps"
            scalable_dir.mkdir(parents=True, exist_ok=True)
            src_512 = theme_dir / "512x512" / "apps" / "com.echo.search.png"
            if src_512.exists():
                import base64
                with open(src_512, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("ascii")
                svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <image width="512" height="512" href="data:image/png;base64,{b64}"/>
</svg>
"""
                (scalable_dir / "com.echo.search.svg").write_text(svg_content, encoding="utf-8")

            if shutil.which("gtk-update-icon-cache"):
                subprocess.run(
                    ["gtk-update-icon-cache", "-qtf", str(user_icons)],
                    capture_output=True, timeout=2
                )
            logger.info("Applied icon theme '%s'", theme)
            return True
        except Exception as e:
            logger.error("Failed to apply icon theme '%s': %s", theme, e)
            return False
