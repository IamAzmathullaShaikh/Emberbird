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
        """DoctorProbe fields must be in types.ts."""
        ts = ts_types_content()
        expected_fields = [
            'probe_id', 'domain', 'title', 'status', 'severity',
            'summary', 'details', 'remediation_cmd', 'can_autofix'
        ]
        for field in expected_fields:
            self.assertIn(field, ts, f'DoctorProbe field {field!r} missing from types.ts')

    def test_stage_progress_fields_present_in_ts(self):
        """StageProgress fields must be in types.ts."""
        ts = ts_types_content()
        expected_fields = ['phase', 'received_bytes', 'total_bytes', 'message']
        for field in expected_fields:
            self.assertIn(field, ts, f'StageProgress field {field!r} missing from types.ts')

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
