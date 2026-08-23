#!/bin/bash
set -e

# ==========================================================
# 🌊 Echo (Spotlight Liquid Glass) - Установщик
# ==========================================================

GREEN="\033[1;32m"
BLUE="\033[1;34m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
RESET="\033[0m"

echo -e "${BLUE}==========================================${RESET}"
echo -e "${BLUE}   🌊 Установка Echo (Spotlight Glass)    ${RESET}"
echo -e "${BLUE}==========================================${RESET}"

# 1. Проверка прав sudo
if [ "$EUID" -ne 0 ] && ! command -v sudo >/dev/null 2>&1; then
    echo -e "${RED}❌ Для установки необходимы привилегии sudo.${RESET}"
    exit 1
fi

SUDO_CMD=""
if [ "$EUID" -ne 0 ]; then
    SUDO_CMD="sudo"
fi

# 2. Установка системных зависимостей через APT
echo -e "\n${YELLOW}[1/4] Проверка и установка системных зависимостей...${RESET}"
$SUDO_CMD apt update -qq || true
$SUDO_CMD apt install -y \
    python3 \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-4.0 \
    gir1.2-gtk4layershell-1.0 \
    libgtk4-layer-shell0 \
    gir1.2-gnomedesktop-4.0 \
    gir1.2-tracker-3.0 \
    python3-rapidfuzz \
    dpkg-dev

# 3. Сборка deb-пакета, если он еще не собран
echo -e "\n${YELLOW}[2/4] Подготовка deb-пакета...${RESET}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f "dist/echo-search_1.0.0_all.deb" ]; then
    echo "Сборка свежего .deb пакета..."
    ./build_deb.sh
fi

# 4. Установка пакета через APT (чтобы разрешить все зависимости нативно)
echo -e "\n${YELLOW}[3/4] Установка пакета в систему...${RESET}"
$SUDO_CMD apt install -y ./dist/echo-search_1.0.0_all.deb

# 5. Настройка глобального шортката Super+Space в GNOME
echo -e "\n${YELLOW}[4/4] Настройка глобального шортката Super + Space (GNOME)...${RESET}"
if command -v gsettings >/dev/null 2>&1; then
    HOTKEY="<Super>space"
    CUSTOM_KEY_SCHEMA="org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
    MEDIA_KEYS="org.gnome.settings-daemon.plugins.media-keys"

    # Ищем свободный или существующий слот
    FOUND_SLOT=""
    for i in {0..15}; do
        KEY_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom$i/"
        EXISTING_NAME=$(gsettings get "${CUSTOM_KEY_SCHEMA}:${KEY_PATH}" name 2>/dev/null || true)
        
        if [ -z "$EXISTING_NAME" ] || [ "$EXISTING_NAME" = "''" ] || [ "$EXISTING_NAME" = "@as []" ] || [[ "$EXISTING_NAME" == *"Echo"* ]]; then
            FOUND_SLOT="$KEY_PATH"
            break
        fi
    done

    if [ -n "$FOUND_SLOT" ]; then
        gsettings set "${CUSTOM_KEY_SCHEMA}:${FOUND_SLOT}" name 'Echo'
        gsettings set "${CUSTOM_KEY_SCHEMA}:${FOUND_SLOT}" command 'echo-search'
        gsettings set "${CUSTOM_KEY_SCHEMA}:${FOUND_SLOT}" binding "$HOTKEY"

        # Обновляем список активных кастомных биндингов
        CURRENT_BINDINGS=$(gsettings get "$MEDIA_KEYS" custom-keybindings)
        if [[ "$CURRENT_BINDINGS" != *"$FOUND_SLOT"* ]]; then
            if [ "$CURRENT_BINDINGS" = "@as []" ] || [ -z "$CURRENT_BINDINGS" ]; then
                NEW_BINDINGS="['$FOUND_SLOT']"
            else
                NEW_BINDINGS=$(echo "$CURRENT_BINDINGS" | sed "s/]$/, '$FOUND_SLOT']/")
            fi
            gsettings set "$MEDIA_KEYS" custom-keybindings "$NEW_BINDINGS"
        fi
        echo -e "${GREEN}✓ Хоткей ${HOTKEY} успешно зарегистрирован!${RESET}"
    else
        echo -e "${YELLOW}ℹ Не удалось автоматически выделить слот для хоткея. Вы можете задать его в Настройках GNOME -> Комбинации клавиш.${RESET}"
    fi
else
    echo -e "${YELLOW}ℹ gsettings не найден. Настройте команду 'echo-search' в настройках вашей рабочей среды.${RESET}"
fi

echo -e "\n${GREEN}==========================================${RESET}"
echo -e "${GREEN}✨ Echo успешно установлен и готов к работе!${RESET}"
echo -e "• Запуск по горячей клавише: ${BLUE}Super + Space${RESET} (Win + Пробел)"
echo -e "• Запуск из терминала:       ${BLUE}echo-search${RESET}"
echo -e "• Запуск из меню приложений: ${BLUE}Echo${RESET}"
echo -e "• Удаление:                  ${YELLOW}./uninstall.sh${RESET} или ${YELLOW}sudo apt remove echo-search${RESET}"
echo -e "${GREEN}==========================================${RESET}"
