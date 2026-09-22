#!/usr/bin/env python3
"""test_cli.py — contract tests for the `emberbird` CLI (PH-20).

The CLI must stay a *surface* over the platform engines, never a second
implementation. These tests pin that by cross-checking its output against the
engines and the registry directly, so a CLI that began inventing facts — the
exact failure this project has already been bitten by — would fail here rather
than look plausible.
"""

from __future__ import annotations

import contextlib
import io
import json
import platform as host
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_DIR = REPO_ROOT / "platform" / "cli"
if str(CLI_DIR) not in sys.path:
    sys.path.insert(0, str(CLI_DIR))

from emberbird.__main__ import main  # noqa: E402

REGISTRY_PATH = REPO_ROOT / "data" / "releases" / "releases.json"


def run_cli(*argv: str) -> tuple[int, str]:
    """Invoke the CLI in-process, capturing stdout and any argparse noise."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        code = main(list(argv))
    return code, buffer.getvalue()


def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


class TestCliSurface(unittest.TestCase):
    def test_version_reports_the_cli_and_the_registry_contract(self):
        code, out = run_cli("version", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertTrue(payload["cli"], "the CLI must report its own version")
        self.assertEqual(payload["registry"]["schema_version"], registry()["schema_version"])

    def test_status_host_facts_come_from_the_running_machine(self):
        code, out = run_cli("status", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["host"]["system"], host.system())
        self.assertEqual(payload["host"]["machine"], host.machine())

    def test_status_reports_registry_truth_without_inventing_a_number(self):
        code, out = run_cli("status", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        truth = registry()
        self.assertEqual(payload["registry"]["release_count"], len(truth["releases"]))
        self.assertEqual(
            payload["registry"]["generated_at"], truth["generation"]["generated_at"]
        )

    def test_status_latest_matches_the_registrys_newest_entry_per_kind(self):
        payload = json.loads(run_cli("status", "--json")[1])
        truth = registry()
        for entry in payload["registry"]["latest"]:
            same_kind = [r for r in truth["releases"] if r.get("kind") == entry["kind"]]
            self.assertTrue(same_kind, f"CLI reported an unknown kind: {entry['kind']!r}")
            newest = max(same_kind, key=lambda r: r.get("published_at", ""))
            self.assertEqual(entry["release_id"], newest["release_id"])

    def test_doctor_json_is_the_engine_report_not_a_summary(self):
        code, out = run_cli("doctor", "--json")
        payload = json.loads(out)
        # The CLI must pass the engine's verdict through, not compute its own.
        self.assertEqual(code, payload["exit_code"])
        expected = 2 if payload["fail_count"] else (1 if payload["warn_count"] else 0)
        self.assertEqual(code, expected, "exit code must follow the engine's own contract")
        self.assertEqual(len(payload["probes"]), 12)
        self.assertEqual(len(payload["probes"]), payload["total_probes"])
        # The PH-05 fields prove the CLI delegates to the engine instead of
        # re-deriving probe output for itself.
        for probe in payload["probes"]:
            for key in ("evidence", "timestamp", "verification"):
                self.assertIn(key, probe, f"{probe['probe_id']} missing {key}")

    def test_registry_delegates_to_the_release_engine(self):
        code, out = run_cli("registry", "latest")
        self.assertEqual(code, 0)
        tags = {r["tag"] for r in registry()["releases"]}
        self.assertTrue(
            any(tag in out for tag in tags),
            f"registry latest printed no known release tag: {out!r}",
        )

    def test_no_subcommand_prints_help_and_fails(self):
        code, out = run_cli()
        self.assertEqual(code, 2)
        self.assertIn("usage: emberbird", out)

    def test_unknown_subcommand_is_rejected(self):
        with self.assertRaises(SystemExit) as caught:
            run_cli("teleport")
        self.assertNotEqual(caught.exception.code, 0)

    def test_cli_runs_as_a_user_would_invoke_it(self):
        """Run the entry point as a subprocess, not in-process.

        The in-process tests above cannot catch an import that only resolves
        because the test happened to put the package root on `sys.path` — which
        is exactly how `emberbird version` first crashed when run as a script.
        """
        script = REPO_ROOT / "platform" / "cli" / "emberbird" / "__main__.py"
        for argv in (["version", "--json"], ["status", "--json"]):
            result = subprocess.run(
                [sys.executable, str(script), *argv],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(result.returncode, 0, f"{argv}: {result.stderr}")
            payload = json.loads(result.stdout)
            self.assertTrue(payload, f"{argv} produced no JSON")

    def test_deferred_capabilities_are_absent_rather_than_stubbed(self):
        """Anti-Stub rule 16: a subcommand exists only when it does real work.

        `runtime`, `app`, `backup`, `update` and `logs` depend on surfaces that
        do not exist yet, so they must not appear as stubs. When one is built,
        this test fails and the roadmap must be updated to claim it.
        """
        for deferred in ("runtime", "app", "backup", "update", "logs"):
            with self.assertRaises(SystemExit, msg=f"{deferred} must not exist yet"):
                run_cli(deferred)


if __name__ == "__main__":
    unittest.main()
