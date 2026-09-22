"""The lifecycle read-side contract (PH-02 Python side, PH-20 CLI surface).

The Rust core owns the lifecycle; ``platform/lifecycle`` reads the snapshot it
writes and applies the same recovery rules. These tests pin that contract in
both directions — derived from the Rust source where possible, so the two
sides cannot drift silently.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUST_RUNTIME_STATE = ROOT / "apps/manager/src-tauri/src/runtime_state.rs"
CLI_SCRIPT = ROOT / "platform/cli/emberbird/__main__.py"

sys.path.insert(0, str(ROOT / "platform"))

import lifecycle  # noqa: E402


def screaming_snake(name: str) -> str:
    """Rust variant name -> serde SCREAMING_SNAKE_CASE wire name."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).upper()


def rust_source() -> str:
    return RUST_RUNTIME_STATE.read_text(encoding="utf-8")


class TestLifecycleContract(unittest.TestCase):
    """The Python reader must agree with the Rust engine it reads from."""

    def test_schema_version_matches_the_rust_engine(self):
        match = re.search(
            r"pub const LIFECYCLE_SCHEMA_VERSION: u32 = (\d+);", rust_source()
        )
        self.assertIsNotNone(match, "failed to parse LIFECYCLE_SCHEMA_VERSION from runtime_state.rs")
        self.assertEqual(lifecycle.SCHEMA_VERSION, int(match.group(1)))

    def test_every_rust_state_is_known_to_the_python_reader(self):
        match = re.search(r"pub enum RuntimeState\s*\{([^}]+)\}", rust_source(), re.DOTALL)
        self.assertIsNotNone(match, "failed to parse the RuntimeState enum")
        rust_states = {
            screaming_snake(v.strip())
            for v in match.group(1).split(",")
            if v.strip() and not v.strip().startswith("//")
        }
        self.assertEqual(len(rust_states), 14, f"expected 14 Rust states, found {rust_states}")
        missing = rust_states - lifecycle.KNOWN_STATES
        self.assertEqual(missing, set(), f"Rust states unknown to the Python reader: {missing}")

    def test_recovery_rules_match_the_rust_engine(self):
        """Parse Rust ``fn reconcile`` and require identical rules."""
        source = rust_source()
        match = re.search(r"fn reconcile\(persisted: RuntimeState\) -> Option<\(RuntimeState, RecoveryAction\)> \{(.*?)\n\}", source, re.DOTALL)
        self.assertIsNotNone(match, "failed to parse fn reconcile from runtime_state.rs")
        body = match.group(1)

        rust_rules: dict[str, tuple[str | None, str | None]] = {}
        # Strip comments so prose cannot look like code (the recurring trap).
        body = re.sub(r"//[^\n]*", "", body)
        for arm in re.finditer(
            r"([A-Za-z_0-9 |]+?)=>\s*(None|Some\(\((\w+),\s*RecoveryAction::(\w+)\)\))",
            body,
        ):
            variants = [v.strip() for v in arm.group(1).split("|") if v.strip()]
            if arm.group(2) == "None":
                for variant in variants:
                    rust_rules[screaming_snake(variant)] = (None, None)
            else:
                target = screaming_snake(arm.group(3))
                # RecoveryAction's wire token (RecoveryAction::as_str) is the
                # SCREAMING_SNAKE_CASE form of the Rust variant.
                action = screaming_snake(arm.group(4))
                for variant in variants:
                    rust_rules[screaming_snake(variant)] = (target, action)

        self.assertTrue(rust_rules, "parsed no reconcile arms — the guard is blind, not the code clean")
        self.assertEqual(
            lifecycle.RECOVERY_RULES,
            rust_rules,
            "Python recovery rules drifted from the Rust engine's fn reconcile",
        )

    def test_recovery_never_promotes_and_never_claims_in_flight(self):
        """Property: recovery is less-or-equally specific, never in-flight."""
        for state in lifecycle.KNOWN_STATES:
            verdict = lifecycle.recover(state)
            self.assertFalse(
                verdict["presumed"] in lifecycle.BUSY_STATES,
                f"recovery of {state} claims in-flight {verdict['presumed']}",
            )
            self.assertNotEqual(verdict["presumed"], "RUNNING", "a restart cannot prove RUNNING")

    def test_recovery_outcome_matches_the_rust_classification(self):
        # Rust: Interrupted exactly when the persisted state was busy.
        self.assertEqual(lifecycle.recover("INSTALLING")["outcome"], "INTERRUPTED")
        self.assertEqual(lifecycle.recover("UPDATING")["outcome"], "INTERRUPTED")
        self.assertEqual(lifecycle.recover("RUNNING")["outcome"], "RE_ESTABLISHED")
        self.assertEqual(lifecycle.recover("DEGRADED")["outcome"], "RE_ESTABLISHED")
        self.assertEqual(lifecycle.recover("INSTALLED")["outcome"], "RESTORED")


class TestSnapshotReading(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.snapshot = Path(self.tmp.name) / "lifecycle.json"

    def write_snapshot(self, body: str):
        self.snapshot.write_text(body, encoding="utf-8")

    def test_absence_is_evidence_not_an_error(self):
        self.assertIsNone(lifecycle.read_snapshot(self.snapshot))
        report = lifecycle.describe(self.snapshot)
        self.assertFalse(report["snapshot_present"])
        self.assertEqual(report["path"], str(self.snapshot))

    def test_a_valid_snapshot_round_trips_with_its_trail(self):
        self.write_snapshot(
            json.dumps(
                {
                    "version": lifecycle.SCHEMA_VERSION,
                    "state": "RUNNING",
                    "history": [
                        {"from": "INSTALLED", "to": "STARTING", "at": "2026-09-22T00:00:00.000Z", "reason": "launch"},
                        {"from": "STARTING", "to": "RUNNING", "at": "2026-09-22T00:00:05.000Z", "reason": "health check passed"},
                    ],
                }
            )
        )
        report = lifecycle.describe(self.snapshot)
        self.assertTrue(report["snapshot_present"])
        self.assertEqual(report["recovery"]["presumed"], "INSTALLED")
        self.assertEqual(report["recovery"]["action"], "RESTART")
        self.assertEqual(len(report["trail"]), 2)
        self.assertEqual(report["last_move_at"], "2026-09-22T00:00:05.000Z")

    def test_a_corrupt_snapshot_raises_and_is_never_guessed(self):
        self.write_snapshot("{ this is not json")
        with self.assertRaises(lifecycle.LifecycleSnapshotError):
            lifecycle.read_snapshot(self.snapshot)

    def test_a_future_schema_raises_with_its_version(self):
        self.write_snapshot(json.dumps({"version": lifecycle.SCHEMA_VERSION + 3, "state": "INSTALLED", "history": []}))
        with self.assertRaises(lifecycle.LifecycleSnapshotError) as ctx:
            lifecycle.read_snapshot(self.snapshot)
        self.assertIn(str(lifecycle.SCHEMA_VERSION + 3), str(ctx.exception))

    def test_an_unknown_state_raises(self):
        self.write_snapshot(json.dumps({"version": lifecycle.SCHEMA_VERSION, "state": "SOMETHING_ELSE", "history": []}))
        with self.assertRaises(lifecycle.LifecycleSnapshotError):
            lifecycle.read_snapshot(self.snapshot)


class TestLifecycleCLI(unittest.TestCase):
    """The CLI surface reports the snapshot through the engine — as a user runs it."""

    def run_cli(self, *argv: str, extra_env: dict[str, str] | None = None):
        env = dict(os.environ)
        env.update(extra_env or {})
        return subprocess.run(
            [sys.executable, str(CLI_SCRIPT), *argv],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )

    def test_lifecycle_reports_an_absent_snapshot_without_inventing_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.json"
            result = self.run_cli("lifecycle", "--json", extra_env={"EMBERBIRD_LIFECYCLE_PATH": str(path)})
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["snapshot_present"])
            self.assertNotIn("recovered_state", payload, "no snapshot means no state claim")

    def test_lifecycle_reports_a_recovered_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lifecycle.json"
            path.write_text(
                json.dumps(
                    {
                        "version": lifecycle.SCHEMA_VERSION,
                        "state": "UPDATING",
                        "history": [
                            {"from": "INSTALLED", "to": "UPDATING", "at": "2026-09-22T00:00:00.000Z", "reason": "upgrade started"}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = self.run_cli("lifecycle", "--json", extra_env={"EMBERBIRD_LIFECYCLE_PATH": str(path)})
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["was"], "UPDATING")
            self.assertEqual(payload["recovered_state"], "BROKEN")
            self.assertEqual(payload["action"], "ROLL_BACK")
            self.assertEqual(payload["outcome"], "INTERRUPTED")

    def test_lifecycle_refuses_a_corrupt_snapshot_with_a_failure_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lifecycle.json"
            path.write_text("not json {", encoding="utf-8")
            result = self.run_cli("lifecycle", "--json", extra_env={"EMBERBIRD_LIFECYCLE_PATH": str(path)})
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertIn("error", payload)

    def test_lifecycle_subcommand_runs_as_a_user_would_invoke_it(self):
        result = self.run_cli("lifecycle")
        # Either a real report or the honest no-snapshot note — never a crash.
        self.assertIn(result.returncode, (0, 1), result.stderr)
        self.assertTrue(result.stdout.strip(), "the CLI must always explain itself")


if __name__ == "__main__":
    unittest.main()
