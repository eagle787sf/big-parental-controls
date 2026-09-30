#!/bin/bash
# Build the RPM from the current checkout. On Fedora Atomic / Bazzite run it
# inside a toolbox or distrobox:  toolbox create && toolbox enter
set -euo pipefail
cd "$(dirname "$0")/../.."
VERSION=$(sed -n 's/^Version: *//p' packaging/fedora/big-parental-controls.spec)
TOP=$(mktemp -d)
mkdir -p "$TOP"/{SOURCES,SPECS,BUILD,RPMS,SRPMS}
git archive --format=tar.gz --prefix="big-parental-controls-$VERSION/" \
    -o "$TOP/SOURCES/big-parental-controls-$VERSION.tar.gz" HEAD
rpmbuild --define "_topdir $TOP" -bb packaging/fedora/big-parental-controls.spec
mkdir -p dist
cp "$TOP"/RPMS/*/*.rpm dist/
rm -rf "$TOP"
ls -1 dist/*.rpm
