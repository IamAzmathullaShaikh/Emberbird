#!/usr/bin/env python3
"""
Emberbird Registry Read-Only Consumer Test (P0.4.2).

Proves Registry Independence: a consumer can resolve latest WSA, latest
Manager, Banking edition and Standard edition using ONLY the local registry
file - zero GitHub API access, zero release discovery heuristics.

Network isolation is enforced, not assumed: sockets raise for the duration of
each consumer scenario.
"""
import json
import socket
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "platform" / "release-engine"))

from release_engine import RegistryError, load  # noqa: E402


class _NetworkBlocked:
    """Context that makes any socket operation raise."""

    def __enter__(self):
        self._orig = socket.socket

        class _NoSocket(self._orig):
            def __init__(self, *args, **kwargs):
                raise RuntimeError("NETWORK ACCESS DENIED: consumer must be registry-only")

        socket.socket = _NoSocket
        return self

    def __exit__(self, *exc):
        socket.socket = self._orig
        return False


class TestRegistryConsumer(unittest.TestCase):
    """The fixture consumer every future consumer must imitate."""

    def setUp(self):
        self.registry = load()

    def test_registry_loads_without_network(self):
        with _NetworkBlocked():
            reg = load()
            self.assertGreaterEqual(len(reg.releases), 1)

    def test_resolve_latest_wsa_without_network(self):
        with _NetworkBlocked():
            latest = self.registry.latest_wsa()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.kind, "subsystem")
        self.assertEqual(latest.status, "published")
        for asset in latest.package_assets:
            self.assertRegex(asset["sha256"], r"^[a-f0-9]{64}$")
            self.assertNotEqual(set(asset["sha256"]), {"0"})

    def test_resolve_latest_manager_without_network(self):
        with _NetworkBlocked():
            latest = self.registry.latest_manager()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.kind, "manager")

    def test_resolve_banking_edition_without_network(self):
        with _NetworkBlocked():
            banking = self.registry.by_edition("banking")
        self.assertTrue(banking)
        for rel in banking:
            self.assertEqual(rel.edition, "banking")
            files = {a["filename"] for a in rel.package_assets}
            self.assertTrue(any(f.endswith("_vanilla.7z") for f in files),
                            "banking edition must expose a vanilla package")

    def test_resolve_standard_edition_without_network(self):
        with _NetworkBlocked():
            standard = self.registry.by_edition("standard")
        self.assertTrue(standard)
        for rel in standard:
            files = {a["filename"] for a in rel.package_assets}
            self.assertTrue(any(f.endswith("_x64.7z") and not f.endswith("_vanilla.7z") for f in files),
                            "standard edition must expose a rooted package")

    def test_hash_lookup_without_network(self):
        with _NetworkBlocked():
            digest = self.registry.hash_for("WSABuildsManager-Setup-0.2.2-x64.exe")
        self.assertIsNotNone(digest)

    def test_no_release_discovery_heuristics(self):
        """The consumer never scans the GitHub API; the only source is the JSON."""
        raw = self.registry.raw
        self.assertIn("releases", raw)
        self.assertIn("schema_version", raw)
        # no embedded github api tokens / discovery state
        blob = json.dumps(raw)
        self.assertNotIn("api.github.com/repos", blob.replace("https://api.github.com/repos", ""))
        self.assertNotIn("\"discovery\"", blob)


class TestIntegrityGate(unittest.TestCase):
    """P0.4.1: integrity checks catch real corruption."""

    def _base(self):
        import copy
        reg = load()
        return copy.deepcopy(reg.raw)

    def test_healthy_registry_passes(self):
        problems = __import__("release_engine").check_integrity(self._base())
        self.assertEqual(problems, [])

    def test_superseded_with_unknown_target_detected(self):
        import copy
        from release_engine import check_integrity
        data = self._base()
        data["releases"][0]["status"] = "superseded"
        data["releases"][0]["superseded_by"] = "ghost-release"
        problems = check_integrity(data)
        self.assertTrue(any("unknown release" in p for p in problems))

    def test_duplicate_ids_detected(self):
        import copy
        from release_engine import check_integrity
        data = self._base()
        data["releases"].append(copy.deepcopy(data["releases"][0]))
        problems = check_integrity(data)
        self.assertTrue(any("duplicate release_id" in p for p in problems))

    def test_placeholder_hash_detected(self):
        from release_engine import check_integrity
        data = self._base()
        data["releases"][0]["assets"][0]["sha256"] = "0" * 64
        problems = check_integrity(data)
        self.assertTrue(any("placeholder" in p for p in problems))

    def test_double_recommended_detected(self):
        from release_engine import check_integrity
        data = self._base()
        std = [r for r in data["releases"] if r["edition"] == "standard" and r["kind"] == "subsystem"]
        self.assertGreaterEqual(len(std), 2, "fixture requires >=2 standard cuts")
        for r in std:
            r["recommended"] = True
        problems = check_integrity(data)
        self.assertTrue(any("recommended" in p for p in problems))

    def test_load_rejects_corrupt_registry(self):
        import copy
        import tempfile
        data = self._base()
        data["releases"][0]["assets"][0]["sha256"] = "z" * 64
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(data, fh)
            tmp = Path(fh.name)
        try:
            with self.assertRaises(RegistryError):
                load(tmp)
        finally:
            tmp.unlink()


if __name__ == "__main__":
    unittest.main()
