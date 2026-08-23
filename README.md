<div align="center">

<img src="assets/icons/com.echo.search.svg" alt="Echo Search Logo" width="128" height="128">

# Echo Search

### 🌊 Элегантный лаунчер и центр продуктивности в стиле Liquid Glass для Linux

[![Version](https://img.shields.io/badge/version-1.0.3-blue.svg?style=for-the-badge)](https://github.com/dezaetterg/echo-search/releases)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20(Wayland%20%7C%20X11)-orange.svg?style=for-the-badge)](https://github.com/dezaetterg/echo-search)
[![GTK4](https://img.shields.io/badge/UI-GTK%204%20%2B%20Libadwaita-brightgreen.svg?style=for-the-badge)](https://www.gtk.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow.svg?style=for-the-badge)](https://www.python.org/)

<p align="center">
  <b>Echo Search</b> — сверхбыстрый и визуально совершенный Spotlight-лаунчер для рабочего стола Linux.<br>
  Создан для моментального поиска файлов, запуска приложений, управления буфером обмена и быстрых расчетов.
</p>

</div>

---

## ✨ Ключевые возможности

* 🚀 **Умный запуск приложений**
  Нечеткий (fuzzy) поиск установленных программ с автоматической поддержкой транслитерации раскладки клавиатуры (например, `ghbdtn` мгновенно найдет нужное приложение).

* 📂 **Глубокий поиск файлов и документов**
  Интеграция с GNOME Tracker 3 SPARQL. Мгновенная фильтрация по категориям (Документы, Изображения, Видео, Аудио, Архивы) и встроенный предпросмотр содержимого.

* 📋 **Менеджер буфера обмена**
  История скопированных фрагментов текста с интерактивной панелью предпросмотра, быстрым поиском и копированием в 1 клик. Поддерживает Wayland (`wl-clipboard`) и X11 (`xclip`).

* 🧮 **Калькулятор и конвертер единиц**
  Вычисление математических выражений, процентов и конвертация величин прямо в поисковой строке.

* 🎭 **База эмодзи и символов**
  Быстрый поиск смайлов по ключевым словам и эмоциям с мгновенной вставкой.

* 🎨 **Эстетика Liquid Glass**
  Полупрозрачный стеклянный интерфейс с мягким размытием фона, динамическим изменением размера окна и плавной анимацией открытия.

* 🌍 **Мультиязычность**
  Полный перевод интерфейса на 13 языков, включая русский, английский, испанский, немецкий, французский, китайский и японский.

---

## 📥 Установка

### Вариант 1. Универсальный установщик (Рекомендуется)
Автоматически определяет дистрибутив, ставит зависимости, собирает пакет и настраивает горячую клавишу **Super + Space**:

```bash
git clone https://github.com/dezaetterg/echo-search.git
cd echo_search
chmod +x install.sh
./install.sh
```

### Вариант 2. Debian / Ubuntu / Linux Mint / PikaOS (.deb)
Скачайте готовый пакет со страницы [Releases](https://github.com/dezaetterg/echo-search/releases) и установите:

```bash
sudo apt install ./echo-search_1.0.3_all.deb
```

### Вариант 3. Arch Linux / Manjaro (PKGBUILD)
```bash
git clone https://github.com/dezaetterg/echo-search.git
cd echo_search
makepkg -si
```

### Вариант 4. Fedora / RHEL / openSUSE (RPM)
```bash
git clone https://github.com/dezaetterg/echo-search.git
cd echo_search
chmod +x build_rpm.sh
./build_rpm.sh
sudo dnf install ./echo-search-1.0.3-1.noarch.rpm
```

### Вариант 5. Прямой запуск из исходного кода
```bash
# Установка базовых библиотек (на примере Ubuntu/Debian)
sudo apt install python3-gi gir1.2-gtk-4.0 python3-rapidfuzz gir1.2-gtk4layershell-1.0 gir1.2-tracker-3.0

# Запуск приложения
python3 main.py
```

---

## ⌨️ Горячие клавиши и управление

| Клавиша | Действие |
| :--- | :--- |
| **Super + Space** | Открыть или скрыть Echo Search |
| **Стрелки ↑ / ↓** | Навигация по списку найденных результатов |
| **Enter** | Запустить приложение или открыть выбранный файл |
| **Tab** | Быстрое переключение между категориями и фильтрами |
| **Esc** | Очистить поле ввода или закрыть лаунчер |

---

## ⚙️ Настройка и кастомизация

Файл пользовательской конфигурации создается автоматически при первом запуске:
`~/.config/echo-search/config.json`

В нем можно настраивать:
* Темы оформления (Liquid Glass Silver, Dark, Light)
* Степень прозрачности и эффект размытия фона
* Позицию и отступы окна на экране
* Набор активных провайдеров поиска

---

## 🛠️ Стек технологий

* **Графический стек:** Python 3.10+, GTK 4, Libadwaita, Gtk4LayerShell (Wayland Layer Shell Protocol)
* **Поисковый движок:** RapidFuzz (нечеткое сопоставление C++ бэкендом), GNOME Tracker 3 SPARQL
* **Система:** D-Bus, Freedesktop Desktop Entry Specification, XDG Base Directory

---

## 📄 Лицензия

Проект распространяется под свободной лицензией **GNU General Public License v3.0 (GPLv3)**. Подробности в файле [LICENSE](LICENSE).

Автор: **[@dezaetterg](https://github.com/dezaetterg)**
