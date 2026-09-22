"""QG-3: Type drift detection between Rust IPC structs and TypeScript types.

This test reads both the Rust source and the TypeScript types file and checks
that every Rust struct field that is #[serde] serialized has a corresponding
property in the TypeScript types file.

This is a structural guard, not full code generation. Full automation is in
QG-3 (tauri-specta) once a stable release is available.
"""
import unittest
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
RUST_SRC = ROOT / 'apps/manager/src-tauri/src'
TS_TYPES = ROOT / 'apps/manager/src/lib/types.ts'

def extract_rust_struct_fields(rust_file: Path, struct_name: str) -> set[str]:
    """Extract field names from a Rust struct."""
    content = rust_file.read_text(encoding='utf-8')
    # Find the struct block
    pattern = rf'pub struct {struct_name}\s*{{([^}}]+)}}'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return set()
    block = match.group(1)
    # Extract field names (pub field_name: Type)
    fields = re.findall(r'pub\s+(\w+)\s*:', block)
    return set(fields)

def ts_types_content() -> str:
    return TS_TYPES.read_text(encoding='utf-8')

class TestTypeDrift(unittest.TestCase):
    """Guard against silent drift between Rust IPC structs and TypeScript types."""

    def test_wsa_status_fields_present_in_ts(self):
        """WsaStatus Rust fields must all appear in types.ts."""
        ts = ts_types_content()
        expected_fields = [
            'installed', 'package_version', 'developer_mode_enabled',
             'virtualization_enabled', 'is_running', 'install_path',
            'vhdx_path', 'state', 'state_evidence'
        ]
        for field in expected_fields:
            self.assertIn(field, ts, f'WsaStatus field {field!r} missing from types.ts')

    def test_upgrade_preflight_fields_present_in_ts(self):
        """UpgradePreflight fields must be in types.ts."""
        ts = ts_types_content()
        expected_fields = [
            'windows_version_ok', 'windows_build', 'required_windows_build',
            'dev_mode_ok', 'virtualization_ok', 'disk_space_ok',
            'free_disk_bytes', 'required_disk_bytes', 'wsa_running',
            'has_existing_vhdx', 'warnings', 'errors', 'can_upgrade'
        ]
        for field in expected_fields:
            self.assertIn(field, ts, f'UpgradePreflight field {field!r} missing from types.ts')

    def test_doctor_probe_fields_present_in_ts(self):
        """Every DoctorProbe field in Rust must appear in types.ts.

        Derived from the Rust struct rather than a hardcoded list: a field added
        to `DoctorProbe` without the TypeScript mirror is invisible to a baked-in
        list, which is exactly the drift this guard exists to catch.
        """
        rust_fields = extract_rust_struct_fields(RUST_SRC / 'doctor.rs', 'DoctorProbe')
        self.assertTrue(
            rust_fields,
            'failed to parse DoctorProbe from doctor.rs — the guard is blind, not the code clean',
        )
        ts = ts_types_content()
        missing = sorted(field for field in rust_fields if field not in ts)
        self.assertEqual(
            missing, [],
            f'DoctorProbe fields declared in Rust but missing from types.ts: {missing}',
        )

    def test_doctor_probe_ph05_fields_mirrored(self):
        """PH-05 added evidence, timestamp and verification to each probe."""
        ts = ts_types_content()
        for field in ['evidence', 'timestamp', 'verification', 'captured_at']:
            self.assertIn(field, ts, f'PH-05 field {field!r} missing from types.ts')
        for token in ['NOT_ATTEMPTED', 'VERIFIED', 'STILL_FAILING']:
            self.assertIn(
                token, ts,
                f'PH-05 verification token {token!r} missing from types.ts',
            )

    def test_stage_progress_fields_present_in_ts(self):
        """StageProgress fields must be in types.ts."""
        ts = ts_types_content()
        expected_fields = ['phase', 'received_bytes', 'total_bytes', 'message']
        for field in expected_fields:
            self.assertIn(field, ts, f'StageProgress field {field!r} missing from types.ts')

    def test_lifecycle_report_fields_present_in_ts(self):
        """Every LifecycleReport field in Rust must appear in types.ts.

        Derived from the Rust struct: a field added to `LifecycleReport`
        without the TypeScript mirror is invisible to a baked-in list.
        """
        rust_fields = extract_rust_struct_fields(RUST_SRC / 'runtime_state.rs', 'LifecycleReport')
        self.assertTrue(
            rust_fields,
            'failed to parse LifecycleReport from runtime_state.rs — the guard is blind, not the code clean',
        )
        ts = ts_types_content()
        missing = sorted(field for field in rust_fields if field not in ts)
        self.assertEqual(
            missing, [],
            f'LifecycleReport fields declared in Rust but missing from types.ts: {missing}',
        )

    def test_lifecycle_state_values_in_ts(self):
        """All 14 RuntimeState values must exist in types.ts.

        Derived from the Rust enum rather than a hardcoded list, so a state
        added on the Rust side without the TS mirror fails here.
        """
        content = (RUST_SRC / 'runtime_state.rs').read_text(encoding='utf-8')
        match = re.search(
            r'pub enum RuntimeState\s*\{([^}]+)\}', content, re.DOTALL
        )
        self.assertIsNotNone(match, 'failed to parse the RuntimeState enum')
        variants = [
            v.strip() for v in match.group(1).split(',')
            if v.strip() and not v.strip().startswith('//')
        ]
        self.assertEqual(len(variants), 14, f'expected 14 lifecycle states, found {variants}')
        # serde(rename_all = "SCREAMING_SNAKE_CASE") — the wire names are the
        # camel-case conversion, not the Rust identifiers.
        def screaming_snake(name: str) -> str:
            return re.sub(r'(?<!^)(?=[A-Z])', '_', name).upper()

        ts = ts_types_content()
        for variant in variants:
            wire = screaming_snake(variant)
            self.assertIn(
                f"'{wire}'", ts,
                f'RuntimeState {variant!r} (wire: {wire!r}) missing from types.ts',
            )

    def test_backup_metadata_fields_present_in_ts(self):
        """BackupMetadata fields must be in types.ts."""
        ts = ts_types_content()
        expected_fields = [
            'id', 'timestamp', 'wsa_version', 'source_path',
            'backup_path', 'file_size_bytes', 'sha256', 'description', 'status'
        ]
        for field in expected_fields:
            self.assertIn(field, ts, f'BackupMetadata field {field!r} missing from types.ts')

    def test_stage_phase_values_in_ts(self):
        """StagePhase enum values must be in types.ts."""
        ts = ts_types_content()
        for phase in ['downloading', 'verifying', 'extracting', 'done']:
            self.assertIn(phase, ts, f'StagePhase value {phase!r} missing from types.ts')

    def test_navigation_tab_values_in_ts(self):
        """NavigationTab must include all 6 tab identifiers."""
        ts = ts_types_content()
        for tab in ['dashboard', 'updates', 'backups', 'restore', 'doctor', 'licenses']:
            self.assertIn(tab, ts, f'NavigationTab value {tab!r} missing from types.ts')

if __name__ == '__main__':
    unittest.main()
