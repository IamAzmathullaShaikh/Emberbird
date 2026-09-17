#!/usr/bin/env python3
"""Emberbird Project Doctor — CLI Entry Point (Phase D1).

Command-line interface for the diagnostic and self-healing subsystem.

Usage:
  python -m platform.doctor              # Standard human-readable diagnostic scan
  python -m platform.doctor --json       # Machine-readable JSON output for integrations
  python -m platform.doctor --fix        # Interactive elevated remediation mode
  python -m platform.doctor --fix --yes  # Non-interactive elevated remediation
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure repo root and platform are importable
PLATFORM_DIR = Path(__file__).resolve().parent.parent
if str(PLATFORM_DIR) not in sys.path:
    sys.path.insert(0, str(PLATFORM_DIR))

from doctor import DoctorEngine, ProbeSeverity, ProbeStatus


def print_terminal_report(report) -> None:
    print("=" * 80)
    print(f"  Emberbird Doctor -- Host Diagnostic & Health Inspection (v{report.version})")
    print(f"  OS: {report.system_os} {report.os_release} ({report.architecture})")
    print(f"  Status: {report.overall_status.value} | Exit Code: {report.exit_code}")
    print(f"  Passed: {report.passed_count} | Warnings: {report.warn_count} | Failures: {report.fail_count}")
    print("=" * 80)
    print(f"{'Probe':<8} {'Domain':<24} {'Status':<8} {'Summary'}")
    print("-" * 80)

    for probe in report.probes:
        status_tag = probe.status.value
        print(f"{probe.probe_id:<8} {probe.domain:<24} {status_tag:<8} {probe.summary}")

    print("=" * 80)

    # If warnings or failures exist, print detailed recommendations
    actionable = [p for p in report.probes if p.status in (ProbeStatus.WARN, ProbeStatus.FAIL)]
    if actionable:
        print("\nACTIONABLE REMEDIATIONS & NEXT STEPS:")
        for idx, p in enumerate(actionable, 1):
            sev = p.severity.value
            print(f"\n{idx}. [{sev}] {p.probe_id}: {p.title}")
            print(f"   Details: {p.details}")
            if p.remediation_cmd:
                print(f"   Suggested Fix: {p.remediation_cmd}")
            if p.can_autofix:
                print(f"   --> Run 'python -m platform.doctor --fix' to automatically apply this fix.")
        print("\n" + "-" * 80)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m platform.doctor",
        description="Emberbird Project Doctor: WSA Host Virtualization Diagnostic & Self-Healing CLI",
    )
    parser.add_argument("--json", action="store_true", help="Emit structured machine-readable JSON output")
    parser.add_argument("--fix", action="store_true", help="Run elevated remediation for detected issues")
    parser.add_argument("-y", "--yes", action="store_true", help="Non-interactive mode for remediation")

    args = parser.parse_args(argv)
    engine = DoctorEngine()

    if args.fix:
        print("=" * 80)
        print("  Emberbird Doctor -- Elevated Self-Healing Remediation")
        print("=" * 80)
        code, logs = engine.apply_remediation(non_interactive=args.yes)
        for log in logs:
            print(log)
        return code

    report = engine.run_diagnostics()

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print_terminal_report(report)

    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
