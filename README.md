<div align="center">

# 🌊 Echo — Liquid Glass Spotlight Launcher
### Современный быстрый лаунчер в стиле Liquid Glass для Linux (GNOME / Wayland)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-GNOME%20%7C%20Wayland-informational.svg)](https://www.gnome.org/)
[![GTK4](https://img.shields.io/badge/GUI-GTK%204%20%2B%20LayerShell-green.svg)](https://www.gtk.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Debian Package](https://img.shields.io/badge/Package-.deb%20(Ubuntu%2FDebian)-red.svg)](https://github.com/demid/spotlight_liquidglass/releases)

<p align="center">
  <b>Умный поиск приложений • Поиск файлов через Tracker 3 • Буфер обмена • Эмодзи • Калькулятор и конвертер • Превью</b>
</p>

</div>

---

## ✨ Возможности

- 🪟 **Liquid Glass & macOS Эстетика**: Полупрозрачные акриловые слои, динамический `backdrop-filter` блюр, светлая и темная темы, плавные Revealer-анимации.
- 🚀 **Мгновенный поиск приложений**: Нечеткий (Fuzzy) поиск с поддержкой русской транслитерации и фонетики (находит "стим" -> Steam, "телеграм" -> Telegram).
- 📁 **Полнотекстовый поиск файлов**: Глубокая интеграция с GNOME Tracker 3 SPARQL и локальный кэш файловой системы для моментального отклика.
- 📋 **Менеджер буфера обмена**: История скопированного текста и изображений с предпросмотром и быстрым копированием.
- 😀 **Каталог Emoji и специальных символов**: Удобный поиск и вставка эмодзи, математических знаков и типографики.
- 🧮 **Встроенный калькулятор и конвертер**: Вычисление математических выражений (`sqrt`, `sin`, `log`, степени) и конвертация единиц измерения на лету.
- 🔍 **Инспектор предпросмотра**: Детальные карточки с метаданными, миниатюрами файлов, категориями и быстрыми действиями.
- ⚡ **Нативный Wayland Overlay**: Работает поверх всех окон благодаря **gtk4-layer-shell**.

---

## 📦 Быстрая установка (.deb пакет)

### Вариант 1. Установка готового .deb пакета (Рекомендуется)

Скачайте `.deb` файл из раздела [Releases](https://github.com/demid/spotlight_liquidglass/releases) и установите через `apt` (все зависимости установятся автоматически):

```bash
# Установка через APT (автоматически подтягивает зависимости)
sudo apt install ./echo-search_1.0.0_all.deb
```

---

### Вариант 2. Установка через автоматический скрипт

Клонируйте репозиторий и запустите интерактивный установщик:

```bash
git clone https://github.com/demid/spotlight_liquidglass.git
cd spotlight_liquidglass
./install.sh
```

> **Скрипт автоматически:**
> 1. Установит все необходимые системные зависимости через `apt`.
> 2. Соберет `.deb` пакет и установит его в систему.
> 3. Зарегистрирует глобальную горячую клавишу **Super + Space** (Win + Пробел) в GNOME.

---

### Вариант 3. Ручная сборка .deb из исходников

Если вы хотите собрать пакет самостоятельно:

```bash
git clone https://github.com/demid/spotlight_liquidglass.git
cd spotlight_liquidglass

# Сборка deb-пакета
./build_deb.sh

# Установка собранного пакета
sudo apt install ./dist/echo-search_1.0.0_all.deb
```

---

## ⌨️ Горячие клавиши и управление

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

---

## 🛠 Системные требования и зависимости

Пакет предназначен для **Ubuntu 22.04+**, **Debian 12+**, **Pop!_OS**, **Linux Mint**, **PikaOS** и любых других дистрибутивов с GNOME/Wayland.

### Зависимости (устанавливаются автоматически пакетом):
- `python3` (>= 3.10)
- `python3-gi` и `python3-gi-cairo` (GObject Introspection)
- `gir1.2-gtk-4.0` (GTK 4)
- `gir1.2-gtk4layershell-1.0` и `libgtk4-layer-shell0` (Wayland Layer Shell)
- `gir1.2-gnomedesktop-4.0` (Генерация миниатюр GNOME)
- `gir1.2-tracker-3.0` (Движок индексации файлов)
- `python3-rapidfuzz` (Быстрый нечеткий поиск)

---

## ⚙️ Настройки и кастомизация

Файл конфигурации создается автоматически при первом запуске:
`~/.config/echo-search/config.json`

```json
{
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

Для чистого удаления приложения из системы:

```bash
# Через скрипт (удалит пакет и очистит хоткей GNOME):
./uninstall.sh

# Либо стандартно через APT:
sudo apt remove echo-search
```

---

## 🤝 Участие в разработке

1. Форкните репозиторий
2. Создайте ветку для функции (`git checkout -b feature/awesome-feature`)
3. Закоммитьте изменения (`git commit -m 'feat: add awesome feature'`)
4. Отправьте ветку в origin (`git push origin feature/awesome-feature`)
5. Откройте Pull Request

---

## 📄 Лицензия

Распространяется под лицензией **MIT**. Подробности в файле [LICENSE](LICENSE).
