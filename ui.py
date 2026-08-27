import sys
import os
import gi

try:
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk, GObject, Pango, Gio, GLib
except ValueError as e:
    print(f"[FATAL] GTK version error: {e}", file=sys.stderr)
    sys.exit(1)

from search_engine import SearchEngine
from providers import SearchResult
from modes import ModeManager
from i18n import t, i18n

UNFOLD_TRANSITION_MAP = {
    "slide_down": Gtk.RevealerTransitionType.SLIDE_DOWN,
    "swing_down": Gtk.RevealerTransitionType.SWING_DOWN,
    "none": Gtk.RevealerTransitionType.NONE
}


class EchoUI(Gtk.Window):
    def __init__(self, application=None, config_manager=None):
        super().__init__(application=application)
        self.config_manager = config_manager
        self.set_title("Echo")
        
        self.engine = SearchEngine(config_manager=self.config_manager)
        if self.config_manager:
            self.config_manager.apply_to_engine(self.engine)
            
        self.mode_manager = None
        
        self._setup_ui()
        self._setup_css()
        self._setup_shortcuts()
        self.connect("realize", self._on_realize)
        self.connect("unmap", self._on_unmap)

        # Initialize with default search mode
        if self.mode_manager:
            self.mode_manager.set_mode("Search")
            self.update_revealer_state()
            self.mode_manager.on_search_changed("")

    def _on_unmap(self, widget):
        """Reclaims preview resources and triggers garbage collection when window is hidden."""
        try:
            import gc
            if self.mode_manager and hasattr(self.mode_manager, "modes"):
                search_mode = self.mode_manager.modes.get("Search")
                if search_mode and hasattr(search_mode, "clear_preview_and_resources"):
                    search_mode.clear_preview_and_resources()
            gc.collect()
        except Exception:
            pass

    def _on_realize(self, widget):
        self._apply_compositor_blur()

    def _apply_compositor_blur(self):
        """Enables native hardware compositor blur (KWin / X11 / Picom) without shaders."""
        try:
            surface = self.get_surface()
            if surface:
                import gi
                gi.require_version('GdkX11', '4.0')
                from gi.repository import GdkX11
                if isinstance(surface, GdkX11.X11Surface):
                    xid = surface.get_xid()
                    import subprocess
                    subprocess.Popen(
                        ["xprop", "-id", str(xid), "-f", "_KDE_NET_WM_BLUR_BEHIND_REGION", "32c", "-set", "_KDE_NET_WM_BLUR_BEHIND_REGION", "0"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
        except Exception:
            pass

    def _setup_css(self):
        provider = Gtk.CssProvider()
        css_paths = [
            os.path.expanduser("~/.local/share/echo-search/style.css"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css'),
            "/usr/share/echo-search/style.css",
            "/usr/lib/echo-search/style.css",
            "/usr/local/share/echo-search/style.css"
        ]
        
        for path in css_paths:
            if os.path.exists(path):
                try:
                    provider.load_from_path(path)
                    Gtk.StyleContext.add_provider_for_display(
                        Gdk.Display.get_default(),
                        provider,
                        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                    )
                    break
                except Exception as e:
                    print(f"Error loading CSS from {path}: {e}")
            
        if self.config_manager:
            theme = self.config_manager.get("theme", "dark_glass")
            if theme == "silver":
                theme = "dark_glass"
                
            is_light = theme in ("light", "light_glass")
            is_glass = theme in ("dark_glass", "light_glass")
            
            try:
                import gi
                gi.require_version("Adw", "1")
                from gi.repository import Adw
                sm = Adw.StyleManager.get_default()
                if is_light:
                    sm.set_color_scheme(Adw.ColorScheme.PREFER_LIGHT)
                else:
                    sm.set_color_scheme(Adw.ColorScheme.PREFER_DARK)
            except Exception:
                pass
                
            transparency = self.config_manager.get("transparency", 0.60 if is_glass else 0.15)
            alpha = max(0.0, min(1.0, round(1.0 - float(transparency), 2)))
            blur = self.config_manager.get("blur", True)
            
            backdrop = "backdrop-filter: blur(40px);" if blur else "backdrop-filter: none;"
            
            if is_light:
                if theme == "light_glass":
                    bg_color = f"rgba(246, 246, 252, {alpha})"
                    window_border = "1px solid rgba(255, 255, 255, 0.90)"
                    window_shadow = "inset 0 1px 0 0 rgba(255, 255, 255, 0.95), 0 28px 64px -12px rgba(0, 0, 0, 0.18), 0 12px 24px -6px rgba(0, 0, 0, 0.10)"
                    card_bg = "rgba(255, 255, 255, 0.65)"
                    card_border = "1px solid rgba(255, 255, 255, 0.90)"
                    search_bg = "rgba(255, 255, 255, 0.75)"
                    search_border = "1px solid rgba(255, 255, 255, 0.95)"
                    mode_btn_bg = "rgba(255, 255, 255, 0.68)"
                    mode_btn_border = "1px solid rgba(255, 255, 255, 0.90)"
                    mode_btn_active = "rgba(255, 255, 255, 0.95)"
                    card_shadow = "0 4px 20px rgba(0, 0, 0, 0.05)"
                    meta_card_bg = "rgba(255, 255, 255, 0.55)"
                    emoji_badge_bg = "rgba(255, 255, 255, 0.75)"
                else:
                    bg_color = f"rgba(240, 240, 245, {alpha})"
                    window_border = "1px solid rgba(0, 0, 0, 0.08)"
                    window_shadow = "0 28px 64px -12px rgba(0, 0, 0, 0.15), 0 12px 24px -6px rgba(0, 0, 0, 0.08)"
                    card_bg = "#ffffff"
                    card_border = "1px solid rgba(0, 0, 0, 0.06)"
                    search_bg = "#ffffff"
                    search_border = "1px solid rgba(0, 0, 0, 0.06)"
                    mode_btn_bg = "#ffffff"
                    mode_btn_border = "1px solid rgba(0, 0, 0, 0.06)"
                    mode_btn_active = "#ffffff"
                    card_shadow = "0 4px 14px rgba(0, 0, 0, 0.05)"
                    meta_card_bg = "#f9f9fb"
                    emoji_badge_bg = "rgba(0, 0, 0, 0.04)"

                theme_css = f"""
                .capsule-window-ui {{ color: #1c1c1e; }}
                .capsule-window-ui .search-icon {{ color: #8e8e93; }}
                
                .capsule-window-ui .search-wrapper {{
                    background-color: {search_bg};
                    border: {search_border};
                    border-radius: 16px;
                    padding: 4px 12px;
                    box-shadow: {card_shadow};
                }}
                
                .capsule-window-ui #search-entry,
                .capsule-window-ui #search-entry text,
                .capsule-window-ui .search-wrapper entry,
                .capsule-window-ui .search-wrapper text {{ 
                    background: transparent;
                    background-color: transparent;
                    color: #1c1c1e; 
                    caret-color: #007aff; 
                    border: none;
                    box-shadow: none;
                    outline: none;
                }}
                .capsule-window-ui #search-entry:focus,
                .capsule-window-ui #search-entry text:focus,
                .capsule-window-ui .search-wrapper entry:focus {{ 
                    border: none;
                    box-shadow: none; 
                    outline: none;
                    background: transparent;
                    background-color: transparent;
                }}
                
                .capsule-window-ui #search-entry placeholder,
                .capsule-window-ui #search-entry text > placeholder,
                .capsule-window-ui .search-wrapper entry placeholder,
                .capsule-window-ui .search-wrapper text > placeholder,
                .capsule-window-ui entry placeholder {{
                    color: rgba(60, 60, 67, 0.6);
                    opacity: 1.0;
                }}
                
                .capsule-window-ui .empty-state-box {{
                    background-color: {card_bg};
                    border: {card_border};
                    border-radius: 16px;
                    margin: 0 8px 16px 16px;
                    padding: 32px 20px;
                    box-shadow: {card_shadow};
                }}
                .capsule-window-ui .empty-state-icon {{
                    color: #8e8e93;
                    opacity: 0.7;
                    margin-bottom: 8px;
                }}
                .capsule-window-ui label.empty-state-title {{
                    color: #1c1c1e;
                    font-size: 16px;
                    font-weight: 600;
                    margin-bottom: 4px;
                }}
                .capsule-window-ui label.empty-state-desc {{
                    color: #8e8e93;
                    font-size: 13px;
                }}
                
                .capsule-window-ui label.result-title {{ color: #1c1c1e; }}
                .capsule-window-ui label.result-desc {{ color: #8e8e93; }}
                
                /* Explicit dark icons for light themes */
                .capsule-window-ui image,
                .capsule-window-ui .result-icon,
                .capsule-window-ui image.result-icon,
                .capsule-window-ui .preview-hero-icon,
                .capsule-window-ui image.preview-hero-icon,
                .capsule-window-ui .preview-icon,
                .capsule-window-ui image.preview-icon,
                .capsule-window-ui .empty-state-icon,
                .capsule-window-ui image.empty-state-icon,
                .capsule-window-ui .result-row image,
                .capsule-window-ui row image {{
                    color: #1c1c1e;
                    -gtk-icon-palette: default;
                }}
                
                .capsule-window-ui .result-emoji-badge {{
                    background: {emoji_badge_bg};
                    border: 1px solid rgba(0, 0, 0, 0.06);
                }}
                
                .capsule-window-ui #results-list {{
                    background-color: {card_bg};
                    border: {card_border};
                    border-radius: 16px;
                    margin: 0 8px 16px 16px;
                    padding: 8px;
                    box-shadow: {card_shadow};
                }}
                
                .capsule-window-ui row, .capsule-window-ui .result-row {{ background-color: transparent; }}
                .capsule-window-ui row:hover, .capsule-window-ui .result-row:hover {{ 
                    background-color: rgba(0, 0, 0, 0.04); 
                    border-radius: 8px; 
                }}
                
                .capsule-window-ui row:selected, .capsule-window-ui .result-row:selected {{
                    background-color: rgba(0, 0, 0, 0.06);
                    color: #1c1c1e;
                    box-shadow: none;
                    border-radius: 8px;
                }}
                
                .capsule-window-ui .chip,
                .capsule-window-ui .apps-filter-pill {{
                    color: #8e8e93;
                    border: 1px solid rgba(0, 0, 0, 0.06);
                    background-color: rgba(255, 255, 255, 0.6);
                }}
                .capsule-window-ui .chip:hover,
                .capsule-window-ui .apps-filter-pill:hover {{ 
                    background-color: #ffffff; 
                    color: #1c1c1e;
                }}
                .capsule-window-ui .chip.active,
                .capsule-window-ui .apps-filter-pill.active {{
                    background-color: #ffffff;
                    color: #1c1c1e;
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
                }}
                
                .capsule-window-ui .main-separator {{ background-color: transparent; }}
                
                .capsule-window-ui label.preview-main-title {{ color: #1c1c1e; text-shadow: none; }}
                .capsule-window-ui label.preview-main-subtitle {{ color: #8e8e93; text-shadow: none; }}
                
                .capsule-window-ui label.launchpad-title,
                .capsule-window-ui label.finder-title,
                .capsule-window-ui label.emoji-title,
                .capsule-window-ui label.files-section-title {{ 
                    color: #1c1c1e; 
                    text-shadow: none; 
                }}
                
                .capsule-window-ui .launchpad-card.selected label.launchpad-title,
                .capsule-window-ui .launchpad-card:selected label.launchpad-title,
                .capsule-window-ui .finder-card.selected label.finder-title,
                .capsule-window-ui .finder-card:selected label.finder-title,
                .capsule-window-ui .emoji-card.selected label.emoji-title,
                .capsule-window-ui .emoji-card:selected label.emoji-title {{
                    color: #1c1c1e;
                }}
                
                .capsule-window-ui .preview-panel {{
                    background-color: {card_bg};
                    border: {card_border};
                    border-radius: 16px;
                    margin: 0 16px 16px 8px;
                    border-left: none;
                    box-shadow: {card_shadow};
                }}
                
                .capsule-window-ui .preview-meta-card {{
                    background: {meta_card_bg};
                    border: 1px solid rgba(0, 0, 0, 0.04);
                }}
                .capsule-window-ui label.preview-meta-key {{ color: rgba(0, 0, 0, 0.5); font-weight: 600; }}
                .capsule-window-ui label.preview-meta-val {{ color: #1c1c1e; font-weight: 500; }}
                
                .capsule-window-ui .preview-btn {{
                    background: #ffffff;
                    color: #1c1c1e;
                    border: 1px solid rgba(0, 0, 0, 0.08);
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
                }}
                .capsule-window-ui .preview-btn:hover {{
                    background: #f9f9fb;
                    color: #000000;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
                }}
                
                .capsule-window-ui .mode-button {{
                    background: {mode_btn_bg};
                    border: {mode_btn_border};
                    color: #636366;
                    box-shadow: {card_shadow};
                }}
                .capsule-window-ui .mode-button:hover {{
                    background: {mode_btn_active};
                    color: #1c1c1e;
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
                }}
                .capsule-window-ui .mode-button.active {{
                    background: {mode_btn_active};
                    color: #1c1c1e;
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
                }}
                
                /* Настройки в светлой теме */
                .capsule-window-ui .settings-group-title {{
                    color: rgba(60, 60, 67, 0.65);
                }}
                .capsule-window-ui .settings-card {{
                    background: {card_bg};
                    border: {card_border};
                    box-shadow: {card_shadow};
                }}
                .capsule-window-ui .settings-row {{
                    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
                }}
                .capsule-window-ui .settings-row:hover {{
                    background: rgba(0, 0, 0, 0.02);
                }}
                .capsule-window-ui .settings-row-title {{
                    color: #1c1c1e;
                }}
                .capsule-window-ui .settings-row-subtitle {{
                    color: rgba(60, 60, 67, 0.7);
                }}
                .capsule-window-ui .settings-value-label {{
                    color: #1c1c1e;
                }}
                .capsule-window-ui .shortcut-button {{
                    background: #f2f2f7;
                    color: #1c1c1e;
                    border: 1px solid rgba(0, 0, 0, 0.1);
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
                }}
                .capsule-window-ui .shortcut-button:hover {{
                    background: #e5e5ea;
                    color: #000000;
                }}
                .capsule-window-ui .shortcut-button.recording {{
                    background: rgba(0, 122, 255, 0.1);
                    border-color: #007aff;
                    color: #007aff;
                }}
                .capsule-window-ui .settings-theme-selector {{
                    background: #e5e5ea;
                    border: 1px solid rgba(0, 0, 0, 0.04);
                }}
                .capsule-window-ui .theme-pill {{
                    color: #636366;
                }}
                .capsule-window-ui .theme-pill:hover {{
                    color: #000000;
                    background: rgba(0, 0, 0, 0.04);
                }}
                .capsule-window-ui .theme-pill.active {{
                    background: #ffffff;
                    color: #000000;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
                }}
                .capsule-window-ui scale.settings-slider trough {{
                    background: rgba(0, 0, 0, 0.12);
                }}
                .capsule-window-ui .settings-reset-btn {{
                    background: #ffffff;
                    border: 1px solid rgba(255, 59, 48, 0.3);
                    color: #ff3b30;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
                }}
                .capsule-window-ui .settings-reset-btn:hover {{
                    background: rgba(255, 59, 48, 0.1);
                    color: #d70015;
                }}
                """
            else:
                if theme in ("dark_glass", "silver"):
                    bg_color = f"rgba(26, 27, 34, {alpha})"
                    window_border = "1px solid rgba(255, 255, 255, 0.16)"
                    window_shadow = "inset 0 1px 0 0 rgba(255, 255, 255, 0.25), 0 28px 64px -12px rgba(0, 0, 0, 0.65), 0 12px 24px -6px rgba(0, 0, 0, 0.45)"
                    card_bg = "rgba(255, 255, 255, 0.07)"
                    card_border = "1px solid rgba(255, 255, 255, 0.12)"
                    search_bg = "rgba(255, 255, 255, 0.10)"
                    search_border = "1px solid rgba(255, 255, 255, 0.16)"
                    mode_btn_bg = "rgba(255, 255, 255, 0.08)"
                    mode_btn_border = "1px solid rgba(255, 255, 255, 0.12)"
                    mode_btn_active = "rgba(255, 255, 255, 0.24)"
                    card_shadow = "0 4px 20px rgba(0, 0, 0, 0.30)"
                    meta_card_bg = "rgba(255, 255, 255, 0.08)"
                    emoji_badge_bg = "rgba(255, 255, 255, 0.10)"
                else:
                    bg_color = f"rgba(28, 28, 30, {alpha})"
                    window_border = "1px solid rgba(255, 255, 255, 0.08)"
                    window_shadow = "0 28px 64px -12px rgba(0, 0, 0, 0.60), 0 12px 24px -6px rgba(0, 0, 0, 0.40)"
                    card_bg = "#2c2c2e"
                    card_border = "1px solid rgba(255, 255, 255, 0.08)"
                    search_bg = "#2c2c2e"
                    search_border = "1px solid rgba(255, 255, 255, 0.10)"
                    mode_btn_bg = "#2c2c2e"
                    mode_btn_border = "1px solid rgba(255, 255, 255, 0.10)"
                    mode_btn_active = "#3a3a3c"
                    card_shadow = "0 4px 14px rgba(0, 0, 0, 0.25)"
                    meta_card_bg = "#3a3a3c"
                    emoji_badge_bg = "rgba(255, 255, 255, 0.08)"

                theme_css = f"""
                .capsule-window-ui {{ color: #f5f5f7; }}
                .capsule-window-ui .search-icon {{ color: rgba(255, 255, 255, 0.7); }}
                
                .capsule-window-ui .search-wrapper {{
                    background-color: {search_bg};
                    border: {search_border};
                    border-radius: 16px;
                    padding: 4px 12px;
                    box-shadow: {card_shadow};
                }}
                
                .capsule-window-ui #search-entry,
                .capsule-window-ui #search-entry text,
                .capsule-window-ui .search-wrapper entry,
                .capsule-window-ui .search-wrapper text {{ 
                    background: transparent;
                    background-color: transparent;
                    color: #ffffff; 
                    caret-color: #007aff; 
                    border: none;
                    box-shadow: none;
                    outline: none;
                }}
                .capsule-window-ui #search-entry:focus,
                .capsule-window-ui #search-entry text:focus,
                .capsule-window-ui .search-wrapper entry:focus {{ 
                    border: none;
                    box-shadow: none; 
                    outline: none;
                    background: transparent;
                    background-color: transparent;
                }}
                
                .capsule-window-ui label.result-title {{ color: #ffffff; }}
                .capsule-window-ui label.result-desc {{ color: rgba(255, 255, 255, 0.6); }}
                
                /* Explicit white icons for dark themes */
                .capsule-window-ui image,
                .capsule-window-ui .result-icon,
                .capsule-window-ui image.result-icon,
                .capsule-window-ui .preview-hero-icon,
                .capsule-window-ui image.preview-hero-icon,
                .capsule-window-ui .preview-icon,
                .capsule-window-ui image.preview-icon,
                .capsule-window-ui .empty-state-icon,
                .capsule-window-ui image.empty-state-icon,
                .capsule-window-ui .result-row image,
                .capsule-window-ui row image {{
                    color: #ffffff;
                    -gtk-icon-palette: default;
                }}
                
                .capsule-window-ui .result-emoji-badge {{
                    background: {emoji_badge_bg};
                    border: 1px solid rgba(255, 255, 255, 0.12);
                }}
                
                .capsule-window-ui .result-row {{
                    background: transparent;
                    background-color: transparent;
                    border: none;
                    box-shadow: none;
                }}
                .capsule-window-ui row {{
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 12px;
                    margin: 2px 0;
                    padding: 0;
                }}
                .capsule-window-ui row:hover {{ 
                    background-color: rgba(255, 255, 255, 0.09);
                    border: 1px solid rgba(255, 255, 255, 0.40);
                    box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.55),
                                0 0 14px rgba(255, 255, 255, 0.20),
                                0 2px 8px rgba(0, 0, 0, 0.25);
                }}
                .capsule-window-ui row:selected,
                .capsule-window-ui row:selected:hover {{
                    background-color: rgba(255, 255, 255, 0.18);
                    color: #ffffff;
                    border: 1px solid rgba(255, 255, 255, 0.70);
                    box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.80),
                                0 0 20px rgba(255, 255, 255, 0.30),
                                0 4px 16px rgba(0, 0, 0, 0.40);
                }}
                
                .capsule-window-ui .mode-button {{
                    background: {mode_btn_bg};
                    color: rgba(255, 255, 255, 0.75);
                    border: {mode_btn_border};
                    box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.35),
                                0 4px 14px rgba(0, 0, 0, 0.30),
                                0 1px 3px rgba(0, 0, 0, 0.20);
                }}
                .capsule-window-ui .mode-button:hover {{
                    background: {mode_btn_active};
                    color: #ffffff;
                    border: 1px solid rgba(255, 255, 255, 0.48);
                    box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.60),
                                0 6px 18px rgba(0, 0, 0, 0.35),
                                0 0 14px rgba(255, 255, 255, 0.20);
                }}
                .capsule-window-ui .mode-button.active {{
                    background: {mode_btn_active};
                    color: #ffffff;
                    border: 1px solid rgba(255, 255, 255, 0.70);
                    box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.75),
                                0 6px 20px rgba(0, 0, 0, 0.40),
                                0 0 18px rgba(255, 255, 255, 0.30);
                }}
                
                /* Настройки в темной теме */
                .capsule-window-ui .settings-group-title {{
                    color: rgba(255, 255, 255, 0.45);
                }}
                .capsule-window-ui .settings-card {{
                    background: {card_bg};
                    border: {card_border};
                    box-shadow: {card_shadow};
                }}
                .capsule-window-ui .settings-row {{
                    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
                }}
                .capsule-window-ui .settings-row:hover {{
                    background: rgba(255, 255, 255, 0.03);
                }}
                .capsule-window-ui .settings-row-title {{
                    color: rgba(255, 255, 255, 0.9);
                }}
                .capsule-window-ui .settings-row-subtitle {{
                    color: rgba(255, 255, 255, 0.45);
                }}
                .capsule-window-ui .settings-value-label {{
                    color: rgba(255, 255, 255, 0.85);
                }}
                .capsule-window-ui .shortcut-button {{
                    background: rgba(255, 255, 255, 0.08);
                    color: rgba(255, 255, 255, 0.9);
                    border: 1px solid rgba(255, 255, 255, 0.12);
                }}
                .capsule-window-ui .shortcut-button:hover {{
                    background: rgba(255, 255, 255, 0.14);
                    color: #ffffff;
                }}
                .capsule-window-ui .shortcut-button.recording {{
                    background: rgba(0, 122, 255, 0.2);
                    border-color: #007aff;
                    color: #007aff;
                }}
                .capsule-window-ui .settings-theme-selector {{
                    background: rgba(0, 0, 0, 0.3);
                    border: 1px solid rgba(255, 255, 255, 0.06);
                }}
                .capsule-window-ui .theme-pill {{
                    color: rgba(255, 255, 255, 0.6);
                }}
                .capsule-window-ui .theme-pill:hover {{
                    color: rgba(255, 255, 255, 0.9);
                    background: rgba(255, 255, 255, 0.05);
                }}
                .capsule-window-ui .theme-pill.active {{
                    background: rgba(255, 255, 255, 0.18);
                    color: #ffffff;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
                }}
                .capsule-window-ui scale.settings-slider trough {{
                    background: rgba(255, 255, 255, 0.15);
                }}
                .capsule-window-ui .settings-reset-btn {{
                    background: rgba(255, 255, 255, 0.06);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    color: rgba(255, 255, 255, 0.65);
                }}
                .capsule-window-ui .settings-reset-btn:hover {{
                    background: rgba(255, 59, 48, 0.15);
                    border-color: rgba(255, 59, 48, 0.3);
                    color: #ff453a;
                }}
                """
                
            dynamic_css = f"""
            .capsule-window-ui {{
                background-color: {bg_color};
                {backdrop}
            }}
            {theme_css}
            """
            
            if hasattr(self, '_dynamic_css_provider') and self._dynamic_css_provider:
                Gtk.StyleContext.remove_provider_for_display(
                    Gdk.Display.get_default(),
                    self._dynamic_css_provider
                )
                
            self._dynamic_css_provider = Gtk.CssProvider()
            self._dynamic_css_provider.load_from_data(dynamic_css.encode('utf-8'))
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                self._dynamic_css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_USER
            )

    def _setup_ui(self):
        # Самый внешний контейнер окна
        self.root_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.root_box.add_css_class("root-box")
        self.root_box.set_valign(Gtk.Align.START)
        # Обертка для перемещения окна на Wayland
        self.window_handle = Gtk.WindowHandle()
        self.window_handle.set_child(self.root_box)
        self.set_child(self.window_handle)

        # Наружный контейнер для градиентной окантовки основной капсулы
        self.outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.outer_box.add_css_class("outer-border-box")
        self.outer_box.set_valign(Gtk.Align.START)
        self.outer_box.set_hexpand(True)
        self.root_box.append(self.outer_box)

        # Основной контейнер-капсула (UI)
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.add_css_class("capsule-window-ui")
        self.main_box.set_valign(Gtk.Align.START) 
        self.outer_box.append(self.main_box)

        # --- ОБНОВЛЕННЫЙ HEADER ДЛЯ СВЕТЛОЙ ТЕМЫ ---
        # Общий контейнер для строки поиска и кнопок режимов
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.header_box.set_hexpand(True)
        self.header_box.set_spacing(12)
        self.header_box.set_margin_top(12)
        self.header_box.set_margin_start(16)
        self.header_box.set_margin_end(16)
        self.header_box.set_margin_bottom(8)
        self.main_box.append(self.header_box)
        
        # Контейнер только для поиска (иконка + ввод)
        self.search_wrapper = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.search_wrapper.set_hexpand(True)
        self.search_wrapper.add_css_class("search-wrapper")
        self.header_box.append(self.search_wrapper)

        # Иконка поиска
        search_icon = Gtk.Image.new_from_icon_name("system-search-symbolic")
        search_icon.set_pixel_size(24)
        search_icon.add_css_class("search-icon")
        self.search_wrapper.append(search_icon)

        # Поле ввода
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text(t("search_placeholder"))
        self.entry.set_hexpand(True)
        self.entry.set_name("search-entry")
        self.entry.connect("changed", self.on_search_changed)
        self.entry.connect("activate", self.on_search_activate)
        self.search_wrapper.append(self.entry)
        
        # Контейнер для кнопок режимов с анимацией появления (Revealer)
        self.mode_buttons_revealer = Gtk.Revealer()
        self.mode_buttons_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_LEFT)
        
        animations = self.config_manager.get("animations") if self.config_manager else True
        anim_duration = 260 if animations else 0
        self.mode_buttons_revealer.set_transition_duration(anim_duration)
        
        self.mode_buttons_revealer.set_halign(Gtk.Align.END)
        self.mode_buttons_revealer.set_valign(Gtk.Align.CENTER)
        
        self.mode_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.mode_buttons_box.set_spacing(6)
        self.mode_buttons_revealer.set_child(self.mode_buttons_box)
        
        # Кнопки режимов добавляются В HEADER (внутри основной капсулы)
        self.header_box.append(self.mode_buttons_revealer)
        
        # Кнопки режимов (Mode Buttons)
        all_modes = [
            ("Apps", "view-app-grid-symbolic"),
            ("Files", "folder-symbolic"),
            ("Clipboard", "edit-paste-symbolic"),
            ("Emoji", "emblem-favorite-symbolic"),
            ("Settings", "preferences-system-symbolic")
        ]
        
        # Проверка поддержки буфера обмена на текущем дисплее/сервере
        clipboard_supported = True
        try:
            disp = Gdk.Display.get_default()
            if not disp or not disp.get_clipboard():
                clipboard_supported = False
        except Exception:
            clipboard_supported = False

        enabled_modes_list = self.config_manager.get("enabled_modes") if self.config_manager else [m[0] for m in all_modes]
        self.mode_buttons = {}
        for name, icon_name in all_modes:
            btn = Gtk.Button()
            btn.set_valign(Gtk.Align.CENTER) # Запрещает растягивание по вертикали (чтобы были идеальные круги)
            btn.set_halign(Gtk.Align.CENTER)
            btn.add_css_class("mode-button")
            # Set fixed icon size using image
            image = Gtk.Image.new_from_icon_name(icon_name)
            image.set_pixel_size(16)
            btn.set_child(image)
            MODE_TOOLTIP_KEYS = {
                "Apps": "mode_apps",
                "Files": "mode_files",
                "Clipboard": "mode_clipboard",
                "Emoji": "mode_emoji",
                "Settings": "mode_settings"
            }
            btn.set_tooltip_text(t(MODE_TOOLTIP_KEYS.get(name, name)))
            btn.connect("clicked", self.on_mode_button_clicked, name)
            
            is_visible = (name in enabled_modes_list)
            if name == "Clipboard" and not clipboard_supported:
                is_visible = False
                
            btn.set_visible(is_visible)
            self.mode_buttons_box.append(btn)
            self.mode_buttons[name] = btn
            
        # Инициализируем ModeManager и оборачиваем в Revealer для динамической высоты окна
        self.mode_manager = ModeManager(self)
        
        # Единый контейнер для всех режимов, задающий глобальные отступы
        self.results_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.results_container.add_css_class("results-container")
        self.results_container.add_css_class("folded")
        self.results_container.append(self.mode_manager.get_widget())
        
        unfold_mode = self.config_manager.get("unfold_animation", "fade_slide_down") if self.config_manager else "fade_slide_down"
        transition_type = UNFOLD_TRANSITION_MAP.get(unfold_mode, Gtk.RevealerTransitionType.SLIDE_DOWN)
        revealer_duration = anim_duration if unfold_mode != "none" else 0
        
        self.results_revealer = Gtk.Revealer()
        self.results_revealer.set_transition_type(transition_type)
        self.results_revealer.set_transition_duration(revealer_duration)
        self.results_revealer.set_child(self.results_container)
        self.results_revealer.set_reveal_child(False)
        self.results_revealer.connect("notify::child-revealed", self._on_results_revealed_changed)
        
        self.main_box.append(self.results_revealer)

    def _on_results_revealed_changed(self, revealer, param):
        if not revealer.get_reveal_child() and not revealer.get_child_revealed():
            self.set_default_size(650, 1)

    def _setup_shortcuts(self):
        key_ctrl = Gtk.EventControllerKey.new()
        key_ctrl.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_ctrl)

    def on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            query = self.entry.get_text()
            if self.mode_manager and self.mode_manager.active_mode_name != "Search":
                self.mode_manager.set_mode("Search")
                self.entry.set_text("")
                self.update_revealer_state()
                return True
            elif query:
                self.entry.set_text("")
                self.update_revealer_state()
                return True
            else:
                self.hide()
                return True
                
        # Выход из режима по Backspace, если строка поиска пустая
        if keyval == Gdk.KEY_BackSpace:
            if self.mode_manager and self.mode_manager.active_mode_name != "Search":
                if len(self.entry.get_text()) == 0:
                    self.mode_manager.set_mode("Search")
                    self.update_revealer_state()
                    return True
                
        elif state & Gdk.ModifierType.CONTROL_MASK:
            if keyval in (Gdk.KEY_l, Gdk.KEY_L):
                self.entry.grab_focus()
                self.entry.select_region(0, -1)
                return True
            elif keyval in (Gdk.KEY_k, Gdk.KEY_K):
                self.entry.set_text("")
                return True
            
        # Delegate other keys to active mode
        if self.mode_manager:
            return self.mode_manager.on_key_pressed(keyval, state)
            
        return False

    def update_revealer_state(self):
        active = self.mode_manager.active_mode_name
        should_reveal_modes = active != "Search"
        
        query = self.entry.get_text().strip()
        has_text = len(query) > 0
        should_reveal_results = has_text or should_reveal_modes
        
        # Кнопки видны всегда, когда активен глобальный поиск
        should_show_buttons = True
        self.mode_buttons_revealer.set_reveal_child(should_show_buttons)
        
        if hasattr(self, 'results_revealer'):
            self.results_revealer.set_reveal_child(should_reveal_results)
            if should_reveal_results:
                self.results_container.remove_css_class("folded")
                if active == "Search":
                    preview_enabled = self.config_manager.get("preview_enabled") if getattr(self, "config_manager", None) else True
                    preview_width = self.config_manager.get("preview_width") if getattr(self, "config_manager", None) else 420
                    self.set_default_size(650 + (preview_width if preview_enabled else 0), 1)
                elif active in ("Apps", "Files", "Clipboard", "Emoji"):
                    self.set_default_size(1050, 1)
                elif active == "Settings":
                    self.set_default_size(820, 1)
            else:
                self.results_container.add_css_class("folded")
                if not self.results_revealer.get_child_revealed():
                    self.set_default_size(650, 1)
        
        # Обновляем подсветку кнопок
        for name, btn in self.mode_buttons.items():
            if name == active:
                btn.add_css_class("active")
            else:
                btn.remove_css_class("active")

    def on_mode_button_clicked(self, button, mode_name):
        if self.mode_manager.active_mode_name == mode_name:
            # Toggle back to search if clicking the same mode
            self.mode_manager.set_mode("Search")
        else:
            self.mode_manager.set_mode(mode_name)
            
        self.update_revealer_state()
        self.entry.grab_focus()

    def on_search_changed(self, editable):
        query = self.entry.get_text().strip()
        
        # --- DEBUG MODE ENTRY POINTS ---
        if query == "/apps" and self.mode_manager:
            self.entry.set_text("")
            self.mode_manager.set_mode("Apps")
            self.update_revealer_state()
            return
        elif query == "/files" and self.mode_manager:
            self.entry.set_text("")
            self.mode_manager.set_mode("Files")
            self.update_revealer_state()
            return
        elif query == "/clip" and self.mode_manager:
            self.entry.set_text("")
            self.mode_manager.set_mode("Clipboard")
            self.update_revealer_state()
            return
        elif query == "/emoji" and self.mode_manager:
            self.entry.set_text("")
            self.mode_manager.set_mode("Emoji")
            self.update_revealer_state()
            return
        elif query == "/settings" and self.mode_manager:
            self.entry.set_text("")
            self.mode_manager.set_mode("Settings")
            self.update_revealer_state()
            return
        # -------------------------------
        
        self.update_revealer_state()
        if self.mode_manager:
            self.mode_manager.on_search_changed(query)

    def on_search_activate(self, entry):
        # Trigger enter on active mode
        if self.mode_manager:
            self.mode_manager.on_key_pressed(Gdk.KEY_Return, 0)
    def reload_config(self):
        # Обновляем CSS
        self._setup_css()
        
        # Обновляем анимации и стиль развертывания
        animations = self.config_manager.get("animations") if self.config_manager else True
        unfold_mode = self.config_manager.get("unfold_animation", "fade_slide_down") if self.config_manager else "fade_slide_down"
        anim_duration = 260 if animations else 0
        revealer_duration = anim_duration if unfold_mode != "none" else 0
        self.mode_buttons_revealer.set_transition_duration(anim_duration)
        if hasattr(self, 'results_revealer'):
            transition_type = UNFOLD_TRANSITION_MAP.get(unfold_mode, Gtk.RevealerTransitionType.SLIDE_DOWN)
            self.results_revealer.set_transition_type(transition_type)
            self.results_revealer.set_transition_duration(revealer_duration)
            
        # Применяем фильтр источников к движку
        if self.config_manager and hasattr(self, 'engine'):
            self.config_manager.apply_to_engine(self.engine)
            if hasattr(self.engine, 'reload_providers'):
                self.engine.reload_providers()
            
        # Обновляем режимы
        enabled_modes_list = self.config_manager.get("enabled_modes") if self.config_manager else ["Apps", "Files", "Clipboard", "Emoji", "Settings"]
        for name, btn in self.mode_buttons.items():
            btn.set_visible(name in enabled_modes_list)
            
        # Если активный режим был отключен, возвращаемся в Search
        if self.mode_manager and self.mode_manager.active_mode_name not in enabled_modes_list and self.mode_manager.active_mode_name != "Search":
            self.mode_manager.set_mode("Search")
            
        self.update_revealer_state()
        
        # Обновляем превью-панель "на лету"
        if hasattr(self, 'mode_manager') and self.mode_manager:
            search_mode = self.mode_manager.modes.get("Search")
            if search_mode and hasattr(search_mode, 'preview_container'):
                preview_width = self.config_manager.get("preview_width") if self.config_manager else 420
                search_mode.preview_container.set_size_request(preview_width, -1)
                
                preview_enabled = self.config_manager.get("preview_enabled") if self.config_manager else True
                if not preview_enabled:
                    search_mode.preview_container.set_visible(False)
                    self.set_default_size(650, 1)
                    
        # Обновление подсказок и плейсхолдера при смене языка
        MODE_TOOLTIP_KEYS = {
            "Apps": "mode_apps",
            "Files": "mode_files",
            "Clipboard": "mode_clipboard",
            "Emoji": "mode_emoji",
            "Settings": "mode_settings"
        }
        for name, btn in self.mode_buttons.items():
            btn.set_tooltip_text(t(MODE_TOOLTIP_KEYS.get(name, name)))
        if hasattr(self, 'mode_manager') and self.mode_manager:
            self.mode_manager.refresh_placeholder()
