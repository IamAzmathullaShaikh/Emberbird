"""CLI: python -m platform.release_engine [validate|latest|release ID]"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path as _Path

sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from release_engine import (  # noqa: E402
    REGISTRY_PATH,
    PolicyError,
    apply_policy,
    diff_registries,
    has_drift,
    load,
    utc_now_iso,
    validate_file,
    validate_schema_file,
    verify_vault,
)


def _network_fetcher(entry: dict) -> str:
    """Real fetcher for `verify`: stream the published artifact and hash it.
    The engine core never touches the network; this is the CLI's bridge."""
    digest = hashlib.sha256()
    with urllib.request.urlopen(entry["source_url"], timeout=120) as resp:  # noqa: S310
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


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
        "--current", default=None,
        help="Path to the current releases.json snapshot (defaults to data/releases/releases.json)",
    )
    diff_parser.add_argument(
        "--fail-on-drift", action="store_true",
        help="Exit non-zero when drift is detected (policy gate)",
    )
    verify_parser = sub.add_parser(
        "verify",
        help="Verify vault mirror statuses against published reality (network)",
    )
    verify_parser.add_argument(
        "--registry", default=None,
        help="Path to the registry to verify (default: data/releases/releases.json)",
    )
    verify_parser.add_argument(
        "--write", action="store_true",
        help="Persist updated mirror statuses back to the registry",
    )
    apply_parser = sub.add_parser(
        "apply-policy",
        help="Set the recommended release from a policy decision (clause 9)",
    )
    apply_parser.add_argument("--decision", required=True, help="Path to a policy decision JSON file")
    apply_parser.add_argument("--registry", default=None, help="Path to the registry (default: data/releases/releases.json)")
    apply_parser.add_argument(
        "--output", default=None,
        help="Write the updated registry here instead of in place",
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
    if args.command == "verify":
        reg_path = _Path(args.registry) if args.registry else REGISTRY_PATH
        if not reg_path.is_file():
            print(f"registry not found: {reg_path}")
            return 1
        registry = json.loads(reg_path.read_text(encoding="utf-8"))
        report = verify_vault(registry, _network_fetcher)
        print(
            f"VERIFY: checked={report['checked']} verified={report['verified']} "
            f"mismatches={len(report['mismatches'])} errors={len(report['errors'])}"
        )
        for m in report["mismatches"]:
            print(f"  MISMATCH {m['artifact']}: expected={m['expected']} actual={m['actual']}")
        for e in report["errors"]:
            print(f"  ERROR    {e['artifact']}: {e['error']}")
        if args.write:
            reg_path.write_text(
                json.dumps(registry, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
            )
            print(f"updated registry written: {reg_path}")
        return 0 if not report["mismatches"] else 1
    if args.command == "apply-policy":
        reg_path = _Path(args.registry) if args.registry else REGISTRY_PATH
        decision_path = _Path(args.decision)
        if not reg_path.is_file():
            print(f"registry not found: {reg_path}")
            return 1
        if not decision_path.is_file():
            print(f"decision file not found: {decision_path}")
            return 1
        registry = json.loads(reg_path.read_text(encoding="utf-8"))
        try:
            decision = json.loads(decision_path.read_text(encoding="utf-8"))
            updated = apply_policy(registry, decision)
        except (PolicyError, json.JSONDecodeError) as err:
            print(f"apply-policy refused: {err}")
            return 1
        out_path = _Path(args.output) if args.output else reg_path
        out_path.write_text(
            json.dumps(updated, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
        )
        print(f"policy applied: recommended={decision.get('release_id')} by={updated['policy']['recommended_by']}")
        return 0
    if args.command == "diff":
        prev_path = _Path(args.previous)
        if not prev_path.is_file():
            print(f"previous registry not found: {prev_path}")
            return 1
        curr_path = _Path(args.current) if args.current else REGISTRY_PATH
        if not curr_path.is_file():
            print(f"current registry not found: {curr_path}")
            return 1
        try:
            previous = json.loads(prev_path.read_text(encoding="utf-8"))
            # Read current registry directly: drift analysis must work
            # even when current state fails integrity checks (that is
            # exactly when it is most needed). `validate` owns integrity.
            current = json.loads(curr_path.read_text(encoding="utf-8"))
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
