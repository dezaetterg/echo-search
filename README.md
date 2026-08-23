<div align="center">

# 🌊 Echo — Spotlight Liquid Glass Launcher
### Современный быстрый лаунчер в стиле Liquid Glass для Linux
#### Поддержка 13 языков • Мультидистрибутивность (Debian, Arch, Fedora, openSUSE) • Поддержка GNOME, KDE, XFCE, Hyprland, Sway

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platforms](https://img.shields.io/badge/Linux-Ubuntu%20%7C%20Debian%20%7C%20Arch%20%7C%20Fedora%20%7C%20openSUSE-informational.svg)](https://www.linux.org/)
[![DE Support](https://img.shields.io/badge/DE-GNOME%20%7C%20KDE%20%7C%20XFCE%20%7C%20Hyprland%20%7C%20Sway-purple.svg)](https://www.gtk.org/)
[![Languages](https://img.shields.io/badge/i18n-13%20Languages-green.svg)](#-локализация-13-языков)
[![GTK4](https://img.shields.io/badge/GUI-GTK%204%20%2B%20LayerShell-green.svg)](https://www.gtk.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Debian Package](https://img.shields.io/badge/Package-.deb-red.svg)](https://github.com/demid/spotlight_liquidglass/releases)
[![Arch AUR](https://img.shields.io/badge/Package-PKGBUILD%20(AUR)-blue.svg)](PKGBUILD)
[![Fedora RPM](https://img.shields.io/badge/Package-.rpm-orange.svg)](echo-search.spec)

<p align="center">
  <b>Умный поиск приложений • Полнотекстовый поиск файлов (Tracker 3) • Буфер обмена • Эмодзи • Калькулятор и конвертер • Инспектор превью</b>
</p>

</div>

---

## ✨ Возможности

- 🪟 **Liquid Glass & macOS Эстетика**: Полупрозрачные акриловые слои, динамический `backdrop-filter` блюр, светлая и темная темы, плавные Revealer-анимации.
- 🌍 **Полноценная локализация**: Поддержка 13 мировых языков с автоопределением из системной локали (`ru`, `en`, `es`, `de`, `fr`, `zh`, `ja`, `it`, `pt`, `tr`, `uk`, `kk`, `ar`).
- 🐧 **Кросс-дистрибутивность и мульти-DE**: Работает в Wayland и X11 на GNOME, KDE Plasma, XFCE, Cinnamon, Hyprland, Sway.
- 🚀 **Мгновенный поиск приложений**: Нечеткий (Fuzzy) поиск с поддержкой русской транслитерации и фонетики (находит "стим" -> Steam, "телеграм" -> Telegram).
- 📁 **Полнотекстовый поиск файлов**: Глубокая интеграция с GNOME Tracker 3 SPARQL и локальный кэш файловой системы для моментального отклика.
- 📋 **Менеджер буфера обмена**: История скопированного текста и изображений с предпросмотром и быстрым копированием.
- 😀 **Каталог Emoji и специальных символов**: Удобный поиск и вставка эмодзи, математических знаков и типографики.
- 🧮 **Встроенный калькулятор и конвертер**: Вычисление математических выражений (`sqrt`, `sin`, `log`, степени) и конвертация единиц измерения на лету.
- 🔍 **Инспектор предпросмотра**: Детальные карточки с метаданными, миниатюрами файлов, категориями и быстрыми действиями.
- ⚡ **Нативный Wayland Overlay & X11 Fallback**: Работает поверх всех окон благодаря **gtk4-layer-shell**, а также поддерживает X11 сессии.

---

## 🌐 Локализация (13 Языков)

Вся локализация вынесена в модуль [`i18n.py`](i18n.py). Язык определяется автоматически при запуске или задается в настройках:

| Код | Язык | Native Name |
| :---: | :--- | :--- |
| **`ru`** | Русский | Русский |
| **`en`** | English | English |
| **`es`** | Spanish | Español |
| **`de`** | German | Deutsch |
| **`fr`** | French | Français |
| **`zh`** | Chinese (Simplified) | 简体中文 |
| **`ja`** | Japanese | 日本語 |
| **`it`** | Italian | Italiano |
| **`pt`** | Portuguese | Português |
| **`tr`** | Turkish | Türkçe |
| **`uk`** | Ukrainian | Українська |
| **`kk`** | Kazakh | Қазақша |
| **`ar`** | Arabic | العربية |

---

## 📦 Установка на различные Linux дистрибутивы

### 1. Универсальный автоустановщик (Рекомендуется)
Автоматически определяет дистрибутив (`apt`, `pacman`, `dnf`, `zypper`), ставит зависимости, собирает/устанавливает пакет и настраивает горячую клавишу для вашей среды рабочего стола:

```bash
git clone https://github.com/demid/spotlight_liquidglass.git
cd spotlight_liquidglass
chmod +x install.sh
./install.sh
```

---

### 2. Ubuntu / Debian / Linux Mint / Pop!_OS (.deb)

Скачайте `.deb` файл из [Releases](https://github.com/demid/spotlight_liquidglass/releases) или соберите локально:

```bash
# Сборка пакета:
./build_deb.sh

# Установка:
sudo apt install ./dist/echo-search_1.0.0_all.deb
```

---

### 3. Arch Linux / Manjaro / EndeavourOS (PKGBUILD)

Сборка и установка через `makepkg`:

```bash
# Установка зависимостей и сборка пакета Arch
makepkg -si
```

---

### 4. Fedora / RHEL / CentOS / Rocky Linux / openSUSE (.rpm)

Сборка `.rpm` пакета с использованием `build_rpm.sh`:

```bash
# Сборка RPM пакета
./build_rpm.sh

# Установка в Fedora/RHEL:
sudo dnf install ./dist/rpm/echo-search-1.0.0-1.*.noarch.rpm

# Установка в openSUSE:
sudo zypper install ./dist/rpm/echo-search-1.0.0-1.*.noarch.rpm
```

---

## 🖥 Поддержка Desktop Environments & Настройка хоткеев

Echo Search автоматически регистрирует горячую клавишу **`Super + Space`** (Win + Пробел) для большинства популярных DE:

- **GNOME / Cinnamon**: Автоматическая регистрация через `gsettings`.
- **KDE Plasma 5 / 6**: Автоматическая регистрация через `kglobalshortcutsrc` (`Meta+Space`).
- **XFCE**: Автоматическая регистрация через `xfconf-query`.
- **Hyprland**: Добавьте в `~/.config/hypr/hyprland.conf`:
  ```ini
  bind = SUPER, SPACE, exec, echo-search
  ```
- **Sway / i3**: Добавьте в `~/.config/sway/config`:
  ```ini
  bindsym $mod+space exec echo-search
  ```

---

## ⌨️ Управление и горячие клавиши

| Сочетание / Команда | Действие |
| :--- | :--- |
| **`Super + Space`** | Открыть / скрыть лаунчер Echo |
| **`Esc`** | Очистить строку поиска / закрыть лаунчер |
| **`Enter`** | Запустить выбранное приложение / открыть файл |
| **`Ctrl + L`** | Выделить весь текст в строке поиска |
| **`Ctrl + K`** | Очистить поле ввода |
| **`Стрелки Вверх / Вниз`** | Навигация по списку результатов |
| **`Tab`** | Переключение между списком и предпросмотром |

### Быстрые команды перехода в режимы:
- `/apps` — переключиться в режим Launchpad приложений
- `/files` — переключиться в режим проводника файлов
- `/clip` — открыть историю буфера обмена
- `/emoji` — открыть каталог эмодзи
- `/settings` — открыть параметры приложения

---

## ⚙️ Файл настроек

Файл конфигурации создается автоматически при первом запуске:
`~/.config/echo-search/config.json`

```json
{
    "language": "auto",
    "theme": "dark",
    "blur": true,
    "transparency": 0.70,
    "preview_enabled": true,
    "preview_width": 420,
    "results_limit": 20,
    "animations": true,
    "launch_at_login": false,
    "launch_shortcut": "<Super>Space",
    "applications": true,
    "files": true,
    "clipboard": true,
    "emoji": true,
    "calculator": true,
    "commands": true,
    "settings": true,
    "recent_when_empty": true,
    "search_history": true
}
```

---

## 🗑 Удаление

Для полного удаления приложения:

```bash
# Через скрипт (удалит пакет и очистит хоткеи):
./uninstall.sh

# Либо через пакетный менеджер вашей системы:
# Debian/Ubuntu: sudo apt remove echo-search
# Arch Linux:    sudo pacman -R echo-search
# Fedora:        sudo dnf remove echo-search
# openSUSE:      sudo zypper remove echo-search
```

---

## 📄 Лицензия

Распространяется под лицензией **MIT**. См. [LICENSE](LICENSE).
