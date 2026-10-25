#!/bin/bash
# Echo Search Uninstaller
set -euo pipefail

INSTALL_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}"
DESKTOP_DIR="$DATA_DIR/applications"
ICON_DIR="$DATA_DIR/icons/hicolor/scalable/apps"
THEMES_ICON_DIR="$DATA_DIR/icons/echo-search"
APP_DIR="$DATA_DIR/echo-search"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/echo-search"
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/echo-search"

BOLD='\033[1m'
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BOLD}Echo Search Uninstaller${NC}"
echo
echo "The following will be removed:"
echo "  $INSTALL_DIR/echo-search"
echo "  $DESKTOP_DIR/com.echo.search.desktop"
echo "  $ICON_DIR/com.echo.search.svg"
echo "  $DATA_DIR/icons/hicolor/*/apps/com.echo.search.png"
echo "  $THEMES_ICON_DIR"
echo "  $APP_DIR/"
echo
echo "The following will be KEPT (your settings, custom styles, and search history):"
echo "  $CONFIG_DIR"
echo "  $CACHE_DIR"
echo

AUTO_CONFIRM=false
for arg in "$@"; do
    case "$arg" in
        -y|--yes)
            AUTO_CONFIRM=true
            ;;
    esac
done

if [ "$AUTO_CONFIRM" = false ]; then
    read -rp "Proceed with uninstall? [y/N] " answer
    case "$answer" in
        [yY][eE][sS]|[yY]) ;;
        *)
            echo "Uninstall cancelled."
            exit 0
            ;;
    esac
fi

echo "Removing files..."
rm -f  "$INSTALL_DIR/echo-search"
rm -f  "$DESKTOP_DIR/com.echo.search.desktop"
rm -f  "$ICON_DIR/com.echo.search.svg"
for s in 48 64 128 256 512; do
    rm -f "$DATA_DIR/icons/hicolor/${s}x${s}/apps/com.echo.search.png"
done
rm -rf "$THEMES_ICON_DIR"
rm -rf "$APP_DIR"

if command -v update-desktop-database > /dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache > /dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$DATA_DIR/icons/hicolor" 2>/dev/null || true
fi

echo
echo -e "${GREEN}Echo Search has been uninstalled.${NC}"
echo
echo "Your configuration and history are preserved at: $CONFIG_DIR"
echo "To also remove them, run:"
echo -e "  ${RED}rm -rf $CONFIG_DIR $CACHE_DIR${NC}"
