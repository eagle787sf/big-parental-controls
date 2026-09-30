"""Tests for distribution detection and per-distro default blocks."""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from big_parental_controls.core.distro import default_blocks, family_from_os_release


class TestFamilyDetection(unittest.TestCase):
    def test_known_distributions(self):
        cases = {
            ("biglinux", "arch"): "arch",
            ("cachyos", "arch"): "arch",
            ("manjaro", "arch"): "arch",
            ("fedora", ""): "fedora",
            ("bazzite", "fedora"): "fedora",
            ("ubuntu", "debian"): "debian",
            ("debian", ""): "debian",
            ("linuxmint", "ubuntu debian"): "debian",
        }
        for (ident, like), expected in cases.items():
            with self.subTest(ident=ident):
                self.assertEqual(
                    family_from_os_release({"ID": ident, "ID_LIKE": like}), expected
                )

    def test_unknown_distribution(self):
        self.assertEqual(family_from_os_release({"ID": "gentoo"}), "unknown")
        self.assertEqual(family_from_os_release({}), "unknown")


class TestDefaultBlocks(unittest.TestCase):
    def test_package_managers_per_family(self):
        self.assertIn("/usr/bin/pacman", default_blocks("arch", False))
        self.assertIn("/usr/bin/apt", default_blocks("debian", False))
        self.assertIn("/usr/bin/dnf", default_blocks("fedora", False))
        self.assertIn("/usr/bin/rpm-ostree", default_blocks("fedora", True))
        self.assertNotIn("/usr/bin/pacman", default_blocks("fedora", False))

    def test_flatpak_kept_usable_on_immutable_systems(self):
        self.assertIn("/usr/bin/flatpak", default_blocks("fedora", False))
        self.assertNotIn("/usr/bin/flatpak", default_blocks("fedora", True))

    def test_unknown_family_blocks_everything(self):
        blocks = default_blocks("unknown", False)
        for path in ("/usr/bin/pacman", "/usr/bin/apt", "/usr/bin/dnf", "/usr/bin/ssh"):
            self.assertIn(path, blocks)

    def test_all_paths_absolute(self):
        for fam in ("arch", "fedora", "debian", "unknown"):
            for path in default_blocks(fam, False):
                self.assertTrue(path.startswith("/"), path)


if __name__ == "__main__":
    unittest.main()
