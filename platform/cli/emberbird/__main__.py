#!/usr/bin/env python3
"""emberbird — the Emberbird command-line interface (PH-20).

A single entry point over the platform engines. This module owns argument
parsing and presentation **only**: it never reimplements a probe, a registry
lookup or a status rule, so it cannot disagree with the engines it reports on.

Functional today:

    emberbird version            CLI, Python and registry versions
    emberbird status            host facts and registry truth
    emberbird doctor [--fix]    the host diagnostic engine
    emberbird lifecycle [--path P]  reconciled runtime lifecycle (read-only)
    emberbird registry <cmd>    delegated to the release engine

Recorded as pending in TODO.md (PH-20) rather than stubbed here — each needs a
surface that does not exist yet:

    runtime …   needs PH-08 (runtime control)
    app …       needs PH-09 (app manager)
    backup …    needs PH-16 (backup engine)
    update …    needs PH-17 (update engine)
    logs        needs PH-45 (observability)

Anti-Stub rule 16 applies: a subcommand exists here only when it does real work.
"""

from __future__ import annotations

import argparse
import importlib
import json
import platform as host
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
PLATFORM_DIR = REPO_ROOT / "platform"
CLI_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "data" / "releases" / "releases.json"

# Every root the CLI must be able to import from: its own package (so the file
# also works when run as a plain script, not only as an installed console
# script) plus the sibling platform engines.
IMPORT_ROOTS = (CLI_ROOT, PLATFORM_DIR, PLATFORM_DIR / "release-engine")


def _import_roots_on_path() -> None:
    for root in IMPORT_ROOTS:
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))


def _cli_version() -> str:
    _import_roots_on_path()
    return importlib.import_module("emberbird").__version__


def _load_engine(module: str):
    """Import a platform engine, or fail loudly. Never invent data as a fallback."""
    _import_roots_on_path()
    try:
        return importlib.import_module(module)
    except ImportError as exc:  # pragma: no cover - depends on checkout layout
        raise SystemExit(f"emberbird: cannot load the {module} engine from {PLATFORM_DIR}: {exc}")


def _load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.is_file():
        raise SystemExit(f"emberbird: registry not found at {REGISTRY_PATH}")
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"emberbird: registry at {REGISTRY_PATH} is not valid JSON: {exc}")


def _latest_per_kind(registry: dict[str, Any]) -> list[dict[str, Any]]:
    """The newest published release per kind, read straight from the registry."""
    newest: dict[str, dict[str, Any]] = {}
    for release in registry.get("releases", []):
        kind = str(release.get("kind", "unknown"))
        current = newest.get(kind)
        if current is None or release.get("published_at", "") > current.get("published_at", ""):
            newest[kind] = release
    return [
        {
            "kind": kind,
            "release_id": release.get("release_id"),
            "tag": release.get("tag"),
            "channel": release.get("channel"),
            "edition": release.get("edition"),
            "architectures": release.get("architectures", []),
            "status": release.get("status"),
            "published_at": release.get("published_at"),
            "recommended": bool(release.get("recommended", False)),
        }
        for kind, release in sorted(newest.items())
    ]


def _emit(payload: dict[str, Any], as_json: bool, lines: list[str]) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=False))
        return
    for line in lines:
        print(line)


def cmd_version(args: argparse.Namespace) -> int:
    registry = _load_registry()
    payload = {
        "cli": _cli_version(),
        "python": host.python_version(),
        "registry": {
            "schema_version": registry.get("schema_version"),
            "migration_version": registry.get("migration_version"),
            "compatibility_level": registry.get("compatibility_level"),
        },
    }
    registry_line = payload["registry"]
    _emit(
        payload,
        args.json,
        [
            f"emberbird CLI    {payload['cli']}",
            f"python           {payload['python']}",
            f"registry schema  {registry_line['schema_version']} "
            f"(migration {registry_line['migration_version']}, "
            f"{registry_line['compatibility_level']})",
        ],
    )
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    doctor = _load_engine("doctor")
    registry = _load_registry()
    generation = registry.get("generation", {})
    latest = _latest_per_kind(registry)

    payload = {
        "host": {
            "system": host.system(),
            "release": host.release(),
            "machine": host.machine(),
            "is_windows": doctor.is_windows(),
            "elevated": doctor.is_admin(),
        },
        "registry": {
            "generated_at": generation.get("generated_at"),
            "generated_by": generation.get("tool"),
            "mode": generation.get("mode"),
            "release_count": len(registry.get("releases", [])),
            "latest": latest,
        },
    }

    host_info = payload["host"]
    lines = [
        f"host        {host_info['system']} {host_info['release']} ({host_info['machine']})",
        f"windows     {host_info['is_windows']}",
        f"elevated    {host_info['elevated']}",
        "",
        f"registry    {generation.get('generated_at')} "
        f"by {generation.get('tool')} ({generation.get('mode')})",
        f"releases    {payload['registry']['release_count']}",
    ]
    for entry in latest:
        marker = " (recommended)" if entry["recommended"] else ""
        lines.append(
            f"  latest {entry['kind']:<9} {entry['tag']} "
            f"[{entry['edition']}, {', '.join(entry['architectures'])}]{marker}"
        )
    _emit(payload, args.json, lines)
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    doctor = _load_engine("doctor")
    engine = doctor.DoctorEngine()

    if args.fix:
        code, logs = engine.apply_remediation(non_interactive=args.yes)
        for line in logs:
            print(line)
        return code

    report = engine.run_diagnostics()
    payload = report.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False))
        return report.exit_code

    print(f"Emberbird Doctor — {payload['platform_name']} {payload['version']}")
    print(f"host      {payload['system_os']} {payload['os_release']} ({payload['architecture']})")
    print(f"captured  {payload['captured_at']}")
    print()
    for probe in payload["probes"]:
        print(f"[{probe['status']:<3}] {probe['probe_id']}  {probe['title']}")
        if probe["status"] in ("FAIL", "WARN"):
            print(f"        {probe['summary']}")
            if probe.get("remediation_cmd"):
                print(f"        fix: {probe['remediation_cmd']}")
    print()
    print(
        f"{payload['passed_count']} pass · {payload['warn_count']} warn · "
        f"{payload['fail_count']} fail"
    )
    return report.exit_code


def cmd_lifecycle(args: argparse.Namespace) -> int:
    """Report the reconciled runtime lifecycle from the persisted snapshot.

    Read-only on purpose: transitions are the Manager's (and one day the CLI's
    own, via PH-20's control surface). What a CLI *can* do honestly today is
    read the same snapshot the Rust engine writes, apply the same recovery
    rules, and report — never inventing state when the file is absent or
    unreadable.
    """
    lifecycle = _load_engine("lifecycle")
    path = Path(args.path) if args.path else None
    try:
        report = lifecycle.describe(path)
    except lifecycle.LifecycleSnapshotError as exc:
        # Resolve the default path defensively: on hosts without LOCALAPPDATA
        # even *asking* for the default raises, and a crash inside an error
        # handler would leave the user with a traceback and no explanation.
        try:
            shown_path = str(path or lifecycle.default_snapshot_path())
        except lifecycle.LifecycleSnapshotError:
            shown_path = "(platform default; LOCALAPPDATA is not set)"
        payload = {"error": str(exc), "path": shown_path}
        _emit(payload, args.json, [f"lifecycle  unreadable: {exc}"])
        return 1

    if not report["snapshot_present"]:
        payload = {
            "snapshot_present": False,
            "path": report["path"],
            "note": (
                "No lifecycle snapshot exists. The Manager writes one when it "
                "reconciles runtime state; run the Manager once, or set "
                "EMBERBIRD_LIFECYCLE_PATH / --path to an explicit snapshot."
            ),
        }
        _emit(payload, args.json, [f"lifecycle  no snapshot at {report['path']}", payload["note"]])
        return 0

    recovery = report["recovery"]
    payload = {
        "snapshot_present": True,
        "path": report["path"],
        "schema_version": report["schema_version"],
        "recovered_state": recovery["presumed"],
        "was": recovery["was"],
        "action": recovery["action"],
        "outcome": recovery["outcome"],
        "last_move_at": report["last_move_at"],
        "trail_length": len(report["trail"]),
        "trail": report["trail"],
    }
    lines = [
        f"state      {recovery['presumed']} (recovered from {recovery['was']})",
        f"outcome    {recovery['outcome']}"
        + (f" — {recovery['action']}" if recovery["action"] else ""),
        f"trail      {len(report['trail'])} recorded moves, last at {report['last_move_at']}",
    ]
    _emit(payload, args.json, lines)
    return 0


def _delegate_registry(rest: list[str]) -> int:
    """Hand registry commands to the release engine — one implementation, not two."""
    _import_roots_on_path()
    try:
        engine_main = importlib.import_module("release_engine.__main__")
    except ImportError as exc:  # pragma: no cover - depends on checkout layout
        raise SystemExit(f"emberbird: cannot load the release engine: {exc}")
    return engine_main.main(rest)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="emberbird",
        description="Emberbird — diagnostics, status and registry truth.",
    )
    sub = parser.add_subparsers(dest="command")

    version_parser = sub.add_parser("version", help="CLI, Python and registry versions")
    version_parser.add_argument("--json", action="store_true", help="machine-readable output")

    status_parser = sub.add_parser("status", help="host facts and registry truth")
    status_parser.add_argument("--json", action="store_true", help="machine-readable output")

    doctor_parser = sub.add_parser("doctor", help="run the host diagnostic engine")
    doctor_parser.add_argument("--json", action="store_true", help="machine-readable output")
    doctor_parser.add_argument(
        "--fix",
        action="store_true",
        help="apply autofixable remediations (requires an elevated shell)",
    )
    doctor_parser.add_argument(
        "--yes",
        action="store_true",
        help="do not prompt before applying remediations",
    )

    lifecycle_parser = sub.add_parser(
        "lifecycle",
        help="report the reconciled runtime lifecycle from the persisted snapshot",
    )
    lifecycle_parser.add_argument("--json", action="store_true", help="machine-readable output")
    lifecycle_parser.add_argument(
        "--path",
        default=None,
        help="explicit snapshot path (default: %%LOCALAPPDATA%%\\Emberbird\\lifecycle.json, "
        "overridable via EMBERBIRD_LIFECYCLE_PATH)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # `registry` takes arbitrary pass-through arguments, so it is dispatched
    # before argparse rather than modelled as a subparser with REMAINDER.
    if argv and argv[0] == "registry":
        return _delegate_registry(argv[1:])

    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        "version": cmd_version,
        "status": cmd_status,
        "doctor": cmd_doctor,
        "lifecycle": cmd_lifecycle,
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 2
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
