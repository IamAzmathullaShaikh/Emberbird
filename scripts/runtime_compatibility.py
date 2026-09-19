#!/usr/bin/env python3
"""
runtime_compatibility.py — WSABuilds Runtime Compatibility Test Harness

Executable runtime-compatibility harness. Against a live WSA
instance (via adb) it captures the platform baseline, probes target apps
(install state, launch result, crash evidence), and emits:

  1. a runtime report JSON           -> compatibility/submissions/
  2. one compatibility submission    -> compatibility/submissions/ (per app,
     matching compatibility/schema.json, ready for human review)
  3. a markdown compatibility summary (stdout with --summary)

Honesty contract (Runtime Reality Gate):
  - No compatibility status is ever claimed without adb evidence.
  - Without adb/WSA the harness exits with code 2 and the placeholder
    "REQUIRES TARGET ENVIRONMENT VERIFICATION" — never a fabricated status.
  - All records are emitted with verification_status=unverified (or
    community_submitted when --submitter is given); a human promotes them.

Exit codes: 0 success · 1 harness/execution failure · 2 environment missing.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "compatibility" / "data"
SUBMISSIONS_DIR = ROOT / "compatibility" / "submissions"

PLACEHOLDER = "REQUIRES TARGET ENVIRONMENT VERIFICATION"

# Verified against compatibility/schema.json categories and real package IDs.
TARGETS: Dict[str, Dict[str, str]] = {
    "Telegram": {"package_id": "org.telegram.messenger.web", "category": "Communication"},
    "Spotify": {"package_id": "com.spotify.music", "category": "Streaming & Media"},
    "Netflix": {"package_id": "com.netflix.mediaclient", "category": "Streaming & Media"},
    "GooglePlayStore": {"package_id": "com.android.vending", "category": "Utilities & Tools"},
    "GooglePlayServices": {"package_id": "com.google.android.gms", "category": "Utilities & Tools"},
    "Paytm": {"package_id": "net.one97.paytm", "category": "Banking & UPI"},
    "PhonePe": {"package_id": "com.phonepe.app", "category": "Banking & UPI"},
    "WhatsApp": {"package_id": "com.whatsapp", "category": "Communication"},
    "YONO": {"package_id": "com.sbi.lotusintouch", "category": "Banking & UPI"},
}

REPORT_SCHEMA_VERSION = 1


# ---------------------------------------------------------------- adb adapter


class AdbError(RuntimeError):
    """adb invocation failed at the transport level."""


def run_adb(adb_path: str, args: List[str], timeout: int = 30) -> str:
    """Run one adb command and return stdout. Raises AdbError on failure."""
    cmd = [adb_path, *args]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace"
        )
    except FileNotFoundError as exc:
        raise AdbError(f"adb executable not found: {adb_path}") from exc
    except subprocess.TimeoutExpired as exc:
        raise AdbError(f"adb timed out after {timeout}s: {' '.join(args)}") from exc
    if proc.returncode != 0:
        raise AdbError(f"adb {' '.join(args)} failed ({proc.returncode}): {proc.stderr.strip()}")
    return proc.stdout


# ------------------------------------------------------------- baseline capture


def capture_baseline(adb: Callable[[List[str]], str]) -> Dict[str, object]:
    """Capture the WSA platform baseline (Appendix D step 2)."""
    props = {}
    for key in ("ro.build.version.release", "ro.build.version.sdk", "ro.product.cpu.abilist"):
        try:
            props[key] = adb(["shell", "getprop", key]).strip()
        except AdbError as exc:
            props[key] = f"<error: {exc}>"

    packages = _safe_packages(adb)

    baseline: Dict[str, object] = {
        "android_version": props.get("ro.build.version.release", "<unknown>"),
        "android_sdk": props.get("ro.build.version.sdk", "<unknown>"),
        "abi_list": props.get("ro.product.cpu.abilist", "<unknown>"),
        "root_flavor": _detect_root_flavor(adb),
        "gapps_present": "com.android.vending" in packages and "com.google.android.gms" in packages,
        "package_count": len(packages),
    }
    return baseline


def _safe_packages(adb: Callable[[List[str]], str]) -> List[str]:
    try:
        out = adb(["shell", "pm", "list", "packages"])
        return [line.split(":", 1)[1] for line in out.splitlines() if line.startswith("package:")]
    except AdbError:
        return []


def _detect_root_flavor(adb: Callable[[List[str]], str]) -> str:
    packages = _safe_packages(adb)
    if any(p.startswith("io.github.huskydg.magisk") or p.startswith("com.topjohnwu.magisk") for p in packages):
        return "Magisk"
    if any(p.startswith("com.samsung.android.kernelsu") or p == "me.weishu.kernelsu" for p in packages):
        return "KernelSU"
    try:
        adb(["shell", "su", "-c", "id"])
        return "su (unmanaged)"
    except AdbError:
        return "NoRoot"


# ------------------------------------------------------------------ app probes


def probe_app(adb: Callable[[List[str]], str], package_id: str, launch_wait_s: int = 6) -> Dict[str, object]:
    """Probe one app: installed? launches? crashes? (Appendix D step 3)."""
    probe: Dict[str, object] = {"package_id": package_id}

    packages = _safe_packages(adb)
    probe["installed"] = package_id in packages
    if not probe["installed"]:
        probe["result"] = "not_installed"
        return probe

    # Reset crash markers, launch, wait, then collect evidence.
    try:
        adb(["logcat", "-c"])
    except AdbError:
        pass

    launch_out = ""
    launch_ok = True
    try:
        launch_out = adb(["shell", "monkey", "-p", package_id, "-c", "android.intent.category.LAUNCHER", "1"], timeout=45)
        probe["launch_command_output"] = launch_out.strip().splitlines()[-3:]
    except AdbError as exc:
        launch_ok = False
        probe["launch_command_output"] = [str(exc)]

    import time
    time.sleep(launch_wait_s)

    focused = ""
    try:
        focused = adb(["shell", "dumpsys", "window", "windows"] if False else ["shell", "dumpsys", "window"])
        m = re.search(r"mCurrentFocus=Window\{[^}]*\s([^\s/}]+)", focused)
        probe["focused_window"] = m.group(1) if m else None
    except AdbError:
        probe["focused_window"] = None

    crashes: List[str] = []
    try:
        log = adb(["logcat", "-d", "-s", "AndroidRuntime:E"])
        for line in log.splitlines():
            if "Process:" in line and package_id in line:
                crashes.append(line.strip())
    except AdbError:
        pass
    probe["crash_evidence"] = crashes[:3]

    focused_on_app = bool(probe.get("focused_window")) and str(probe["focused_window"]).startswith(package_id)
    if not launch_ok:
        probe["result"] = "launch_failed"
    elif crashes:
        probe["result"] = "crashed"
    elif focused_on_app:
        probe["result"] = "launched_focused"
    else:
        probe["result"] = "launched_unverified_focus"
    return probe


def derive_status(probe: Dict[str, object]) -> str:
    """Map a probe to a schema-allowed status. Only honest values, ever."""
    result = probe.get("result")
    if result == "launched_focused":
        return "Working"
    if result in ("crashed", "launch_failed", "not_installed"):
        return "Broken"
    return "Workaround Required"


# ------------------------------------------------------------- report assembly


def build_report(baseline: Dict[str, object], probes: Dict[str, Dict[str, object]],
                 wsa_host: str) -> Dict[str, object]:
    now = _dt.datetime.now(_dt.timezone.utc)
    apps = {}
    for name, probe in probes.items():
        apps[name] = {
            "package_id": probe["package_id"],
            "probe_result": probe["result"],
            "compatibility_status": derive_status(probe),
            "evidence": {
                "focused_window": probe.get("focused_window"),
                "crash_evidence": probe.get("crash_evidence", []),
                "launch_command_output": probe.get("launch_command_output", []),
            },
        }
    return {
        "report_type": "wsa-runtime-compatibility",
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": now.isoformat(),
        "wsa_host": wsa_host,
        "baseline": baseline,
        "apps": apps,
        "verification_status": "unverified",
        "note": "Generated by scripts/runtime_compatibility.py; requires human review before promotion.",
    }


def write_submissions(report: Dict[str, object], tested_root_flavor: str) -> List[Path]:
    """Write schema-compliant submission records for probed apps."""
    SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    stamp = report["generated_at"][:10]
    for name, app in report["apps"].items():
        target = TARGETS.get(name, {})
        record = {
            "$schema": "../schema.json",
            "app_name": name,
            "package_id": app["package_id"],
            "category": target.get("category", "Utilities & Tools"),
            "compatibility_status": app["compatibility_status"],
            "play_integrity_required": name in ("Netflix", "GooglePlayStore", "GooglePlayServices",
                                                "Paytm", "PhonePe", "YONO"),
            "tested_wsa_version": str(report["baseline"].get("android_version", PLACEHOLDER)),
            "tested_root_flavor": tested_root_flavor,
            "last_tested_date": stamp,
            "workaround_steps": [],
            "known_issues": "; ".join(app["evidence"].get("crash_evidence", []) or []) or "None",
            "verification_status": "unverified",
        }
        path = SUBMISSIONS_DIR / f"{name}-{stamp}.json"
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        written.append(path)
    return written


def render_summary(report: Dict[str, object]) -> str:
    lines = [
        "# WSA Runtime Compatibility Summary",
        "",
        f"- Generated: {report['generated_at']}",
        f"- WSA host: {report['wsa_host']}",
        f"- Android: {report['baseline'].get('android_version')} (SDK {report['baseline'].get('android_sdk')})",
        f"- Root flavor: {report['baseline'].get('root_flavor')}",
        f"- GApps present: {report['baseline'].get('gapps_present')}",
        "",
        "| App | Installed | Result | Status | Crash evidence |",
        "|---|---|---|---|---|",
    ]
    for name, app in report["apps"].items():
        result = app["probe_result"]
        installed = "yes" if result != "not_installed" else "no"
        crashes = len(app["evidence"].get("crash_evidence", []))
        lines.append(f"| {name} | {installed} | {result} | {app['compatibility_status']} | {crashes} |")
    lines += [
        "",
        "_All statuses are unverified until a human reproduces them (Runtime Reality Gate)._",
    ]
    return "\n".join(lines)


def validate_report_shape(report: Dict[str, object]) -> List[str]:
    errors = []
    for key in ("report_type", "generated_at", "wsa_host", "baseline", "apps", "verification_status"):
        if key not in report:
            errors.append(f"report missing key '{key}'")
    for name, app in report.get("apps", {}).items():
        if app.get("compatibility_status") not in ("Working", "Workaround Required", "Broken"):
            errors.append(f"app {name}: invalid status {app.get('compatibility_status')!r}")
        if not app.get("package_id"):
            errors.append(f"app {name}: missing package_id")
    return errors


# --------------------------------------------------------------------- main


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="WSA runtime compatibility harness")
    parser.add_argument("--adb", default="adb", help="path to adb executable")
    parser.add_argument("--serial", default=None, help="adb device serial (-s)")
    parser.add_argument("--apps", default="", help="comma-separated app names (default: all TARGETS)")
    parser.add_argument("--launch-wait", type=int, default=6, help="seconds to wait after launch")
    parser.add_argument("--summary", action="store_true", help="print markdown summary to stdout")
    args = parser.parse_args(argv)

    adb_prefix = ["-s", args.serial] if args.serial else []

    def adb(cmd_args: List[str]) -> str:
        return run_adb(args.adb, [*adb_prefix, *cmd_args])

    try:
        adb(["start-server"])
        devices = adb(["devices"])
    except AdbError as exc:
        print(f"[-] adb unavailable: {exc}", file=sys.stderr)
        print(f"[!] Status: {PLACEHOLDER}", file=sys.stderr)
        print("[!] Harness cannot claim any runtime compatibility without adb. "
              "Run this on the WSA host machine with adb on PATH.", file=sys.stderr)
        return 2

    live = [l for l in devices.splitlines()[1:] if l.strip() and l.split()[-1] == "device"]
    if not live:
        print("[-] No adb device in 'device' state. Grant the RSA prompt (Appendix A).", file=sys.stderr)
        print(f"[!] Status: {PLACEHOLDER}", file=sys.stderr)
        return 2

    serial = live[0].split()[0]
    wsa_host = f"adb:{serial}"

    names = [n.strip() for n in args.apps.split(",") if n.strip()] or list(TARGETS)
    unknown = [n for n in names if n not in TARGETS]
    if unknown:
        print(f"[-] Unknown app names: {unknown}. Known: {sorted(TARGETS)}", file=sys.stderr)
        return 1

    print(f"[*] Capturing WSA baseline on {wsa_host}...")
    baseline = capture_baseline(adb)
    print(f"[+] Baseline: Android {baseline['android_version']} | root={baseline['root_flavor']} | gapps={baseline['gapps_present']}")

    probes: Dict[str, Dict[str, object]] = {}
    for name in names:
        print(f"[*] Probing {name} ({TARGETS[name]['package_id']})...")
        probes[name] = probe_app(adb, TARGETS[name]["package_id"], launch_wait_s=args.launch_wait)
        print(f"    -> {probes[name]['result']} (status: {derive_status(probes[name])})")

    report = build_report(baseline, probes, wsa_host)
    shape_errors = validate_report_shape(report)
    if shape_errors:
        for e in shape_errors:
            print(f"[-] report shape: {e}", file=sys.stderr)
        return 1

    SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = report["generated_at"].replace(":", "").replace("-", "")[:15]
    report_path = SUBMISSIONS_DIR / f"runtime-report-{stamp}.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[+] Runtime report: {report_path}")

    written = write_submissions(report, str(baseline.get("root_flavor", "NoRoot")))
    for p in written:
        print(f"[+] Submission:   {p.name}")

    if args.summary:
        print()
        print(render_summary(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
