#!/usr/bin/env python3
"""Track 0 installer invariants — regression guards for upstream/installer/Install.ps1.

Each test encodes a stabilization fix so a future edit cannot silently revert it:

  T0.1  Single primary entry point — exactly one user-facing launch (Play Store);
        no Magisk double-launch.
  T0.2  Developer Settings bypass — the VM warm-up boots wsa://settings AFTER the
        new package is registered and before the primary launch, with a bounded
        vmmemWSA poll (no blind sleeps).
  T0.3  Zombie-lock shutdown — Stop-EmberbirdSubsystem waits for vmmemWSA to exit
        before falling back to Stop-Process -Force, keeping userdata.vhdx unlocked.
  T0.5  Dev-mode replace — a development-mode install is removed with
        -PreserveApplicationData before registering the new package (no silent
        same-version no-op like the one observed during live validation).

Also guards scripts/optimize-subsystem.ps1: it must never claim RAM tuning or
other fabricated operations (Zero-Mock law).
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALLER = REPO_ROOT / "upstream" / "installer" / "Install.ps1"
OPTIMIZE = REPO_ROOT / "scripts" / "optimize-subsystem.ps1"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def installer_text() -> str:
    return read(INSTALLER)


def function_block(text: str, name: str, end_marker: str) -> str:
    """Return the body of `Function <name> { ... }` up to end_marker."""
    start = text.index(f"Function {name} {{")
    end = text.index(end_marker, start)
    return text[start:end]


class TestTrack0SingleLaunch(unittest.TestCase):
    """T0.1 — the installer triggers exactly one primary entry point."""

    def test_finish_launches_only_the_play_store(self):
        text = installer_text()
        finish_block = function_block(text, "Finish", "\nIf ((Check-Windows11)")
        self.assertEqual(
            finish_block.count("Start-Process"),
            1,
            "Finish must trigger exactly one primary entry point",
        )
        self.assertIn("wsa://com.android.vending", finish_block)
        self.assertNotIn("wsa://com.topjohnwu.magisk", finish_block)

    def test_warmup_launch_is_shut_down_before_finish(self):
        text = installer_text()
        finish_block = function_block(text, "Finish", "\nIf ((Check-Windows11)")
        self.assertLess(
            finish_block.index("Start-EmberbirdWarmUp"),
            finish_block.index("Start-Process"),
            "warm-up must complete (and be shut down) before the single launch",
        )
        warmup = function_block(text, "Start-EmberbirdWarmUp", "Function Finish")
        self.assertIn("Stop-EmberbirdSubsystem", warmup)

    def test_no_duplicate_primary_launch_outside_finish(self):
        text = installer_text()
        launches = re.findall(r"Start-Process\s+\"wsa://", text)
        # One inside Start-EmberbirdWarmUp (wsa://settings), one in Finish.
        self.assertEqual(len(launches), 2, f"unexpected wsa:// launches: {launches}")


class TestTrack0WarmUpOrdering(unittest.TestCase):
    """T0.2 — warm-up runs after registration, not on the old package."""

    def test_warmup_runs_after_register(self):
        text = installer_text()
        reg = text.index(
            "Add-AppxPackage -ForceApplicationShutdown -ForceUpdateFromAnyVersion -Register"
        )
        warmup_def = text.index("Function Start-EmberbirdWarmUp {")
        finish_call = text.index("\n    Finish", reg)
        self.assertLess(
            warmup_def,
            finish_call,
            "warm-up implementation must precede the post-register Finish call",
        )
        finish_block = function_block(text, "Finish", "\nIf ((Check-Windows11)")
        self.assertIn("Start-EmberbirdWarmUp", finish_block)

    def test_warmup_polls_vmmem_bounded(self):
        text = installer_text()
        warmup = function_block(text, "Start-EmberbirdWarmUp", "Function Finish")
        self.assertIn("vmmemWSA", warmup)
        self.assertIn("deadline", warmup)
        self.assertIn("90", warmup, "warm-up must have a bounded deadline")

    def test_old_dead_code_gone(self):
        text = installer_text()
        # The pre-register warm-up block that warmed the OLD install (and could
        # never initialize ADB for the new one) must not return.
        self.assertNotIn("This sequence often forces the ADB daemon", text)


class TestTrack0ZombieLockShutdown(unittest.TestCase):
    """T0.3 — subsystem shutdown waits for the VM worker (userdata.vhdx lock)."""

    def test_shutdown_function_exists_and_polls_vmmem(self):
        text = installer_text()
        stop_fn = function_block(text, "Stop-EmberbirdSubsystem", "Function Start-EmberbirdWarmUp")
        self.assertIn("vmmemWSA", stop_fn)
        self.assertIn("/shutdown", stop_fn)
        self.assertIn("Stop-Process -Name \"vmmemWSA\" -Force", stop_fn)

    def test_shutdown_runs_before_register(self):
        text = installer_text()
        stop_call = text.index("Stop-EmberbirdSubsystem\n")
        register = text.index(
            "Add-AppxPackage -ForceApplicationShutdown -ForceUpdateFromAnyVersion -Register"
        )
        self.assertLess(
            stop_call,
            register,
            "the lock-free shutdown must run before package registration",
        )


class TestTrack0DevModeReplace(unittest.TestCase):
    """T0.5 — dev-mode installs are replaced with data preservation, not no-op'd."""

    def test_dev_mode_replace_block_exists_before_register(self):
        text = installer_text()
        block = text.index("$Installed.IsDevelopmentMode")
        register = text.index(
            "Add-AppxPackage -ForceApplicationShutdown -ForceUpdateFromAnyVersion -Register"
        )
        self.assertLess(block, register)
        window = text[block:register]
        self.assertIn("Remove-AppxPackage -PreserveApplicationData", window)

    def test_legacy_prompt_only_covers_non_dev_mode(self):
        text = installer_text()
        legacy = text.index("There is already one installed WSA")
        self.assertIn("-Not ($Installed.IsDevelopmentMode)", text[legacy - 400:legacy])


class TestOptimizeSubsystemNoMock(unittest.TestCase):
    """Zero-Mock law: the maintenance script must not fabricate effects."""

    def test_script_exists_and_compacts(self):
        text = read(OPTIMIZE)
        self.assertIn("compact vdisk", text)
        self.assertIn("vmmemWSA", text)

    def test_script_does_not_claim_ram_tuning(self):
        text = read(OPTIMIZE).lower()
        self.assertNotIn("set-vmmemory", text)
        self.assertNotIn("vmmemmemory", text)
        self.assertNotIn("-memorymaximumbytes", text)


if __name__ == "__main__":
    unittest.main()
