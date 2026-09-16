#!/usr/bin/env python3
"""
e2e_clean_room.py — Clean-room end-to-end verification for WSABuilds.

Executes, from a clean state and without trusting any pre-existing output:
  1. Tool inventory (records what is locally executable; missing CI-only
     tooling yields SKIP with a reason, never a fabricated PASS).
  2. Fresh multi-edition WSA builds via tools/build_local.py
     (Standard = Magisk root, Banking = vanilla/no-root; both with Pico GApps).
  3. Artifact reality gates on every built edition: structural integrity,
     package identity, Magisk ramdisk policy, and GApps integration.
  4. Release metadata + checksum generation for each edition.
  5. Distribution-level gates (version sync + Winget manifests).
  6. Manager local gates: TypeScript check + unit tests (the release binary
     itself is built and published by CI; see GOVERNANCE.md).
  7. Website gates: unit tests + production build with CI environment.

Exit code 0 only if every executed phase passed and every skipped phase
declared a reason.

Usage:
    python scripts/e2e_clean_room.py [--skip-builds] [--skip-website]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parent.parent
WSA_SCRIPTS = REPO_ROOT / "tools"
WSA_OUTPUT = REPO_ROOT / "output"
MANAGER_DIR = REPO_ROOT / "apps" / "manager"
WEBSITE_DIR = REPO_ROOT / "website"

EDITIONS = [
    {"key": "standard", "root_sol": "magisk", "suffix": "", "vanilla": False},
    {"key": "banking", "root_sol": "none", "suffix": "_vanilla", "vanilla": True},
]

results: list[dict] = []


def record(phase: str, status: str, detail: str = "") -> None:
    results.append({"phase": phase, "status": status, "detail": detail})
    marker = {"PASS": "[+]", "FAIL": "[-]", "SKIP": "[!]"}[status]
    print(f"{marker} {phase}: {status}{(' — ' + detail) if detail else ''}")


def resolve_cmd(cmd: list[str]) -> list[str]:
    """Resolve the executable through PATH/PATHEXT (Windows .cmd shims need this)."""
    resolved = shutil.which(cmd[0])
    return ([resolved, *cmd[1:]] if resolved else cmd)


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 1200) -> tuple[int, str]:
    proc = subprocess.run(
        resolve_cmd(cmd), cwd=cwd or REPO_ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output


def find_wsa_version() -> str:
    """Detect the WSA version produced by the builder (defaults to 2407.40000.4.0)."""
    for entry in sorted(WSA_OUTPUT.glob("WSA_*")):
        if entry.is_dir() and entry.name.startswith("WSA_"):
            parts = entry.name.split("_")
            if len(parts) >= 2:
                return parts[1]
    return "2407.40000.4.0"


def phase_tool_inventory() -> dict:
    print("\n=== PHASE 1: Tool inventory ===")
    tools = {}
    for name, probe in [
        ("python", [sys.executable, "--version"]),
        ("node", ["node", "--version"]),
        ("npm", ["npm", "--version"]),
        ("rust", ["cargo", "--version"]),
        ("nsis", ["makensis", "-VERSION"]),
        ("7zip", ["7z", "--help"]),
    ]:
        try:
            code, out = run(probe, timeout=60)
            available = code == 0
            first = (out.strip().splitlines() or [""])[0]
        except (OSError, subprocess.TimeoutExpired):
            available, first = False, ""
        tools[name] = available
        print(f"    {name:8s}: {'available' if available else 'NOT FOUND'} {first}")
    return tools


def phase_clean_wsa_builds(tools: dict) -> dict[str, Path]:
    print("\n=== PHASE 2: Clean multi-edition WSA builds (build_local.py) ===")
    built: dict[str, Path] = {}
    if not tools.get("python"):
        for ed in EDITIONS:
            record(f"build/{ed['key']}", "SKIP", "python unavailable")
        return built

    # Clean-room precondition: remove any previous build outputs for both editions.
    for ed in EDITIONS:
        for stale in WSA_OUTPUT.glob(f"WSA_*{ed['suffix']}"):
            print(f"    [clean] removing stale {stale.name}/")
            shutil.rmtree(stale, ignore_errors=True)

    wsa_version = find_wsa_version()
    for ed in EDITIONS:
        target = WSA_OUTPUT / f"WSA_{wsa_version}_x64{ed['suffix']}"
        code, out = run(
            [sys.executable, "build_local.py",
             "--root-sol", ed["root_sol"], "--gapps", "pico", "--arch", "x64"],
            cwd=WSA_SCRIPTS, timeout=1800,
        )
        if code == 0 and target.is_dir():
            n_files = sum(1 for _ in target.rglob("*") if _.is_file())
            record(f"build/{ed['key']}", "PASS", f"{target.name}/ ({n_files} files)")
            built[ed["key"]] = target
        else:
            tail = (out.strip().splitlines() or ["<no output>"])[-3:]
            record(f"build/{ed['key']}", "FAIL", " | ".join(tail))
    return built


def phase_artifact_reality_gates(built: dict[str, Path]) -> None:
    print("\n=== PHASE 3: Artifact reality gates (per edition) ===")
    for ed in EDITIONS:
        pkg = built.get(ed["key"])
        if not pkg:
            continue

        # 3a. Structural presence of non-fakeable artifacts.
        required = ["Install.ps1", "AppxManifest.xml", "Tools/initrd.img", "Tools/initrd.img.bak"]
        missing = [r for r in required if not (pkg / r).exists()]
        if missing:
            record(f"gate/structure/{ed['key']}", "FAIL", f"missing {missing}")
        else:
            record(f"gate/structure/{ed['key']}", "PASS", "installer, manifest, initrd (+stock backup) present")

        # 3b. Structural integrity validator.
        code, out = run([sys.executable, "scripts/validate_package_integrity.py",
                         "--package-dir", str(pkg)])
        (record if code == 0 else record)(f"gate/integrity/{ed['key']}",
                                          "PASS" if code == 0 else "FAIL",
                                          "" if code == 0 else out.strip()[-200:])

        # 3c. Package identity validator.
        code, out = run([sys.executable, "scripts/validate_package_identity.py",
                         "--package-dir", str(pkg)])
        (record if code == 0 else record)(f"gate/identity/{ed['key']}",
                                          "PASS" if code == 0 else "FAIL",
                                          "" if code == 0 else out.strip()[-200:])

        # 3d. Magisk ramdisk policy (rooted vs vanilla).
        cmd = [sys.executable, "scripts/validate_magisk.py", "--package-dir", str(pkg)]
        if ed["vanilla"]:
            cmd.append("--vanilla")
        code, out = run(cmd)
        if code == 0:
            mode = "VANILLA_UNROOTED" if ed["vanilla"] else "MAGISK_ROOTED"
            record(f"gate/magisk/{ed['key']}", "PASS", mode)
        else:
            record(f"gate/magisk/{ed['key']}", "FAIL", out.strip()[-200:])

        # 3e. GApps integration.
        code, out = run([sys.executable, "scripts/validate_gapps.py", "--package-dir", str(pkg)])
        (record if code == 0 else record)(f"gate/gapps/{ed['key']}",
                                          "PASS" if code == 0 else "FAIL",
                                          "" if code == 0 else out.strip()[-200:])


def phase_release_metadata(built: dict[str, Path], tools: dict) -> None:
    print("\n=== PHASE 4: Release metadata + checksum generation ===")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for ed in EDITIONS:
        pkg = built.get(ed["key"])
        if not pkg:
            continue
        out_dir = REPO_ROOT / "dist_clean" / f"{ed['key']}-{stamp}"
        code, out = run([sys.executable, "scripts/generate_release_metadata.py",
                         "--package-dir", str(pkg), "--output-dir", str(out_dir)])
        artifacts = sorted(p.name for p in out_dir.iterdir()) if out_dir.is_dir() else []
        if code == 0 and artifacts:
            record(f"metadata/{ed['key']}", "PASS", ", ".join(artifacts))
        else:
            record(f"metadata/{ed['key']}", "FAIL", out.strip()[-200:])


def phase_distribution_gates() -> None:
    print("\n=== PHASE 5: Distribution-level gates ===")
    code, out = run([sys.executable, "scripts/validate_distribution.py"])
    (record if code == 0 else record)("gate/distribution", "PASS" if code == 0 else "FAIL",
                                      "" if code == 0 else out.strip()[-300:])


def phase_manager(tools: dict) -> None:
    print("\n=== PHASE 6: Manager local gates ===")
    if not tools.get("node"):
        record("manager/typecheck", "SKIP", "node unavailable")
        record("manager/tests", "SKIP", "node unavailable")
        return
    code, out = run(["npx", "tsc", "--noEmit"], cwd=MANAGER_DIR, timeout=600)
    record("manager/typecheck", "PASS" if code == 0 else "FAIL",
           "" if code == 0 else out.strip()[-300:])
    code, out = run(["node", "--test", "tests/"], cwd=MANAGER_DIR, timeout=600)
    record("manager/tests", "PASS" if code == 0 else "FAIL",
           "" if code == 0 else out.strip()[-300:])
    record("manager/release-binary", "SKIP",
           "built+published by CI (winget-release.yml); Rust/NSIS toolchain not present locally")


def phase_website(tools: dict, skip: bool) -> None:
    print("\n=== PHASE 7: Website gates ===")
    if skip:
        record("website/tests", "SKIP", "--skip-website")
        record("website/build", "SKIP", "--skip-website")
        return
    if not tools.get("node"):
        record("website/tests", "SKIP", "node unavailable")
        record("website/build", "SKIP", "node unavailable")
        return
    env = dict(os.environ)
    env.setdefault("SITE_URL", "https://wsabuilds-website.pages.dev")
    env.setdefault("PUBLIC_GITHUB_REPO", "IamAzmathullaShaikh/Emberbird")
    env.setdefault("PUBLIC_GITHUB_REPO_URL", "https://github.com/IamAzmathullaShaikh/Emberbird")
    env.setdefault("PUBLIC_RELEASES_URL", "https://github.com/IamAzmathullaShaikh/Emberbird/releases")

    code, out = run(["node", "--test", "tests/"], cwd=WEBSITE_DIR, timeout=600)
    record("website/tests", "PASS" if code == 0 else "FAIL",
           "" if code == 0 else out.strip()[-300:])

    try:
        proc = subprocess.run(resolve_cmd(["npx", "astro", "build"]), cwd=WEBSITE_DIR,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=900, env=env)
        combined = (proc.stdout or "") + (proc.stderr or "")
        record("website/build", "PASS" if proc.returncode == 0 else "FAIL",
               "production build" if proc.returncode == 0 else combined.strip()[-300:])
    except (OSError, subprocess.TimeoutExpired) as exc:
        record("website/build", "FAIL", str(exc))


def main() -> int:
    parser = argparse.ArgumentParser(description="WSABuilds clean-room E2E verification")
    parser.add_argument("--skip-builds", action="store_true", help="skip fresh WSA builds")
    parser.add_argument("--skip-website", action="store_true", help="skip website gates")
    args = parser.parse_args()

    print("=" * 60)
    print(" WSABuilds Clean-Room E2E Verification")
    print("=" * 60)

    tools = phase_tool_inventory()

    if args.skip_builds:
        print("\n=== PHASE 2-4 skipped (--skip-builds) ===")
        built: dict[str, Path] = {}
    else:
        built = phase_clean_wsa_builds(tools)
        phase_artifact_reality_gates(built)
        phase_release_metadata(built, tools)

    phase_distribution_gates()
    phase_manager(tools)
    phase_website(tools, args.skip_website)

    print("\n" + "=" * 60)
    print(" SUMMARY")
    print("=" * 60)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    for r in results:
        print(f"  {r['status']:4s} {r['phase']}")
    print(f"\n  {passed} passed, {failed} failed, {skipped} skipped (with reasons)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
