"""CLI: python -m platform.release_engine [validate|latest|release ID]"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path as _Path

sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from release_engine import load, validate_file  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="platform.release_engine", description="Emberbird Release Engine")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("validate", help="Run registry integrity checks")
    sub.add_parser("latest", help="Show latest WSA and Manager releases")
    rel_parser = sub.add_parser("release", help="Show one release by id")
    rel_parser.add_argument("release_id")
    args = parser.parse_args(argv)

    if args.command in (None, "validate"):
        return validate_file()
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
    return 2


if __name__ == "__main__":
    sys.exit(main())
