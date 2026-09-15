"""CLI: python -m platform.release_engine [validate|latest|release ID]"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path as _Path

sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from release_engine import (  # noqa: E402
    REGISTRY_PATH,
    diff_registries,
    has_drift,
    load,
    validate_file,
    validate_schema_file,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="platform.release_engine", description="Emberbird Release Engine")
    sub = parser.add_subparsers(dest="command")
    validate_parser = sub.add_parser("validate", help="Run registry integrity checks")
    validate_parser.add_argument(
        "--schema", action="store_true",
        help="Also enforce the Draft-07 schema contract (CI Truth Gate)",
    )
    sub.add_parser("latest", help="Show latest WSA and Manager releases")
    rel_parser = sub.add_parser("release", help="Show one release by id")
    rel_parser.add_argument("release_id")
    diff_parser = sub.add_parser("diff", help="Diff registry state against a previous registry (drift detection)")
    diff_parser.add_argument("previous", help="Path to the previous releases.json snapshot")
    diff_parser.add_argument(
        "--fail-on-drift", action="store_true",
        help="Exit non-zero when drift is detected (policy gate)",
    )
    args = parser.parse_args(argv)

    if args.command in (None, "validate"):
        rc = validate_file()
        if args.schema and rc == 0:
            rc = validate_schema_file()
        return rc
    if args.command == "latest":
        reg = load()
        for label, rel in (("WSA", reg.latest_wsa()), ("Manager", reg.latest_manager())):
            if rel is None:
                print(f"{label}: (none)")
                continue
            print(f"{label}: {rel.release_id} tag={rel.tag} status={rel.status}")
            for a in rel.package_assets:
                print(f"    {a['filename']}  sha256={a['sha256'][:16]}...")
        return 0
    if args.command == "release":
        reg = load()
        rel = reg.by_id(args.release_id)
        if rel is None:
            print(f"unknown release_id: {args.release_id}")
            return 1
        print(json.dumps(rel.raw, indent=2))
        return 0
    if args.command == "diff":
        prev_path = _Path(args.previous)
        if not prev_path.is_file():
            print(f"previous registry not found: {prev_path}")
            return 1
        try:
            previous = json.loads(prev_path.read_text(encoding="utf-8"))
            # Read the current registry directly: drift analysis must work
            # even when the current state fails integrity checks (that is
            # exactly when it is most needed). `validate` owns integrity.
            current = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        except Exception as err:
            print(f"diff failed: {err}")
            return 1
        diff = diff_registries(previous, current)
        if not has_drift(diff):
            print("NO DRIFT: registries are semantically identical")
            return 0
        print("DRIFT DETECTED:")
        if diff["added_releases"]:
            print(f"  added releases:   {diff['added_releases']}")
        if diff["removed_releases"]:
            print(f"  removed releases: {diff['removed_releases']}")
        if diff["hash_changes"]:
            print(f"  hash changes:     {len(diff['hash_changes'])}")
            for c in diff["hash_changes"][:10]:
                print(f"    - {c}")
        if diff["status_changes"]:
            print(f"  status changes:   {diff['status_changes']}")
        return 2 if args.fail_on_drift else 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
