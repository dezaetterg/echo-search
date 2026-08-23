import os
import json
from pathlib import Path
from i18n import i18n

class ConfigManager:
    def __init__(self):
        self.config_dir = Path(os.path.expanduser("~/.config/echo-search"))
        self.config_file = self.config_dir / "config.json"
        
        self.defaults = {
            "theme": "light",
            "language": "auto",
            "blur": True,
            "transparency": 0.70,
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

    def get(self, key):
        if key == "enabled_modes":
            modes = []
            if self.config.get("applications", True): modes.append("Apps")
            if self.config.get("files", True): modes.append("Files")
            if self.config.get("clipboard", True): modes.append("Clipboard")
            if self.config.get("emoji", True): modes.append("Emoji")
            if self.config.get("settings", True): modes.append("Settings")
            return modes
        return self.config.get(key, self.defaults.get(key))

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
        import subprocess
        # 1. GNOME / Cinnamon / MATE
        try:
            result = subprocess.run(['gsettings', 'get', 'org.gnome.settings-daemon.plugins.media-keys', 'custom-keybindings'], capture_output=True, text=True)
            if result.returncode == 0:
                bindings = result.stdout.strip().replace('@as', '').strip()
                import ast
                paths = ast.literal_eval(bindings) if '[' in bindings else []
                for path in paths:
                    name_res = subprocess.run(['gsettings', 'get', f'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{path}', 'name'], capture_output=True, text=True)
                    if 'Echo' in name_res.stdout or 'Spotlight Glass' in name_res.stdout or 'echo-search' in name_res.stdout:
                        subprocess.run(['gsettings', 'set', f'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{path}', 'binding', hotkey_str])
                        break
        except Exception:
            pass

        # 2. XFCE
        try:
            subprocess.run(['xfconf-query', '-c', 'xfce4-keyboard-shortcuts', '-p', f'/commands/custom/{hotkey_str}', '-n', '-t', 'string', '-s', 'echo-search'], capture_output=True)
        except Exception:
            pass

        # 3. KDE Plasma
        try:
            kde_tool = 'kwriteconfig6' if subprocess.run(['which', 'kwriteconfig6'], capture_output=True).returncode == 0 else 'kwriteconfig5'
            subprocess.run([kde_tool, '--file', 'kglobalshortcutsrc', '--group', 'com.echo.search.desktop', '--key', '_launch', f'Meta+Space,none,Echo'], capture_output=True)
        except Exception:
            pass
