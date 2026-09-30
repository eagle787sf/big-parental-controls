# Fedora / Fedora Atomic (Silverblue, Kinoite, Bazzite, Bluefin, Aurora) package.
#
# Build from a git checkout (on Atomic desktops, inside a toolbox/distrobox):
#   sudo dnf install rpm-build rpmdevtools cargo rust
#   make rpm        (or: packaging/fedora/build-rpm.sh)
#
# Install:
#   Fedora Workstation/KDE:  sudo dnf install ./big-parental-controls-*.rpm
#   Fedora Atomic / Bazzite: sudo rpm-ostree install ./big-parental-controls-*.rpm
#                            systemctl reboot

%global debug_package %{nil}

Name:           big-parental-controls
Version:        1.0.0
Release:        1%{?dist}
Summary:        Parental controls and supervised accounts
License:        GPL-3.0-or-later
URL:            https://github.com/biglinux/big-parental-controls
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  cargo >= 1.87
BuildRequires:  rust >= 1.87
BuildRequires:  make
BuildRequires:  systemd-rpm-macros

Requires:       python3 >= 3.11
Requires:       python3-gobject
Requires:       python3-cairo
Requires:       gtk4
Requires:       libadwaita
Requires:       accountsservice
Requires:       accountsservice-libs
Requires:       malcontent
Requires:       polkit
Requires:       acl
Requires:       libnotify
Requires:       shadow-utils
Requires:       util-linux
Requires:       gettext
Recommends:     nftables
%{?systemd_requires}

%description
Native Linux parental controls suite: supervised child accounts, app
restrictions, screen time limits, DNS-based web filtering and local-only
activity monitoring. Uses AccountsService, malcontent, polkit, ACLs and
nftables. On image-based systems (Fedora Atomic, Bazzite) where /usr is
read-only, blocked programs are enforced by the daemon instead of ACLs.

%prep
%autosetup

%build
make build

%install
make install DESTDIR=%{buildroot} DISTRO=fedora

%check
cd big-age-signal && cargo test --release

%post
%systemd_post big-parental-daemon.service
%{_prefix}/lib/big-parental-controls/pkg-post-install || :

%preun
%systemd_preun big-parental-daemon.service
if [ $1 -eq 0 ]; then
    %{_prefix}/lib/big-parental-controls/pkg-pre-remove || :
fi

%postun
%systemd_postun_with_restart big-parental-daemon.service

# Package upgrades replace binaries and drop their ACLs: re-apply them
# (no-op on rpm-ostree systems, where /usr is read-only)
%transfiletriggerin -- %{_bindir}
if [ -x %{_prefix}/lib/big-parental-controls/acl-reapply ] && [ ! -e /run/ostree-booted ]; then
    %{_prefix}/lib/big-parental-controls/acl-reapply >/dev/null 2>&1 || :
fi

%files
%license COPYING
%doc README.md
%{_bindir}/big-parental-controls
%{_bindir}/big-age-signal
%{_prefix}/lib/big-parental-controls/
%{_unitdir}/big-parental-daemon.service
%{_userunitdir}/big-age-signal.service
%{_sysusersdir}/big-parental-controls.conf
%{_datadir}/applications/big-parental-controls.desktop
%{_datadir}/icons/hicolor/scalable/apps/big-parental-controls.svg
%{_datadir}/dbus-1/interfaces/br.com.biglinux.AgeSignal.xml
%{_datadir}/dbus-1/services/br.com.biglinux.AgeSignal.service
%{_datadir}/dbus-1/system.d/br.com.biglinux.ParentalDaemon.conf
%{_datadir}/polkit-1/actions/br.com.biglinux.parental-controls.policy
%{_datadir}/polkit-1/rules.d/50-big-parental-controls.rules
%{_datadir}/locale/*/LC_MESSAGES/big-parental-controls.mo
%dir %{_localstatedir}/lib/big-parental-controls
%dir %attr(0700,root,root) %{_localstatedir}/lib/big-parental-controls/activity

%changelog
* Wed Sep 30 2026 BigLinux <dev@biglinux.com.br> - 1.0.0-1
- Fedora and Fedora Atomic packaging
