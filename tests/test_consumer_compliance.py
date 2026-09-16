#!/usr/bin/env python3
"""E1.5 — M3: Consumer compliance tests.

Pins the S4 Consumer Purity Matrix (docs/CONSUMER_MATRIX.md) against the code:
  - the engine core stays offline-pure (zero network tokens)
  - the website's direct-GitHub-discovery inventory is CLOSED — no new
    discovery modules may appear; E3B shrinks this set to zero
  - the manager's release-URL derivation inventory is CLOSED — E3C shrinks it
  - matrix file exists (the audit basis)

stdlib-only; runs in CI unchanged.
"""
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# --- inventoried direct-discovery modules (the closed set) ---
WEBSITE_DISCOVERY_MODULES = [
    "website/src/lib/github.ts",
    "website/src/lib/release-service.ts",
]
MANAGER_DERIVATION_MODULES = [
    "apps/manager/src/lib/env.ts",
    "apps/manager/src/lib/ipc.ts",
    "apps/manager/src/lib/types.ts",  # carries the releases_url type field
]

DISCOVERY_TOKENS = ("api.github.com", "releases/latest", "/releases?per_page")
ENGINE_NETWORK_TOKENS = ("urllib", "requests", "api.github.com", "http.client", "socket")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


class TestEnginePurity(unittest.TestCase):
    def test_engine_core_is_offline_pure(self):
        core = (REPO_ROOT / "platform/release-engine/release_engine/__init__.py").read_text(encoding="utf-8")
        hits = [t for t in ENGINE_NETWORK_TOKENS if t in core]
        self.assertEqual(hits, [], f"engine core must stay offline-pure; found: {hits}")

    def test_engine_cli_may_network(self):
        """The CLI is the sanctioned network boundary (verify command)."""
        cli = (REPO_ROOT / "platform/release-engine/release_engine/__main__.py").read_text(encoding="utf-8")
        self.assertIn("urllib", cli, "CLI verify fetcher should live in __main__ only")


class TestClosedDiscoveryInventory(unittest.TestCase):
    def test_website_discovery_inventory_holds(self):
        """The two inventoried website modules must contain discovery; any OTHER
        website module containing it is a new (forbidden) discovery path."""
        offenders = []
        website_src = REPO_ROOT / "website" / "src"
        for p in website_src.rglob("*.ts"):
            text = read(p)
            rel = p.relative_to(REPO_ROOT).as_posix().replace("\\", "/")
            if any(tok in text for tok in DISCOVERY_TOKENS):
                if rel not in WEBSITE_DISCOVERY_MODULES:
                    offenders.append(rel)
        self.assertEqual(offenders, [], f"NEW website GitHub-discovery paths are forbidden (matrix closed): {offenders}")

    def test_website_inventoried_modules_still_discover(self):
        """Until E3B lands, the inventoried modules must still hold the
        discovery code — proving the inventory tracks reality, not fiction."""
        for rel in WEBSITE_DISCOVERY_MODULES:
            p = REPO_ROOT / rel
            if p.exists():
                self.assertTrue(
                    any(tok in read(p) for tok in DISCOVERY_TOKENS),
                    f"{rel} left the discovery inventory without an E3B migration record",
                )

    def test_manager_derivation_inventory_holds(self):
        offenders = []
        manager_src = REPO_ROOT / "apps" / "manager" / "src"
        for p in manager_src.rglob("*.ts*"):
            text = read(p)
            rel = p.relative_to(REPO_ROOT).as_posix().replace("\\", "/")
            if any(tok in text for tok in ("releases_url", "VITE_PUBLIC_RELEASES_URL")):
                if rel not in MANAGER_DERIVATION_MODULES:
                    offenders.append(rel)
        self.assertEqual(offenders, [], f"NEW manager release-URL derivation paths are forbidden (matrix closed): {offenders}")

    def test_matrix_document_exists(self):
        matrix = REPO_ROOT / "docs" / "CONSUMER_MATRIX.md"
        self.assertTrue(matrix.is_file(), "docs/CONSUMER_MATRIX.md (S4) must exist")


class TestMatrixTruthfulness(unittest.TestCase):
    def test_matrix_records_pending_consumers(self):
        matrix = read(REPO_ROOT / "docs" / "CONSUMER_MATRIX.md")
        self.assertIn("E3B pending", matrix)
        self.assertIn("E3C pending", matrix)
        self.assertIn("Migrated", matrix)


if __name__ == "__main__":
    unittest.main()
