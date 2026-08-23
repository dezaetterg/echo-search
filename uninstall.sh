#!/bin/bash
set -e

# ==========================================================
# 🌊 Echo (Spotlight Liquid Glass) - Скрипт удаления
# ==========================================================

GREEN="\033[1;32m"
BLUE="\033[1;34m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
RESET="\033[0m"

echo -e "${YELLOW}==========================================${RESET}"
echo -e "${YELLOW}       Удаление Echo (Spotlight Glass)    ${RESET}"
echo -e "${YELLOW}==========================================${RESET}"

SUDO_CMD=""
if [ "$EUID" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
        SUDO_CMD="sudo"
    else
        echo -e "${RED}❌ Для удаления необходимы привилегии sudo.${RESET}"
        exit 1
    fi
fi

# 1. Удаление пакета
echo -e "${BLUE}[1/2] Удаление системного пакета echo-search...${RESET}"
$SUDO_CMD apt remove -y echo-search || true

# 2. Удаление шортката из GNOME
echo -e "${BLUE}[2/2] Очистка сочетаний клавиш...${RESET}"
if command -v gsettings >/dev/null 2>&1; then
    CUSTOM_KEY_SCHEMA="org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
    MEDIA_KEYS="org.gnome.settings-daemon.plugins.media-keys"

    for i in {0..15}; do
        KEY_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom$i/"
        EXISTING_NAME=$(gsettings get "${CUSTOM_KEY_SCHEMA}:${KEY_PATH}" name 2>/dev/null || true)
        if [[ "$EXISTING_NAME" == *"Echo"* ]]; then
            gsettings reset-recursively "${CUSTOM_KEY_SCHEMA}:${KEY_PATH}" || true
        fi
    done
fi

echo -e "\n${GREEN}==========================================${RESET}"
echo -e "${GREEN}✓ Echo успешно удален из системы.${RESET}"
echo -e "Пользовательские настройки сохранены в ~/.config/echo-search."
echo -e "Если вы хотите удалить и их, выполните: rm -rf ~/.config/echo-search ~/.local/share/echo"
echo -e "${GREEN}==========================================${RESET}"
