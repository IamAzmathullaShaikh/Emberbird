#!/usr/bin/env python3
"""Consumer compliance tests.

Pins the consumer purity invariants against the code:
  - the engine core stays offline-pure (zero network tokens)
  - the website's direct-GitHub-discovery inventory is CLOSED — no new
    discovery modules may appear; E3B shrinks this set to zero
  - the manager's release-URL derivation inventory is CLOSED — E3C shrinks it

stdlib-only; runs in CI unchanged.
"""
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# --- inventoried direct-discovery modules (the closed set) ---
# E3B.4: production src is discovery-free. `website/src/lib/github.ts` was
# deleted; `website/src/lib/release-service.ts` now consumes the Ember
# Registry. The legacy provider survives ONLY as the test-tree parity oracle
# (website/tests/lib/github-release-oracle.ts), which is not production code.
WEBSITE_DISCOVERY_MODULES = []
MANAGER_DERIVATION_MODULES = [
    "apps/manager/src/lib/env.ts",
    "apps/manager/src/lib/ipc.ts",
    "apps/manager/src/lib/types.ts",  # carries the releases_url type field
]
# E3C: release truth resolves from the bundled registry; the legacy stub
# wrapper must never return.
MANAGER_FORBIDDEN_TOKENS = ("getLatestReleases",)

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
        """After E3B.4, no production website module may discover releases via
        the GitHub API — the registry is the only source of release truth."""
        website_src = REPO_ROOT / "website" / "src"
        offenders = [
            p.relative_to(REPO_ROOT).as_posix().replace("\\", "/")
            for p in website_src.rglob("*.ts")
            if any(tok in read(p) for tok in DISCOVERY_TOKENS)
        ]
        self.assertEqual(
            offenders, [],
            f"website production code still performs GitHub discovery (E3B.4 violated): {offenders}",
        )

    def test_parity_oracle_stays_out_of_production(self):
        """The legacy provider exists only as the S2 parity oracle; production
        code must never import it (mentions in comments are fine — imports are
        the real leak)."""
        oracle = REPO_ROOT / "website" / "tests" / "lib" / "github-release-oracle.ts"
        self.assertTrue(oracle.is_file(), "parity oracle missing")
        src = REPO_ROOT / "website" / "src"
        leaked = [
            p.relative_to(REPO_ROOT).as_posix().replace("\\", "/")
            for p in src.rglob("*.ts")
            if ("github-release-oracle" in read(p)
                and any(
                    line.strip().startswith(("import", "from", "export * from"))
                    and "github-release-oracle" in line
                    for line in read(p).splitlines()
                ))
        ]
        self.assertEqual(leaked, [], f"oracle imported from production: {leaked}")

    def test_manager_derivation_inventory_holds(self):
        offenders = []
        manager_src = REPO_ROOT / "apps" / "manager" / "src"
        for p in manager_src.rglob("*.ts*"):
            text = read(p)
            rel = p.relative_to(REPO_ROOT).as_posix().replace("\\", "/")
            if any(tok in text for tok in ("releases_url", "VITE_PUBLIC_RELEASES_URL")):
                if rel not in MANAGER_DERIVATION_MODULES:
                    offenders.append(rel)
            if any(tok in text for tok in MANAGER_FORBIDDEN_TOKENS) and "lib/registry.ts" not in rel:
                offenders.append(rel + " (forbidden legacy discovery token)")
        self.assertEqual(offenders, [], f"manager derivation/compliance violations (matrix closed): {offenders}")

    def test_manager_registry_resolution_exists(self):
        """E3C: the Manager's release-truth module must exist and consume the
        bundled registry (no network)."""
        reg = REPO_ROOT / "apps" / "manager" / "src" / "lib" / "registry.ts"
        self.assertTrue(reg.is_file(), "manager registry module missing")
        text = read(reg)
        self.assertIn("releases.json", text)
        self.assertNotIn("api.github.com", text)
        self.assertNotIn("releases/latest", text)


if __name__ == "__main__":
    unittest.main()
