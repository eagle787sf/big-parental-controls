"""Distribution detection and per-distro defaults.

Supported families:
- ``arch``    — Arch Linux, BigLinux, Manjaro, CachyOS, EndeavourOS
- ``fedora``  — Fedora Workstation/KDE and other dnf-based systems
- ``debian``  — Ubuntu, Debian and derivatives

Independently of the family, a system may be *immutable* (Fedora Atomic
desktops such as Silverblue/Kinoite, Bazzite, Bluefin, Aurora…). On those
systems ``/usr`` is read-only, so filesystem ACLs cannot be placed on
binaries and blocked programs are enforced by the daemon instead.
"""

from __future__ import annotations

import functools
import os

OS_RELEASE_PATHS = ("/etc/os-release", "/usr/lib/os-release")


def _parse_os_release(path: str) -> dict[str, str]:
    data: dict[str, str] = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                data[key] = value.strip().strip('"').strip("'")
    except OSError:
        pass
    return data


@functools.lru_cache(maxsize=1)
def os_release() -> dict[str, str]:
    """Return the parsed os-release file (empty dict if unavailable)."""
    for path in OS_RELEASE_PATHS:
        data = _parse_os_release(path)
        if data:
            return data
    return {}


def family_from_os_release(data: dict[str, str]) -> str:
    """Map os-release ID/ID_LIKE to a distro family."""
    ids = [data.get("ID", "").lower()]
    ids += data.get("ID_LIKE", "").lower().split()
    for ident in ids:
        if ident in ("arch", "archlinux", "manjaro", "biglinux", "cachyos", "endeavouros"):
            return "arch"
        if ident in ("fedora", "rhel", "centos", "bazzite", "bluefin", "aurora"):
            return "fedora"
        if ident in ("debian", "ubuntu"):
            return "debian"
    return "unknown"


@functools.lru_cache(maxsize=1)
def family() -> str:
    """Return the distro family of the running system."""
    return family_from_os_release(os_release())


@functools.lru_cache(maxsize=1)
def is_immutable() -> bool:
    """True on image-based systems whose /usr is read-only (Fedora Atomic, Bazzite…)."""
    if os.path.exists("/run/ostree-booted"):
        return True
    try:
        return os.statvfs("/usr").f_flag & os.ST_RDONLY != 0
    except OSError:
        return False


# Programs blocked for every supervised account, regardless of distro.
# Paths that do not exist on the running system are skipped.
_COMMON_BLOCKS = [
    "/usr/bin/flatpak",
    "/usr/bin/snap",
    "/usr/bin/ssh",
    "/usr/bin/rustdesk",
]

_FAMILY_BLOCKS: dict[str, list[str]] = {
    "arch": [
        "/usr/bin/pacman",
        "/usr/bin/pamac-manager",
        "/usr/bin/pamac-installer",
        "/usr/bin/pamac-daemon",
        "/usr/bin/yay",
        "/usr/bin/paru",
        "/usr/bin/octopi",
        "/usr/bin/cachyos-pi",
    ],
    "fedora": [
        "/usr/bin/dnf",
        "/usr/bin/dnf5",
        "/usr/bin/dnf-3",
        "/usr/bin/yum",
        "/usr/bin/rpm-ostree",
        "/usr/bin/ujust",
        "/usr/bin/ujust-picker",
        "/usr/bin/distrobox",
        "/usr/bin/toolbox",
        "/usr/bin/podman",
    ],
    "debian": [
        "/usr/bin/apt",
        "/usr/bin/apt-get",
        "/usr/bin/aptitude",
        "/usr/bin/dpkg",
        "/usr/bin/nala",
        "/usr/bin/snap-store",
    ],
}


def default_blocks(fam: str | None = None, immutable: bool | None = None) -> list[str]:
    """Return the default list of programs to block for supervised accounts."""
    fam = fam or family()
    immutable = is_immutable() if immutable is None else immutable
    if fam in _FAMILY_BLOCKS:
        extra = _FAMILY_BLOCKS[fam]
    else:
        # Unknown distro: include everything, missing paths are ignored later.
        extra = [p for paths in _FAMILY_BLOCKS.values() for p in paths]
    common = _COMMON_BLOCKS
    if immutable:
        # Most desktop apps are Flatpaks on image-based systems, so the flatpak
        # binary must stay usable; installs are denied by the malcontent app filter.
        common = [p for p in common if p != "/usr/bin/flatpak"]
    return extra + common
