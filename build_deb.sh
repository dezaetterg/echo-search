#!/bin/bash
set -e

# ==========================================
# Echo Search - Debian Package Builder
# ==========================================

VERSION="1.0.0"
PKG_NAME="echo-search"
ARCH="all"
DIST_DIR="$(pwd)/dist"
BUILD_DIR="$(pwd)/build/deb-package"
OUTPUT_DEB="${DIST_DIR}/${PKG_NAME}_${VERSION}_${ARCH}.deb"

echo "=========================================="
echo "📦 Сборка deb-пакета: ${PKG_NAME} v${VERSION}"
echo "=========================================="

# 1. Проверка наличия dpkg-deb
if ! command -v dpkg-deb >/dev/null 2>&1; then
    echo "❌ Ошибка: Утилита 'dpkg-deb' не найдена. Установите dpkg-dev:"
    echo "   sudo apt install -y dpkg-dev"
    exit 1
fi

# 2. Очистка временных файлов
echo "[1/6] Очистка предыдущих сборок..."
rm -rf "$BUILD_DIR"
mkdir -p "$DIST_DIR"
mkdir -p "$BUILD_DIR"

# 3. Создание структуры каталогов FHS
echo "[2/6] Создание структуры каталогов пакета..."
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/usr/bin"
mkdir -p "${BUILD_DIR}/usr/lib/${PKG_NAME}"
mkdir -p "${BUILD_DIR}/usr/share/${PKG_NAME}"
mkdir -p "${BUILD_DIR}/usr/share/applications"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps"

for s in 48 64 128 256 512; do
    mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/${s}x${s}/apps"
done

# 4. Копирование файлов приложения
echo "[3/6] Копирование компонентов приложения..."

# Бинарный исполняемый wrapper
cat <<'EOF' > "${BUILD_DIR}/usr/bin/echo-search"
#!/bin/sh
exec /usr/bin/python3 /usr/lib/echo-search/main.py "$@"
EOF
chmod 755 "${BUILD_DIR}/usr/bin/echo-search"

# Python код в /usr/lib/echo-search
cp *.py "${BUILD_DIR}/usr/lib/${PKG_NAME}/"
cp -r modes providers "${BUILD_DIR}/usr/lib/${PKG_NAME}/"

# Удаление всех __pycache__ и .pyc из пакета
find "${BUILD_DIR}/usr/lib/${PKG_NAME}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${BUILD_DIR}/usr/lib/${PKG_NAME}" -name "*.pyc" -delete 2>/dev/null || true

# Ресурсы в /usr/share/echo-search
cp style.css emoji.json "${BUILD_DIR}/usr/share/${PKG_NAME}/"

# Desktop Entry
cp debian/echo-search.desktop "${BUILD_DIR}/usr/share/applications/com.echo.search.desktop"

# Иконки
cp assets/icons/com.echo.search.svg "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps/com.echo.search.svg"
for s in 48 64 128 256 512; do
    if [ -f "assets/icons/hicolor/${s}x${s}/apps/com.echo.search.png" ]; then
        cp "assets/icons/hicolor/${s}x${s}/apps/com.echo.search.png" "${BUILD_DIR}/usr/share/icons/hicolor/${s}x${s}/apps/com.echo.search.png"
    fi
done

# Файлы управления DEBIAN
echo "[4/6] Подготовка метаданных пакета..."
cp debian/control "${BUILD_DIR}/DEBIAN/control"
cp debian/postinst "${BUILD_DIR}/DEBIAN/postinst"
cp debian/postrm "${BUILD_DIR}/DEBIAN/postrm"

chmod 755 "${BUILD_DIR}/DEBIAN/postinst"
chmod 755 "${BUILD_DIR}/DEBIAN/postrm"
chmod 644 "${BUILD_DIR}/DEBIAN/control"

# 5. Установка стандартных прав доступа
echo "[5/6] Настройка прав доступа (root-owner)..."
find "${BUILD_DIR}" -type d -exec chmod 755 {} +
find "${BUILD_DIR}/usr/lib" -type f -exec chmod 644 {} +
find "${BUILD_DIR}/usr/share" -type f -exec chmod 644 {} +
chmod 755 "${BUILD_DIR}/usr/bin/echo-search"
chmod 755 "${BUILD_DIR}/DEBIAN/postinst" "${BUILD_DIR}/DEBIAN/postrm"

# 6. Сборка deb-пакета
echo "[6/6] Сборка .deb архива..."
dpkg-deb --build --root-owner-group "$BUILD_DIR" "$OUTPUT_DEB"

# Генерация контрольной суммы
cd "$DIST_DIR"
sha256sum "$(basename "$OUTPUT_DEB")" > "$(basename "$OUTPUT_DEB").sha256"
cd - >/dev/null

echo "=========================================="
echo "✅ Пакет успешно собран!"
echo "Файл: $OUTPUT_DEB"
echo "Размер: $(du -h "$OUTPUT_DEB" | cut -f1)"
echo "SHA256: $(cat "${OUTPUT_DEB}.sha256")"
echo "=========================================="
echo ""
echo "Для установки пакета выполните:"
echo "sudo apt install $OUTPUT_DEB"
echo "=========================================="
