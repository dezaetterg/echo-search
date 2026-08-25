#!/bin/bash
set -e

# ==========================================================
# 🌊 Echo Search - Universal Linux Installer
# Multi-Distribution: Debian/Ubuntu, Arch, Fedora, openSUSE
# Multi-DE: GNOME, KDE Plasma, XFCE, Cinnamon, Hyprland, Sway
# ==========================================================

GREEN="\033[1;32m"
BLUE="\033[1;34m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
RED="\033[1;31m"
RESET="\033[0m"

echo -e "${BLUE}====================================================${RESET}"
echo -e "${BLUE}        🌊 Universal Echo Search Installer          ${RESET}"
echo -e "${BLUE}====================================================${RESET}"

# 1. Проверка прав sudo
SUDO_CMD=""
if [ "$EUID" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
        SUDO_CMD="sudo"
    else
        echo -e "${RED}❌ Ошибка: Для установки требуются права root или sudo.${RESET}"
        exit 1
    fi
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 2. Определение дистрибутива и пакетного менеджера
DISTRO="unknown"
PKG_MGR="unknown"

if command -v apt-get >/dev/null 2>&1; then
    DISTRO="debian"
    PKG_MGR="apt"
elif command -v pacman >/dev/null 2>&1; then
    DISTRO="arch"
    PKG_MGR="pacman"
elif command -v dnf >/dev/null 2>&1; then
    DISTRO="fedora"
    PKG_MGR="dnf"
elif command -v zypper >/dev/null 2>&1; then
    DISTRO="opensuse"
    PKG_MGR="zypper"
fi

echo -e "\n${CYAN}[1/4] Обнаружен пакетный менеджер: ${YELLOW}${PKG_MGR}${RESET}"

# 3. Установка системных зависимостей
echo -e "${YELLOW}Установка системных зависимостей...${RESET}"

case "$PKG_MGR" in
    apt)
        # Включение universe на Ubuntu/Mint если репозиторий был отключен
        if command -v add-apt-repository >/dev/null 2>&1; then
            $SUDO_CMD add-apt-repository -y universe >/dev/null 2>&1 || true
        fi
        $SUDO_CMD apt-get update -qq || true

        # Обязательные базовые пакеты
        $SUDO_CMD apt-get install -y python3 python3-gi python3-gi-cairo gir1.2-gtk-4.0 dpkg-dev || true
        
        # GnomeDesktop (для превью)
        $SUDO_CMD apt-get install -y gir1.2-gnomedesktop-4.0 2>/dev/null || \
        $SUDO_CMD apt-get install -y libgnome-desktop-4-2 2>/dev/null || \
        $SUDO_CMD apt-get install -y gir1.2-gnomedesktop-3.0 2>/dev/null || true

        # Установка rapidfuzz (через apt или pip)
        if ! $SUDO_CMD apt-get install -y python3-rapidfuzz 2>/dev/null; then
            if command -v pip3 >/dev/null 2>&1 || command -v pip >/dev/null 2>&1; then
                pip install --break-system-packages rapidfuzz 2>/dev/null || pip install rapidfuzz 2>/dev/null || true
            fi
        fi

        # Опциональные расширения (только если они есть в репозиториях вашей системы)
        $SUDO_CMD apt-get install -y gir1.2-tracker-3.0 2>/dev/null || true
        $SUDO_CMD apt-get install -y gir1.2-gtk4layershell-1.0 libgtk4-layer-shell0 2>/dev/null || true
        ;;
    pacman)
        $SUDO_CMD pacman -Sy --noconfirm --needed \
            python \
            python-gobject \
            cairo \
            gtk4 \
            gtk4-layer-shell \
            gnome-desktop-4 \
            tracker3 \
            python-rapidfuzz
        ;;
    dnf)
        $SUDO_CMD dnf install -y \
            python3 \
            python3-gobject \
            gtk4 \
            gtk4-layer-shell \
            gnome-desktop4 \
            tracker3 \
            python3-rapidfuzz
        ;;
    zypper)
        $SUDO_CMD zypper --non-interactive install \
            python3 \
            python3-gobject \
            gtk4-schema \
            typelib-1_0-Gtk-4_0 \
            typelib-1_0-Gtk4LayerShell-1_0 \
            libgnome-desktop-4-2 \
            tracker \
            python3-rapidfuzz
        ;;
    *)
        echo -e "${YELLOW}⚠ Неизвестный пакетный менеджер. Убедитесь, что установлены: GTK4, Gtk4LayerShell, Python 3, PyGObject, rapidfuzz.${RESET}"
        ;;
esac

# 4. Остановка старых процессов и очистка кэшей
echo -e "\n${YELLOW}[2/4] Установка Echo Search и обновление компонентов...${RESET}"
pkill -9 -f "python.*echo-search" 2>/dev/null || true
pkill -9 -f "python.*spotlight" 2>/dev/null || true

# Очистка устаревших локальных копий в ~/.local, если запущен от имени пользователя
if [ -n "$SUDO_USER" ] && [ "$SUDO_USER" != "root" ]; then
    user_home=$(eval echo "~$SUDO_USER")
    rm -rf "$user_home/.local/share/echo-search/__pycache__" "$user_home/.local/share/spotlight-glass" 2>/dev/null || true
    # Синхронизируем и в ~/.local/share/echo-search, если пользователь запускает из local bin
    if [ -d "$user_home/.local/share/echo-search" ]; then
        sudo -u "$SUDO_USER" cp *.py style.css emoji.json "$user_home/.local/share/echo-search/" 2>/dev/null || true
        sudo -u "$SUDO_USER" cp -r modes providers "$user_home/.local/share/echo-search/" 2>/dev/null || true
    fi
fi

if [ "$PKG_MGR" = "apt" ]; then
    # Если на Debian/Ubuntu - собираем и ставим чистый .deb пакет
    ./build_deb.sh
    $SUDO_CMD apt-get install -y --no-install-recommends ./dist/echo-search_latest.deb || $SUDO_CMD dpkg -i ./dist/echo-search_latest.deb
else
    # Универсальная прямая установка FHS
    $SUDO_CMD mkdir -p /usr/lib/echo-search/modes /usr/lib/echo-search/providers
    $SUDO_CMD mkdir -p /usr/share/echo-search
    $SUDO_CMD mkdir -p /usr/share/applications
    $SUDO_CMD mkdir -p /usr/share/icons/hicolor/scalable/apps
    for s in 48 64 128 256 512; do
        $SUDO_CMD mkdir -p "/usr/share/icons/hicolor/${s}x${s}/apps"
    done

    $SUDO_CMD cp *.py style.css emoji.json /usr/lib/echo-search/
    $SUDO_CMD cp modes/*.py /usr/lib/echo-search/modes/
    $SUDO_CMD cp providers/*.py /usr/lib/echo-search/providers/
    $SUDO_CMD cp style.css emoji.json /usr/share/echo-search/

    # Wrapper
    $SUDO_CMD bash -c 'cat << "EOF" > /usr/bin/echo-search
#!/bin/sh
exec python3 /usr/lib/echo-search/main.py "$@"
EOF'
    $SUDO_CMD chmod 755 /usr/bin/echo-search

    # Desktop & Icon
    $SUDO_CMD cp debian/echo-search.desktop /usr/share/applications/com.echo.search.desktop
    $SUDO_CMD cp assets/icons/com.echo.search.svg /usr/share/icons/hicolor/scalable/apps/com.echo.search.svg
    for s in 48 64 128 256 512; do
        if [ -f "assets/icons/hicolor/${s}x${s}/apps/com.echo.search.png" ]; then
            $SUDO_CMD cp "assets/icons/hicolor/${s}x${s}/apps/com.echo.search.png" "/usr/share/icons/hicolor/${s}x${s}/apps/com.echo.search.png"
        fi
    done

    # Обновление системных кэшей
    command -v update-desktop-database >/dev/null 2>&1 && $SUDO_CMD update-desktop-database -q || true
    command -v gtk-update-icon-cache >/dev/null 2>&1 && $SUDO_CMD gtk-update-icon-cache -qtf /usr/share/icons/hicolor || true
fi

# 5. Определение Desktop Environment и настройка горячей клавиши
echo -e "
${YELLOW}[3/4] Настройка глобального хоткея Super + Space...${RESET}"

# Функция выполнения от имени реального пользователя десктопа (даже если скрипт запущен через sudo)
run_desktop_cmd() {
    if [ -n "$SUDO_USER" ] && [ "$SUDO_USER" != "root" ]; then
        local user_uid
        user_uid=$(id -u "$SUDO_USER" 2>/dev/null || echo "1000")
        local dbus_bus="unix:path=/run/user/${user_uid}/bus"
        sudo -u "$SUDO_USER" DBUS_SESSION_BUS_ADDRESS="$dbus_bus" "$@" 2>/dev/null ||         sudo -u "$SUDO_USER" "$@" 2>/dev/null ||         "$@" 2>/dev/null || true
    else
        "$@" 2>/dev/null || true
    fi
}

DE="${XDG_CURRENT_DESKTOP:-$DESKTOP_SESSION}"
DE_LOWER=$(echo "$DE" | tr '[:upper:]' '[:lower:]')
HOTKEY_CONFIGURED=false

# Cinnamon (Linux Mint)
if [[ "$DE_LOWER" == *"cinnamon"* ]] || [[ "$XDG_CURRENT_DESKTOP" == *"X-Cinnamon"* ]]; then
    if command -v gsettings >/dev/null 2>&1; then
        # Отключаем конфликтующие системные хоткеи Cinnamon на Super+Space
        run_desktop_cmd gsettings set org.cinnamon.desktop.keybindings.wm switch-input-source "['']"
        run_desktop_cmd gsettings set org.cinnamon.desktop.keybindings.wm switch-input-source-backward "['']"
        run_desktop_cmd gsettings set org.cinnamon.desktop.keybindings.wm switch-to-workspace-left "['']"
        run_desktop_cmd gsettings set org.cinnamon.desktop.keybindings.wm switch-to-workspace-down "['']"

        CUSTOM_SCHEMA="org.cinnamon.desktop.keybindings.custom-keybinding"
        MAIN_SCHEMA="org.cinnamon.desktop.keybindings"

        CURRENT_LIST=$(run_desktop_cmd gsettings get "$MAIN_SCHEMA" custom-list 2>/dev/null || echo "@as []")
        
        FOUND_SLOT=""
        FOUND_PATH=""
        for i in {0..15}; do
            SLOT_ID="custom$i"
            SLOT_PATH="/org/cinnamon/desktop/keybindings/custom-keybindings/custom$i/"
            NAME=$(run_desktop_cmd gsettings get "${CUSTOM_SCHEMA}:${SLOT_PATH}" name 2>/dev/null || true)
            if [ -z "$NAME" ] || [ "$NAME" = "''" ] || [ "$NAME" = "@as []" ] || [[ "$NAME" == *"Echo"* ]]; then
                FOUND_SLOT="$SLOT_ID"
                FOUND_PATH="$SLOT_PATH"
                break
            fi
        done

        if [ -n "$FOUND_SLOT" ]; then
            run_desktop_cmd gsettings set "${CUSTOM_SCHEMA}:${FOUND_PATH}" name 'Echo Search'
            run_desktop_cmd gsettings set "${CUSTOM_SCHEMA}:${FOUND_PATH}" command 'echo-search'
            run_desktop_cmd gsettings set "${CUSTOM_SCHEMA}:${FOUND_PATH}" binding "['<Super>space', '<Super>Cyrillic_em']"

            if [[ "$CURRENT_LIST" != *"$FOUND_SLOT"* ]]; then
                if [ "$CURRENT_LIST" = "@as []" ] || [ -z "$CURRENT_LIST" ] || [ "$CURRENT_LIST" = "[]" ]; then
                    NEW_LIST="['$FOUND_SLOT']"
                else
                    NEW_LIST=$(echo "$CURRENT_LIST" | sed "s/]$/, '$FOUND_SLOT']/")
                fi
                run_desktop_cmd gsettings set "$MAIN_SCHEMA" custom-list "['__dummy__']"
            run_desktop_cmd gsettings set "$MAIN_SCHEMA" custom-list "$NEW_LIST"
            fi
            echo -e "${GREEN}✓ Хоткей Super + Space зарегистрирован в Cinnamon (Linux Mint)!${RESET}"
            HOTKEY_CONFIGURED=true
        fi
    fi
fi

# GNOME / Budgie / Unity
if [ "$HOTKEY_CONFIGURED" = false ] && ([[ "$DE_LOWER" == *"gnome"* ]] || [[ "$DE_LOWER" == *"budgie"* ]] || [[ "$DE_LOWER" == *"unity"* ]]); then
    if command -v gsettings >/dev/null 2>&1; then
        HOTKEY="<Super>space"
        CUSTOM_KEY_SCHEMA="org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
        MEDIA_KEYS="org.gnome.settings-daemon.plugins.media-keys"

        FOUND_SLOT=""
        for i in {0..15}; do
            KEY_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom$i/"
            EXISTING_NAME=$(run_desktop_cmd gsettings get "${CUSTOM_KEY_SCHEMA}:${KEY_PATH}" name 2>/dev/null || true)
            if [ -z "$EXISTING_NAME" ] || [ "$EXISTING_NAME" = "''" ] || [ "$EXISTING_NAME" = "@as []" ] || [[ "$EXISTING_NAME" == *"Echo"* ]]; then
                FOUND_SLOT="$KEY_PATH"
                break
            fi
        done

        if [ -n "$FOUND_SLOT" ]; then
            run_desktop_cmd gsettings set "${CUSTOM_KEY_SCHEMA}:${FOUND_SLOT}" name 'Echo Search'
            run_desktop_cmd gsettings set "${CUSTOM_KEY_SCHEMA}:${FOUND_SLOT}" command 'echo-search'
            run_desktop_cmd gsettings set "${CUSTOM_KEY_SCHEMA}:${FOUND_SLOT}" binding "$HOTKEY"

            CURRENT_BINDINGS=$(run_desktop_cmd gsettings get "$MEDIA_KEYS" custom-keybindings 2>/dev/null || echo "[]")
            if [[ "$CURRENT_BINDINGS" != *"$FOUND_SLOT"* ]]; then
                if [ "$CURRENT_BINDINGS" = "@as []" ] || [ -z "$CURRENT_BINDINGS" ] || [ "$CURRENT_BINDINGS" = "[]" ]; then
                    NEW_BINDINGS="['$FOUND_SLOT']"
                else
                    NEW_BINDINGS=$(echo "$CURRENT_BINDINGS" | sed "s/]$/, '$FOUND_SLOT']/")
                fi
                run_desktop_cmd gsettings set "$MEDIA_KEYS" custom-keybindings "$NEW_BINDINGS"
            fi
            echo -e "${GREEN}✓ Хоткей ${HOTKEY} зарегистрирован в GNOME!${RESET}"
            HOTKEY_CONFIGURED=true
        fi
    fi
fi

# KDE Plasma 5/6
if [[ "$DE_LOWER" == *"kde"* ]] || [[ "$DE_LOWER" == *"plasma"* ]]; then
    if command -v kwriteconfig6 >/dev/null 2>&1; then
        run_desktop_cmd kwriteconfig6 --file kglobalshortcutsrc --group "com.echo.search.desktop" --key "_launch" "Meta+Space,none,Echo"
        run_desktop_cmd qdbus org.kde.KGlobalAccel /KGlobalAccel reloadConfig >/dev/null 2>&1 || true
        echo -e "${GREEN}✓ Хоткей Meta+Space зарегистрирован в KDE Plasma 6!${RESET}"
        HOTKEY_CONFIGURED=true
    elif command -v kwriteconfig5 >/dev/null 2>&1; then
        run_desktop_cmd kwriteconfig5 --file kglobalshortcutsrc --group "com.echo.search.desktop" --key "_launch" "Meta+Space,none,Echo"
        run_desktop_cmd qdbus org.kde.KGlobalAccel /KGlobalAccel reloadConfig >/dev/null 2>&1 || true
        echo -e "${GREEN}✓ Хоткей Meta+Space зарегистрирован в KDE Plasma 5!${RESET}"
        HOTKEY_CONFIGURED=true
    fi
fi

# XFCE
if [[ "$DE_LOWER" == *"xfce"* ]]; then
    if command -v xfconf-query >/dev/null 2>&1; then
        run_desktop_cmd xfconf-query -c xfce4-keyboard-shortcuts -p "/commands/custom/<Super>space" -n -t string -s "echo-search" 2>/dev/null ||         run_desktop_cmd xfconf-query -c xfce4-keyboard-shortcuts -p "/commands/custom/<Super>space" -s "echo-search"
        echo -e "${GREEN}✓ Хоткей Super+Space зарегистрирован в XFCE!${RESET}"
        HOTKEY_CONFIGURED=true
    fi
fi

# MATE
if [[ "$DE_LOWER" == *"mate"* ]]; then
    if command -v gsettings >/dev/null 2>&1; then
        MATE_CUSTOM="org.mate.SettingsDaemon.plugins.media-keys.custom-keybinding"
        for i in {0..15}; do
            MATE_PATH="/org/mate/settings-daemon/plugins/media-keys/custom-keybindings/custom$i/"
            NAME=$(run_desktop_cmd gsettings get "${MATE_CUSTOM}:${MATE_PATH}" name 2>/dev/null || true)
            if [ -z "$NAME" ] || [ "$NAME" = "''" ] || [[ "$NAME" == *"Echo"* ]]; then
                run_desktop_cmd gsettings set "${MATE_CUSTOM}:${MATE_PATH}" name 'Echo Search'
                run_desktop_cmd gsettings set "${MATE_CUSTOM}:${MATE_PATH}" action 'echo-search'
                run_desktop_cmd gsettings set "${MATE_CUSTOM}:${MATE_PATH}" binding '<Super>space'
                echo -e "${GREEN}✓ Хоткей Super+Space зарегистрирован в MATE!${RESET}"
                HOTKEY_CONFIGURED=true
                break
            fi
        done
    fi
fi

# Hyprland
if [ -f "$HOME/.config/hypr/hyprland.conf" ]; then
    if ! grep -q "echo-search" "$HOME/.config/hypr/hyprland.conf"; then
        echo -e "${CYAN}ℹ Для Hyprland добавьте в ~/.config/hypr/hyprland.conf:${RESET}"
        echo -e "  ${YELLOW}bind = SUPER, SPACE, exec, echo-search${RESET}"
    fi
fi

# Sway / i3
if [ -f "$HOME/.config/sway/config" ]; then
    if ! grep -q "echo-search" "$HOME/.config/sway/config"; then
        echo -e "${CYAN}ℹ Для Sway добавьте в ~/.config/sway/config:${RESET}"
        echo -e "  ${YELLOW}bindsym \$mod+space exec echo-search${RESET}"
    fi
fi

# 6. Финал
echo -e "\n${GREEN}====================================================${RESET}"
echo -e "${GREEN}✨ Echo Search успешно установлен и готов к работе!${RESET}"
echo -e "• Команда вызова:            ${BLUE}echo-search${RESET}"
echo -e "• Языки интерфейса:          ${CYAN}13 языков (автоопределение RU/EN/ES/DE/FR/ZH/JA/IT/PT/TR/UK/KK/AR)${RESET}"
echo -e "• Горячая клавиша:           ${BLUE}Super + Space${RESET} (Win + Пробел)"
echo -e "• Удаление из системы:       ${YELLOW}./uninstall.sh${RESET}"
echo -e "${GREEN}====================================================${RESET}"
