#!/usr/bin/env python3
"""P1 tests: registry reality-sync automation, vault verification, policy write path.

- P1.1 (registry-drift.yml): scheduled regeneration from published reality,
  engine diff gate, issue-only escalation. The workflow must NEVER auto-commit:
  published reality enters the repository through reviewed changes only.
- P1.2: engine `verify` command checks vault mirror statuses against the
  published assets through an injected fetcher (tests run fully offline).
- P1.3: engine `apply-policy` command sets `recommended` only with
  `policy.recommended_by` provenance and a dated rationale (Contract clause 9).

stdlib-only; runs in CI unchanged.
"""
import copy
import json
import re
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "platform" / "release-engine"))
sys.path.insert(0, str(REPO_ROOT / "tests"))

from release_engine import Registry  # noqa: E402
import release_engine as engine  # noqa: E402

from fixture import FIXTURE  # noqa: E402

DRIFT_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "registry-drift.yml"
WORKFLOWS_DOC = REPO_ROOT / ".github" / "WORKFLOWS.md"


class TestRegistryDriftWorkflow(unittest.TestCase):
    """P1.1: the reality-sync workflow exists, is documented, and never auto-commits."""

    @classmethod
    def setUpClass(cls):
        cls.exists = DRIFT_WORKFLOW.is_file()
        cls.workflow = DRIFT_WORKFLOW.read_text(encoding="utf-8") if cls.exists else ""
        cls.doc = WORKFLOWS_DOC.read_text(encoding="utf-8")

    def test_workflow_exists(self):
        self.assertTrue(self.exists, "registry-drift.yml (P1.1) must exist")

    def test_scheduled_trigger(self):
        self.assertRegex(self.workflow, r"schedule:")
        self.assertRegex(self.workflow, r"cron:")

    def test_regenerates_registry_from_reality(self):
        self.assertIn("build_registry.py", self.workflow, "workflow must regenerate the registry from live reality")

    def test_diff_gate_invoked(self):
        self.assertRegex(self.workflow, r"diff\s", "workflow must gate via the engine diff command")

    def test_never_auto_commits(self):
        """Policy: reality enters the repository through reviewed changes only."""
        forbidden = [r"git\s+commit", r"git\s+push", r"stefanzweifel.*auto-commit", r"auto-commit-action"]
        for pattern in forbidden:
            self.assertIsNone(
                re.search(pattern, self.workflow),
                f"registry-drift.yml must never auto-commit (matched {pattern!r})",
            )

    def test_escalates_via_issue(self):
        self.assertRegex(self.workflow, r"issues\.create", "drift must escalate by opening an issue")
        self.assertRegex(self.workflow, r"issues\.update", "drift must update an existing issue, not spam duplicates")
        self.assertIn("registry-drift", self.workflow, "drift issues must carry the registry-drift label")

    def test_documented_in_workflows_md(self):
        self.assertIn("registry-drift.yml", self.doc, "P1.1 workflow must be documented in WORKFLOWS.md (Priority 4 guard)")

    def test_no_hardcoded_release_truth_in_workflow(self):
        """The workflow derives everything from the generator + engine; no tags/hashes."""
        self.assertIsNone(
            re.search(r"wsa-v[0-9]|Windows_11_[0-9]|[a-f0-9]{64}", self.workflow),
            "workflow must not embed release truth",
        )


class TestGeneratorTokenSupport(unittest.TestCase):
    """Scheduled CI runs need authenticated API access (rate limits)."""

    def test_github_token_honored(self):
        import os

        from scripts_helper import load_generator  # noqa: F401  (sets up path)

        gen = load_generator()
        old = os.environ.pop("GITHUB_TOKEN", None)
        try:
            os.environ["GITHUB_TOKEN"] = " test-token-123 "
            headers = gen.github_headers()
        finally:
            os.environ.pop("GITHUB_TOKEN", None)
            if old is not None:
                os.environ["GITHUB_TOKEN"] = old
        self.assertEqual(headers.get("Authorization"), "Bearer test-token-123", "token must be trimmed and sent as Bearer")
        self.assertIn("User-Agent", headers)

    def test_no_token_means_anonymous(self):
        import os

        from scripts_helper import load_generator

        gen = load_generator()
        old = os.environ.pop("GITHUB_TOKEN", None)
        try:
            headers = gen.github_headers()
        finally:
            if old is not None:
                os.environ["GITHUB_TOKEN"] = old
        self.assertNotIn("Authorization", headers)


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self, amount=-1):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestVaultVerification(unittest.TestCase):
    """P1.2: verify_vault checks mirror status against the published asset."""

    def _registry(self, status="unverified"):
        reg = copy.deepcopy(FIXTURE)
        for vault in reg["vault"]:
            vault["mirror_status"] = status
        return reg

    def test_verify_passes_when_hashes_match(self):
        reg = self._registry()
        fetches = []

        def fake_fetch(entry):
            fetches.append(entry["artifact"])
            return entry["sha256"]  # published reality agrees with the registry

        report = engine.verify_vault(reg, fetcher=fake_fetch)
        self.assertEqual(report["checked"], len(reg["vault"]))
        self.assertEqual(report["mismatches"], [])
        self.assertEqual(fetches, [v["artifact"] for v in reg["vault"]])
        for vault in reg["vault"]:
            self.assertEqual(vault["mirror_status"], "available", "matching reality must mark the entry available")

    def test_verify_flags_hash_mismatch(self):
        reg = self._registry()
        frozen = copy.deepcopy(reg)

        def fake_fetch(entry):
            return "0" * 64  # published hash differs

        report = engine.verify_vault(reg, fetcher=fake_fetch)
        self.assertEqual(len(report["mismatches"]), len(reg["vault"]))
        by_name = {v["artifact"]: v["sha256"] for v in frozen["vault"]}
        for m in report["mismatches"]:
            self.assertEqual(m["expected"], by_name[m["artifact"]])
            self.assertEqual(m["actual"], "0" * 64)
            self.assertNotEqual(m["expected"], m["actual"])
            self.assertEqual(next(v for v in reg["vault"] if v["artifact"] == m["artifact"])["sha256"], by_name[m["artifact"]], "verification must never rewrite hash claims")

    def test_verify_records_fetch_errors(self):
        reg = self._registry()

        def fake_fetch(entry):
            raise urllib.error.URLError("network down")

        report = engine.verify_vault(reg, fetcher=fake_fetch)
        self.assertEqual(len(report["errors"]), len(reg["vault"]))
        self.assertTrue(all("network down" in e["error"] for e in report["errors"]))

    def test_report_shape(self):
        reg = self._registry()
        report = engine.verify_vault(reg, fetcher=lambda entry: entry["sha256"])
        for key in ("checked", "verified", "mismatches", "errors"):
            self.assertIn(key, report)

    def test_verify_is_schema_safe(self):
        """verify_vault may only write schema-legal tokens/fields."""
        reg = self._registry()
        engine.verify_vault(reg, fetcher=lambda entry: entry["sha256"])
        for vault in reg["vault"]:
            self.assertIn(vault["mirror_status"], ("available", "unverified", "missing"))
            self.assertIn("last_verified_at", vault)


class TestApplyPolicyCommand(unittest.TestCase):
    """P1.3: recommended is a policy decision with provenance, never an assumption."""

    def _registry(self):
        return copy.deepcopy(FIXTURE)

    def _policy(self, release_id, by="ember-observatory", rationale="Banking edition validated on field telemetry."):
        return {
            "release_id": release_id,
            "recommended_by": by,
            "rationale": rationale,
            "decided_at": "2026-09-16",
        }

    def test_apply_sets_recommended_with_provenance(self):
        reg = self._registry()
        rid = reg["releases"][0]["release_id"]
        updated = engine.apply_policy(reg, self._policy(rid))
        target = next(r for r in updated["releases"] if r["release_id"] == rid)
        self.assertTrue(target["recommended"])
        self.assertIn("policy", updated, "provenance lives in the registry-root policy object")
        self.assertEqual(updated["policy"]["recommended_by"], "ember-observatory")
        self.assertEqual(updated["policy"]["rationale"], self._policy(rid)["rationale"])

    def test_apply_refuses_missing_provenance(self):
        reg = self._registry()
        rid = reg["releases"][0]["release_id"]
        policy = self._policy(rid)
        del policy["recommended_by"]
        with self.assertRaises(engine.PolicyError):
            engine.apply_policy(reg, policy)

    def test_apply_refuses_missing_rationale(self):
        reg = self._registry()
        rid = reg["releases"][0]["release_id"]
        policy = self._policy(rid)
        policy["rationale"] = ""
        with self.assertRaises(engine.PolicyError):
            engine.apply_policy(reg, policy)

    def test_apply_refuses_unknown_release(self):
        reg = self._registry()
        with self.assertRaises(engine.PolicyError):
            engine.apply_policy(reg, self._policy("no-such-release"))

    def test_apply_is_single_recommended(self):
        reg = self._registry()
        first = reg["releases"][0]["release_id"]
        second = reg["releases"][1]["release_id"]
        reg = engine.apply_policy(reg, self._policy(first))
        reg = engine.apply_policy(reg, self._policy(second))
        flagged = [r for r in reg["releases"] if r.get("recommended")]
        self.assertEqual([r["release_id"] for r in flagged], [second], "recommended must be unique across the registry")

    def test_apply_does_not_touch_latest(self):
        """Contract clause 9: latest stays a chronological fact; policy never edits it."""
        reg = self._registry()
        rid = reg["releases"][0]["release_id"]
        before = copy.deepcopy(reg["releases"])
        updated = engine.apply_policy(reg, self._policy(rid))
        for old, new in zip(before, updated["releases"]):
            self.assertEqual(old["published_at"], new["published_at"], "policy must not alter chronology")

    def test_apply_replaces_previous_decision(self):
        """Re-applying policy moves the single recommendation."""
        reg = self._registry()
        first = reg["releases"][0]["release_id"]
        second = reg["releases"][1]["release_id"]
        reg = engine.apply_policy(reg, self._policy(first, rationale="first decision"))
        reg = engine.apply_policy(reg, self._policy(second, rationale="supersedes first"))
        self.assertFalse(any(r.get("recommended") for r in reg["releases"] if r["release_id"] == first))
        self.assertEqual(reg["policy"]["rationale"], "supersedes first")


class TestPolicyCarryOver(unittest.TestCase):
    """Reality-sync regeneration must preserve policy decisions (P1.3)."""

    def _policy(self, release_id, by="ember-observatory", rationale="Banking edition validated on field telemetry."):
        return {
            "release_id": release_id,
            "recommended_by": by,
            "rationale": rationale,
            "decided_at": "2026-09-16",
        }

    def test_generator_carries_recommendation(self):
        from scripts_helper import load_generator

        gen = load_generator()
        reg = copy.deepcopy(FIXTURE)
        # Target the fixture's own manager release: the generator derives
        # release_id from the tag, so payload and policy must agree.
        mgr = next(r for r in FIXTURE["releases"] if r["kind"] == "manager")
        rid = mgr["release_id"]
        reg = engine.apply_policy(reg, self._policy(rid))
        asset = next(a for a in mgr["assets"] if a.get("role") == "package")
        payload = [
            {
                "tag_name": mgr["tag"],
                "published_at": mgr["published_at"],
                "draft": False,
                "prerelease": False,
                "assets": [
                    {
                        "name": asset["filename"],
                        "size": asset.get("size_bytes", 1),
                        "browser_download_url": f"https://example.invalid/{asset['filename']}",
                    }
                ],
            }
        ]
        # Offline generation: the compute-fallback is patched to fixture truth.
        with mock.patch.object(gen, "sha256_of_asset", side_effect=lambda a, retries=3: asset["sha256"]):
            out = gen.generate(payload, reg)
        target = next(r for r in out["releases"] if r["release_id"] == rid)
        self.assertTrue(target.get("recommended"), "regeneration must carry the policy decision")
        self.assertEqual(out["policy"]["recommended_by"], "ember-observatory")


class TestPolicyAndVerifyCli(unittest.TestCase):
    """The new engine commands are wired into the CLI."""

    def _cli_text(self):
        return (REPO_ROOT / "platform" / "release-engine" / "release_engine" / "__main__.py").read_text(encoding="utf-8")

    def test_verify_command_exists(self):
        self.assertIn('"verify"', self._cli_text())

    def test_apply_policy_command_exists(self):
        self.assertIn('"apply-policy"', self._cli_text())

    def test_engine_exports(self):
        for name in ("verify_vault", "apply_policy", "PolicyError"):
            self.assertTrue(hasattr(engine, name), f"engine must export {name}")


if __name__ == "__main__":
    unittest.main()
