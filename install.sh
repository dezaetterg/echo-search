#!/bin/bash
# Echo Search Installer
# Standalone installer with system detection, dependency auto-resolution, and desktop integration.
set -euo pipefail

# --- Paths ---
INSTALL_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}"
DESKTOP_DIR="$DATA_DIR/applications"
ICON_DIR="$DATA_DIR/icons/hicolor/scalable/apps"
THEMES_ICON_DIR="$DATA_DIR/icons/echo-search"
APP_DIR="$DATA_DIR/echo-search"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/echo-search"
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/echo-search"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Color Definitions (ANSI 256 + 24-bit TrueColor) ---
C_CYAN='\033[38;2;100;220;255m'
C_SKY='\033[38;5;75m'
C_BLUE='\033[38;2;70;140;255m'
C_GOLD='\033[38;5;220m'
C_AMBER='\033[38;5;208m'
C_WHITE='\033[1;37m'
C_GREEN='\033[38;5;48m'
C_RED='\033[38;5;196m'
C_YELLOW='\033[38;5;226m'
C_DIM='\033[38;5;245m'
C_BOLD='\033[1m'
C_RESET='\033[0m'

# --- Helpers ---
info()    { echo -e "  ${C_GREEN}[✓]${C_RESET} $*"; }
warn()    { echo -e "  ${C_YELLOW}[!]${C_RESET} $*"; }
err()     { echo -e "  ${C_RED}[✗]${C_RESET} $*" >&2; }
item()    { echo -e "  ${C_SKY}•${C_RESET} $*"; }
section() { echo -e "\n${C_BOLD}${C_SKY}$*${C_RESET}"; }

# --- Check non-interactive argument ---
AUTO_CONFIRM=false
for arg in "$@"; do
    case "$arg" in
        -y|--yes)
            AUTO_CONFIRM=true
            ;;
    esac
done

# --- Print Colorful CLI Banner ---
print_banner() {
    echo
    echo -e "${C_CYAN}       ▄▄▄▄▄▄▄▄▄▄▄▄${C_RESET}                            ${C_WHITE}${C_BOLD}E C H O   S E A R C H${C_RESET}"
    echo -e "${C_CYAN}    ▄▀▀▀          ▀▀▄${C_RESET}                          ${C_DIM}Spotlight Launcher & Productivity Suite${C_RESET}"
    echo -e "${C_CYAN}  ▄▀   ${C_BLUE}▄▄▄▄▄▄▄▄▄▄${C_RESET}${C_CYAN}   ▀▄${C_RESET}        "
    echo -e "${C_CYAN} █   ${C_BLUE}▄▀          ▀▄${C_RESET}${C_CYAN}   █${C_RESET}                        ${C_SKY}Ecosystem :${C_RESET} ${C_WHITE}Echo Desktop${C_RESET}"
    echo -e "${C_CYAN} █  ${C_BLUE}█              █${C_RESET}${C_CYAN}  █${C_RESET}                        ${C_SKY}Platform  :${C_RESET} ${C_WHITE}Linux (All Distros & DEs)${C_RESET}"
    echo -e "${C_CYAN} █   ${C_BLUE}▀▄          ▄▀${C_RESET}${C_CYAN}   █${C_RESET}                        ${C_SKY}Engine    :${C_RESET} ${C_WHITE}PyGObject + GTK 4 + Layer-Shell${C_RESET}"
    echo -e "${C_CYAN}  ▀▄   ${C_BLUE}▀▀▀▀▀▀▀▀▀▀${C_RESET}${C_CYAN}   ▄▀ ▀▄${C_RESET}                      ${C_SKY}Shortcut  :${C_RESET} ${C_WHITE}Super + Space (Win + Space)${C_RESET}"
    echo -e "${C_CYAN}    ▀▀▄▄        ▄▄▀▀     ▀▄${C_RESET}                    "
    echo -e "${C_CYAN}        ▀▀▀▀▀▀▀▀           ▀▄▄${C_RESET}                    \033[38;5;244m[Echo]\033[0m            \033[38;5;244m[Search]\033[0m"
    echo -e "${C_CYAN}                              ▀▀${C_RESET}               "
    echo
}

# --- System Detection ---
detect_system() {
    DISTRO_NAME="Linux"
    DISTRO_ID="unknown"
    if [ -f /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        DISTRO_NAME="${PRETTY_NAME:-$NAME}"
        DISTRO_ID="${ID:-unknown}"
    fi

    DESKTOP_ENV="${XDG_CURRENT_DESKTOP:-${DESKTOP_SESSION:-Unknown}}"
    ARCH_NAME="$(uname -m)"

    # Detect package manager
    PKG_MGR="unknown"
    if command -v apt-get > /dev/null 2>&1; then
        PKG_MGR="apt"
    elif command -v dnf > /dev/null 2>&1; then
        PKG_MGR="dnf"
    elif command -v pacman > /dev/null 2>&1; then
        PKG_MGR="pacman"
    elif command -v zypper > /dev/null 2>&1; then
        PKG_MGR="zypper"
    fi
}

print_system_info() {
    section "Host Environment:"
    item "Distribution : ${C_WHITE}${DISTRO_NAME}${C_RESET} (${ARCH_NAME})"
    item "Desktop Env  : ${C_WHITE}${DESKTOP_ENV}${C_RESET}"
    item "Pkg Manager  : ${C_WHITE}${PKG_MGR}${C_RESET}"
    item "Supported DE : ${C_GREEN}All Environments${C_RESET} (GNOME, Cinnamon, KDE Plasma, XFCE, MATE, LXQt, COSMIC, Tiling WMs)"
}

# --- Dependencies Verification & Auto-Resolve ---
check_and_resolve_dependencies() {
    section "Checking Dependencies:"

    MISSING_REQUIRED=()
    MISSING_OPTIONAL=()

    # 1. Python 3
    if command -v python3 > /dev/null 2>&1; then
        PY_VER="$(python3 --version 2>&1 | awk '{print $2}')"
        info "Python 3 (${PY_VER}) found."
    else
        err "Python 3 not found."
        MISSING_REQUIRED+=("python3")
    fi

    # 2. PyGObject (python3-gi)
    if python3 -c "import gi" 2>/dev/null; then
        info "PyGObject (python3-gi) found."
    else
        err "PyGObject (python3-gi) not found."
        MISSING_REQUIRED+=("gi")
    fi

    # 3. GTK 4
    if python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk" 2>/dev/null; then
        GTK_VER="$(python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk; print(f'{Gtk.MAJOR_VERSION}.{Gtk.MINOR_VERSION}.{Gtk.MICRO_VERSION}')" 2>/dev/null || echo '4.x')"
        info "GTK 4 (${GTK_VER}) found."
    else
        err "GTK 4 (gir1.2-gtk-4.0 / gtk4) not found."
        MISSING_REQUIRED+=("gtk4")
    fi

    # 4. Cairo
    if python3 -c "import cairo" 2>/dev/null; then
        info "Cairo (python3-cairo) found."
    else
        err "Cairo (python3-cairo / pycairo) not found."
        MISSING_REQUIRED+=("cairo")
    fi

    # 5. RapidFuzz (ultra fast fuzzy search matching)
    if python3 -c "import rapidfuzz" 2>/dev/null; then
        info "RapidFuzz found."
    else
        warn "RapidFuzz (python3-rapidfuzz) not found."
        MISSING_OPTIONAL+=("rapidfuzz")
    fi

    # 6. Libadwaita (Adaptive theme integration)
    if python3 -c "import gi; gi.require_version('Adw', '1'); from gi.repository import Adw" 2>/dev/null; then
        ADW_VER="$(python3 -c "import gi; gi.require_version('Adw', '1'); from gi.repository import Adw; print(Adw.VERSION_STRING)" 2>/dev/null || echo '1.x')"
        info "libadwaita (${ADW_VER}) found. Native GNOME integration active."
    else
        warn "libadwaita (gir1.2-adw-1) not installed."
        echo -e "      ${C_DIM}Note: Echo Search works across all desktop environments (Cinnamon, KDE, XFCE, MATE, WMs) via GTK 4.${C_RESET}"
    fi

    # 7. GTK4 Layer Shell (Wayland overlay)
    if python3 -c "import gi; gi.require_version('Gtk4LayerShell', '1.0'); from gi.repository import Gtk4LayerShell" 2>/dev/null; then
        info "gtk4-layer-shell found. Native Wayland overlay mode active."
    else
        warn "gtk4-layer-shell not installed (will run in standard GTK4 window mode on Wayland)."
        MISSING_OPTIONAL+=("layer_shell")
    fi

    # 8. GNOME Tracker 3 (Deep file search)
    if python3 -c "import gi; gi.require_version('Tracker', '3.0'); from gi.repository import Tracker" 2>/dev/null; then
        info "Tracker 3 found. Deep file indexing enabled."
    else
        warn "Tracker 3 not installed (file search will use instant cached filesystem scanner)."
    fi

    # 9. Requests (Currency & Weather)
    if python3 -c "import requests" 2>/dev/null; then
        info "Requests found. Online weather and currency rates active."
    else
        warn "python3-requests not installed."
        MISSING_OPTIONAL+=("requests")
    fi

    # 10. Pillow (Icon theme generator and previews)
    if python3 -c "import PIL" 2>/dev/null; then
        info "Pillow (PIL) found. Dynamic icon and theme generator active."
    else
        warn "python3-pil / Pillow not installed."
        MISSING_OPTIONAL+=("pillow")
    fi

    # 11. GtkSourceView 5 (Quick Look code syntax)
    if python3 -c "import gi; gi.require_version('GtkSource', '5'); from gi.repository import GtkSource" 2>/dev/null; then
        info "GtkSourceView 5 found. Quick Look syntax highlighting active."
    else
        warn "gtksourceview-5 not found. Quick Look will display text in clean monospace."
        MISSING_OPTIONAL+=("gtksource")
    fi

    # Handle Missing Required Dependencies
    if [ ${#MISSING_REQUIRED[@]} -gt 0 ]; then
        echo
        err "Required system packages are missing."
        suggest_and_install_packages true "${MISSING_REQUIRED[@]}"
    fi

    # Offer to install missing optional packages
    if [ ${#MISSING_OPTIONAL[@]} -gt 0 ]; then
        suggest_and_install_packages false "${MISSING_OPTIONAL[@]}"
    fi
}

# Map missing tokens to distro packages
get_distro_packages() {
    local target_pkg="$1"
    case "$PKG_MGR" in
        apt)
            case "$target_pkg" in
                python3)      echo "python3" ;;
                gi)           echo "python3-gi" ;;
                gtk4)         echo "gir1.2-gtk-4.0" ;;
                cairo)        echo "python3-gi-cairo python3-cairo" ;;
                rapidfuzz)    echo "python3-rapidfuzz" ;;
                adw)          echo "gir1.2-adw-1" ;;
                layer_shell)  echo "gir1.2-gtk4layershell-1.0 libgtk4-layer-shell0" ;;
                tracker)      echo "tracker gir1.2-tracker-3.0" ;;
                requests)     echo "python3-requests" ;;
                pillow)       echo "python3-pil" ;;
                gtksource)    echo "gir1.2-gtksource-5" ;;
            esac
            ;;
        dnf)
            case "$target_pkg" in
                python3)      echo "python3" ;;
                gi)           echo "python3-gobject" ;;
                gtk4)         echo "gtk4" ;;
                cairo)        echo "python3-cairo" ;;
                rapidfuzz)    echo "python3-rapidfuzz" ;;
                adw)          echo "libadwaita" ;;
                layer_shell)  echo "gtk4-layer-shell" ;;
                tracker)      echo "tracker3" ;;
                requests)     echo "python3-requests" ;;
                pillow)       echo "python3-pillow" ;;
                gtksource)    echo "gtksourceview5" ;;
            esac
            ;;
        pacman)
            case "$target_pkg" in
                python3)      echo "python" ;;
                gi)           echo "python-gobject" ;;
                gtk4)         echo "gtk4" ;;
                cairo)        echo "python-cairo" ;;
                rapidfuzz)    echo "python-rapidfuzz" ;;
                adw)          echo "libadwaita" ;;
                layer_shell)  echo "gtk4-layer-shell" ;;
                tracker)      echo "tracker3" ;;
                requests)     echo "python-requests" ;;
                pillow)       echo "python-pillow" ;;
                gtksource)    echo "gtksourceview5" ;;
            esac
            ;;
        zypper)
            case "$target_pkg" in
                python3)      echo "python3" ;;
                gi)           echo "python3-gobject" ;;
                gtk4)         echo "gtk4-schema" ;;
                cairo)        echo "python3-cairo" ;;
                rapidfuzz)    echo "python3-rapidfuzz" ;;
                adw)          echo "libadwaita-1-0" ;;
                layer_shell)  echo "gtk4-layer-shell" ;;
                tracker)      echo "tracker" ;;
                requests)     echo "python3-requests" ;;
                pillow)       echo "python3-Pillow" ;;
                gtksource)    echo "gtksourceview5" ;;
            esac
            ;;
        *)
            echo "$target_pkg"
            ;;
    esac
}

suggest_and_install_packages() {
    local is_required="$1"
    shift
    local missing_items=("$@")

    local install_list=""
    for m in "${missing_items[@]}"; do
        pkgs="$(get_distro_packages "$m")"
        install_list="$install_list $pkgs"
    done
    install_list="$(echo "$install_list" | xargs)"

    if [ -z "$install_list" ]; then
        return
    fi

    echo
    if [ "$is_required" = true ]; then
        echo -e "  ${C_BOLD}${C_RED}Required missing package(s):${C_RESET} ${C_WHITE}$install_list${C_RESET}"
    else
        echo -e "  ${C_BOLD}${C_SKY}Optional package(s) for enhanced features:${C_RESET} ${C_WHITE}$install_list${C_RESET}"
    fi

    echo -e "  Command: "
    case "$PKG_MGR" in
        apt)    echo "    sudo apt install -y $install_list" ;;
        dnf)    echo "    sudo dnf install -y $install_list" ;;
        pacman) echo "    sudo pacman -S --needed $install_list" ;;
        zypper) echo "    sudo zypper install -y $install_list" ;;
        *)      echo "    Install: $install_list" ;;
    esac
    echo

    if [ "$PKG_MGR" != "unknown" ]; then
        local prompt_text
        if [ "$is_required" = true ]; then
            prompt_text="  Install required dependencies automatically via sudo? [y/N]: "
        else
            prompt_text="  Install recommended optional packages now? [y/N]: "
        fi

        if [ "$AUTO_CONFIRM" = true ]; then
            if [ "$is_required" = true ]; then
                answer="y"
            else
                answer="n"
            fi
        else
            read -rp "$prompt_text" answer
        fi

        case "$answer" in
            [yY][eE][sS]|[yY])
                echo -e "  ${C_SKY}Running package manager...${C_RESET}"
                case "$PKG_MGR" in
                    apt)    sudo apt-get update && sudo apt-get install -y $install_list ;;
                    dnf)    sudo dnf install -y $install_list ;;
                    pacman) sudo pacman -S --needed --noconfirm $install_list ;;
                    zypper) sudo zypper install -y $install_list ;;
                esac
                echo -e "  ${C_GREEN}Dependencies installed. Continuing installation...${C_RESET}"
                return
                ;;
        esac
    fi

    if [ "$is_required" = true ]; then
        err "Required dependencies are not satisfied. Please install them and re-run install.sh."
        exit 1
    fi
}

# --- Show Target Paths ---
show_target_plan() {
    section "Installation Target Layout:"
    echo -e "  ${C_DIM}┌───────────────────────────────────────────────────────────────────────────┐${C_RESET}"
    echo -e "  ${C_DIM}│${C_RESET}  ${C_BOLD}Launcher Binary${C_RESET}  : ${C_WHITE}$INSTALL_DIR/echo-search${C_RESET}"
    echo -e "  ${C_DIM}│${C_RESET}  ${C_BOLD}Application Core${C_RESET} : ${C_WHITE}$APP_DIR${C_RESET}"
    echo -e "  ${C_DIM}│${C_RESET}  ${C_BOLD}Desktop Entry${C_RESET}    : ${C_WHITE}$DESKTOP_DIR/com.echo.search.desktop${C_RESET}"
    echo -e "  ${C_DIM}│${C_RESET}  ${C_BOLD}Application Icon${C_RESET} : ${C_WHITE}$ICON_DIR/com.echo.search.svg${C_RESET}"
    echo -e "  ${C_DIM}│${C_RESET}  ${C_BOLD}Icon Themes${C_RESET}      : ${C_WHITE}$THEMES_ICON_DIR${C_RESET}"
    echo -e "  ${C_DIM}│${C_RESET}  ${C_BOLD}User Config${C_RESET}      : ${C_WHITE}$CONFIG_DIR${C_RESET}"
    echo -e "  ${C_DIM}│${C_RESET}  ${C_BOLD}Search Cache${C_RESET}     : ${C_WHITE}$CACHE_DIR${C_RESET}"
    echo -e "  ${C_DIM}└───────────────────────────────────────────────────────────────────────────┘${C_RESET}"
    echo

    if [ "$AUTO_CONFIRM" = false ]; then
        read -rp "  Proceed with installation? [Y/n]: " answer
        case "$answer" in
            [nN][oO]|[nN])
                echo "Installation cancelled by user."
                exit 0
                ;;
        esac
    fi
}

# --- Installation Steps ---
perform_installation() {
    section "Installing Echo Search:"

    # 1. Directories
    mkdir -p "$INSTALL_DIR" "$DESKTOP_DIR" "$ICON_DIR" "$APP_DIR" "$CONFIG_DIR" "$CACHE_DIR" "$THEMES_ICON_DIR"
    info "Target directories initialized."

    # 2. Copy application files
    if command -v rsync > /dev/null 2>&1; then
        rsync -a \
            --exclude='.git' \
            --exclude='.gitignore' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='.pytest_cache' \
            --exclude='.ruff_cache' \
            --exclude='tests/' \
            --exclude='dist/' \
            --exclude='build/' \
            --exclude='packaging/' \
            --exclude='scratch/' \
            "$SCRIPT_DIR/" "$APP_DIR/"
    else
        for item in *.py *.css emoji.json echo-search assets modes providers; do
            src="$SCRIPT_DIR/$item"
            if [ -e "$src" ]; then
                cp -r "$src" "$APP_DIR/"
            fi
        done
    fi
    info "Application source files and assets deployed."

    # 3. Launcher
    cp "$SCRIPT_DIR/echo-search" "$INSTALL_DIR/echo-search"
    chmod +x "$INSTALL_DIR/echo-search"
    info "Command launcher installed to $INSTALL_DIR/echo-search"

    # 4. Desktop entry
    if [ -f "$SCRIPT_DIR/com.echo.search.desktop" ]; then
        cp "$SCRIPT_DIR/com.echo.search.desktop" "$DESKTOP_DIR/com.echo.search.desktop"
        info "Desktop application shortcut registered."
    elif [ -f "$SCRIPT_DIR/debian/echo-search.desktop" ]; then
        cp "$SCRIPT_DIR/debian/echo-search.desktop" "$DESKTOP_DIR/com.echo.search.desktop"
        info "Desktop application shortcut registered."
    else
        warn "Desktop entry template missing - skipping."
    fi

    # 5. Icons
    if [ -f "$SCRIPT_DIR/assets/icons/com.echo.search.svg" ]; then
        cp "$SCRIPT_DIR/assets/icons/com.echo.search.svg" "$ICON_DIR/com.echo.search.svg"
        chmod 644 "$ICON_DIR/com.echo.search.svg"
    fi

    for s in 48 64 128 256 512; do
        png_src="$SCRIPT_DIR/assets/icons/hicolor/${s}x${s}/apps/com.echo.search.png"
        if [ -f "$png_src" ]; then
            mkdir -p "$DATA_DIR/icons/hicolor/${s}x${s}/apps"
            cp "$png_src" "$DATA_DIR/icons/hicolor/${s}x${s}/apps/com.echo.search.png"
            chmod 644 "$DATA_DIR/icons/hicolor/${s}x${s}/apps/com.echo.search.png"
        fi
    done

    # Themes (Dark, Light, Aura)
    if [ -d "$SCRIPT_DIR/assets/icons/themes" ]; then
        mkdir -p "$DATA_DIR/icons/echo-search"
        cp -r "$SCRIPT_DIR/assets/icons/themes" "$DATA_DIR/icons/echo-search/"
    fi
    info "Application icons and themes (Dark, Light, Aura) installed."

    # 6. Update desktop & icon caches
    if command -v update-desktop-database > /dev/null 2>&1; then
        update-desktop-database "$DESKTOP_DIR" 2>/dev/null && info "Desktop database updated." || true
    fi
    if command -v gtk-update-icon-cache > /dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$DATA_DIR/icons/hicolor" 2>/dev/null && info "Icon cache updated." || true
    fi

    # 7. Configure Desktop Hotkeys
    configure_desktop_hotkeys
}

# --- Hotkey Configuration for Desktop Environments ---
configure_desktop_hotkeys() {
    section "Configuring Global Shortcut (Super + Space):"
    local de_lower
    de_lower="$(echo "${DESKTOP_ENV}" | tr '[:upper:]' '[:lower:]')"
    local hotkey_configured=false

    # 1. Cinnamon (Linux Mint)
    if [[ "$de_lower" == *"cinnamon"* ]]; then
        if command -v gsettings >/dev/null 2>&1; then
            gsettings set org.cinnamon.desktop.keybindings.wm switch-input-source "['']" 2>/dev/null || true
            gsettings set org.cinnamon.desktop.keybindings.wm switch-input-source-backward "['']" 2>/dev/null || true
            gsettings set org.cinnamon.desktop.keybindings.wm switch-to-workspace-left "['']" 2>/dev/null || true
            gsettings set org.cinnamon.desktop.keybindings.wm switch-to-workspace-down "['']" 2>/dev/null || true

            local custom_schema="org.cinnamon.desktop.keybindings.custom-keybinding"
            local main_schema="org.cinnamon.desktop.keybindings"
            local current_list
            current_list=$(gsettings get "$main_schema" custom-list 2>/dev/null || echo "@as []")

            local found_slot=""
            local found_path=""
            for i in {0..15}; do
                local slot_id="custom$i"
                local slot_path="/org/cinnamon/desktop/keybindings/custom-keybindings/custom$i/"
                local name
                name=$(gsettings get "${custom_schema}:${slot_path}" name 2>/dev/null || true)
                if [ -z "$name" ] || [ "$name" = "''" ] || [ "$name" = "@as []" ] || [[ "$name" == *"Echo"* ]]; then
                    found_slot="$slot_id"
                    found_path="$slot_path"
                    break
                fi
            done

            if [ -n "$found_slot" ]; then
                gsettings set "${custom_schema}:${found_path}" name 'Echo Search'
                gsettings set "${custom_schema}:${found_path}" command 'echo-search'
                gsettings set "${custom_schema}:${found_path}" binding "['<Super>space', '<Super>Cyrillic_em']"

                if [[ "$current_list" != *"$found_slot"* ]]; then
                    local new_list
                    if [ "$current_list" = "@as []" ] || [ -z "$current_list" ] || [ "$current_list" = "[]" ]; then
                        new_list="['$found_slot']"
                    else
                        new_list=$(echo "$current_list" | sed "s/]$/, '$found_slot']/")
                    fi
                    gsettings set "$main_schema" custom-list "['__dummy__']" 2>/dev/null || true
                    gsettings set "$main_schema" custom-list "$new_list" 2>/dev/null || true
                fi
                info "Shortcut Super + Space registered in Cinnamon (Linux Mint)!"
                hotkey_configured=true
            fi
        fi
    fi

    # 2. GNOME / Budgie / Unity
    if [ "$hotkey_configured" = false ] && ([[ "$de_lower" == *"gnome"* ]] || [[ "$de_lower" == *"budgie"* ]] || [[ "$de_lower" == *"unity"* ]]); then
        if command -v gsettings >/dev/null 2>&1; then
            local hotkey="<Super>space"
            local custom_key_schema="org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
            local media_keys="org.gnome.settings-daemon.plugins.media-keys"

            local found_slot=""
            for i in {0..15}; do
                local key_path="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom$i/"
                local existing_name
                existing_name=$(gsettings get "${custom_key_schema}:${key_path}" name 2>/dev/null || true)
                if [ -z "$existing_name" ] || [ "$existing_name" = "''" ] || [ "$existing_name" = "@as []" ] || [[ "$existing_name" == *"Echo"* ]]; then
                    found_slot="$key_path"
                    break
                fi
            done

            if [ -n "$found_slot" ]; then
                gsettings set "${custom_key_schema}:${found_slot}" name 'Echo Search'
                gsettings set "${custom_key_schema}:${found_slot}" command 'echo-search'
                gsettings set "${custom_key_schema}:${found_slot}" binding "$hotkey"

                local current_bindings
                current_bindings=$(gsettings get "$media_keys" custom-keybindings 2>/dev/null || echo "[]")
                if [[ "$current_bindings" != *"$found_slot"* ]]; then
                    local new_bindings
                    if [ "$current_bindings" = "@as []" ] || [ -z "$current_bindings" ] || [ "$current_bindings" = "[]" ]; then
                        new_bindings="['$found_slot']"
                    else
                        new_bindings=$(echo "$current_bindings" | sed "s/]$/, '$found_slot']/")
                    fi
                    gsettings set "$media_keys" custom-keybindings "$new_bindings" 2>/dev/null || true
                fi
                info "Shortcut Super + Space registered in GNOME / Media Keys!"
                hotkey_configured=true
            fi
        fi
    fi

    # 3. KDE Plasma 5/6
    if [[ "$de_lower" == *"kde"* ]] || [[ "$de_lower" == *"plasma"* ]]; then
        if command -v kwriteconfig6 >/dev/null 2>&1; then
            kwriteconfig6 --file kglobalshortcutsrc --group "com.echo.search.desktop" --key "_launch" "Meta+Space,none,Echo" 2>/dev/null || true
            qdbus org.kde.KGlobalAccel /KGlobalAccel reloadConfig >/dev/null 2>&1 || true
            info "Shortcut Meta + Space registered in KDE Plasma 6!"
            hotkey_configured=true
        elif command -v kwriteconfig5 >/dev/null 2>&1; then
            kwriteconfig5 --file kglobalshortcutsrc --group "com.echo.search.desktop" --key "_launch" "Meta+Space,none,Echo" 2>/dev/null || true
            qdbus org.kde.KGlobalAccel /KGlobalAccel reloadConfig >/dev/null 2>&1 || true
            info "Shortcut Meta + Space registered in KDE Plasma 5!"
            hotkey_configured=true
        fi
    fi

    # 4. XFCE
    if [[ "$de_lower" == *"xfce"* ]]; then
        if command -v xfconf-query >/dev/null 2>&1; then
            xfconf-query -c xfce4-keyboard-shortcuts -p "/commands/custom/<Super>space" -n -t string -s "echo-search" 2>/dev/null || \
            xfconf-query -c xfce4-keyboard-shortcuts -p "/commands/custom/<Super>space" -s "echo-search" 2>/dev/null || true
            info "Shortcut Super + Space registered in XFCE!"
            hotkey_configured=true
        fi
    fi

    # 5. MATE
    if [[ "$de_lower" == *"mate"* ]]; then
        if command -v gsettings >/dev/null 2>&1; then
            local mate_custom="org.mate.SettingsDaemon.plugins.media-keys.custom-keybinding"
            for i in {0..15}; do
                local mate_path="/org/mate/settings-daemon/plugins/media-keys/custom-keybindings/custom$i/"
                local name
                name=$(gsettings get "${mate_custom}:${mate_path}" name 2>/dev/null || true)
                if [ -z "$name" ] || [ "$name" = "''" ] || [[ "$name" == *"Echo"* ]]; then
                    gsettings set "${mate_custom}:${mate_path}" name 'Echo Search'
                    gsettings set "${mate_custom}:${mate_path}" action 'echo-search'
                    gsettings set "${mate_custom}:${mate_path}" binding '<Super>space'
                    info "Shortcut Super + Space registered in MATE!"
                    hotkey_configured=true
                    break
                fi
            done
        fi
    fi

    # 6. Hyprland / Sway Tips
    if [ -f "$HOME/.config/hypr/hyprland.conf" ]; then
        if ! grep -q "echo-search" "$HOME/.config/hypr/hyprland.conf"; then
            item "Hyprland: add to ~/.config/hypr/hyprland.conf: ${C_YELLOW}bind = SUPER, SPACE, exec, echo-search${C_RESET}"
        fi
    fi
    if [ -f "$HOME/.config/sway/config" ]; then
        if ! grep -q "echo-search" "$HOME/.config/sway/config"; then
            item "Sway/i3: add to ~/.config/sway/config: ${C_YELLOW}bindsym \$mod+space exec echo-search${C_RESET}"
        fi
    fi

    if [ "$hotkey_configured" = false ]; then
        warn "Auto-shortcut configuration could not determine specific DE handler."
        echo -e "      You can bind ${C_WHITE}Super + Space${C_RESET} to run '${C_SKY}echo-search${C_RESET}' in your system Keyboard Settings."
    fi
}

# --- Summary Card ---
print_summary() {
    local py_v gtk_v layer_mode adw_mode
    py_v="$(python3 --version 2>&1 | awk '{print $2}')"
    gtk_v="$(python3 -c "import gi; gi.require_version('Gtk','4.0'); from gi.repository import Gtk; print(f'{Gtk.MAJOR_VERSION}.{Gtk.MINOR_VERSION}.{Gtk.MICRO_VERSION}')" 2>/dev/null || echo '4.x')"

    if python3 -c "import gi; gi.require_version('Gtk4LayerShell','1.0')" 2>/dev/null; then
        layer_mode="${C_GREEN}Active${C_RESET} (Native Wayland Overlay)"
    else
        layer_mode="${C_DIM}Inactive (Standard GTK 4 Window)${C_RESET}"
    fi

    if python3 -c "import gi; gi.require_version('Adw','1')" 2>/dev/null; then
        adw_mode="Libadwaita (GNOME / Modern GTK 4)"
    else
        adw_mode="Pure GTK 4 (Cinnamon / KDE / XFCE / All DEs)"
    fi

    echo
    echo -e "  ${C_GREEN}${C_BOLD}========================================================================${C_RESET}"
    echo -e "  ${C_WHITE}${C_BOLD}                  Echo Search successfully installed!                  ${C_RESET}"
    echo -e "  ${C_GREEN}------------------------------------------------------------------------${C_RESET}"
    echo -e "  ${C_BOLD}Terminal Command${C_RESET} : ${C_SKY}echo-search${C_RESET}"
    echo -e "  ${C_BOLD}Global Shortcut ${C_RESET} : ${C_GOLD}Super + Space${C_RESET} (Win + Space)"
    echo -e "  ${C_BOLD}Application Menu${C_RESET} : Search for ${C_WHITE}\"Echo\"${C_RESET} in your launcher"
    echo -e "  ${C_BOLD}Layer Shell     ${C_RESET} : ${layer_mode}"
    echo -e "  ${C_BOLD}Active Runtime  ${C_RESET} : Python ${py_v} | GTK ${gtk_v} | ${adw_mode}"
    echo -e "  ${C_BOLD}Compatibility   ${C_RESET} : ${C_GREEN}Universal${C_RESET} (all Linux distros and desktop environments)"
    echo -e "  ${C_GREEN}========================================================================${C_RESET}"

    # Verify if ~/.local/bin is in PATH
    case ":$PATH:" in
        *":$INSTALL_DIR:"*) ;;
        *)
            echo
            warn "'$INSTALL_DIR' is not in your current PATH."
            echo -e "      To run '${C_WHITE}echo-search${C_RESET}' directly from any terminal, add this to ${C_WHITE}~/.bashrc${C_RESET} or ${C_WHITE}~/.zshrc${C_RESET}:"
            echo -e "      ${C_SKY}export PATH=\"\$HOME/.local/bin:\$PATH\"${C_RESET}"
            ;;
    esac
    echo
}

# --- Main Entrypoint ---
main() {
    print_banner
    detect_system
    print_system_info
    check_and_resolve_dependencies
    show_target_plan
    perform_installation
    print_summary
}

main "$@"
