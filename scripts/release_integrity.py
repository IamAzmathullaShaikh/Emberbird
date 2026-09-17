#!/usr/bin/env python3
"""release_integrity.py — Publication Integrity Gate.

The Releases section is the platform's public download surface. Nothing may
reach it that is not a genuine build artifact. This module is the machine that
enforces that rule, so the check never depends on a human reading a log line.

Three verdicts exist, and only one of them is publishable:

  REAL          Container/executable signature matches the declared artifact
                kind and the payload is at or above the plausible-size floor.
  PLACEHOLDER   The bytes carry staging-scaffold markers emitted by
                ``scripts/build_release_candidates.py`` when no real toolchain
                was available (mock WSA package, mock Manager payload).
  UNVERIFIABLE  Signature missing/invalid or the payload is implausibly small
                for its kind — e.g. a 56-byte file claiming to be an installer.

CONTRACT: publishing (``upload_github_release_assets.py``, ``publish_release.py``)
MUST refuse PLACEHOLDER and UNVERIFIABLE artifacts. Fabricating a release asset
is a Responsible-AI violation: users download these files and run them.

stdlib only; deterministic; no network.
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional, Sequence

REAL = "REAL"
PLACEHOLDER = "PLACEHOLDER"
UNVERIFIABLE = "UNVERIFIABLE"

# Byte markers written by the staging scaffold. Their presence is proof that a
# candidate was generated without a real build toolchain.
PLACEHOLDER_MARKERS: tuple[bytes, ...] = (
    b"MZ_EMBERBIRD",
    b"PK_EMBERBIRD",
    b"PAYLOAD_V",
    b"MAGISK_BOOT_IMG_HEADER",
    b"CLEAN_BOOT_IMG_HEADER",
    b"EMBERBIRD_SCAFFOLD",
)

# Plausible-size floors (bytes). A real Windows installer is never 56 bytes.
MIN_BYTES = {
    "installer": 1 << 20,          # 1 MiB
    "desktop-binary": 1 << 20,     # 1 MiB
    "portable": 1 << 18,           # 256 KiB
    "subsystem-archive": 100 << 20,  # 100 MiB
    "metadata": 1,
}

# Archives larger than this are not opened entry-by-entry: a real Emberbird
# subsystem archive is hundreds of MiB, while the staging scaffold is kilobytes.
ARCHIVE_SCAN_LIMIT = 8 << 20

ZIP_LOCAL_HEADER = b"PK\x03\x04"
ZIP_EMPTY_HEADER = b"PK\x05\x06"
SEVEN_ZIP_SIGNATURE = b"7z\xbc\xaf\x27\x1c"
PE_HEADER = b"PE\x00\x00"

_HEX64 = re.compile(r"\b[a-fA-F0-9]{64}\b")
_HEX128 = re.compile(r"\b[a-fA-F0-9]{128}\b")
_PLACEHOLDER_HASH = re.compile(
    r"(REQUIRES REPOSITORY VERIFICATION|0{64}|f{64}\b|PLACEHOLDER)", re.IGNORECASE
)


@dataclass
class ArtifactVerdict:
    path: Path
    kind: str
    size_bytes: int
    verdict: str = REAL
    reasons: list[str] = field(default_factory=list)

    @property
    def publishable(self) -> bool:
        return self.verdict == REAL

    def to_dict(self) -> dict:
        return {
            "artifact": self.path.name,
            "kind": self.kind,
            "size_bytes": self.size_bytes,
            "verdict": self.verdict,
            "reasons": list(self.reasons),
        }


def classify_kind(filename: str) -> str:
    """Infer the artifact role from its published filename."""
    name = filename.lower()
    if name.endswith(".exe"):
        if "setup" in name or "installer" in name:
            return "installer"
        return "desktop-binary"
    if name.endswith(".zip"):
        return "portable" if "portable" in name else "subsystem-archive"
    if name.endswith(".7z"):
        return "subsystem-archive"
    return "metadata"


def _read_head(path: Path, count: int = 4096) -> bytes:
    with open(path, "rb") as f:
        return f.read(count)


def _read_pe_signature(path: Path) -> bool:
    """A PE file points to its 'PE\\0\\0' signature through the DOS header."""
    try:
        with open(path, "rb") as f:
            head = f.read(0x40)
            if len(head) < 0x40 or head[:2] != b"MZ":
                return False
            e_lfanew = int.from_bytes(head[0x3C:0x40], "little")
            if e_lfanew <= 0 or e_lfanew > 1 << 24:
                return False
            f.seek(e_lfanew)
            return f.read(4) == PE_HEADER
    except OSError:
        return False


def find_scaffold_marker_in_zip(path: Path) -> Optional[bytes]:
    """Detect scaffold bytes hidden inside a real ZIP container.

    The candidate builder stages its mock package as a directory and the packager
    then compresses it, so the scaffold markers end up *inside* a legitimate ZIP.
    A header-only check would pass such an archive; this looks through the entries.
    """
    try:
        if path.stat().st_size > ARCHIVE_SCAN_LIMIT:
            return None
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                if name.endswith("/"):
                    continue
                with zf.open(name) as handle:
                    entry_head = handle.read(4096)
                for marker in PLACEHOLDER_MARKERS:
                    if marker in entry_head:
                        return marker
    except (zipfile.BadZipFile, OSError, RuntimeError):
        return None
    return None


def classify_artifact(path: Path) -> ArtifactVerdict:
    """Classify a single candidate artifact."""
    path = Path(path)
    kind = classify_kind(path.name)
    verdict = ArtifactVerdict(path=path, kind=kind, size_bytes=0)

    if not path.is_file():
        verdict.verdict = UNVERIFIABLE
        verdict.reasons.append("file does not exist")
        return verdict

    size = path.stat().st_size
    verdict.size_bytes = size

    if size == 0:
        verdict.verdict = UNVERIFIABLE
        verdict.reasons.append("zero-byte artifact")
        return verdict

    head = _read_head(path)

    for marker in PLACEHOLDER_MARKERS:
        if marker in head:
            verdict.verdict = PLACEHOLDER
            verdict.reasons.append(
                f"staging scaffold marker {marker!r} present - not a real build"
            )
            return verdict

    # A scaffold package compressed by the packager hides its markers inside a
    # legitimate container, so the container itself must be inspected.
    if head.startswith(ZIP_LOCAL_HEADER) or head.startswith(ZIP_EMPTY_HEADER):
        hidden = find_scaffold_marker_in_zip(path)
        if hidden is not None:
            verdict.verdict = PLACEHOLDER
            verdict.reasons.append(
                f"archive contains staging scaffold marker {hidden!r} "
                "- not a real build"
            )
            return verdict

    floor = MIN_BYTES.get(kind, 1)
    if size < floor:
        verdict.verdict = UNVERIFIABLE
        verdict.reasons.append(
            f"{size} bytes is below the {floor}-byte floor for kind '{kind}'"
        )
        return verdict

    if kind in ("installer", "desktop-binary"):
        if not _read_pe_signature(path):
            verdict.verdict = UNVERIFIABLE
            verdict.reasons.append("missing MZ/PE executable signature")
            return verdict
    elif kind in ("portable", "subsystem-archive"):
        if path.suffix.lower() == ".7z":
            if not head.startswith(SEVEN_ZIP_SIGNATURE):
                verdict.verdict = UNVERIFIABLE
                verdict.reasons.append("missing 7z archive signature")
                return verdict
        elif not (head.startswith(ZIP_LOCAL_HEADER) or head.startswith(ZIP_EMPTY_HEADER)):
            verdict.verdict = UNVERIFIABLE
            verdict.reasons.append("missing ZIP archive signature")
            return verdict
    else:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            verdict.verdict = UNVERIFIABLE
            verdict.reasons.append("metadata artifact is not valid UTF-8 text")
            return verdict
        if _PLACEHOLDER_HASH.search(text):
            verdict.verdict = UNVERIFIABLE
            verdict.reasons.append("checksum manifest contains a placeholder hash")
            return verdict
        if "checksum" in path.name.lower() and not (
            _HEX64.search(text) or _HEX128.search(text)
        ):
            verdict.verdict = UNVERIFIABLE
            verdict.reasons.append(
                "checksum manifest contains no SHA-256/512 hex digest"
            )
            return verdict

    verdict.reasons.append("container signature and size floor satisfied")
    return verdict


def audit_artifacts(paths: Iterable[Path]) -> list[ArtifactVerdict]:
    return [classify_artifact(Path(p)) for p in paths]


def collect_directory_artifacts(directory: Path) -> list[Path]:
    """Every regular file in a release directory, skipping internal metadata."""
    directory = Path(directory)
    if not directory.is_dir():
        return []
    skip = {
        "RELEASE_NOTES.md",
        "RELEASE_VALIDATION_REPORT.md",
        "github-release.json",
        "publish-github.sh",
        "publish-github.bat",
        "release-publication-manifest.json",
    }
    return sorted(
        p for p in directory.iterdir() if p.is_file() and p.name not in skip
    )


def gate_report(verdicts: Sequence[ArtifactVerdict]) -> dict:
    blocking = [v for v in verdicts if not v.publishable]
    return {
        "total": len(verdicts),
        "publishable": len(verdicts) - len(blocking),
        "blocking": len(blocking),
        "passed": not blocking,
        "artifacts": [v.to_dict() for v in verdicts],
    }


def format_report(verdicts: Sequence[ArtifactVerdict]) -> str:
    lines = ["", "=== Publication Integrity Gate ==="]
    for v in verdicts:
        mark = "+" if v.publishable else "!"
        lines.append(
            f"  [{mark}] {v.verdict:<12} {v.path.name} "
            f"({v.size_bytes} bytes, kind={v.kind})"
        )
        for reason in v.reasons:
            lines.append(f"        - {reason}")
    report = gate_report(verdicts)
    if report["passed"]:
        lines.append(
            f"  [+] Gate PASSED: {report['publishable']}/{report['total']} "
            "artifacts are genuine build outputs."
        )
    else:
        lines.append(
            f"  [!] Gate FAILED: {report['blocking']}/{report['total']} "
            "artifacts are NOT publishable. Refusing to publish fabricated "
            "or unverifiable release assets."
        )
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Publication Integrity Gate — audit release artifacts before publishing"
    )
    parser.add_argument("paths", nargs="*", type=Path, help="Artifact files to audit")
    parser.add_argument(
        "--dir",
        dest="directories",
        action="append",
        type=Path,
        default=[],
        help="Directory of artifacts to audit (repeatable)",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    targets: list[Path] = list(args.paths)
    for d in args.directories:
        targets.extend(collect_directory_artifacts(d))

    if not targets:
        print("[-] No artifacts supplied to audit.", flush=True)
        return 1

    verdicts = audit_artifacts(targets)
    if args.json:
        print(json.dumps(gate_report(verdicts), indent=2))
    else:
        print(format_report(verdicts))
    return 0 if gate_report(verdicts)["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
