# Maintainer: Echo Search Contributors
pkgname=echo-search
pkgver=1.0.0
pkgrel=1
pkgdesc="Blazing-fast Spotlight & Raycast-inspired desktop search for Linux"
arch=('any')
url="https://github.com/your-username/echo-search"
license=('MIT')
depends=(
    'python>=3.10'
    'python-gobject'
    'gtk4'
    'gtk4-layer-shell'
    'gnome-desktop-4'
    'tracker3'
    'python-rapidfuzz'
)
optdepends=(
    'wl-clipboard: Clipboard manager support for Wayland'
    'xclip: Clipboard manager support for X11'
)
source=("$pkgname-$pkgver.tar.gz")
sha256sums=('SKIP')

package() {
    install -d "$pkgdir/usr/bin"
    install -d "$pkgdir/usr/lib/echo-search"
    install -d "$pkgdir/usr/lib/echo-search/modes"
    install -d "$pkgdir/usr/lib/echo-search/providers"
    install -d "$pkgdir/usr/share/echo-search"
    install -d "$pkgdir/usr/share/applications"
    install -d "$pkgdir/usr/share/icons/hicolor/scalable/apps"
    
    # Python code
    install -m 644 *.py "$pkgdir/usr/lib/echo-search/"
    install -m 644 modes/*.py "$pkgdir/usr/lib/echo-search/modes/"
    install -m 644 providers/*.py "$pkgdir/usr/lib/echo-search/providers/"
    
    # Assets
    install -m 644 style.css "$pkgdir/usr/share/echo-search/"
    install -m 644 emoji.json "$pkgdir/usr/share/echo-search/"
    
    # Bin wrapper
    cat << 'EOF' > "$pkgdir/usr/bin/echo-search"
#!/bin/sh
exec python3 /usr/lib/echo-search/main.py "$@"
EOF
    chmod 755 "$pkgdir/usr/bin/echo-search"
    
    # Desktop and icon
    install -m 644 debian/echo-search.desktop "$pkgdir/usr/share/applications/com.echo.search.desktop"
    install -m 644 assets/icons/com.echo.search.svg "$pkgdir/usr/share/icons/hicolor/scalable/apps/com.echo.search.svg"
}
