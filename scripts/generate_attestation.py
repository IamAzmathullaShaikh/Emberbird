#!/usr/bin/env python3
"""PH-24 — Generate SLSA v0.2 provenance statements for release artifacts.

One in-toto statement per artifact, attesting what the pipeline can *actually*
know: the subject artifact's digest, the source commit it was built from, the
repository URI, and the resolved dependency manifests as materials. The
statement is honest by construction (zero-mock law):

- ``buildStartedOn``/``buildFinishedOn`` are the assembly timestamps (this
  script runs inside the build pipeline; it does not invent earlier times).
- ``completeness.environment`` is ``False`` — the toolchain is not pinned yet
  (that is PH-24's reproducible-builds item).
- ``reproducible`` is ``False`` until a rebuild-and-compare target proves it.
- No signing happens here: the statements are unsigned SLSA attestations,
  suitable for later signature by a key held outside this repo.

Structure follows https://slsa.dev/provenance/v0.2 (in-toto Statement v0.1
envelope) so standard verifiers can consume it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STATEMENT_TYPE = "https://in-toto.io/Statement/v0.1"
PREDICATE_TYPE = "https://slsa.dev/provenance/v0.2"
BUILDER_ID = "https://github.com/Emberbird-WSA/Emberbird/-/blob/main/scripts/assemble_production_release.py"
BUILD_TYPE = "https://emberbird.dev/buildtypes/release-assembly/v1"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(1 << 22):
            h.update(chunk)
    return h.hexdigest().lower()


def _git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def source_commit() -> str:
    """The commit the build claims to come from (overridable for hermetic CI)."""
    override = os.environ.get("EMBERBIRD_SOURCE_COMMIT", "").strip().lower()
    if override:
        return override
    return _git(["rev-parse", "HEAD"])


def source_uri() -> str:
    try:
        return _git(["remote", "get-url", "origin"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "https://github.com/Emberbird-WSA/Emberbird"


def _now_iso() -> str:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _materials() -> list[dict]:
    """What the build consumed: the source tree plus the pinned manifests."""
    materials = [
        {
            "uri": source_uri(),
            "digest": {"gitCommit": source_commit()},
        }
    ]
    cargo_lock = REPO / "apps" / "manager" / "src-tauri" / "Cargo.lock"
    if cargo_lock.is_file():
        materials.append(
            {
                "uri": f"file:{cargo_lock.relative_to(REPO).as_posix()}",
                "digest": {"sha256": sha256_file(cargo_lock)},
            }
        )
    return materials


def build_statement(artifact: Path, tag: str) -> dict:
    """One SLSA v0.2 statement attesting ``artifact``."""
    if not artifact.is_file():
        raise FileNotFoundError(f"cannot attest a missing artifact: {artifact}")
    commit = source_commit()
    if len(commit) != 40 or not all(c in "0123456789abcdef" for c in commit):
        raise ValueError(f"source commit is not a full git SHA: {commit!r}")
    now = _now_iso()
    return {
        "_type": STATEMENT_TYPE,
        "subject": [
            {"name": artifact.name, "digest": {"sha256": sha256_file(artifact)}}
        ],
        "predicateType": PREDICATE_TYPE,
        "predicate": {
            "builder": {"id": BUILDER_ID},
            "buildType": BUILD_TYPE,
            "invocation": {
                "configSource": {
                    "uri": source_uri(),
                    "digest": {"gitCommit": commit},
                    "entryPoint": "scripts/assemble_production_release.py",
                },
                "parameters": {"release_tag": tag},
                "environment": None,
            },
            "materials": _materials(),
            "metadata": {
                "buildInvocationID": f"emberbird-release-{tag}",
                "buildStartedOn": now,
                "buildFinishedOn": now,
                "completeness": {
                    # parameters: recorded above. environment: NOT pinned yet —
                    # claiming it would be a lie the verifier cannot check.
                    "parameters": True,
                    "environment": False,
                    "materials": True,
                },
                # PH-24's reproducible-build item must flip this with a
                # rebuild-and-compare proof, never by editing the flag.
                "reproducible": False,
            },
        },
    }


def validate_statement(statement: dict, artifact: Path) -> list[str]:
    """Structural + digest verification against the artifact on disk."""
    errors: list[str] = []
    if statement.get("_type") != STATEMENT_TYPE:
        errors.append(f"bad _type: {statement.get('_type')}")
    if statement.get("predicateType") != PREDICATE_TYPE:
        errors.append(f"bad predicateType: {statement.get('predicateType')}")
    subject = statement.get("subject", [])
    if len(subject) != 1:
        errors.append("statement must have exactly one subject")
    else:
        if subject[0].get("name") != artifact.name:
            errors.append(f"subject name mismatch: {subject[0].get('name')}")
        digest = subject[0].get("digest", {}).get("sha256")
        if digest != sha256_file(artifact):
            errors.append("subject sha256 does not match the artifact on disk")
    predicate = statement.get("predicate", {})
    invocation = predicate.get("invocation", {})
    commit = invocation.get("configSource", {}).get("digest", {}).get("gitCommit")
    if not commit or len(commit) != 40:
        errors.append(f"configSource digest must be a full git SHA, got: {commit}")
    materials = predicate.get("materials", [])
    if not materials:
        errors.append("materials must list at least the source tree")
    completeness = predicate.get("metadata", {}).get("completeness", {})
    if completeness.get("environment") is not False:
        errors.append(
            "completeness.environment must be False until the toolchain is pinned"
        )
    if predicate.get("metadata", {}).get("reproducible") is not False:
        errors.append(
            "reproducible must be False until a rebuild-and-compare target exists"
        )
    return errors


def write_attestations(dist_dir: Path, artifacts: list[Path], tag: str) -> Path:
    """Write one statement per artifact under ``<dist>/attestations/``."""
    out_dir = dist_dir / "attestations"
    out_dir.mkdir(parents=True, exist_ok=True)
    for artifact in artifacts:
        stmt = build_statement(artifact, tag)
        errors = validate_statement(stmt, artifact)
        if errors:
            for err in errors:
                print(f"ATTESTATION INVALID for {artifact.name}: {err}", file=sys.stderr)
            raise SystemExit(2)
        out = out_dir / f"{artifact.name}.prov.json"
        out.write_text(json.dumps(stmt, indent=2) + "\n", encoding="utf-8")
        try:
            shown = out.relative_to(REPO).as_posix()
        except ValueError:
            shown = str(out)
        print(f"attested {artifact.name} -> {shown}")
    return out_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument(
        "--artifacts",
        nargs="*",
        help="artifact filenames (default: every file in dist-dir except metadata/attestations)",
    )
    args = parser.parse_args(argv)

    if args.artifacts is None:
        skip_prefixes = ("checksums.", "release-metadata.json", "RELEASE_NOTES", "sbom.")
        args.artifacts = [
            p.name
            for p in sorted(args.dist_dir.iterdir())
            if p.is_file() and not p.name.startswith(skip_prefixes)
        ]

    artifacts = [args.dist_dir / name for name in args.artifacts]
    write_attestations(args.dist_dir, artifacts, args.tag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
