# Distro-neutral build/install for big-parental-controls.
#
# Used by the Debian/Ubuntu (debian/), Fedora (packaging/fedora/) and
# Arch/CachyOS (packaging/arch/) packages. The BigLinux PKGBUILD in pkgbuild/
# is kept unchanged.
#
#   make                         # build the Rust daemon
#   make install DESTDIR=/tmp/root DISTRO=debian
#
# DISTRO selects the package-manager hook that re-applies ACLs after upgrades:
#   arch   -> pacman hook (/usr/share/libalpm/hooks)
#   debian -> apt hook (/etc/apt/apt.conf.d)
#   fedora -> none (the RPM spec uses a file trigger instead)
# Default: detected from /etc/os-release.

DESTDIR ?=
CARGO ?= cargo
DISTRO ?= $(shell . /etc/os-release 2>/dev/null; \
	for id in $$ID $$ID_LIKE; do case $$id in \
	(arch|archlinux|manjaro|biglinux|cachyos|endeavouros) echo arch; exit;; \
	(fedora|rhel|centos|bazzite|bluefin|aurora) echo fedora; exit;; \
	(debian|ubuntu) echo debian; exit;; esac; done; echo unknown)

TREE := big-parental-controls
LIBDIR := /usr/lib/big-parental-controls
PYDIR := $(LIBDIR)/python
DAEMON := big-age-signal/target/release/big-parental-daemon

.PHONY: all build install check clean deb rpm arch

all: build

build: $(DAEMON)

$(DAEMON):
	cd big-age-signal && $(CARGO) build --release

install: build
	install -d "$(DESTDIR)/usr"
	cp -r --no-preserve=ownership "$(TREE)/usr/." "$(DESTDIR)/usr/"
	chmod 755 "$(DESTDIR)/usr/bin/big-parental-controls" "$(DESTDIR)$(LIBDIR)"/*
ifneq ($(DISTRO),arch)
	rm -rf "$(DESTDIR)/usr/share/libalpm"
endif
ifeq ($(DISTRO),debian)
	install -Dm644 "$(TREE)/etc/apt/apt.conf.d/99big-parental-controls" \
		"$(DESTDIR)/etc/apt/apt.conf.d/99big-parental-controls"
endif
	# Unified Rust daemon (+ legacy big-age-signal name)
	install -Dm755 "$(DAEMON)" "$(DESTDIR)$(LIBDIR)/big-parental-daemon"
	ln -sf ../lib/big-parental-controls/big-parental-daemon "$(DESTDIR)/usr/bin/big-age-signal"
	# Python package in a private directory (found by the launcher), which
	# avoids differences between site-packages/dist-packages layouts
	install -d "$(DESTDIR)$(PYDIR)"
	cp -r --no-preserve=ownership src/big_parental_controls "$(DESTDIR)$(PYDIR)/"
	find "$(DESTDIR)$(PYDIR)" -name __pycache__ -prune -exec rm -rf {} +
	# State directories (755 so the app user can read user-profiles.json)
	install -dm755 "$(DESTDIR)/var/lib/big-parental-controls"
	install -dm700 "$(DESTDIR)/var/lib/big-parental-controls/activity"

check:
	cd big-age-signal && $(CARGO) test --release
	bash -n "$(TREE)$(LIBDIR)/group-helper"

clean:
	cd big-age-signal && $(CARGO) clean

# Distro packages (output in dist/ or the parent directory for deb)
deb:
	dpkg-buildpackage -us -uc -b

rpm:
	packaging/fedora/build-rpm.sh

arch:
	cd packaging/arch && makepkg -sf
