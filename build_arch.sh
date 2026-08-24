#!/bin/bash
set -e

# ==============================================================================
# Echo Search - Arch Linux Package Builder (.pkg.tar.zst)
# Compatible with Arch Linux, Manjaro, EndeavourOS, Garuda, CachyOS
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION="1.0.7"
RELEASE="1"
PKGNAME="echo-search"
PKG_FULL="${PKGNAME}-${VERSION}-${RELEASE}-any.pkg.tar.zst"

BUILD_DIR="$SCRIPT_DIR/build/arch-package"
DIST_DIR="$SCRIPT_DIR/dist"

echo "=========================================="
echo "📦 Сборка Arch-пакета: ${PKG_FULL}"
echo "=========================================="

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/lib/echo-search/modes"
mkdir -p "$BUILD_DIR/usr/lib/echo-search/providers"
mkdir -p "$BUILD_DIR/usr/share/echo-search"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$BUILD_DIR/usr/share/licenses/echo-search"
mkdir -p "$BUILD_DIR/usr/share/doc/echo-search"
mkdir -p "$DIST_DIR"

# Copy python files
cp -p *.py "$BUILD_DIR/usr/lib/echo-search/"
cp -p modes/*.py "$BUILD_DIR/usr/lib/echo-search/modes/"
cp -p providers/*.py "$BUILD_DIR/usr/lib/echo-search/providers/"

# Copy assets & licenses
cp -p style.css emoji.json "$BUILD_DIR/usr/share/echo-search/"
cp -p LICENSE "$BUILD_DIR/usr/share/licenses/echo-search/LICENSE"
cp -p LICENSE "$BUILD_DIR/usr/share/doc/echo-search/copyright"
cp -p README.md "$BUILD_DIR/usr/share/doc/echo-search/README.md"
cp -p debian/echo-search.desktop "$BUILD_DIR/usr/share/applications/com.echo.search.desktop"
cp -p assets/icons/com.echo.search.svg "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/com.echo.search.svg"

# Executable wrapper
cat << 'BIN_EOF' > "$BUILD_DIR/usr/bin/echo-search"
#!/bin/sh
exec python3 /usr/lib/echo-search/main.py "$@"
BIN_EOF
chmod 755 "$BUILD_DIR/usr/bin/echo-search"

# Calculate installed size
TOTAL_SIZE=$(du -sb "$BUILD_DIR/usr" | awk '{print $1}')
BUILD_DATE=$(date +%s)

# Create .PKGINFO metadata
cat << PKG_EOF > "$BUILD_DIR/.PKGINFO"
pkgname = ${PKGNAME}
pkgbase = ${PKGNAME}
pkgver = ${VERSION}-${RELEASE}
pkgdesc = Fast Spotlight-style desktop search and app launcher for Linux
url = https://github.com/dezaetterg/echo-search
builddate = ${BUILD_DATE}
packager = Echo Contributors <https://github.com/dezaetterg/echo-search>
size = ${TOTAL_SIZE}
arch = any
license = GPL-3.0-or-later
depend = python>=3.10
depend = python-gobject
depend = gtk4
depend = gtk4-layer-shell
depend = gnome-desktop-4
depend = tracker3
depend = python-rapidfuzz
optdepend = wl-clipboard: Clipboard manager support for Wayland
optdepend = xclip: Clipboard manager support for X11
PKG_EOF

# Set canonical package permissions
find "$BUILD_DIR/usr" -type d -exec chmod 755 {} +
find "$BUILD_DIR/usr" -type f -exec chmod 644 {} +
chmod 755 "$BUILD_DIR/usr/bin/echo-search"
chmod 644 "$BUILD_DIR/.PKGINFO"

# Package with tar and zstd
tar -c --owner=0 --group=0 --numeric-owner --mode='a-st' -C "$BUILD_DIR" .PKGINFO usr | zstd -c -T0 > "$DIST_DIR/$PKG_FULL"
cp "$DIST_DIR/$PKG_FULL" "$DIST_DIR/echo-search_latest-any.pkg.tar.zst"

cd "$DIST_DIR"
sha256sum "$PKG_FULL" > "${PKG_FULL}.sha256"
cd "$SCRIPT_DIR"

rm -rf "$BUILD_DIR"
echo "=========================================="
echo "✅ Arch-пакет успешно собран: $DIST_DIR/$PKG_FULL"
ls -lh "$DIST_DIR/$PKG_FULL"
echo "=========================================="
