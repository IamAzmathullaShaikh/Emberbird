"""PH-27 — Emberbird Diagnostic Bundle.

One call produces a sanitized, shareable diagnostics archive built from the
real Doctor engine output (``platform/doctor``): a machine-readable
``diagnostics.json`` plus a human-readable ``README.txt`` whose content digest
covers the JSON, so a reader can confirm the two files describe the same run.

Sanitization is a hard gate, not a courtesy:

* every string value is scanned for secret-shaped tokens (API keys, bearer
  tokens, passwords) and machine identifiers (MAC addresses, Windows product
  IDs, usernames) — matches are replaced with ``[REDACTED]``;
* sanitization runs *last*, over the fully assembled JSON tree, so no section
  can bypass it by adding a field later.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

REDACTED = "[REDACTED]"

# Secret-shaped strings: long random-looking tokens and assignment forms.
# Token prefixes use a lookbehind instead of \b so tokens embedded after an
# underscore ("note_ghp_...") still match — a bare word boundary does not
# exist between two word characters.
_SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|secret|passwd|password|pwd|pass|token)\b\s*[:=]\s*\S+"),
    re.compile(r"(?<![A-Za-z0-9])(?:sk|pk)[-_][A-Za-z0-9_\-]{16,}"),
    re.compile(r"(?<![A-Za-z0-9])ghp_[A-Za-z0-9]{30,}"),
    re.compile(r"(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?<![A-Za-z0-9])eyJ[A-Za-z0-9_\-]{20,}"),  # JWT-shaped
]

# Machine identifiers that single out a specific host or person.
_MACHINE_PATTERNS = [
    re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b"),  # MAC address
    re.compile(r"(?i)\bproduct[_-]?id\b\s*[:=]?\s*[0-9]{5}-[0-9]{5}-[0-9]{5,}"),
    re.compile(r"(?i)\\Users\\(?!Public\b)[A-Za-z0-9_.\- ]{1,32}"),
    re.compile(r"(?i)/home/(?!public\b)[A-Za-z0-9_.\- ]{1,32}"),
    re.compile(r"(?i)\bserial[_-]?number\b\s*[:=]?\s*\S+"),
]

_PATTERNS = _SECRET_PATTERNS + _MACHINE_PATTERNS


def sanitize_text(value: str) -> str:
    """Replace secret-shaped and machine-identifying substrings with [REDACTED]."""
    out = value
    for pattern in _PATTERNS:
        out = pattern.sub(REDACTED, out)
    return out


def sanitize_tree(value: Any) -> Any:
    """Walk a JSON-shaped tree, sanitizing every string leaf and every key."""
    if isinstance(value, dict):
        return {sanitize_text(str(k)): sanitize_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_tree(item) for item in value]
    if isinstance(value, str):
        return sanitize_text(value)
    return value


def collect_sections(engine_runner: Callable[[], Any]) -> dict[str, Any]:
    """Build the bundle sections from the real Doctor engine report.

    ``engine_runner`` is a callable returning a ``DoctorReport`` (the real
    engine by default, injectable in tests). Sections are derived, never
    invented: every field traces to the report the engine produced on this
    host, and every value passes through :func:`sanitize_tree` at assembly.
    """
    report = engine_runner().to_dict()

    probe_summary = [
        {
            "probe_id": probe["probe_id"],
            "status": probe["status"],
            "severity": probe["severity"],
            "title": probe["title"],
            "summary": probe["summary"],
        }
        for probe in report["probes"]
    ]

    return {
        "system": {
            key: report[key]
            for key in (
                "platform_name",
                "version",
                "system_os",
                "os_release",
                "architecture",
                "captured_at",
            )
        },
        "runtime": {
            "overall_status": report["overall_status"],
            "total_probes": report["total_probes"],
            "passed_count": report["passed_count"],
            "warn_count": report["warn_count"],
            "fail_count": report["fail_count"],
            "exit_code": report["exit_code"],
        },
        "probes": probe_summary,
        "adb": {"note": "Loopback port 58526 probed by the doctor; see probes for status."},
        "packages": {
            "note": "Not collected in this edition; see probes for package-service status."
        },
        "logs": {
            "note": "No log files are attached; every field above is already sanitized."
        },
        "artifact_hashes": {},
    }


def readme_text(payload: dict[str, Any], digest: str) -> str:
    """Human-readable cover sheet. ``digest`` is the sha256 of diagnostics.json."""
    system = payload["system"]
    runtime = payload["runtime"]
    lines = [
        "Emberbird Diagnostic Bundle",
        "===========================",
        "",
        f"Platform:     {system['platform_name']} {system['version']}",
        f"Host:         {system['system_os']} {system['os_release']} ({system['architecture']})",
        f"Captured:     {system['captured_at']}",
        "",
        f"Overall:      {runtime['overall_status']}  "
        f"({runtime['passed_count']} pass / {runtime['warn_count']} warn / {runtime['fail_count']} fail)",
        "",
        "diagnostics.json sha256:",
        f"  {digest}",
        "",
        "This bundle is generated from the host doctor report. Secret-shaped",
        "strings and machine identifiers are replaced with [REDACTED]; no log",
        "files are attached.",
    ]
    return "\n".join(lines) + "\n"


def build_bundle(
    out_dir: Path,
    engine_runner: Callable[[], Any],
    archive_writer: Callable[[Path, list[tuple[str, bytes]]], Path] | None = None,
) -> dict[str, Any]:
    """Assemble, sanitize and write the diagnostic bundle.

    Returns a summary dict: archive path, file digests, and the redaction
    count observed during sanitization (for the never-include-secrets tests).
    """
    from datetime import datetime, timezone

    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    out_dir.mkdir(parents=True, exist_ok=True)
    sections = collect_sections(engine_runner)

    # Sanitization runs last, over the fully assembled tree, so no section can
    # bypass it by adding a field later. The redaction count lets the tests
    # prove sanitization actually fired rather than merely being configured.
    sanitized = sanitize_tree(sections)
    clean_json = json.dumps(sanitized, indent=2, sort_keys=True)
    redactions = clean_json.count(REDACTED)

    json_bytes = clean_json.encode("utf-8")
    digest = hashlib.sha256(json_bytes).hexdigest()

    readme = readme_text(sanitized, digest)
    readme_bytes = readme.encode("utf-8")

    # Written as bytes: text mode would translate \n to \r\n on Windows and
    # the loose files would no longer match the zip members byte for byte.
    json_path = out_dir / "diagnostics.json"
    json_path.write_bytes(json_bytes)
    readme_path = out_dir / "README.txt"
    readme_path.write_bytes(readme_bytes)

    files: list[tuple[str, bytes]] = [
        ("diagnostics.json", json_bytes),
        ("README.txt", readme_bytes),
    ]

    if archive_writer is None:
        import zipfile

        archive_path = out_dir / "emberbird-diagnostics.zip"
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for name, data in files:
                zf.writestr(name, data)
    else:
        archive_path = archive_writer(out_dir, files)

    return {
        "archive": str(archive_path),
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in files},
        "redactions": redactions,
        "captured_at": sanitized["system"]["captured_at"],
    }
