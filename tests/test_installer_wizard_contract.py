#!/usr/bin/env python3
"""test_installer_wizard_contract.py — Contract tests for the Installer Wizard UI surface.

FB-3 requires a live Windows + WSA environment for end-to-end validation.
These tests validate the STATIC surface contract without live execution:
  1. InstallerWizard.tsx exists and exports the component
  2. All 5 wizard steps are defined in STEP_LABELS
  3. All required IPC calls are imported
  4. The wizard integrates with StatusCard
  5. The preflight checks surface all required system requirement fields
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANAGER_SRC = REPO_ROOT / "apps" / "manager" / "src"
COMPONENTS = MANAGER_SRC / "components"
LIB = MANAGER_SRC / "lib"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestInstallerWizardSurface(unittest.TestCase):
    def setUp(self):
        self.wizard_src = read(COMPONENTS / "InstallerWizard.tsx")
        self.status_card_src = read(COMPONENTS / "StatusCard.tsx")
        self.ipc_src = read(LIB / "ipc.ts")

    def test_wizard_file_exists(self):
        self.assertTrue((COMPONENTS / "InstallerWizard.tsx").exists())

    def test_wizard_exports_installer_wizard(self):
        self.assertIn("export const InstallerWizard", self.wizard_src)

    def test_wizard_defines_all_5_steps(self):
        required_steps = ["edition", "preflight", "download", "install", "done"]
        for step in required_steps:
            self.assertIn(f"'{step}'", self.wizard_src, f"Step '{step}' not defined in wizard")

    def test_wizard_imports_all_required_ipc_calls(self):
        required_ipc = ["preflightUpgrade", "downloadAndStageRelease", "installWsaPackage"]
        for fn in required_ipc:
            self.assertIn(fn, self.wizard_src, f"IPC function '{fn}' not imported in wizard")

    def test_wizard_uses_store_notifications(self):
        self.assertIn("addNotification", self.wizard_src)

    def test_wizard_has_aria_dialog(self):
        # Accessibility: modal must declare itself as a dialog
        self.assertIn('role="dialog"', self.wizard_src)
        self.assertIn('aria-modal="true"', self.wizard_src)

    def test_wizard_has_close_button(self):
        self.assertIn("aria-label=\"Close", self.wizard_src)

    def test_wizard_uses_stage_progress_bar(self):
        self.assertIn("StageProgressBar", self.wizard_src)

    def test_status_card_integrates_wizard(self):
        self.assertIn("InstallerWizard", self.status_card_src)
        self.assertIn("wizardOpen", self.status_card_src)

    def test_preflight_checks_required_fields(self):
        # The preflight step must surface all system checks from UpgradePreflight
        required_checks = ["windows_version_ok", "dev_mode_ok", "virtualization_ok", "disk_space_ok"]
        for field in required_checks:
            self.assertIn(field, self.wizard_src, f"Preflight field '{field}' not checked in wizard")

    def test_ipc_preflight_bound_to_rust_command(self):
        # preflightUpgrade must invoke 'preflight_upgrade' Rust command
        self.assertIn("preflight_upgrade", self.ipc_src)

    def test_ipc_install_bound_to_rust_command(self):
        self.assertIn("install_wsa_package", self.ipc_src)

    def test_ipc_download_bound_to_rust_command(self):
        self.assertIn("download_and_stage_release", self.ipc_src)


class TestInstallerWizardEditions(unittest.TestCase):
    def setUp(self):
        self.wizard_src = (COMPONENTS / "InstallerWizard.tsx").read_text(encoding="utf-8")

    def test_standard_edition_option_exists(self):
        self.assertIn("standard", self.wizard_src)

    def test_banking_edition_option_exists(self):
        self.assertIn("banking", self.wizard_src)

    def test_wizard_uses_resolve_edition_asset(self):
        # Must resolve edition to a specific registry asset, not hardcode a URL
        self.assertIn("resolveEditionAsset", self.wizard_src)

    def test_edition_selection_is_interactive(self):
        # The wizard must let users pick an edition
        self.assertIn("setSelectedEdition", self.wizard_src)
        self.assertIn("selectedEdition", self.wizard_src)


class TestInstallerWizardErrorHandling(unittest.TestCase):
    def setUp(self):
        self.wizard_src = (COMPONENTS / "InstallerWizard.tsx").read_text(encoding="utf-8")

    def test_wizard_has_error_step(self):
        self.assertIn("'error'", self.wizard_src)

    def test_wizard_surfaces_error_message(self):
        self.assertIn("errorMessage", self.wizard_src)

    def test_wizard_allows_restart_on_error(self):
        # User must be able to restart from error step
        self.assertIn("Start Over", self.wizard_src)

    def test_download_error_is_caught(self):
        # Download step must have try/catch
        download_idx = self.wizard_src.find("handleDownload")
        self.assertGreater(download_idx, -1)
        after_download = self.wizard_src[download_idx:download_idx + 500]
        self.assertIn("catch", after_download)

    def test_install_error_is_caught(self):
        install_idx = self.wizard_src.find("handleInstall")
        self.assertGreater(install_idx, -1)
        after_install = self.wizard_src[install_idx:install_idx + 500]
        self.assertIn("catch", after_install)


if __name__ == "__main__":
    unittest.main()
