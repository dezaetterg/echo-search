#!/bin/bash
set -e

# ==============================================================================
# Echo Search - Universal Portable Linux Package Builder (.tar.gz)
# Compatible with ANY Linux Distribution
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION="1.0.8"
PKGNAME="echo-search"
DIST_DIR="$SCRIPT_DIR/dist"
BUILD_DIR="$SCRIPT_DIR/build/universal-package/echo-search"

echo "=========================================="
echo "📦 Сборка универсального пакета: ${PKGNAME}_${VERSION}_universal.tar.gz"
echo "=========================================="

rm -rf "$SCRIPT_DIR/build/universal-package"
mkdir -p "$BUILD_DIR/modes"
mkdir -p "$BUILD_DIR/providers"
mkdir -p "$BUILD_DIR/assets"
mkdir -p "$DIST_DIR"

# Copy source files, resources and installer
cp -p *.py style.css emoji.json install.sh LICENSE README.md "$BUILD_DIR/"
cp -p modes/*.py "$BUILD_DIR/modes/"
cp -p providers/*.py "$BUILD_DIR/providers/"
cp -rp assets/* "$BUILD_DIR/assets/" 2>/dev/null || true

# Launcher script for portable direct execution
cat << 'BIN_EOF' > "$BUILD_DIR/echo-search"
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
exec python3 "$SCRIPT_DIR/main.py" "$@"
BIN_EOF
chmod +x "$BUILD_DIR/echo-search"
chmod +x "$BUILD_DIR/install.sh"

TAR_NAME="${PKGNAME}_${VERSION}_universal.tar.gz"
tar -czf "$DIST_DIR/$TAR_NAME" -C "$SCRIPT_DIR/build/universal-package" echo-search
cp "$DIST_DIR/$TAR_NAME" "$DIST_DIR/${PKGNAME}_latest_universal.tar.gz"

cd "$DIST_DIR"
sha256sum "$TAR_NAME" > "${TAR_NAME}.sha256"
sha256sum "${PKGNAME}_latest_universal.tar.gz" > "${PKGNAME}_latest_universal.tar.gz.sha256"
cd "$SCRIPT_DIR"

rm -rf "$SCRIPT_DIR/build/universal-package"
echo "=========================================="
echo "✅ Универсальный пакет успешно собран: $DIST_DIR/$TAR_NAME"
ls -lh "$DIST_DIR/$TAR_NAME"
echo "=========================================="
