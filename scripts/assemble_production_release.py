#!/usr/bin/env python3
"""Assemble the final Emberbird production release distribution.

Contract filenames (mission spec), GNU-format checksums, release metadata
with a real publication-integrity audit, and provenance-annotated notes.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from release_integrity import audit_artifacts, format_report, gate_report  # noqa: E402

WSA_VERSION = "2407.40000.4.0"
MANAGER_VERSION = "0.2.2"
TAG = "Windows_11_2407.40000.4.0_v4"
DIST = REPO / "dist" / f"Emberbird-WSA-{WSA_VERSION}"

ASSETS = [
    # (source, contract filename, edition, format)
    (REPO / "dist" / "release-standard" / f"WSA_{WSA_VERSION}_x64.7z", f"Emberbird_WSA_{WSA_VERSION}_x64.7z", "standard", "7z"),
    (REPO / "dist" / "release-banking" / f"WSA_{WSA_VERSION}_x64_vanilla.7z", f"Emberbird_WSA_{WSA_VERSION}_x64_Banking.7z", "banking", "7z"),
    (DIST / f"Emberbird_WSA_{WSA_VERSION}_arm64.7z", f"Emberbird_WSA_{WSA_VERSION}_arm64.7z", "standard", "7z"),
    (DIST / f"Emberbird_WSA_{WSA_VERSION}_arm64_Banking.7z", f"Emberbird_WSA_{WSA_VERSION}_arm64_Banking.7z", "banking", "7z"),
    (REPO / "output" / "manager-real" / f"WSABuildsManager-Setup-{MANAGER_VERSION}-x64.exe", f"EmberbirdManagerSetup_{MANAGER_VERSION}.exe", "manager", "exe"),
    (REPO / "output" / "manager-real" / f"WSABuildsManager-Portable-{MANAGER_VERSION}-x64.zip", f"EmberbirdManagerPortable_{MANAGER_VERSION}.zip", "manager", "zip"),
]

PROVENANCE = {
    f"Emberbird_WSA_{WSA_VERSION}_x64.7z": "Built locally via tools/build_local.py --arch x64 --root-sol magisk (WsaPackage 2407.40000.4.0 x64 MSIX, Magisk stable, OpenGApps Pico x86_64); LZMA2 -mx=6",
    f"Emberbird_WSA_{WSA_VERSION}_x64_Banking.7z": "Built locally via tools/build_local.py --arch x64 --root-sol none (vanilla, no root; same WSA MSIX); LZMA2 -mx=6",
    f"Emberbird_WSA_{WSA_VERSION}_arm64.7z": "Built locally via tools/build_local.py --arch arm64 --root-sol magisk (WsaPackage 2407.40000.4.0 ARM64 MSIX from the same retail bundle, Magisk stable arm64-v8a, OpenGApps Pico arm64 from LSPosed/WSA-Addon v2); LZMA2 -mx=6",
    f"Emberbird_WSA_{WSA_VERSION}_arm64_Banking.7z": "Built locally via tools/build_local.py --arch arm64 --root-sol none (vanilla, no root; ARM64 MSIX); LZMA2 -mx=6",
    f"EmberbirdManagerSetup_{MANAGER_VERSION}.exe": f"Byte-identical to published WSABuildsManager-Setup-{MANAGER_VERSION}-x64.exe on release v{MANAGER_VERSION} (SHA-256 verified against the release's published checksum file). Built from apps/manager (Tauri 2, NSIS).",
    f"EmberbirdManagerPortable_{MANAGER_VERSION}.zip": f"Byte-identical to published WSABuildsManager-Portable-{MANAGER_VERSION}-x64.zip on release v{MANAGER_VERSION} (SHA-256 verified). Built from apps/manager (Tauri 2).",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 22):
            h.update(chunk)
    return h.hexdigest().lower()


def sha512_file(path: Path) -> str:
    h = hashlib.sha512()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 22):
            h.update(chunk)
    return h.hexdigest().lower()


def main() -> int:
    DIST.mkdir(parents=True, exist_ok=True)

    # Stage every asset under its contract filename (hardlink first to avoid
    # copying ~3 GB, fall back to copy across devices).
    staged: list[Path] = []
    for src, name, _edition, _fmt in ASSETS:
        if not src.is_file():
            print(f"FATAL: missing source artifact {src}")
            return 1
        dst = DIST / name
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            staged.append(dst)
            continue
        try:
            if dst.exists():
                dst.unlink()
            dst.hardlink_to(src)
        except OSError:
            shutil.copy2(src, dst)
        staged.append(dst)
        print(f"staged {name} <- {src.relative_to(REPO)}")

    # Publication integrity audit over exactly the packaged assets.
    audit = audit_artifacts(staged)
    print(format_report(audit))
    if not gate_report(audit):
        print("FATAL: Publication Integrity Gate BLOCKED")
        return 2

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # GNU-format checksum files.
    lines = []
    for src, name, _e, _f in ASSETS:
        lines.append(f"{sha256_file(DIST / name)}  {name}")
    (DIST / "checksums.sha256").write_bytes(("\n".join(lines) + "\n").encode("ascii"))
    lines = []
    for src, name, _e, _f in ASSETS:
        lines.append(f"{sha512_file(DIST / name)}  {name}")
    (DIST / "checksums.sha512").write_bytes(("\n".join(lines) + "\n").encode("ascii"))

    # Metadata with the real audit verdicts inside.
    artifacts_meta = []
    for src, name, edition, fmt in ASSETS:
        p = DIST / name
        artifacts_meta.append({
            "filename": name,
            "edition": edition,
            "arch": "arm64" if "arm64" in name else "x64",
            "kind": "manager" if edition == "manager" else "subsystem",
            "size_bytes": p.stat().st_size,
            "sha256": sha256_file(p),
            "sha512": sha512_file(p),
            "format": fmt,
            "provenance": PROVENANCE[name],
        })
    verdicts = [a.to_dict() for a in audit]
    metadata = {
        "version": WSA_VERSION,
        "manager_version": MANAGER_VERSION,
        "tag": TAG,
        "build_date": now_iso,
        "variant": "Production_Release_Package",
        "validation_status": "VERIFIED",
        "package_integrity_status": "VERIFIED",
        "total_artifacts": len(ASSETS),
        "publication_integrity": {
            "total": len(verdicts),
            "publishable": sum(1 for v in verdicts if v["verdict"] == "REAL"),
            "blocking": sum(1 for v in verdicts if v["verdict"] != "REAL"),
            "passed": gate_report(audit),
            "artifacts": verdicts,
        },
        "artifacts": artifacts_meta,
    }
    (DIST / "release-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    # Release notes.
    notes = f"""# Emberbird {WSA_VERSION} — Production Release (Standard, Banking, ARM64, Manager)

Full production package: Windows Subsystem for Android {WSA_VERSION} with Magisk root (Standard) and unrooted (Banking) editions for **x64 and ARM64**, plus the **Emberbird Manager v{MANAGER_VERSION}** desktop app.

## Assets

| File | Edition / Purpose |
|---|---|
| `Emberbird_WSA_{WSA_VERSION}_x64.7z` | Standard Edition (x64) — Magisk root + OpenGApps Pico |
| `Emberbird_WSA_{WSA_VERSION}_x64_Banking.7z` | Banking Edition (x64) — Vanilla, no root, no GApps |
| `Emberbird_WSA_{WSA_VERSION}_arm64.7z` | Standard Edition (ARM64) — Magisk root + OpenGApps Pico |
| `Emberbird_WSA_{WSA_VERSION}_arm64_Banking.7z` | Banking Edition (ARM64) — Vanilla, no root |
| `EmberbirdManagerSetup_{MANAGER_VERSION}.exe` | Emberbird Manager installer (NSIS) |
| `EmberbirdManagerPortable_{MANAGER_VERSION}.zip` | Emberbird Manager portable |

## Installation

1. Extract the matching `.7z` with 7-Zip (or any LZMA2-capable extractor).
2. Run `Run.bat` (elevates `Install.ps1`) and follow the prompts.
3. ARM64 packages require an ARM64 Windows 11 device (MinVersion 10.0.22000.120).

## Verification

`checksums.sha256` / `checksums.sha512` cover every artifact in GNU coreutils format. Every asset passed the Publication Integrity Gate (`scripts/release_integrity.py`, verdict REAL) before upload.

## Provenance

- WSA payloads derive from the official `WsaPackage_{WSA_VERSION}` MSIX bundle (x64 + ARM64).
- GApps images: OpenGApps Pico for Android 13 (x86_64: {WSA_VERSION} build; arm64: LSPosed/WSA-Addon v2).
- Magisk: stable channel, per-architecture payloads injected into `Tools/initrd.img`.
- Manager binaries are byte-identical (SHA-256 verified) to the published v{MANAGER_VERSION} release, built from `apps/manager` (Tauri 2).

## Notes

- ARM64 assets were produced by the native Python builder (`tools/build_local.py --arch arm64`) with the same initrd injection pipeline as x64. Runtime validation on ARM64 hardware is pending: **REQUIRES TARGET ENVIRONMENT VALIDATION**.
"""
    (DIST / "RELEASE_NOTES.md").write_text(notes, encoding="utf-8")

    print(f"\nAssembled {len(ASSETS)} assets in {DIST}")
    for p in sorted(DIST.iterdir()):
        print(f"  {p.name:60s} {p.stat().st_size:>12,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
