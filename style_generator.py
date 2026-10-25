"""Dynamic CSS and theme tokens generator for Spotlight / Echo Search."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ThemeTokens:
    theme: str
    is_light: bool
    is_glass: bool
    alpha: float
    backdrop: str
    jelly_duration: int
    bg_color: str
    card_bg: str
    card_border: str
    search_bg: str
    search_border: str
    mode_btn_bg: str
    mode_btn_border: str
    mode_btn_active: str
    card_shadow: str
    meta_card_bg: str
    emoji_badge_bg: str


def resolve_tokens(config_manager: Any = None, **kwargs: Any) -> ThemeTokens:
    """Resolve color, geometry, and animation tokens from configuration."""
    def get_cfg(key: str, default: Any) -> Any:
        if key in kwargs:
            return kwargs[key]
        if config_manager and hasattr(config_manager, "get"):
            return config_manager.get(key, default)
        return default

    raw_theme = get_cfg("theme", "dark_glass")
    theme = "dark_glass" if raw_theme == "silver" else raw_theme

    is_light = theme in ("light", "light_glass")
    is_glass = theme in ("dark_glass", "light_glass", "aura_glow", "echo_blue")

    default_transparency = 0.60 if is_glass else 0.15
    transparency = get_cfg("transparency", default_transparency)
    anim_speed = get_cfg("animation_speed", 100)
    speed_factor = max(0.2, min(3.0, float(anim_speed) / 100.0))
    jelly_duration = max(30, int(220 / speed_factor))
    alpha = max(0.0, min(1.0, round(1.0 - float(transparency), 2)))
    blur = get_cfg("blur", True)

    backdrop = "backdrop-filter: blur(40px);" if blur else "backdrop-filter: none;"

    if is_light:
        if theme == "light_glass":
            bg_color = f"rgba(246, 246, 252, {alpha})"
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
    else:
        if theme == "aura_glow":
            bg_color = f"rgba(20, 18, 28, {alpha})"
            card_bg = "rgba(255, 255, 255, 0.08)"
            card_border = "1px solid rgba(255, 255, 255, 0.14)"
            search_bg = "rgba(255, 255, 255, 0.11)"
            search_border = "1px solid rgba(160, 120, 255, 0.30)"
            mode_btn_bg = "rgba(255, 255, 255, 0.08)"
            mode_btn_border = "1px solid rgba(255, 255, 255, 0.12)"
            mode_btn_active = "rgba(150, 100, 255, 0.35)"
            card_shadow = "0 4px 20px rgba(0, 0, 0, 0.35)"
            meta_card_bg = "rgba(255, 255, 255, 0.09)"
            emoji_badge_bg = "rgba(160, 120, 255, 0.18)"
        elif theme == "echo_blue":
            bg_color = f"rgba(13, 19, 38, {alpha})"
            card_bg = "rgba(255, 255, 255, 0.06)"
            card_border = "1px solid rgba(80, 130, 220, 0.22)"
            search_bg = "rgba(20, 28, 52, 0.85)"
            search_border = "1px solid rgba(80, 150, 255, 0.30)"
            mode_btn_bg = "rgba(28, 39, 70, 0.65)"
            mode_btn_border = "1px solid rgba(80, 150, 255, 0.20)"
            mode_btn_active = "rgba(50, 120, 240, 0.45)"
            card_shadow = "0 8px 32px rgba(5, 10, 25, 0.45)"
            meta_card_bg = "rgba(28, 39, 70, 0.50)"
            emoji_badge_bg = "rgba(80, 150, 255, 0.22)"
        elif theme in ("dark_glass", "silver"):
            bg_color = f"rgba(26, 27, 34, {alpha})"
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
            card_bg = "rgba(44, 44, 46, 0.65)"
            card_border = "1px solid rgba(255, 255, 255, 0.08)"
            search_bg = "#2c2c2e"
            search_border = "1px solid rgba(255, 255, 255, 0.10)"
            mode_btn_bg = "#2c2c2e"
            mode_btn_border = "1px solid rgba(255, 255, 255, 0.10)"
            mode_btn_active = "#3a3a3c"
            card_shadow = "0 4px 14px rgba(0, 0, 0, 0.25)"
            meta_card_bg = "#3a3a3c"
            emoji_badge_bg = "rgba(255, 255, 255, 0.08)"

    return ThemeTokens(
        theme=theme,
        is_light=is_light,
        is_glass=is_glass,
        alpha=alpha,
        backdrop=backdrop,
        jelly_duration=jelly_duration,
        bg_color=bg_color,
        card_bg=card_bg,
        card_border=card_border,
        search_bg=search_bg,
        search_border=search_border,
        mode_btn_bg=mode_btn_bg,
        mode_btn_border=mode_btn_border,
        mode_btn_active=mode_btn_active,
        card_shadow=card_shadow,
        meta_card_bg=meta_card_bg,
        emoji_badge_bg=emoji_badge_bg,
    )



def _get_outer_box_style(theme: str) -> str:
    """Returns CSS rule for outer border box according to the theme."""
    if theme == "aura_glow":
        return """
                    .capsule-window-ui-root .outer-border-box,
                    .root-box .outer-border-box,
                    .outer-border-box {
                        background-image: linear-gradient(135deg, 
                            rgba(150, 100, 255, 0.95) 0%, 
                            rgba(70, 160, 255, 0.45) 30%, 
                            rgba(255, 90, 180, 0.45) 70%, 
                            rgba(100, 130, 255, 0.95) 100%);
                        border-radius: 25px;
                        box-shadow: 0 0 12px rgba(150, 100, 255, 0.40),
                                    0 4px 14px rgba(0, 0, 0, 0.35);
                    }
                    """
    elif theme == "echo_blue":
        return """
                    .capsule-window-ui-root .outer-border-box,
                    .root-box .outer-border-box,
                    .outer-border-box {
                        border-radius: 25px;
                        background-image: linear-gradient(135deg, 
                            rgba(80, 140, 255, 0.45) 0%, 
                            rgba(40, 70, 150, 0.20) 50%, 
                            rgba(90, 160, 255, 0.45) 100%);
                        box-shadow: 0 0 16px rgba(40, 80, 180, 0.35),
                                    0 8px 32px rgba(5, 10, 25, 0.50);
                    }
                    """
    elif theme in ("light", "light_glass"):
        return """
                .capsule-window-ui-root .outer-border-box,
                .root-box .outer-border-box,
                .outer-border-box {
                    border-radius: 25px;
                    background-image: none;
                    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.10), 0 1px 3px rgba(0, 0, 0, 0.05);
                }
                """
    else:
        return """
                      .capsule-window-ui-root .outer-border-box,
                      .root-box .outer-border-box,
                      .outer-border-box {
                          border-radius: 25px;
                          background-image: none;
                          box-shadow: 0 4px 14px rgba(0, 0, 0, 0.40), 0 1px 3px rgba(0, 0, 0, 0.20);
                      }
                      """


def _get_light_theme_css(tokens: ThemeTokens) -> str:
    """Generates Light theme-specific widget CSS rules."""
    search_bg = tokens.search_bg
    search_border = tokens.search_border
    card_bg = tokens.card_bg
    card_border = tokens.card_border
    card_shadow = tokens.card_shadow
    mode_btn_bg = tokens.mode_btn_bg
    mode_btn_border = tokens.mode_btn_border
    mode_btn_active = tokens.mode_btn_active
    meta_card_bg = tokens.meta_card_bg
    emoji_badge_bg = tokens.emoji_badge_bg

    return f"""                .capsule-window-ui {{ color: #1c1c1e; }}
                .capsule-window-ui .search-icon {{ color: #8e8e93; }}
                
                .capsule-window-ui .search-wrapper {{
                    background-color: {search_bg};
                    border: {search_border};
                    border-radius: 16px;
                    box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.06);
                    padding: 3px 12px;
                    min-height: 38px;
                }}
                
                .capsule-window-ui #search-entry,
                .capsule-window-ui #search-entry text,
                .capsule-window-ui .search-wrapper entry,
                .capsule-window-ui .search-wrapper text {{ 
                    background: transparent;
                    background-color: transparent;
                    color: #1c1c1e; 
                    caret-color: #007aff;
                    font-size: 20px;
                    font-weight: 500;
                    min-height: 34px;
                    padding: 0 8px;
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
                
                /* Category section headers */
                .capsule-window-ui .category-section-header {{
                    margin: 8px 4px 4px 4px;
                }}
                .capsule-window-ui .category-section-header.first-section {{
                    margin-top: 2px;
                }}
                .capsule-window-ui .category-header-dash {{
                    min-width: 14px;
                    min-height: 3px;
                    border-radius: 2px;
                    background: #007aff;
                    margin-right: 4px;
                }}
                .capsule-window-ui .category-header-title {{
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 0.8px;
                    text-transform: uppercase;
                    color: rgba(60, 60, 67, 0.70);
                }}
                .capsule-window-ui .category-header-line {{
                    min-height: 1px;
                    background: rgba(0, 0, 0, 0.06);
                    border-radius: 1px;
                    margin-left: 8px;
                }}

                .capsule-window-ui label.result-title {{ 
                    color: #1c1c1e;
                    font-weight: 600;
                }}
                .capsule-window-ui label.result-desc {{ 
                    color: rgba(60, 60, 67, 0.72); 
                }}
                
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
                
                .capsule-window-ui row, .capsule-window-ui .result-row {{ 
                    background-color: transparent; 
                    border: 1px solid transparent;
                    border-radius: 12px;
                    transition: background-color 120ms cubic-bezier(0.16, 1, 0.3, 1), box-shadow 120ms cubic-bezier(0.16, 1, 0.3, 1);
                }}
                .capsule-window-ui row:hover, .capsule-window-ui .result-row:hover {{ 
                    background-color: rgba(255, 255, 255, 0.45); 
                    border: 1px solid rgba(255, 255, 255, 0.60);
                    border-radius: 12px; 
                }}
                
                .capsule-window-ui row:selected, .capsule-window-ui .result-row:selected,
                .capsule-window-ui row:selected:hover, .capsule-window-ui .result-row:selected:hover {{
                    background: rgba(255, 255, 255, 0.90);
                    border: 1px solid rgba(255, 255, 255, 0.95);
                    color: #1c1c1e;
                    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05), inset 0 1px 1px rgba(255, 255, 255, 1.0);
                    border-radius: 12px;
                    outline: none;
                }}
                .capsule-window-ui row:selected label.result-title,
                .capsule-window-ui .result-row:selected label.result-title {{
                    color: #000000;
                    font-weight: 600;
                }}
                .capsule-window-ui row:selected label.result-desc,
                .capsule-window-ui .result-row:selected label.result-desc {{
                    color: rgba(60, 60, 67, 0.85);
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
                
                .capsule-window-ui .preview-hero-container {{
                    background: rgba(255, 255, 255, 0.80);
                    border: 1px solid rgba(255, 255, 255, 0.95);
                    border-radius: 20px;
                    padding: 14px 18px;
                    margin-bottom: 14px;
                    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06), inset 0 1px 1px #ffffff;
                }}

                .capsule-window-ui .preview-hero-thumbnail,
                image.preview-hero-thumbnail {{
                    border-radius: 16px;
                    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
                }}
                .capsule-window-ui label.preview-main-title {{ 
                    color: #1c1c1e; 
                    font-size: 30px;
                    font-weight: 800;
                    letter-spacing: -0.5px;
                    line-height: 1.15;
                    text-shadow: none; 
                }}
                .capsule-window-ui label.preview-main-subtitle {{ 
                    color: rgba(60, 60, 67, 0.75); 
                    font-size: 16px;
                    font-weight: 500;
                    line-height: 1.35;
                    text-shadow: none; 
                }}
                .capsule-window-ui label.preview-title {{ 
                    color: #1c1c1e; 
                    font-size: 26px;
                    font-weight: 800;
                    letter-spacing: -0.4px;
                    line-height: 1.2;
                }}
                .capsule-window-ui label.preview-subtitle {{ 
                    color: rgba(60, 60, 67, 0.75); 
                    font-size: 15px;
                    font-weight: 500;
                    line-height: 1.35;
                }}
                .capsule-window-ui label.preview-detail-label,
                .capsule-window-ui label.preview-meta-key {{
                    font-size: 11px;
                    font-weight: 600;
                    letter-spacing: 0.8px;
                }}
                .capsule-window-ui label.preview-detail-value,
                .capsule-window-ui label.preview-meta-val {{
                    font-size: 15px;
                    font-weight: 500;
                    line-height: 1.3;
                }}
                
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
                
                .capsule-window-ui .preview-panel {{
                    background: {card_bg};
                    border-left: {card_border};
                    border-radius: 0 0 24px 0;
                }}
                
                .capsule-window-ui .preview-panel.preview-panel-weather {{
                    padding: 0;
                    margin: 0;
                    border-radius: 0 0 24px 0;
                    border-left: 1px solid rgba(255, 255, 255, 0.14);
                    border-top: none;
                    border-right: none;
                    border-bottom: none;
                    box-shadow: inset 1px 0 0 rgba(255, 255, 255, 0.08);
                }}
                
                .capsule-window-ui .preview-meta-card {{
                    background: {meta_card_bg};
                    border: 1px solid rgba(0, 0, 0, 0.04);
                }}
                .capsule-window-ui label.preview-meta-key {{ color: rgba(0, 0, 0, 0.5); font-weight: 600; }}
                .capsule-window-ui label.preview-meta-val {{ color: #1c1c1e; font-weight: 500; }}
                
                .capsule-window-ui .preview-btn {{
                    background: rgba(255, 255, 255, 0.85);
                    color: #1c1c1e;
                    border: 1px solid rgba(0, 0, 0, 0.08);
                    border-radius: 10px;
                    padding: 8px 10px;
                    font-size: 13px;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
                    font-weight: 600;
                }}
                .capsule-window-ui .preview-btn:hover {{
                    background: #ffffff;
                    color: #000000;
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.07);
                }}
                
                .capsule-window-ui .mode-button {{
                    background: {mode_btn_bg};
                    border: {mode_btn_border};
                    color: #636366;
                    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
                    border-radius: 9999px;
                    min-width: 36px;
                    min-height: 36px;
                    padding: 0;
                    outline: none;
                }}
                .capsule-window-ui .mode-button:hover {{
                    background: {mode_btn_active};
                    color: #1c1c1e;
                    border: 1px solid rgba(0, 0, 0, 0.10);
                    border-radius: 9999px;
                    outline: none;
                    box-shadow: inset 0 1px 1px #ffffff;
                }}
                .capsule-window-ui .mode-button.active {{
                    background: {mode_btn_active};
                    color: #1c1c1e;
                    border: 1px solid rgba(0, 0, 0, 0.16);
                    border-radius: 9999px;
                    outline: none;
                    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.08);
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

                .capsule-window-ui .action-footer-bar {{
                    background: transparent;
                    border: none;
                }}
                .capsule-window-ui .action-bar-separator {{
                    background: rgba(0, 0, 0, 0.08);
                }}
                .capsule-window-ui .action-pill-btn:hover {{
                    background: rgba(255, 255, 255, 0.60);
                }}
                .capsule-window-ui .kbd-badge {{
                    background: rgba(255, 255, 255, 0.85);
                    color: #1c1c1e;
                    border: 1px solid rgba(0, 0, 0, 0.10);
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
                    border-radius: 6px;
                    font-weight: 600;
                }}
                .capsule-window-ui .action-pill-text {{
                    color: rgba(60, 60, 67, 0.80);
                    font-size: 12px;
                    font-weight: 500;
                }}
                .capsule-window-ui .alt-shortcut-badge {{
                    background: rgba(255, 255, 255, 0.80);
                    color: rgba(60, 60, 67, 0.80);
                    border: 1px solid rgba(0, 0, 0, 0.08);
                    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 2px 7px;
                }}
                .capsule-window-ui row:selected .alt-shortcut-badge {{
                    background: #ffffff;
                    color: #1c1c1e;
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                }}
"""


def _get_dark_theme_css(tokens: ThemeTokens) -> str:
    """Generates Dark / Glass / Aura theme-specific widget CSS rules."""
    search_bg = tokens.search_bg
    search_border = tokens.search_border
    card_bg = tokens.card_bg
    card_border = tokens.card_border
    card_shadow = tokens.card_shadow
    mode_btn_bg = tokens.mode_btn_bg
    mode_btn_border = tokens.mode_btn_border
    mode_btn_active = tokens.mode_btn_active
    meta_card_bg = tokens.meta_card_bg
    emoji_badge_bg = tokens.emoji_badge_bg

    return f"""                .capsule-window-ui {{ color: #f5f5f7; }}
                .capsule-window-ui .search-icon {{ color: rgba(255, 255, 255, 0.7); }}
                
                .capsule-window-ui .search-wrapper {{
                    background-color: {search_bg};
                    border: {search_border};
                    border-radius: 16px;
                    box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.15);
                    padding: 3px 12px;
                    min-height: 38px;
                }}
                
                .capsule-window-ui #search-entry,
                .capsule-window-ui #search-entry text,
                .capsule-window-ui .search-wrapper entry,
                .capsule-window-ui .search-wrapper text {{ 
                    background: transparent;
                    background-color: transparent;
                    color: #ffffff; 
                    caret-color: #007aff;
                    font-size: 20px;
                    font-weight: 500;
                    min-height: 34px;
                    padding: 0 8px;
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
                
                .capsule-window-ui .preview-panel {{
                    background: rgba(255, 255, 255, 0.02);
                    border-left: 1px solid rgba(255, 255, 255, 0.05);
                }}

                .capsule-window-ui label.preview-main-title {{ 
                    color: #ffffff; 
                    font-size: 30px;
                    font-weight: 800;
                    letter-spacing: -0.5px;
                    line-height: 1.15;
                }}
                .capsule-window-ui label.preview-main-subtitle {{ 
                    color: rgba(255, 255, 255, 0.75); 
                    font-size: 16px; 
                    font-weight: 500;
                    line-height: 1.35;
                }}
                .capsule-window-ui label.preview-title {{ 
                    color: #ffffff; 
                    font-size: 26px;
                    font-weight: 800;
                    letter-spacing: -0.4px;
                    line-height: 1.2;
                }}
                .capsule-window-ui label.preview-subtitle {{ 
                    color: rgba(255, 255, 255, 0.75); 
                    font-size: 15px; 
                    font-weight: 500;
                    line-height: 1.35;
                }}
                .capsule-window-ui label.preview-detail-label,
                .capsule-window-ui label.preview-meta-key {{
                    font-size: 11px;
                    font-weight: 600;
                    letter-spacing: 0.8px;
                }}
                .capsule-window-ui label.preview-detail-value,
                .capsule-window-ui label.preview-meta-val {{
                    font-size: 15px;
                    font-weight: 500;
                    line-height: 1.3;
                }}

                .capsule-window-ui .preview-panel.preview-panel-weather {{
                    padding: 0;
                    margin: 0;
                    border-radius: 0 0 24px 0;
                    border-left: 1px solid rgba(255, 255, 255, 0.14);
                    border-top: none;
                    border-right: none;
                    border-bottom: none;
                    box-shadow: inset 1px 0 0 rgba(255, 255, 255, 0.08);
                }}
                
                .capsule-window-ui .mode-button {{
                    background: {mode_btn_bg};
                    color: rgba(255, 255, 255, 0.75);
                    border: {mode_btn_border};
                    box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.25);
                    border-radius: 9999px;
                    min-width: 36px;
                    min-height: 36px;
                    padding: 0;
                    outline: none;
                }}
                .capsule-window-ui .mode-button:hover {{
                    background: {mode_btn_active};
                    color: #ffffff;
                    border: 1px solid rgba(255, 255, 255, 0.45);
                    box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.50);
                    border-radius: 9999px;
                    outline: none;
                }}
                .capsule-window-ui .mode-button.active {{
                    background: {mode_btn_active};
                    color: #ffffff;
                    border: 1px solid rgba(255, 255, 255, 0.65);
                    box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.60);
                    border-radius: 9999px;
                    outline: none;
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

                .capsule-window-ui .action-footer-bar {{
                    background: transparent;
                    border: none;
                }}
                .capsule-window-ui .action-bar-separator {{
                    background: rgba(255, 255, 255, 0.12);
                }}
                .capsule-window-ui .action-pill-btn:hover {{
                    background: rgba(255, 255, 255, 0.10);
                }}
                .capsule-window-ui .kbd-badge {{
                    background: rgba(255, 255, 255, 0.12);
                    color: #f5f5f7;
                    border: 1px solid rgba(255, 255, 255, 0.16);
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.30);
                }}
                .capsule-window-ui .action-pill-text {{
                    color: rgba(255, 255, 255, 0.72);
                }}
                .capsule-window-ui .action-bar-separator {{
                    background-color: rgba(255, 255, 255, 0.07);
                }}
                .capsule-window-ui .alt-shortcut-badge {{
                    background: rgba(255, 255, 255, 0.08);
                    color: rgba(255, 255, 255, 0.75);
                    border: 1px solid rgba(255, 255, 255, 0.12);
                }}
"""


def _get_dynamic_base_css(tokens: ThemeTokens, outer_box_style: str, theme_css: str) -> str:
    """Combines root window, outer box, theme CSS, weather canvas, and animations."""
    bg_color = tokens.bg_color
    backdrop = tokens.backdrop
    jelly_duration = tokens.jelly_duration
    if tokens.theme == "echo_blue":
        bg_decl = "background: radial-gradient(circle at 78% 8%, rgba(180, 205, 255, 0.18) 0%, rgba(255, 255, 255, 0) 45%), linear-gradient(180deg, #0a0d1a 0%, #11172e 40%, #16203d 75%, #1c274b 100%);"
    else:
        bg_decl = f"background-color: {bg_color};"
    return f"""            window, window.background, .background, window.solid-csd, window.csd, window decoration, decoration, windowhandle, .root-box {{
                background: transparent;
                background-color: transparent;
                border: none;
                box-shadow: none;
                outline: none;
            }}
            .root-box {{
                padding: 28px;
                background: transparent;
                background-color: transparent;
            }}
            .mode-button, button.mode-button, button.circular {{
                border-radius: 9999px;
                min-width: 36px;
                min-height: 36px;
                padding: 0;
            }}
            .capsule-window-ui {{
                min-width: 1050px;
                min-height: 56px;
                border-radius: 24px;
                padding-bottom: 4px;
                {bg_decl}
                {backdrop}
            }}

            /* Complete transparency shield for Echo Search containers across ALL third-party GTK themes */
            .capsule-window-ui scrolledwindow,
            .capsule-window-ui scrolledwindow > viewport,
            .capsule-window-ui viewport,
            .capsule-window-ui list,
            .capsule-window-ui listview,
            .capsule-window-ui gridview,
            .capsule-window-ui .view,
            .capsule-window-ui stack,
            .capsule-window-ui .results-container,
            .capsule-window-ui #results-list {{
                background: transparent;
                background-color: transparent;
                border: none;
                box-shadow: none;
            }}

            .capsule-window-ui row:not(:hover):not(:selected),
            .capsule-window-ui list > row:not(:hover):not(:selected),
            .capsule-window-ui listview > row:not(:hover):not(:selected) {{
                background: transparent;
                background-color: transparent;
            }}

            .capsule-window-ui .apps-glass-container {{
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 24px;
                margin: 0 32px 32px 32px;
                padding: 24px;
                box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.05), 0 10px 20px rgba(0, 0, 0, 0.2);
            }}
            .capsule-window-ui.light-theme .apps-glass-container {{
                background: rgba(0, 0, 0, 0.03);
                border: 1px solid rgba(0, 0, 0, 0.06);
                box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.7), 0 4px 12px rgba(0, 0, 0, 0.04);
            }}
            .capsule-window-ui .apps-glass-container scrolledwindow,
            .capsule-window-ui .apps-glass-container viewport,
            .capsule-window-ui .apps-glass-container gridview,
            .capsule-window-ui .apps-glass-container .view,
            .capsule-window-ui .apps-glass-container listview,
            .capsule-window-ui .apps-glass-container stack {{
                background: transparent;
                background-color: transparent;
                border: none;
                box-shadow: none;
            }}
            {outer_box_style}
{theme_css}

            /* ==========================================================
               FULL ATMOSPHERIC WEATHER CANVAS & AMBIENT GLOW OVERRIDES
               ========================================================== */
            .outer-border-box {{
                transition: box-shadow 0.25s cubic-bezier(0.16, 1, 0.3, 1), background-image 0.25s ease;
            }}
            .root-box .outer-border-box.ambient-weather-bg-clear-day,
            window.ambient-weather-bg-clear-day .outer-border-box {{
                box-shadow: 0 0 24px rgba(53, 142, 232, 0.50), 0 8px 24px rgba(0, 0, 0, 0.35);
                background-image: linear-gradient(135deg, rgba(255, 255, 255, 0.85) 0%, rgba(255, 255, 255, 0.08) 35%, rgba(255, 255, 255, 0.08) 65%, rgba(255, 255, 255, 0.75) 100%);
            }}
            .root-box .outer-border-box.ambient-weather-bg-clear-dusk,
            window.ambient-weather-bg-clear-dusk .outer-border-box {{
                box-shadow: 0 0 26px rgba(113, 103, 128, 0.55), 0 8px 24px rgba(0, 0, 0, 0.40);
                background-image: linear-gradient(135deg, rgba(255, 255, 255, 0.80) 0%, rgba(154, 109, 106, 0.20) 50%, rgba(23, 55, 94, 0.40) 100%);
            }}
            .root-box .outer-border-box.ambient-weather-bg-clear-night,
            window.ambient-weather-bg-clear-night .outer-border-box {{
                box-shadow: 0 0 24px rgba(35, 55, 110, 0.60), 0 8px 24px rgba(0, 0, 0, 0.55);
                background-image: linear-gradient(135deg, rgba(255, 255, 255, 0.80) 0%, rgba(255, 255, 255, 0.08) 35%, rgba(255, 255, 255, 0.08) 65%, rgba(255, 255, 255, 0.75) 100%);
            }}
            .root-box .outer-border-box.ambient-weather-bg-clouds-day,
            .root-box .outer-border-box.ambient-weather-bg-clouds-night,
            window.ambient-weather-bg-clouds-day .outer-border-box,
            window.ambient-weather-bg-clouds-night .outer-border-box {{
                box-shadow: 0 0 24px rgba(90, 115, 145, 0.55), 0 8px 24px rgba(0, 0, 0, 0.35);
                background-image: linear-gradient(135deg, rgba(160, 185, 210, 0.75) 0%, rgba(130, 150, 175, 0.12) 50%, rgba(190, 205, 220, 0.55) 100%);
            }}
            .root-box .outer-border-box.ambient-weather-bg-rain-day,
            .root-box .outer-border-box.ambient-weather-bg-rain-night,
            window.ambient-weather-bg-rain-day .outer-border-box,
            window.ambient-weather-bg-rain-night .outer-border-box {{
                box-shadow: 0 0 24px rgba(60, 100, 150, 0.60), 0 8px 24px rgba(0, 0, 0, 0.45);
                background-image: linear-gradient(135deg, rgba(90, 150, 215, 0.8) 0%, rgba(60, 100, 160, 0.15) 50%, rgba(110, 180, 230, 0.55) 100%);
            }}
            .root-box .outer-border-box.ambient-weather-bg-drizzle-day,
            .root-box .outer-border-box.ambient-weather-bg-drizzle-night,
            window.ambient-weather-bg-drizzle-day .outer-border-box,
            window.ambient-weather-bg-drizzle-night .outer-border-box {{
                box-shadow: 0 0 24px rgba(85, 115, 145, 0.55), 0 8px 24px rgba(0, 0, 0, 0.40);
                background-image: linear-gradient(135deg, rgba(200, 220, 240, 0.85) 0%, rgba(130, 160, 190, 0.15) 50%, rgba(180, 205, 230, 0.65) 100%);
            }}
            .root-box .outer-border-box.ambient-weather-bg-storm-day,
            .root-box .outer-border-box.ambient-weather-bg-storm-night,
            window.ambient-weather-bg-storm-day .outer-border-box,
            window.ambient-weather-bg-storm-night .outer-border-box {{
                box-shadow: 0 0 24px rgba(130, 80, 180, 0.65), 0 8px 24px rgba(0, 0, 0, 0.55);
                background-image: linear-gradient(135deg, rgba(175, 110, 235, 0.85) 0%, rgba(100, 60, 160, 0.15) 50%, rgba(205, 140, 255, 0.55) 100%);
            }}
            .root-box .outer-border-box.ambient-weather-bg-snow-day,
            .root-box .outer-border-box.ambient-weather-bg-snow-night,
            window.ambient-weather-bg-snow-day .outer-border-box,
            window.ambient-weather-bg-snow-night .outer-border-box {{
                box-shadow: 0 0 24px rgba(170, 215, 255, 0.60), 0 8px 24px rgba(0, 0, 0, 0.35);
                background-image: linear-gradient(135deg, rgba(215, 240, 255, 0.9) 0%, rgba(180, 220, 255, 0.15) 50%, rgba(240, 250, 255, 0.75) 100%);
            }}
            .root-box .outer-border-box.ambient-weather-bg-fog-day,
            .root-box .outer-border-box.ambient-weather-bg-fog-night,
            window.ambient-weather-bg-fog-day .outer-border-box,
            window.ambient-weather-bg-fog-night .outer-border-box {{
                box-shadow: 0 0 24px rgba(100, 120, 135, 0.50), 0 8px 24px rgba(0, 0, 0, 0.35);
                background-image: linear-gradient(135deg, rgba(165, 180, 195, 0.75) 0%, rgba(120, 135, 150, 0.12) 50%, rgba(185, 200, 210, 0.55) 100%);
            }}

            .capsule-window-ui {{
                transition: background 0.35s cubic-bezier(0.16, 1, 0.3, 1), color 0.25s ease;
            }}
            
            /* Full Atmospheric Weather Canvas Gradients */
            .capsule-window-ui.weather-canvas-active {{
                color: #ffffff;
            }}
            .capsule-window-ui.weather-canvas-clear-day {{
                background: radial-gradient(circle at 75% 0%, rgba(255, 235, 175, 0.45) 0%, rgba(255, 255, 255, 0) 55%),
                            linear-gradient(180deg, #1c72e8 0%, #2f87ea 35%, #4fa3f7 70%, #68b5fd 100%);
            }}
            .capsule-window-ui.weather-canvas-clear-night {{
                background: radial-gradient(circle at 78% 8%, rgba(180, 205, 255, 0.22) 0%, rgba(255, 255, 255, 0) 45%),
                            linear-gradient(180deg, #0a0d1a 0%, #11172e 40%, #16203d 75%, #1c274b 100%);
            }}
            .capsule-window-ui.weather-canvas-clouds-day {{
                background: linear-gradient(180deg, #7dbadb 0%, #89b9d3 25%, #a0b9c8 55%, #bad3dd 80%, #a0cee3 100%);
            }}
            .capsule-window-ui.weather-canvas-clouds-night {{
                background: linear-gradient(180deg, #11151c 0%, #1a202a 40%, #222a38 75%, #2a3444 100%);
            }}
            .capsule-window-ui.weather-canvas-rain-day {{
                background: linear-gradient(180deg, #8f9eb3 0%, #8c9cac 25%, #7a899c 50%, #718295 75%, #5e728a 100%);
            }}
            .capsule-window-ui.weather-canvas-rain-night {{
                background: linear-gradient(180deg, #0c1219 0%, #131c26 40%, #1c2735 75%, #233142 100%);
            }}
            .capsule-window-ui.weather-canvas-drizzle-day {{
                background: radial-gradient(circle at 75% 10%, rgba(255, 255, 255, 0.30) 0%, rgba(200, 225, 255, 0.14) 25%, rgba(255, 255, 255, 0) 55%),
                            linear-gradient(180deg, #6c8096 0%, #586c82 35%, #46586d 70%, #354556 100%);
            }}
            .capsule-window-ui.weather-canvas-drizzle-night {{
                background: radial-gradient(circle at 75% 10%, rgba(180, 205, 235, 0.15) 0%, rgba(255, 255, 255, 0) 45%),
                            linear-gradient(180deg, #18222e 0%, #202c3c 45%, #2a3a4e 85%, #34465e 100%);
            }}
            .capsule-window-ui.weather-canvas-storm-day,
            .capsule-window-ui.weather-canvas-storm-night {{
                background: radial-gradient(circle at 65% 0%, rgba(200, 160, 255, 0.25) 0%, rgba(255, 255, 255, 0) 45%),
                            linear-gradient(180deg, #251c38 0%, #31254a 40%, #3e305c 75%, #4c3b6f 100%);
            }}
            .capsule-window-ui.weather-canvas-snow-day {{
                background: radial-gradient(circle at 65% 0%, rgba(255, 255, 255, 0.4) 0%, rgba(255, 255, 255, 0) 50%),
                            linear-gradient(180deg, #5b7996 0%, #708ea8 40%, #88a4bc 75%, #9cb7cd 100%);
            }}
            .capsule-window-ui.weather-canvas-snow-night {{
                background: linear-gradient(180deg, #121922 0%, #1b2430 40%, #253140 75%, #2f3e50 100%);
            }}
            .capsule-window-ui.weather-canvas-fog-day,
            .capsule-window-ui.weather-canvas-fog-night {{
                background: linear-gradient(180deg, #37434d 0%, #465460 40%, #566673 75%, #657785 100%);
            }}

            /* Seamless Weather Preview Panel over Full Canvas */
            .capsule-window-ui.weather-canvas-active .preview-weather-full-bg,
            .capsule-window-ui.weather-canvas-active .preview-panel,
            .capsule-window-ui.weather-canvas-active .preview-panel-weather,
            .capsule-window-ui.weather-canvas-active .weather-bg-clear-day,
            .capsule-window-ui.weather-canvas-active .weather-bg-clear-dusk,
            .capsule-window-ui.weather-canvas-active .weather-bg-clear-night,
            .capsule-window-ui.weather-canvas-active .weather-bg-clouds-day,
            .capsule-window-ui.weather-canvas-active .weather-bg-clouds-night,
            .capsule-window-ui.weather-canvas-active .weather-bg-rain-day,
            .capsule-window-ui.weather-canvas-active .weather-bg-rain-night,
            .capsule-window-ui.weather-canvas-active .weather-bg-drizzle-day,
            .capsule-window-ui.weather-canvas-active .weather-bg-drizzle-night,
            .capsule-window-ui.weather-canvas-active .weather-bg-storm-day,
            .capsule-window-ui.weather-canvas-active .weather-bg-storm-night,
            .capsule-window-ui.weather-canvas-active .weather-bg-snow-day,
            .capsule-window-ui.weather-canvas-active .weather-bg-snow-night,
            .capsule-window-ui.weather-canvas-active .weather-bg-fog-day,
            .capsule-window-ui.weather-canvas-active .weather-bg-fog-night,
            .capsule-window-ui.weather-canvas-active .preview-panel.preview-panel-weather,
            .capsule-window-ui.weather-canvas-active .preview-panel.preview-weather-full-bg,
            .capsule-window-ui.weather-canvas-active .preview-panel.weather-bg-clear-day,
            .capsule-window-ui.weather-canvas-active .preview-panel.weather-bg-clear-dusk,
            .capsule-window-ui.weather-canvas-active .preview-panel.weather-bg-clear-night,
            .capsule-window-ui.weather-canvas-active .preview-panel.weather-bg-clouds-day,
            .capsule-window-ui.weather-canvas-active .preview-panel.weather-bg-clouds-night,
            .capsule-window-ui.weather-canvas-active .preview-panel.weather-bg-rain-day,
            .capsule-window-ui.weather-canvas-active .preview-panel.weather-bg-rain-night,
            .capsule-window-ui.weather-canvas-active .preview-panel.weather-bg-drizzle-day,
            .capsule-window-ui.weather-canvas-active .preview-panel.weather-bg-drizzle-night,
            .capsule-window-ui.weather-canvas-active .preview-panel.weather-bg-storm-day,
            .capsule-window-ui.weather-canvas-active .preview-panel.weather-bg-storm-night,
            .capsule-window-ui.weather-canvas-active .preview-panel.weather-bg-snow-day,
            .capsule-window-ui.weather-canvas-active .preview-panel.weather-bg-snow-night,
            .capsule-window-ui.weather-canvas-active .preview-panel.weather-bg-fog-day,
            .capsule-window-ui.weather-canvas-active .preview-panel.weather-bg-fog-night {{
                background: transparent;
                background-image: none;
                box-shadow: none;
            }}
            .capsule-window-ui.weather-canvas-active .preview-panel.preview-panel-weather {{
                border-left: 1px solid rgba(255, 255, 255, 0.12);
            }}

            /* Completely Invisible Scrollbars in Weather Mode */
            .capsule-window-ui.weather-canvas-active .preview-panel scrollbar,
            .capsule-window-ui.weather-canvas-active .preview-panel scrollbar slider,
            .capsule-window-ui.weather-canvas-active .weather-scrolled-window scrollbar,
            .capsule-window-ui.weather-canvas-active .weather-scrolled-window scrollbar slider,
            .capsule-window-ui.weather-canvas-active .preview-panel scrollbar slider:hover,
            .capsule-window-ui.weather-canvas-active .weather-scrolled-window scrollbar slider:hover {{
                opacity: 0;
                min-width: 0;
                min-height: 0;
                background: transparent;
                border: none;
            }}

            /* Unified Frosted Header in Weather Mode */
            .capsule-window-ui.weather-canvas-active .search-wrapper {{
                background-color: rgba(255, 255, 255, 0.18);
                border: 1px solid rgba(255, 255, 255, 0.24);
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.22);
            }}
            .capsule-window-ui.weather-canvas-active #search-entry,
            .capsule-window-ui.weather-canvas-active #search-entry text {{
                color: #ffffff;
            }}
            .capsule-window-ui.weather-canvas-active #search-entry placeholder {{
                color: rgba(255, 255, 255, 0.65);
            }}
            .capsule-window-ui.weather-canvas-active .search-icon {{
                color: rgba(255, 255, 255, 0.90);
            }}
            .capsule-window-ui.weather-canvas-active .mode-button {{
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.18);
                color: #ffffff;
                border-radius: 9999px;
                outline: none;
                box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.20);
            }}
            .capsule-window-ui.weather-canvas-active .mode-button image {{
                color: #ffffff;
            }}
            .capsule-window-ui.weather-canvas-active .mode-button:hover {{
                background: rgba(255, 255, 255, 0.22);
                border-color: rgba(255, 255, 255, 0.32);
                border-radius: 9999px;
                outline: none;
                box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.40);
            }}
            .capsule-window-ui.weather-canvas-active .mode-button.active {{
                background: rgba(255, 255, 255, 0.30);
                border-color: rgba(255, 255, 255, 0.40);
                border-radius: 9999px;
                outline: none;
                box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.50);
            }}

            /* Seamless Results List on Left */
            .capsule-window-ui.weather-canvas-active #results-list {{
                background: transparent;
                background-color: transparent;
                border: none;
                box-shadow: none;
                padding: 0 12px;
            }}
            .capsule-window-ui.weather-canvas-active #results-list row,
            .capsule-window-ui.weather-canvas-active #results-list .result-row {{
                background: transparent;
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 14px;
                margin-bottom: 2px;
            }}
            .capsule-window-ui.weather-canvas-active #results-list row:selected,
            .capsule-window-ui.weather-canvas-active #results-list .result-row:selected,
            .capsule-window-ui.weather-canvas-active #results-list .result-row.selected {{
                background-color: rgba(255, 255, 255, 0.20);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.28);
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.25);
                border-radius: 14px;
            }}
            .capsule-window-ui.weather-canvas-active #results-list row:hover:not(:selected),
            .capsule-window-ui.weather-canvas-active #results-list .result-row:hover:not(:selected) {{
                background-color: rgba(255, 255, 255, 0.10);
                border-radius: 14px;
            }}
            .capsule-window-ui.weather-canvas-active #results-list label.result-title,
            .capsule-window-ui.weather-canvas-active #results-list .result-title {{
                color: #ffffff;
            }}
            .capsule-window-ui.weather-canvas-active #results-list label.result-desc,
            .capsule-window-ui.weather-canvas-active #results-list .result-desc {{
                color: rgba(255, 255, 255, 0.75);
            }}


            .anim-jelly-wobble {{
                animation: jelly_wobble_unfold {jelly_duration}ms cubic-bezier(0.2, 0.9, 0.3, 1) forwards;
            }}
"""


def _get_quick_look_theme_css(theme_mode: str, scoped: bool = False) -> str:
    """Generate CSS rules for Quick Look matching theme_mode (light, aura_glow, or dark)."""
    theme_slug = theme_mode.replace("_", "-")
    if scoped:
        p = f".quick-look-theme-{theme_slug} "
        p_self = f".quick-look-theme-{theme_slug}"
    else:
        p = ""
        p_self = ""

    if theme_mode == "light":
        return f"""
/* Quick Look Light Theme */
{p}.quick-look-card,
{p_self}.quick-look-card {{
    background-color: rgba(255, 255, 255, 0.98);
    border: 1px solid rgba(0, 0, 0, 0.12);
    box-shadow: 0 24px 64px rgba(0, 0, 0, 0.14), 0 2px 10px rgba(0, 0, 0, 0.06);
}}

{p}.quick-look-header {{
    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}}

{p}.quick-look-title,
{p}label.quick-look-title {{
    color: #1d1d1f;
}}

{p}.quick-look-subtitle,
{p}label.quick-look-subtitle {{
    color: #6e6e73;
}}

{p}.quick-look-badge,
{p}label.quick-look-badge {{
    background-color: rgba(0, 0, 0, 0.06);
    border: 1px solid rgba(0, 0, 0, 0.10);
    color: #1d1d1f;
}}

{p}.quick-look-close-btn,
{p}button.quick-look-close-btn {{
    background-color: rgba(0, 0, 0, 0.05);
    border: 1px solid rgba(0, 0, 0, 0.10);
    color: #48484a;
}}

{p}.quick-look-close-btn:hover,
{p}button.quick-look-close-btn:hover {{
    background-color: rgba(0, 0, 0, 0.10);
    color: #000000;
}}

{p}.quick-look-editor-card {{
    background-color: #f6f8fa;
    border: 1px solid rgba(0, 0, 0, 0.10);
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.04), 0 6px 20px rgba(0, 0, 0, 0.06);
}}

{p}.quick-look-editor-toolbar {{
    background-color: #eaecef;
    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}}

{p}.quick-look-editor-stat {{
    color: #57606a;
}}

{p}.quick-look-save-btn {{
    background-color: #f3f4f6;
    border: 1px solid rgba(0, 0, 0, 0.14);
    color: #24292f;
}}

{p}.quick-look-save-btn:hover {{
    background-color: #e5e7eb;
    color: #000000;
}}

{p}.quick-look-save-btn.dirty {{
    background-color: #1a7f37;
    border-color: #116329;
    color: #ffffff;
    box-shadow: 0 0 10px rgba(26, 127, 55, 0.40);
}}

{p}.quick-look-save-btn.dirty:hover {{
    background-color: #116329;
}}

{p}.quick-look-line-numbers-scroll,
{p}.quick-look-line-numbers {{
    background-color: #edf0f2;
    color: #8c959f;
    border-right: 1px solid rgba(0, 0, 0, 0.08);
}}

{p}.quick-look-readonly-badge {{
    background-color: rgba(154, 103, 0, 0.15);
    color: #9a6700;
    border: 1px solid rgba(154, 103, 0, 0.30);
}}

{p}.quick-look-code-view,
{p}textview.quick-look-code-view,
{p}.quick-look-code-view text {{
    background-color: transparent;
    color: #24292f;
    caret-color: #0969da;
}}

{p}.quick-look-text-scroll,
{p}.quick-look-doc-scroll,
{p}.quick-look-doc-view {{
    background-color: #f6f8fa;
    border: 1px solid rgba(0, 0, 0, 0.08);
}}

{p}.quick-look-image-container {{
    background-color: #e9ecef;
    border: 1px solid rgba(0, 0, 0, 0.08);
}}

{p}.quick-look-folder-container {{
    background-color: #f6f8fa;
    border: 1px solid rgba(0, 0, 0, 0.08);
}}

{p}.quick-look-folder-row:hover {{
    background-color: rgba(0, 0, 0, 0.06);
}}

{p}.quick-look-folder-item-name,
{p}label.quick-look-folder-item-name {{
    color: #1f2328;
}}

{p}.quick-look-folder-item-size,
{p}label.quick-look-folder-item-size {{
    color: #656d76;
}}

{p}.quick-look-empty-folder,
{p}label.quick-look-empty-folder {{
    color: #656d76;
}}

{p}.quick-look-audio-hero {{
    background: radial-gradient(circle at center, rgba(37, 99, 235, 0.08), rgba(240, 242, 246, 0.95));
    border: 1px solid rgba(0, 0, 0, 0.08);
}}

{p}.quick-look-audio-disc {{
    color: #2563eb;
}}

{p}.quick-look-audio-title,
{p}label.quick-look-audio-title {{
    color: #1d1d1f;
}}

{p}.quick-look-audio-controls {{
    background-color: rgba(0, 0, 0, 0.04);
    border: 1px solid rgba(0, 0, 0, 0.08);
}}

{p}.quick-look-play-btn,
{p}button.quick-look-play-btn {{
    background-color: #2563eb;
    color: #ffffff;
}}

{p}.quick-look-play-btn:hover,
{p}button.quick-look-play-btn:hover {{
    background-color: #1d4ed8;
}}

{p}.quick-look-audio-time,
{p}label.quick-look-audio-time {{
    color: #656d76;
}}

{p}.quick-look-video-container {{
    background-color: #111113;
    border: 1px solid rgba(0, 0, 0, 0.12);
}}

{p}.quick-look-pdf-container,
{p}.quick-look-pdf-scroll {{
    background-color: #e9ecef;
}}

{p}.quick-look-pdf-toolbar {{
    background-color: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(0, 0, 0, 0.12);
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
}}

{p}.quick-look-toolbar-sep {{
    background-color: rgba(0, 0, 0, 0.12);
}}

{p}.quick-look-page-btn {{
    color: #24292f;
}}

{p}.quick-look-page-btn:hover {{
    background-color: rgba(0, 0, 0, 0.08);
    color: #000000;
}}

{p}.quick-look-page-label {{
    color: #24292f;
}}

{p}.quick-look-generic-box {{
    background-color: #f6f8fa;
    border: 1px solid rgba(0, 0, 0, 0.08);
}}

{p}.quick-look-media-icon {{
    color: #2563eb;
}}

{p}.quick-look-media-title {{
    color: #1f2328;
}}

{p}.quick-look-path-label {{
    color: #57606a;
    background-color: rgba(0, 0, 0, 0.05);
    border: 1px solid rgba(0, 0, 0, 0.06);
}}

{p}.quick-look-footer {{
    border-top: 1px solid rgba(0, 0, 0, 0.08);
}}

{p}.quick-look-action-btn,
{p}button.quick-look-action-btn {{
    background-color: rgba(0, 0, 0, 0.05);
    border: 1px solid rgba(0, 0, 0, 0.12);
    color: #1d1d1f;
}}

{p}button.quick-look-action-btn label {{
    color: #1d1d1f;
}}

{p}.quick-look-action-btn:hover,
{p}button.quick-look-action-btn:hover {{
    background-color: rgba(0, 0, 0, 0.10);
    color: #000000;
}}

{p}.quick-look-action-btn.primary-action,
{p}button.quick-look-action-btn.primary-action {{
    background-color: #0071e3;
    border-color: #005bb5;
    color: #ffffff;
}}

{p}button.quick-look-action-btn.primary-action label {{
    color: #ffffff;
}}

{p}.quick-look-action-btn.primary-action:hover,
{p}button.quick-look-action-btn.primary-action:hover {{
    background-color: #005bb5;
}}

{p}.quick-look-hint,
{p}label.quick-look-hint {{
    color: #86868b;
}}
"""
    elif theme_mode == "aura_glow":
        return f"""
/* Quick Look Aura Glow Theme */
{p}.quick-look-card,
{p_self}.quick-look-card {{
    background-color: rgba(22, 17, 34, 0.96);
    border: 1px solid rgba(168, 85, 247, 0.35);
    box-shadow: 0 28px 70px rgba(0, 0, 0, 0.80), 0 0 28px rgba(168, 85, 247, 0.22);
}}

{p}.quick-look-header {{
    border-bottom: 1px solid rgba(168, 85, 247, 0.20);
}}

{p}.quick-look-title,
{p}label.quick-look-title {{
    color: #ffffff;
}}

{p}.quick-look-subtitle,
{p}label.quick-look-subtitle {{
    color: #d8b4fe;
}}

{p}.quick-look-badge,
{p}label.quick-look-badge {{
    background-color: rgba(168, 85, 247, 0.16);
    border: 1px solid rgba(168, 85, 247, 0.35);
    color: #e9d5ff;
}}

{p}.quick-look-close-btn,
{p}button.quick-look-close-btn {{
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(168, 85, 247, 0.25);
    color: #e9d5ff;
}}

{p}.quick-look-close-btn:hover,
{p}button.quick-look-close-btn:hover {{
    background-color: rgba(168, 85, 247, 0.30);
    color: #ffffff;
    border-color: rgba(168, 85, 247, 0.50);
}}

{p}.quick-look-editor-card {{
    background-color: rgba(14, 11, 23, 0.95);
    border: 1px solid rgba(168, 85, 247, 0.22);
    box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.08), 0 12px 36px rgba(0, 0, 0, 0.55);
}}

{p}.quick-look-editor-toolbar {{
    background-color: rgba(168, 85, 247, 0.08);
    border-bottom: 1px solid rgba(168, 85, 247, 0.18);
}}

{p}.quick-look-editor-stat {{
    color: #d8b4fe;
}}

{p}.quick-look-save-btn {{
    background-color: rgba(168, 85, 247, 0.15);
    border: 1px solid rgba(168, 85, 247, 0.35);
    color: #ffffff;
}}

{p}.quick-look-save-btn:hover {{
    background-color: rgba(168, 85, 247, 0.30);
    border-color: rgba(168, 85, 247, 0.60);
    box-shadow: 0 0 14px rgba(168, 85, 247, 0.40);
}}

{p}.quick-look-save-btn.dirty {{
    background-image: linear-gradient(135deg, #a855f7, #6366f1);
    border-color: #c084fc;
    color: #ffffff;
    box-shadow: 0 0 14px rgba(168, 85, 247, 0.60);
}}

{p}.quick-look-line-numbers-scroll,
{p}.quick-look-line-numbers {{
    background-color: rgba(9, 7, 16, 0.98);
    color: rgba(168, 85, 247, 0.55);
    border-right: 1px solid rgba(168, 85, 247, 0.20);
}}

{p}.quick-look-readonly-badge {{
    background-color: rgba(255, 184, 108, 0.20);
    color: #ffb86c;
    border: 1px solid rgba(255, 184, 108, 0.40);
}}

{p}.quick-look-code-view,
{p}textview.quick-look-code-view,
{p}.quick-look-code-view text {{
    background-color: transparent;
    color: #f8f8f2;
    caret-color: #c084fc;
}}

{p}.quick-look-text-scroll,
{p}.quick-look-doc-scroll,
{p}.quick-look-doc-view {{
    background-color: rgba(14, 11, 23, 0.95);
    border: 1px solid rgba(168, 85, 247, 0.20);
}}

{p}.quick-look-image-container {{
    background-color: rgba(9, 7, 16, 0.90);
    border: 1px solid rgba(168, 85, 247, 0.20);
}}

{p}.quick-look-folder-container {{
    background-color: rgba(14, 11, 23, 0.95);
    border: 1px solid rgba(168, 85, 247, 0.20);
}}

{p}.quick-look-folder-row:hover {{
    background-color: rgba(168, 85, 247, 0.15);
}}

{p}.quick-look-folder-item-name,
{p}label.quick-look-folder-item-name {{
    color: #ffffff;
}}

{p}.quick-look-folder-item-size,
{p}label.quick-look-folder-item-size {{
    color: #d8b4fe;
}}

{p}.quick-look-empty-folder,
{p}label.quick-look-empty-folder {{
    color: #a855f7;
}}

{p}.quick-look-audio-hero {{
    background: radial-gradient(circle at center, rgba(168, 85, 247, 0.25), rgba(14, 11, 23, 0.96));
    border: 1px solid rgba(168, 85, 247, 0.25);
    box-shadow: 0 0 24px rgba(168, 85, 247, 0.15);
}}

{p}.quick-look-audio-disc {{
    color: #c084fc;
}}

{p}.quick-look-audio-title,
{p}label.quick-look-audio-title {{
    color: #ffffff;
}}

{p}.quick-look-audio-controls {{
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(168, 85, 247, 0.20);
}}

{p}.quick-look-play-btn,
{p}button.quick-look-play-btn {{
    background-image: linear-gradient(135deg, #a855f7, #6366f1);
    color: #ffffff;
    box-shadow: 0 0 16px rgba(168, 85, 247, 0.50);
}}

{p}.quick-look-audio-time,
{p}label.quick-look-audio-time {{
    color: #d8b4fe;
}}

{p}.quick-look-video-container {{
    background-color: #000000;
    border: 1px solid rgba(168, 85, 247, 0.25);
    box-shadow: 0 0 20px rgba(168, 85, 247, 0.15);
}}

{p}.quick-look-pdf-toolbar {{
    background-color: rgba(28, 20, 48, 0.92);
    border: 1px solid rgba(168, 85, 247, 0.30);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.50), 0 0 15px rgba(168, 85, 247, 0.20);
}}

{p}.quick-look-toolbar-sep {{
    background-color: rgba(168, 85, 247, 0.30);
}}

{p}.quick-look-page-btn {{
    color: #e9d5ff;
}}

{p}.quick-look-page-btn:hover {{
    background-color: rgba(168, 85, 247, 0.25);
    color: #ffffff;
}}

{p}.quick-look-page-label {{
    color: #ffffff;
}}

{p}.quick-look-generic-box {{
    background-color: rgba(14, 11, 23, 0.90);
    border: 1px solid rgba(168, 85, 247, 0.20);
}}

{p}.quick-look-media-icon {{
    color: #c084fc;
}}

{p}.quick-look-media-title {{
    color: #ffffff;
}}

{p}.quick-look-path-label {{
    color: #d8b4fe;
    background-color: rgba(168, 85, 247, 0.12);
    border: 1px solid rgba(168, 85, 247, 0.25);
}}

{p}.quick-look-footer {{
    border-top: 1px solid rgba(168, 85, 247, 0.20);
}}

{p}.quick-look-action-btn,
{p}button.quick-look-action-btn {{
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(168, 85, 247, 0.28);
    color: #ffffff;
}}

{p}button.quick-look-action-btn label {{
    color: #ffffff;
}}

{p}.quick-look-action-btn:hover,
{p}button.quick-look-action-btn:hover {{
    background-color: rgba(168, 85, 247, 0.25);
    border-color: rgba(168, 85, 247, 0.50);
}}

{p}.quick-look-action-btn.primary-action,
{p}button.quick-look-action-btn.primary-action {{
    background-image: linear-gradient(135deg, #a855f7, #6366f1);
    border: 1px solid rgba(192, 132, 252, 0.50);
    color: #ffffff;
    box-shadow: 0 0 16px rgba(168, 85, 247, 0.45);
}}

{p}button.quick-look-action-btn.primary-action label {{
    color: #ffffff;
}}

{p}.quick-look-hint,
{p}label.quick-look-hint {{
    color: rgba(216, 180, 254, 0.70);
}}
"""
    else:  # Dark mode
        return f"""
/* Quick Look Dark Theme */
{p}.quick-look-card,
{p_self}.quick-look-card {{
    background-color: rgba(22, 25, 35, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 28px 70px rgba(0, 0, 0, 0.70), 0 0 0 1px rgba(255, 255, 255, 0.08);
}}

{p}.quick-look-header {{
    border-bottom: 1px solid rgba(255, 255, 255, 0.10);
}}

{p}.quick-look-title,
{p}label.quick-look-title {{
    color: #ffffff;
}}

{p}.quick-look-subtitle,
{p}label.quick-look-subtitle {{
    color: rgba(255, 255, 255, 0.60);
}}

{p}.quick-look-badge,
{p}label.quick-look-badge {{
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: rgba(255, 255, 255, 0.90);
}}

{p}.quick-look-close-btn,
{p}button.quick-look-close-btn {{
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.10);
    color: rgba(255, 255, 255, 0.70);
}}

{p}.quick-look-close-btn:hover,
{p}button.quick-look-close-btn:hover {{
    background-color: rgba(255, 255, 255, 0.18);
    color: #ffffff;
}}

{p}.quick-look-editor-card {{
    background-color: rgba(18, 19, 24, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.08), 0 12px 36px rgba(0, 0, 0, 0.45);
}}

{p}.quick-look-editor-toolbar {{
    background-color: rgba(255, 255, 255, 0.04);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}}

{p}.quick-look-editor-stat {{
    color: rgba(255, 255, 255, 0.55);
}}

{p}.quick-look-save-btn {{
    background-color: rgba(255, 255, 255, 0.09);
    border: 1px solid rgba(255, 255, 255, 0.18);
    color: #ffffff;
}}

{p}.quick-look-save-btn:hover {{
    background-color: rgba(255, 255, 255, 0.20);
    border-color: rgba(255, 255, 255, 0.40);
}}

{p}.quick-look-save-btn.dirty {{
    background-color: #238636;
    border-color: #3fb950;
    color: #ffffff;
    box-shadow: 0 0 12px rgba(46, 160, 67, 0.50);
}}

{p}.quick-look-line-numbers-scroll,
{p}.quick-look-line-numbers {{
    background-color: rgba(0, 0, 0, 0.25);
    color: rgba(255, 255, 255, 0.32);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}}

{p}.quick-look-readonly-badge {{
    background-color: rgba(210, 153, 34, 0.20);
    color: #d29922;
    border: 1px solid rgba(210, 153, 34, 0.40);
}}

{p}.quick-look-code-view,
{p}textview.quick-look-code-view,
{p}.quick-look-code-view text {{
    background-color: transparent;
    color: #e6edf3;
    caret-color: #58a6ff;
}}

{p}.quick-look-text-scroll,
{p}.quick-look-doc-scroll,
{p}.quick-look-doc-view {{
    background-color: rgba(12, 14, 20, 0.92);
    border: 1px solid rgba(255, 255, 255, 0.08);
}}

{p}.quick-look-image-container {{
    background-color: rgba(0, 0, 0, 0.40);
    border: 1px solid rgba(255, 255, 255, 0.08);
}}

{p}.quick-look-folder-container {{
    background-color: #0b0d14;
    border: 1px solid rgba(255, 255, 255, 0.08);
}}

{p}.quick-look-folder-row:hover {{
    background-color: rgba(255, 255, 255, 0.08);
}}

{p}.quick-look-folder-item-name,
{p}label.quick-look-folder-item-name {{
    color: #f1f5f9;
}}

{p}.quick-look-folder-item-size,
{p}label.quick-look-folder-item-size {{
    color: #64748b;
}}

{p}.quick-look-empty-folder,
{p}label.quick-look-empty-folder {{
    color: #64748b;
}}

{p}.quick-look-audio-hero {{
    background: radial-gradient(circle at center, rgba(59, 130, 246, 0.18), rgba(11, 13, 20, 0.95));
    border: 1px solid rgba(255, 255, 255, 0.10);
}}

{p}.quick-look-audio-disc {{
    color: #60a5fa;
}}

{p}.quick-look-audio-title,
{p}label.quick-look-audio-title {{
    color: #ffffff;
}}

{p}.quick-look-audio-controls {{
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.10);
}}

{p}.quick-look-play-btn,
{p}button.quick-look-play-btn {{
    background-color: #3b82f6;
    color: #ffffff;
}}

{p}.quick-look-play-btn:hover,
{p}button.quick-look-play-btn:hover {{
    background-color: #2563eb;
}}

{p}.quick-look-audio-time,
{p}label.quick-look-audio-time {{
    color: #94a3b8;
}}

{p}.quick-look-video-container {{
    background-color: #000000;
    border: 1px solid rgba(255, 255, 255, 0.10);
}}

{p}.quick-look-pdf-toolbar {{
    background-color: rgba(255, 255, 255, 0.09);
    border: 1px solid rgba(255, 255, 255, 0.14);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
}}

{p}.quick-look-toolbar-sep {{
    background-color: rgba(255, 255, 255, 0.18);
}}

{p}.quick-look-page-btn {{
    color: rgba(255, 255, 255, 0.75);
}}

{p}.quick-look-page-btn:hover {{
    background-color: rgba(255, 255, 255, 0.16);
    color: #ffffff;
}}

{p}.quick-look-page-label {{
    color: rgba(255, 255, 255, 0.85);
}}

{p}.quick-look-generic-box {{
    background-color: rgba(0, 0, 0, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.06);
}}

{p}.quick-look-media-icon {{
    color: #60a5fa;
}}

{p}.quick-look-media-title {{
    color: #ffffff;
}}

{p}.quick-look-path-label {{
    color: rgba(255, 255, 255, 0.60);
    background-color: rgba(255, 255, 255, 0.05);
}}

{p}.quick-look-footer {{
    border-top: 1px solid rgba(255, 255, 255, 0.10);
}}

{p}.quick-look-action-btn,
{p}button.quick-look-action-btn {{
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.14);
    color: #ffffff;
}}

{p}button.quick-look-action-btn label {{
    color: #ffffff;
}}

{p}.quick-look-action-btn:hover,
{p}button.quick-look-action-btn:hover {{
    background-color: rgba(255, 255, 255, 0.18);
}}

{p}.quick-look-action-btn.primary-action,
{p}button.quick-look-action-btn.primary-action {{
    background-color: #3b82f6;
    border-color: #60a5fa;
    color: #ffffff;
}}

{p}button.quick-look-action-btn.primary-action label {{
    color: #ffffff;
}}

{p}.quick-look-hint,
{p}label.quick-look-hint {{
    color: rgba(255, 255, 255, 0.45);
}}
"""


def _get_quick_look_css(tokens: ThemeTokens) -> str:
    """Generate dynamic CSS for Quick Look matching the active theme and providing scoped rules."""
    active_mode = "light" if tokens.is_light else ("aura_glow" if tokens.theme == "aura_glow" else "dark")

    scoped_light = _get_quick_look_theme_css("light", scoped=True)
    scoped_aura = _get_quick_look_theme_css("aura_glow", scoped=True)
    scoped_dark = _get_quick_look_theme_css("dark", scoped=True)
    active_unscoped = _get_quick_look_theme_css(active_mode, scoped=False)

    return f"{scoped_light}\n\n{scoped_aura}\n\n{scoped_dark}\n\n{active_unscoped}"


def build_dynamic_css(config_manager: Any = None, **kwargs: Any) -> str:
    """Master entry point to build dynamic CSS from config tokens."""
    tokens = resolve_tokens(config_manager, **kwargs)
    outer_box_style = _get_outer_box_style(tokens.theme)
    if tokens.is_light:
        theme_css = _get_light_theme_css(tokens)
    else:
        theme_css = _get_dark_theme_css(tokens)
    base_css = _get_dynamic_base_css(tokens, outer_box_style, theme_css)
    ql_css = _get_quick_look_css(tokens)
    return f"{base_css}\n\n{ql_css}"
