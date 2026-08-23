<div align="center">

<img src="assets/logo.png" alt="Echo Search Logo" width="120">

# Echo Search

**Лаунчер приложений и быстрый поиск для Linux (GTK 4 / Wayland / X11)**

[![Version](https://img.shields.io/badge/version-1.0.3-blue.svg?style=flat-square)](https://github.com/dezaetterg/echo-search/releases)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux-orange.svg?style=flat-square)](https://github.com/dezaetterg/echo-search)
[![GTK4](https://img.shields.io/badge/UI-GTK%204-brightgreen.svg?style=flat-square)](https://www.gtk.org/)

<br>

<img src="assets/preview.png" alt="Echo Search" width="750">

</div>

## Возможности

* **Поиск приложений**: запуск установленных `.desktop` программ с нечетким (fuzzy) поиском и автоматической транслитерацией ошибочной раскладки клавиатуры.
* **Поиск файлов**: поиск документов и медиафайлов через GNOME Tracker 3 SPARQL с фильтрацией по типам (документы, изображения, видео, аудио, архивы).
* **История буфера обмена**: хранение и поиск недавних фрагментов текста с панелью предпросмотра (поддержка `wl-clipboard` на Wayland и `xclip` на X11).
* **Калькулятор и конвертер**: подсчет математических выражений и перевод единиц измерения прямо в строке ввода.
* **Поиск эмодзи**: база символов и эмодзи с поиском по ключевым словам.
* **Интерфейс**: полупрозрачное окно с размытием фона и адаптацией под системную тему.
* **Локализация**: встроенная поддержка 13 языков.

## Совместимость и тестирование

* **Дистрибутивы**: приложение разрабатывалось и тестировалось на Debian-based системах: **PikaOS**, **Debian 13 (Trixie)** и **Linux Mint**. Пакеты для Arch Linux и Fedora сгенерированы по спецификациям, но отдельное тестирование на них пока не проводилось.
* **Окружения рабочего стола**: протестировано на **GNOME** и **Cinnamon**. В теории поддерживаются все современные окружения (KDE Plasma, XFCE, Hyprland, Sway).

## Установка

### 1. Универсальный установщик
Скрипт проверяет пакетный менеджер, ставит системные зависимости и настраивает вызов по **Super + Space**:

```bash
git clone https://github.com/dezaetterg/echo-search.git
cd echo-search
chmod +x install.sh
./install.sh
```

### 2. Debian / Ubuntu / Linux Mint / PikaOS (.deb)
Готовый пакет доступен на странице [Releases](https://github.com/dezaetterg/echo-search/releases):

```bash
sudo apt install ./echo-search_1.0.3_all.deb
```

### 3. Arch Linux / Manjaro
Сборка локального пакета через `makepkg` или скрипт:

```bash
git clone https://github.com/dezaetterg/echo-search.git
cd echo-search
makepkg -si
```

### 4. Fedora / openSUSE (RPM)
```bash
git clone https://github.com/dezaetterg/echo-search.git
cd echo-search
./build_rpm.sh
sudo dnf install ./echo-search-1.0.3-1.noarch.rpm
```

### 5. Запуск из исходного кода
```bash
python3 main.py
```

### Если пакеты или репозитории недоступны (Linux Mint / Ubuntu)

Если система сообщает, что пакеты GTK4 или зависимости не найдены, включите репозиторий `universe`:

```bash
sudo add-apt-repository universe
sudo apt update
```

## Управление

* `Super + Space` : открыть или скрыть окно
* `Стрелки вверх / вниз` : навигация по списку
* `Enter` : запустить программу или открыть файл
* `Tab` : переключение между категориями
* `Esc` : очистить ввод или закрыть окно

## Конфигурация

Файл настроек создается автоматически при первом запуске:
`~/.config/echo-search/config.json`

Параметры позволяют менять тему оформления (Liquid Glass Silver, Dark, Light), уровень прозрачности, отступы окна и список активных модулей поиска.

## Зависимости

* Python 3.10+
* GTK 4, Libadwaita, Gtk4LayerShell
* Rapidfuzz
* GNOME Tracker 3 (опционально для глубокого поиска файлов)
* `wl-clipboard` или `xclip` (для буфера обмена)

## Лицензия

GNU General Public License v3.0 (GPLv3). Подробнее в файле [LICENSE](LICENSE).

Автор: **[@dezaetterg](https://github.com/dezaetterg)**
