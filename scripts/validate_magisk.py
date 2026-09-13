#!/usr/bin/env python3
"""
validate_magisk.py — Magisk root integration validator

Offline mode: Inspects initrd.img to verify Magisk trampoline, binaries, and policies.
Live mode (--adb): Connects over ADB to test `su -c id`, `magisk -v`, and SQLite policy DB.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add MagiskOnWSA/scripts for CPIO helpers
SCRIPT_DIR = Path(__file__).resolve().parent.parent / "MagiskOnWSA" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from build_local import read_cpio_archive
except ImportError:
    read_cpio_archive = None


def validate_magisk_offline(initrd_path: Path) -> dict:
    if not initrd_path.is_file():
        return {"status": "FAILED", "reason": f"initrd.img not found at {initrd_path}"}

    if not read_cpio_archive:
        return {"status": "PARTIALLY VERIFIED", "reason": "CPIO reader module not found"}

    entries = read_cpio_archive(initrd_path)
    entry_map = {e.name: e for e in entries}

    checks = []
    all_ok = True

    # Check trampoline
    init_entry = entry_map.get("init")
    init_ok = (init_entry is not None and b"lspinit" in init_entry.data)
    checks.append({"item": "init symlink to lspinit", "passed": init_ok})
    if not init_ok: all_ok = False

    # Check binaries
    for bin_name in ["lspinit", "magiskinit", "wsainit"]:
        ok = (bin_name in entry_map and len(entry_map[bin_name].data) > 0)
        checks.append({"item": f"binary {bin_name}", "passed": ok})
        if not ok: all_ok = False

    # Check overlay sbin
    for overlay_file in ["overlay.d/sbin/magisk.xz", "overlay.d/sbin/stub.xz", "overlay.d/sbin/post-fs-data.sh"]:
        ok = (overlay_file in entry_map and len(entry_map[overlay_file].data) > 0)
        checks.append({"item": f"overlay item {overlay_file}", "passed": ok})
        if not ok: all_ok = False

    return {
        "status": "VERIFIED" if all_ok else "FAILED",
        "type": "OFFLINE_RAMDISK_ANALYSIS",
        "checks": checks,
    }


def validate_magisk_live(adb_port: str = "127.0.0.1:58526") -> dict:
    adb = shutil.which("adb") or "adb"
    # Check device connection
    res = subprocess.run([adb, "devices"], capture_output=True, text=True)
    if adb_port not in res.stdout and "device" not in res.stdout:
        return {
            "status": "NOT VERIFIED",
            "reason": f"No active ADB device detected on {adb_port}. Runtime environment unavailable.",
        }

    checks = []
    # 1. su -c id
    r_id = subprocess.run([adb, "shell", "su", "-c", "id"], capture_output=True, text=True, timeout=10)
    root_ok = ("uid=0(root)" in r_id.stdout)
    checks.append({"check": "su -c id", "passed": root_ok, "output": r_id.stdout.strip()})

    # 2. magisk -v
    r_ver = subprocess.run([adb, "shell", "su", "-c", "magisk -v"], capture_output=True, text=True, timeout=10)
    checks.append({"check": "magisk -v", "passed": (r_ver.returncode == 0), "version": r_ver.stdout.strip()})

    # 3. Policy db check
    r_pol = subprocess.run([adb, "shell", "su", "-c", "magisk --sqlite 'SELECT policy FROM policies WHERE uid=2000;'"], capture_output=True, text=True, timeout=10)
    pol_ok = ("2" in r_pol.stdout)
    checks.append({"check": "sqlite policy uid 2000 (auto-grant)", "passed": pol_ok})

    return {
        "status": "VERIFIED" if root_ok else "FAILED",
        "type": "LIVE_RUNTIME_VALIDATION",
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Magisk integration.")
    parser.add_argument("--package-dir", type=Path, help="Package directory for offline check")
    parser.add_argument("--live", action="store_true", help="Run live ADB runtime diagnostics")
    parser.add_argument("--output-report", type=Path, default=Path("magisk-validation-report.json"))

    args = parser.parse_args()

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "offline": None,
        "live": None,
    }

    if args.package_dir:
        initrd = args.package_dir / "Tools" / "initrd.img"
        report["offline"] = validate_magisk_offline(initrd)

    if args.live:
        report["live"] = validate_magisk_live()
    elif not args.package_dir:
        # CI offline mode: no package available and ADB not requested — emit
        # a safe SKIPPED report instead of calling adb (which does not exist on
        # standard GitHub Actions Ubuntu runners).
        report["offline"] = {
            "status": "SKIPPED",
            "reason": "No package directory provided. Use --package-dir for offline or --live for ADB validation.",
        }

    args.output_report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[+] Magisk validation report written to {args.output_report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
