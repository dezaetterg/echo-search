<div align="center">

<img src="assets/icons/echo-dark.png" alt="Echo Search Dark Icon" width="128">

# Echo Search

**Application and file launcher for Linux**

[English](#echo-search) | [Русский](#echo-search-ru)

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg?style=flat-square)](https://github.com/dezaetterg/echo-search/releases)
[![License](https://img.shields.io/badge/license-GPLv3-green.svg?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux-orange.svg?style=flat-square)](https://github.com/dezaetterg/echo-search)
[![GTK4](https://img.shields.io/badge/UI-GTK%204-brightgreen.svg?style=flat-square)](https://www.gtk.org/)

<br>

<img src="assets/preview.png" alt="Echo Search Preview" width="800">

</div>

## Features

* **Application Search**: Launch installed `.desktop` applications with fuzzy matching and keyboard layout transliteration.
* **File Search**: Search documents and media files via GNOME Tracker 3 SPARQL with category filtering (documents, images, videos, audio, archives, source code).
* **File Preview**: Preview files by pressing Space with syntax highlighting (GtkSourceView), image preview, and file metadata.
* **Clipboard History**: Store and search recent clipboard entries with preview panel (`wl-clipboard` support).
* **Calculator and Unit Converter**: Evaluate mathematical expressions and convert physical units in the input line.
* **Currency Converter**: Conversion of world currencies and cryptocurrencies (e.g., `100 usd in rub`, `50 eur in gbp`).
* **World Clock**: Local time and time zones across cities (`time tokyo`, `time in new york`).
* **Weather**: Weather summary for cities (temperature, feels like, humidity, wind, precipitation, atmospheric pressure). Atmospheric effects with hardware-accelerated CSS gradients. Data from Open-Meteo API.
* **Web Search**: Queries to Google, Yandex, DuckDuckGo, YouTube, GitHub, Wikipedia, Bing, and Brave.
* **System Commands**: Lock screen, reboot, power off, suspend, and log out.
* **Emoji & Symbol Picker**: Library of symbols and emoji with categories and descriptive search.
* **Interface**: Translucent design with background blur, system theme adaptation (Portal DBus), and accent color selection.
* **Bottom Action Bar**: Context-aware bottom bar displaying instant shortcut actions (Launch, Reveal in Folder, Copy Path, Quick Look, and Delete).
* **Instant Jump (Alt + 1..9)**: Instantly launch or select any of the top 9 search results or grid items without arrow navigation.
* **App Icon Themes**: Choose between Dark, Light, and Aura Glow icon variants in settings with automated icon cache sync.
  <br>
  <img src="assets/icons/echo-dark.png" width="54" alt="Dark Theme">
  <img src="assets/icons/echo-light.png" width="54" alt="Light Theme">
  <img src="assets/icons/echo-aura.png" width="54" alt="Aura Glow Theme">
* **Quick Look**: Fast file inspection window with code syntax highlighting, rich media preview, metadata inspection, and F11 fullscreen toggle.
* **Settings**: Configuration panel for themes, transparency, global hotkeys, and search providers.
* **Multi-layout Shortcut Support**: Global keybindings work on any keyboard layout (RU / EN).

## Screenshots

| Search & Preview Panel | Applications Grid & Categories |
| :-: | :-: |
| <img src="assets/screenshots/01_search_preview.png" width="440" alt="Search with Preview"> | <img src="assets/screenshots/02_apps_grid.png" width="440" alt="Applications Grid"> |
| Clipboard History | Emoji & Symbol Picker |
| :-: | :-: |
| <img src="assets/screenshots/03_clipboard_history.png" width="440" alt="Clipboard History"> | <img src="assets/screenshots/04_emoji_picker.png" width="440" alt="Emoji Picker"> |

<br>

<div align="center">
  <h3>Settings Panel</h3>
  <img src="assets/screenshots/05_settings.png" width="620" alt="Echo Search Settings">
</div>

## Compatibility & Testing

* **Distributions**: Tested on **Arch Linux**, Debian-based systems (**Debian 13**, **Ubuntu**, **Linux Mint**, **PikaOS**), and **Fedora**.
* **Desktop Environments**: Tested on **KDE Plasma** and **GNOME**. Works on Wayland compositors (Hyprland, Sway, etc.).
* **Display Server**: Requires **Wayland** (`gtk4-layer-shell` protocol). **Important:** On all desktop environments under **X11**, the application does not work properly.

## Data Sources & APIs

* **Weather**: [Open-Meteo API](https://open-meteo.com/) (weather forecasts, city geocoding, hourly parameters). Free for non-commercial use.
* **Currency Rates**: ExchangeRate-API and CoinGecko feeds.

## Installation

### 1. Installation via Script (install.sh)
The script checks dependencies, installs packages, and configures **Super + Space**:

```bash
git clone https://github.com/dezaetterg/echo-search.git
cd echo-search
chmod +x install.sh
./install.sh
```

### 2. Debian / Ubuntu / Linux Mint / PikaOS (.deb)
Pre-built `.deb` package from **[Releases](https://github.com/dezaetterg/echo-search/releases)**:

```bash
# If downloaded via browser:
sudo apt install ~/Downloads/echo-search_*.deb

# Or via terminal:
wget -O /tmp/echo-search.deb https://github.com/dezaetterg/echo-search/releases/latest/download/echo-search_1.4.0_all.deb
sudo apt install /tmp/echo-search.deb
```

### 3. Arch Linux / Manjaro
Build local package using `makepkg`:

```bash
git clone https://github.com/dezaetterg/echo-search.git
cd echo-search
makepkg -si
```

### 4. Fedora / openSUSE / RHEL (.rpm)
```bash
sudo dnf install https://github.com/dezaetterg/echo-search/releases/latest/download/echo-search_latest.noarch.rpm
```

### 5. Portable Archive (.tar.gz)
Archive from **[Releases](https://github.com/dezaetterg/echo-search/releases)**:

```bash
tar -xzf echo-search_*_universal.tar.gz
cd echo-search
./install.sh
```

### 6. Run from Source
```bash
python3 main.py
```

### Uninstallation

To cleanly remove Echo Search installed via `install.sh`:

```bash
chmod +x uninstall.sh
./uninstall.sh
# To automatically confirm removal:
./uninstall.sh -y
```
*(User configuration and search history in `~/.config/echo-search` and `~/.cache/echo-search` are preserved).*

### If Packages or Repositories are Missing (Ubuntu / Linux Mint)
If GTK4 packages or dependencies are missing, enable the `universe` repository:

```bash
sudo add-apt-repository universe
sudo apt update
```

## Controls & Shortcuts

* `Super + Space` (or custom configured shortcut): open or toggle launcher window
* `Alt + 1` .. `Alt + 9`: instant launch or selection of the corresponding result/card
* `Up / Down Arrows` (or `Ctrl + N` / `Ctrl + P`): navigate through results
* `Enter`: launch selected app, open file, or execute action
* `Shift + Enter`: reveal selected file in its parent directory
* `Alt + C` or `Ctrl + Shift + C`: copy file path, calculation result, or text to clipboard
* `Space` or `Ctrl + Y`: toggle Quick Look file inspection
* `Shift + Delete`: remove entry from clipboard or query history
* `Ctrl + /` or `Ctrl + ?`: toggle action bar shortcut hints
* `Tab`: switch between mode categories (Search, Apps, Files, Clipboard, Emoji, Settings)
* `Esc`: clear query input or dismiss window

### Slash Navigation Commands

Type any of the following commands into the search entry to instantly jump between modes:
* `/apps` — Applications grid
* `/files` — File browser & categories
* `/clip` — Clipboard history
* `/emoji` — Emoji & symbol picker
* `/settings` — Settings panel

### CLI Usage

```bash
echo-search            # Launch or bring Echo Search to focus
echo-search --toggle   # Toggle launcher window visibility
echo-search --show     # Force show launcher window
echo-search --hide     # Hide launcher window
echo-search --version  # Print current version
echo-search --help     # Show CLI options
```

## Configuration

Settings file path:
`~/.config/echo-search/config.json`

Parameters can also be changed in the settings panel in the upper right corner of the interface (parameters button).

## Dependencies

* Python 3.10+
* GTK 4, Libadwaita, Gtk4LayerShell
* GtkSourceView 5
* Rapidfuzz
* GNOME Tracker 3 (optional, for file search)
* `wl-clipboard` (for clipboard history)

## License

GNU General Public License v3.0 (GPLv3). See [LICENSE](LICENSE).

Author: **[@dezaetterg](https://github.com/dezaetterg)**

---

<a id="echo-search-ru"></a>

<div align="center">

<img src="assets/icons/echo-dark.png" alt="Echo Search Dark Icon" width="128">

# Echo Search (RU)

**Лаунчер приложений и файлов для Linux**

[English](#echo-search) | [Русский](#echo-search-ru)

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg?style=flat-square)](https://github.com/dezaetterg/echo-search/releases)
[![License](https://img.shields.io/badge/license-GPLv3-green.svg?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux-orange.svg?style=flat-square)](https://github.com/dezaetterg/echo-search)
[![GTK4](https://img.shields.io/badge/UI-GTK%204-brightgreen.svg?style=flat-square)](https://www.gtk.org/)

<br>

<img src="assets/preview.png" alt="Echo Search Preview" width="800">

</div>

## Возможности

* **Поиск приложений**: запуск установленных `.desktop` программ с нечетким (fuzzy) поиском и автоматической транслитерацией ошибочной раскладки клавиатуры.
* **Поиск файлов**: поиск документов и медиафайлов через GNOME Tracker 3 SPARQL с фильтрацией по типам (документы, изображения, видео, аудио, архивы, исходный код).
* **Предпросмотр файлов**: просмотр файлов по нажатию клавиши Space с подсветкой синтаксиса исходного кода (GtkSourceView), просмотром изображений и метаданных.
* **История буфера обмена**: хранение и поиск недавних фрагментов текста с панелью предпросмотра (поддержка `wl-clipboard`).
* **Калькулятор и конвертер единиц**: вычисление математических выражений и перевод физических величин прямо в строке ввода.
* **Конвертер валют**: пересчет мировых валют и криптовалют (например, `100 usd в rub`, `50 eur in gbp`).
* **Мировое время**: текущее время и часовые пояса в городах мира (`время токио`, `time in new york`).
* **Погода**: сводка погоды для городов (температура, ощущаемая температура, влажность, ветер, осадки, атмосферное давление). Атмосферные эффекты на аппаратных CSS-градиентах. Данные из Open-Meteo API.
* **Веб-поиск**: переход к поисковым системам Google, Яндекс, DuckDuckGo, YouTube, GitHub, Wikipedia, Bing и Brave.
* **Системные команды**: блокировка экрана, перезагрузка, выключение, спящий режим и завершение сеанса.
* **Поиск символов и эмодзи**: библиотека с категоризацией и поиском по описанию.
* **Интерфейс**: полупрозрачный дизайн с размытием фона, адаптацией под системную тему (Portal DBus) и выбором акцентных цветов.
* **Нижняя панель действий (Action Bar)**: контекстная плашка с подсказками доступных горячих клавиш (Запуск, Открыть папку, Скопировать путь, Предпросмотр, Удалить).
* **Быстрый запуск (Alt + 1..9)**: мгновенный выбор и выполнение любого из первых 9 результатов поиска или плиток без перемещения стрелками.
* **Темы иконки приложения**: переключение между темами значка (Dark, Light, Aura Glow) в настройках с автоматическим обновлением системного кэша иконок.
  <br>
  <img src="assets/icons/echo-dark.png" width="54" alt="Темная иконка">
  <img src="assets/icons/echo-light.png" width="54" alt="Светлая иконка">
  <img src="assets/icons/echo-aura.png" width="54" alt="Aura Glow">
* **Быстрый просмотр Quick Look**: окно предпросмотра файлов по Space или `Ctrl+Y` с подсветкой синтаксиса кода, метаданными и полноэкранным режимом (F11).
* **Настройки**: панель конфигурации тем оформления, прозрачности, глобальных хоткеев и модулей поиска.
* **Мультиязычный ввод**: глобальные сочетания клавиш работают на любых раскладках клавиатуры (RU / EN).

## Скриншоты интерфейса

| Поиск и панель предпросмотра | Сетка приложений и категории |
| :-: | :-: |
| <img src="assets/screenshots/01_search_preview.png" width="440" alt="Поиск с предпросмотром"> | <img src="assets/screenshots/02_apps_grid.png" width="440" alt="Сетка приложений"> |
| История буфера обмена | Поиск эмодзи и символов |
| :-: | :-: |
| <img src="assets/screenshots/03_clipboard_history.png" width="440" alt="Буфер обмена"> | <img src="assets/screenshots/04_emoji_picker.png" width="440" alt="Поиск эмодзи"> |

<br>

<div align="center">
  <h3>Панель настроек</h3>
  <img src="assets/screenshots/05_settings.png" width="620" alt="Настройки Echo Search">
</div>

## Совместимость и тестирование

* **Дистрибутивы**: приложение протестировано и работает на **Arch Linux**, а также на Debian-based системах (**Debian 13**, **Ubuntu**, **Linux Mint**, **PikaOS**) и **Fedora**.
* **Окружения рабочего стола**: протестировано и работает на **KDE Plasma** и **GNOME**. Также поддерживаются современные окружения с поддержкой Wayland (Hyprland, Sway и др.).
* **Графические серверы**: требуется **Wayland** (используется протокол `gtk4-layer-shell`). **Важно:** на всех графических окружениях (DE) под управлением **X11** приложение работает некорректно.

## Источники данных и API

* **Погода и прогноз**: данные сервиса [Open-Meteo API](https://open-meteo.com/) (прогноз погоды, геокодинг городов, почасовые параметры). API доступно бесплатно для некоммерческих проектов.
* **Курсы валют**: котировки ExchangeRate-API и CoinGecko.

## Установка

### 1. Установка через скрипт (install.sh)
Скрипт проверяет пакетный менеджер, ставит системные зависимости и настраивает вызов по **Super + Space**:

```bash
git clone https://github.com/dezaetterg/echo-search.git
cd echo-search
chmod +x install.sh
./install.sh
```

### 2. Debian / Ubuntu / Linux Mint / PikaOS (.deb)
Пакет `.deb` доступен на странице **[Releases](https://github.com/dezaetterg/echo-search/releases)**:

```bash
# Если файл скачан через браузер:
sudo apt install ~/Загрузки/echo-search_*.deb || sudo apt install ~/Downloads/echo-search_*.deb

# Либо через терминал:
wget -O /tmp/echo-search.deb https://github.com/dezaetterg/echo-search/releases/latest/download/echo-search_1.4.0_all.deb
sudo apt install /tmp/echo-search.deb
```

### 3. Arch Linux / Manjaro
Сборка локального пакета через `makepkg`:

```bash
git clone https://github.com/dezaetterg/echo-search.git
cd echo-search
makepkg -si
```

### 4. Fedora / openSUSE / RHEL (.rpm)
```bash
sudo dnf install https://github.com/dezaetterg/echo-search/releases/latest/download/echo-search_latest.noarch.rpm
```

### 5. Переносимый архив (.tar.gz для любого Linux)
Архив со страницы **[Releases](https://github.com/dezaetterg/echo-search/releases)**:

```bash
tar -xzf echo-search_*_universal.tar.gz
cd echo-search
./install.sh
```

### 6. Запуск из исходного кода
```bash
python3 main.py
```

### Удаление приложения

Для чистого удаления Echo Search, установленного через `install.sh`:

```bash
chmod +x uninstall.sh
./uninstall.sh
# Для автоматического подтверждения удаления:
./uninstall.sh -y
```
*(Пользовательские настройки и история в `~/.config/echo-search` и `~/.cache/echo-search` сохраняются).*

### Если пакеты или репозитории недоступны (Linux Mint / Ubuntu)

Если система сообщает, что пакеты GTK4 или зависимости не найдены, включите репозиторий `universe`:

```bash
sudo add-apt-repository universe
sudo apt update
```

## Управление и горячие клавиши

* `Super + Space` (или настроенный хоткей): открыть или скрыть окно лаунчера
* `Alt + 1` .. `Alt + 9`: мгновенный выбор или запуск соответствующего результата
* `Стрелки вверх / вниз` (или `Ctrl + N` / `Ctrl + P`): навигация по списку результатов
* `Enter`: запуск выбранной программы, открытие файла или выполнение действия
* `Shift + Enter`: открыть содержащую папку с выбранным файлом
* `Alt + C` или `Ctrl + Shift + C`: скопировать путь файла, результат вычислений или текст
* `Space` или `Ctrl + Y`: открыть/закрыть быстрый предпросмотр файла (Quick Look)
* `Shift + Delete`: удалить запись из истории буфера обмена или недавних запросов
* `Ctrl + /` или `Ctrl + ?`: скрыть или показать панель подсказок хоткеев (Action Bar)
* `Tab`: переключение между категориями (Поиск, Приложения, Файлы, Буфер, Эмодзи, Настройки)
* `Esc`: очистить строку ввода или закрыть окно

### Слэш-команды навигации

В строке поиска можно быстро переключить режим лаунчера, введя команду:
* `/apps` — Сетка приложений
* `/files` — Поиск и категории файлов
* `/clip` — История буфера обмена
* `/emoji` — Символы и эмодзи
* `/settings` — Панель настроек

### Консольные команды CLI

```bash
echo-search            # Запустить или выдвинуть лаунчер на передний план
echo-search --toggle   # Переключить видимость окна лаунчера
echo-search --show     # Показать окно лаунчера
echo-search --hide     # Скрыть окно лаунчера
echo-search --version  # Показать текущую версию
echo-search --help     # Справка по консольным аргументам
```

## Конфигурация

Файл пользовательских настроек сохраняется по пути:
`~/.config/echo-search/config.json`

Параметры также можно изменять в панели настроек в правом верхнем углу интерфейса (кнопка параметров).

## Зависимости

* Python 3.10+
* GTK 4, Libadwaita, Gtk4LayerShell
* GtkSourceView 5
* Rapidfuzz
* GNOME Tracker 3 (опционально для глубокого поиска файлов)
* `wl-clipboard` (для буфера обмена)

## Лицензия

GNU General Public License v3.0 (GPLv3). Подробнее в файле [LICENSE](LICENSE).

Автор: **[@dezaetterg](https://github.com/dezaetterg)**
