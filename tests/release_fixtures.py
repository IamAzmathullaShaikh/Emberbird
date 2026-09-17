#!/usr/bin/env python3
"""Realistic release-artifact fixtures for the release pipeline tests.

The Publication Integrity Gate (scripts/release_integrity.py) refuses fabricated
bytes, so pipeline tests must supply artifacts that carry genuine container
signatures. A real Windows Subsystem for Android archive is >100 MiB, which no
unit test should write; the size floors are therefore lowered for tests via
``relaxed_floors``. Everything that actually protects release integrity —
signature validation, scaffold detection, refusal behaviour — stays fully
exercised.

stdlib-only; runs in CI unchanged.
"""

import contextlib
import struct
import sys
import zipfile
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import release_integrity as ri  # noqa: E402

# Test-only floors. Production floors live in release_integrity.MIN_BYTES and
# are pinned by tests/test_release_integrity.py.
TEST_FLOORS = {
    "installer": 64,
    "desktop-binary": 64,
    "portable": 64,
    "subsystem-archive": 64,
    "metadata": 1,
}


@contextlib.contextmanager
def relaxed_floors(floors=None):
    """Lower the size floors for the duration of a test."""
    with mock.patch.dict(ri.MIN_BYTES, dict(floors or TEST_FLOORS)):
        yield


def write_pe(path, size=512):
    """A structurally valid PE image (MZ + e_lfanew -> PE\\0\\0)."""
    payload = bytearray(b"\x00" * max(size, 0x100))
    payload[0:2] = b"MZ"
    struct.pack_into("<I", payload, 0x3C, 0x80)
    payload[0x80:0x84] = b"PE\x00\x00"
    Path(path).write_bytes(bytes(payload))
    return Path(path)


def write_zip(path, payload=b"genuine-package-bytes"):
    """A real ZIP container."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("AppxManifest.xml", "<Package/>")
        if payload:
            zf.writestr("payload.bin", payload)
    return Path(path)


def write_7z(path, size=512):
    """A real 7z container signature followed by opaque stream bytes."""
    Path(path).write_bytes(ri.SEVEN_ZIP_SIGNATURE + b"\x00\x04" + b"\x00" * max(size - 8, 0))
    return Path(path)


def write_checksums(directory, artifacts):
    """A genuine checksums manifest for the given artifacts."""
    import hashlib

    directory = Path(directory)
    lines = []
    for name in artifacts:
        digest = hashlib.sha256((directory / name).read_bytes()).hexdigest()
        lines.append(f"{digest}  {name}")
    (directory / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return directory / "checksums.sha256"


def stage_standard_candidate(staging_dir, version="2407.40000.4.0"):
    """A genuine (if tiny) standard-edition candidate directory."""
    target = Path(staging_dir) / f"WSA_{version}_x64"
    target.mkdir(parents=True, exist_ok=True)
    (target / "AppxManifest.xml").write_text("<Package/>", encoding="utf-8")
    (target / "Install.ps1").write_text("# install\n", encoding="utf-8")
    (target / "payload.bin").write_bytes(b"genuine-wsa-payload" * 64)
    return target


def stage_manager_binaries(staging_dir, version="0.2.3"):
    """Genuine Manager installer + portable artifacts, identity-derived names."""
    base = Path(staging_dir)
    prefix = "EmberbirdManager"
    setup = write_pe(base / f"{prefix}-Setup-{version}-x64.exe")
    portable = write_zip(base / f"{prefix}-Portable-{version}-x64.zip")
    return setup, portable
