Name:           echo-search
Version:        1.0.7
Release:        1%{?dist}
Summary:        Fast Spotlight-style desktop search and app launcher for Linux
License:        GPL-3.0-or-later
URL:            https://github.com/dezaetterg/echo-search
BuildArch:      noarch

Requires:       python3 >= 3.10
Requires:       python3-gobject
Requires:       gtk4
Requires:       gtk4-layer-shell
Requires:       gnome-desktop4
Requires:       tracker3
Requires:       python3-rapidfuzz

%description
Echo Search is a modern application launcher and desktop search
utility for Linux desktops. It supports applications, files, calculator,
unit converter, clipboard history, emoji search, system commands, and multilingual localization.

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_prefix}/lib/echo-search/modes
mkdir -p %{buildroot}%{_prefix}/lib/echo-search/providers
mkdir -p %{buildroot}%{_datadir}/echo-search
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
mkdir -p %{buildroot}%{_datadir}/licenses/echo-search

# Install source files
cp -p *.py %{buildroot}%{_prefix}/lib/echo-search/
cp -p modes/*.py %{buildroot}%{_prefix}/lib/echo-search/modes/
cp -p providers/*.py %{buildroot}%{_prefix}/lib/echo-search/providers/
cp -p style.css emoji.json %{buildroot}%{_datadir}/echo-search/
cp -p LICENSE %{buildroot}%{_datadir}/licenses/echo-search/

# Executable wrapper
cat << 'EOF' > %{buildroot}%{_bindir}/echo-search
#!/bin/sh
exec python3 %{_prefix}/lib/echo-search/main.py "$@"
EOF
chmod 755 %{buildroot}%{_bindir}/echo-search

# Desktop entry and icon
cp -p debian/echo-search.desktop %{buildroot}%{_datadir}/applications/com.echo.search.desktop
cp -p assets/icons/com.echo.search.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/com.echo.search.svg

%files
%{_bindir}/echo-search
%{_prefix}/lib/echo-search
%{_datadir}/echo-search
%{_datadir}/applications/com.echo.search.desktop
%{_datadir}/icons/hicolor/scalable/apps/com.echo.search.svg
%{_datadir}/licenses/echo-search/LICENSE

%changelog
* Fri Aug 21 2026 Echo Contributors <contact@echo-search.org> - 1.0.6-1
- Update with dynamic capsule expansion, GNOME/Cinnamon fixes, and GPLv3 license
