#!/bin/bash
set -e

# ==============================================================================
# Echo Search - RPM Package Builder
# Compatible with Fedora, RHEL, CentOS, AlmaLinux, Rocky Linux, openSUSE
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION="1.0.0"
RPM_TOPDIR="$SCRIPT_DIR/build_rpm_tree"

echo "==> Building Echo Search RPM package v${VERSION}..."

if ! command -v rpmbuild &>/dev/null; then
    echo "Error: rpmbuild is not installed. Install it via 'sudo dnf install rpm-build' or 'sudo zypper install rpm-build'."
    exit 1
fi

rm -rf "$RPM_TOPDIR" dist/rpm
mkdir -p "$RPM_TOPDIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
mkdir -p dist/rpm

cp echo-search.spec "$RPM_TOPDIR/SPECS/"

rpmbuild --define "_topdir $RPM_TOPDIR" \
         --define "_sourcedir $SCRIPT_DIR" \
         -bb "$RPM_TOPDIR/SPECS/echo-search.spec"

find "$RPM_TOPDIR/RPMS" -name "*.rpm" -exec cp {} dist/rpm/ \;
rm -rf "$RPM_TOPDIR"

echo "==> RPM package successfully created in dist/rpm/:"
ls -lh dist/rpm/*.rpm
