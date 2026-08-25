import os
import json
from pathlib import Path
from i18n import i18n

def _detect_system_theme() -> str:
    """Detects whether user's system desktop environment prefers dark or light theme."""
    # 1. Check GNOME / Libadwaita / Freedesktop color-scheme
    try:
        import subprocess
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
    except Exception:
        pass

    # 2. Check GTK theme name
    try:
        import subprocess
        res = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
            capture_output=True, text=True, timeout=1
        )
        if res.returncode == 0:
            val = res.stdout.strip().strip("'").lower()
            if "dark" in val:
                return "dark"
    except Exception:
        pass

    # 3. Check KDE Plasma configuration
    try:
        kdeglobals = Path(os.path.expanduser("~/.config/kdeglobals"))
        if kdeglobals.exists():
            with open(kdeglobals, "r", encoding="utf-8") as f:
                content = f.read().lower()
                if "colorcheme=breezedark" in content or "dark" in content:
                    return "dark"
    except Exception:
        pass

    return "dark"

class ConfigManager:
    def __init__(self):
        self.config_dir = Path(os.path.expanduser("~/.config/echo-search"))
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
            "launch_at_login": False,
            "launch_shortcut": "<Super>Space",
            
            "applications": True,
            "files": True,
            "clipboard": True,
            "emoji": True,
            "calculator": True,
            "commands": True,
            "settings": True,
            
            "recent_when_empty": True,
            "search_history": True
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
                    
                    # Backwards compatibility with Tahoe Settings
                    if self.config.get("theme") == "silver":
                        self.config["theme"] = "dark_glass"
                    
                    if "enabled_modes" in user_config:
                        modes = user_config["enabled_modes"]
                        self.config["applications"] = "Apps" in modes
                        self.config["files"] = "Files" in modes
                        self.config["clipboard"] = "Clipboard" in modes
                        self.config["emoji"] = "Emoji" in modes
            except Exception as e:
                print(f"Error loading config: {e}")
        else:
            self.save()
            
        i18n.set_language(self.config.get("language", "auto"))
        self._sync_autostart(self.get("launch_at_login"))

    def save(self):
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            # Ensure enabled_modes is explicitly written for Tahoe Settings GUI
            self.config["enabled_modes"] = self.get("enabled_modes")
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

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
                
        engine.providers = active

    def set(self, key, value):
        self.config[key] = value
        self.save()
        if key == "language":
            i18n.set_language(value)
        elif key in ("launch_shortcut", "hotkey"):
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
                print(f"Error enabling autostart: {e}")
        else:
            if desktop_file.exists():
                try:
                    desktop_file.unlink()
                except Exception as e:
                    print(f"Error disabling autostart: {e}")

    def _sync_desktop_hotkey(self, hotkey_str):
        import subprocess, re, ast

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
                        subprocess.run(['gsettings', f'set', f'{CUSTOM_SCHEMA}:{ru_slot}', 'binding', ru_binding])
                else:
                    if ru_slot and ru_slot in current_paths:
                        subprocess.run(['gsettings', 'reset-recursively', f'{CUSTOM_SCHEMA}:{ru_slot}'])
                        current_paths.remove(ru_slot)

                subprocess.run(['gsettings', 'set', MEDIA_KEYS, 'custom-keybindings', str(current_paths)])
        except Exception as e:
            print(f'Error syncing GNOME hotkey: {e}')

        # 2. Cinnamon (Linux Mint) - Supports multiple bindings per slot natively
        try:
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
                    subprocess.run(['gsettings', 'set', CINNAMON_MAIN, 'custom-list', str(slots)])
        except Exception as e:
            print(f'Error syncing Cinnamon hotkey: {e}')

        # 3. XFCE
        try:
            subprocess.run(['xfconf-query', '-c', 'xfce4-keyboard-shortcuts', '-p', f'/commands/custom/{hotkey_str}', '-n', '-t', 'string', '-s', 'echo-search'], capture_output=True)
            if ru_binding:
                subprocess.run(['xfconf-query', '-c', 'xfce4-keyboard-shortcuts', '-p', f'/commands/custom/{ru_binding}', '-n', '-t', 'string', '-s', 'echo-search'], capture_output=True)
        except Exception:
            pass

        # 4. KDE Plasma
        try:
            kde_tool = 'kwriteconfig6' if subprocess.run(['which', 'kwriteconfig6'], capture_output=True).returncode == 0 else 'kwriteconfig5'
            kde_hotkey = hotkey_str.replace('<Super>', 'Meta+').replace('<Ctrl>', 'Ctrl+').replace('<Alt>', 'Alt+').replace('<Shift>', 'Shift+')
            subprocess.run([kde_tool, '--file', 'kglobalshortcutsrc', '--group', 'com.echo.search.desktop', '--key', '_launch', f'{kde_hotkey},none,Echo'], capture_output=True)
        except Exception:
            pass
