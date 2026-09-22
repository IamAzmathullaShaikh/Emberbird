/**
 * Authoritative subsystem lifecycle states (mirror of the Rust `SubsystemState`).
 * Values are SCREAMING_SNAKE_CASE exactly as the backend serializes them.
 */
export type SubsystemState =
  | 'NOT_INSTALLED'
  | 'INSTALLED'
  | 'INSTALLED_OUTDATED'
  | 'PARTIALLY_INSTALLED'
  | 'UNKNOWN';

export interface WsaStatus {
  installed: boolean;
  package_version: string | null;
  developer_mode_enabled: boolean;
  virtualization_enabled: boolean;
  is_running: boolean;
  install_path: string | null;
  vhdx_path: string | null;
  /** Authoritative lifecycle state — the ONLY source the UI may render install wording from. */
  state: SubsystemState;
  /** Evidence trail explaining how `state` was derived on the backend. */
  state_evidence: string[];
}

export interface ReleaseAsset {
  name: string;
  size: number;
  browser_download_url: string;
  architecture: 'x64' | 'arm64' | 'unknown';
  /** Registry row truth; 'unknown' when the row declares no root solution. */
  root_flavor: 'Magisk' | 'KernelSU' | 'None' | 'unknown';
  gapps_flavor: 'Pico' | 'MindTheGapps' | 'None' | 'unknown';
  /** Registry edition this asset belongs to (subsystem rows only). */
  edition?: 'standard' | 'banking';
}

export interface ReleaseInfo {
  tag_name: string;
  name: string;
  published_at: string;
  body: string;
  assets: ReleaseAsset[];
}

export interface UpdateStatus {
  update_available: boolean;
  current_version: string;
  latest_version: string;
  latest_release: ReleaseInfo | null;
}

export interface ManagerEnvConfig {
  github_repo: string;
  repo_url: string;
  releases_url: string;
}

export interface BackupMetadata {
  id: string;
  timestamp: string;
  wsa_version: string;
  source_path: string;
  backup_path: string;
  file_size_bytes: number;
  sha256: string;
  description: string | null;
  status: string;
}

export interface BackupResult {
  success: boolean;
  metadata: BackupMetadata | null;
  error: string | null;
}

export interface RestoreCandidate {
  id: string;
  timestamp: string;
  wsa_version: string;
  backup_path: string;
  file_size_bytes: number;
  sha256: string;
  description: string | null;
  is_valid: boolean;
  validation_error: string | null;
}

export interface RestorePreflight {
  can_restore: boolean;
  candidate_id: string;
  backup_path: string;
  target_path: string;
  backup_size_bytes: number;
  sha256: string;
  warnings: string[];
  errors: string[];
}

export interface RestoreResult {
  success: boolean;
  candidate_id: string;
  restored_path: string;
  restored_sha256: string;
  message: string;
}

export interface UpgradePreflight {
  /** null = the host build could not be read (UNVERIFIED — never a pass). */
  windows_version_ok: boolean | null;
  windows_build: number | null;
  /** Minimum supported build from preflight truth — the UI renders this, not a hardcoded string. */
  required_windows_build: number;
  dev_mode_ok: boolean;
  virtualization_ok: boolean;
  /** null = free space could not be measured (UNVERIFIED — never a pass). */
  disk_space_ok: boolean | null;
  free_disk_bytes: number | null;
  required_disk_bytes: number;
  wsa_running: boolean;
  has_existing_vhdx: boolean;
  warnings: string[];
  errors: string[];
  can_upgrade: boolean;
}

export interface UpgradeOptions {
  package_path: string;
  create_backup: boolean;
  backup_note?: string;
}

export interface UpgradeResult {
  success: boolean;
  backup_metadata: BackupMetadata | null;
  installed_manifest: string | null;
  message: string;
}

export interface InstallResult {
  success: boolean;
  package_path: string;
  message: string;
}

/** FB-3 — phases of the download→verify→extract→stage pipeline. */
export type StagePhase = 'downloading' | 'verifying' | 'extracting' | 'done';

/** Progress payload emitted on the `stage-progress` Tauri event. */
export interface StageProgress {
  phase: StagePhase;
  received_bytes: number;
  total_bytes: number;
  message: string;
}

/** Result of download_and_stage_release: a verified, extracted package. */
export interface StagedAsset {
  archive_path: string;
  staged_path: string;
  manifest_path: string;
  sha256: string;
  size_bytes: number;
}

export interface DoctorProbe {
  probe_id: string;
  domain: string;
  title: string;
  status: 'PASS' | 'WARN' | 'FAIL' | 'UNKNOWN' | 'N/A';
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  summary: string;
  details: string;
  remediation_cmd?: string | null;
  can_autofix: boolean;
  /** PH-05: the observation backing this verdict. */
  evidence: string;
  /** PH-05: capture time of the observation (UTC, RFC 3339). */
  timestamp: string;
  /** PH-05: whether a remediation was re-probed and cleared the fault. */
  verification: 'NOT_ATTEMPTED' | 'VERIFIED' | 'STILL_FAILING' | 'N/A';
}

export interface DoctorReportData {
  platform_name: string;
  version: string;
  system_os: string;
  os_release: string;
  architecture: string;
  overall_status: 'PASS' | 'WARN' | 'FAIL' | 'UNKNOWN' | 'N/A';
  exit_code: number;
  total_probes: number;
  passed_count: number;
  warn_count: number;
  fail_count: number;
  /** PH-05: report-level capture time, so a stored report is dated evidence. */
  captured_at: string;
  probes: DoctorProbe[];
}

export type NavigationTab = 'dashboard' | 'updates' | 'backups' | 'restore' | 'doctor' | 'licenses';

// ---------------------------------------------------------------------------
// Runtime lifecycle (PH-02 engine, PH-08 surface). Mirrors runtime_state.rs.
// ---------------------------------------------------------------------------

/** Authoritative runtime lifecycle states — mirrors `RuntimeState`. */
export type RuntimeState =
  | 'UNKNOWN'
  | 'NOT_INSTALLED'
  | 'CHECKING'
  | 'INSTALLING'
  | 'INSTALLED'
  | 'STARTING'
  | 'RUNNING'
  | 'STOPPING'
  | 'STOPPED'
  | 'DEGRADED'
  | 'BROKEN'
  | 'UPDATING'
  | 'ROLLING_BACK'
  | 'UNINSTALLING';

/** One recorded lifecycle move — mirrors `StateChange`. */
export interface LifecycleStateChange {
  from: RuntimeState;
  to: RuntimeState;
  /** UTC, RFC 3339 with milliseconds. */
  at: string;
  reason: string;
}

/** How a fresh process reconciled its persisted lifecycle — mirrors `ReconciliationOutcome`. */
export type ReconciliationOutcome =
  | { kind: 'FRESH'; state: RuntimeState }
  | { kind: 'RECOVERED'; recovered: RuntimeState; state: RuntimeState; action: string }
  | { kind: 'UNREADABLE'; reason: string };

/** The reconciled lifecycle plus its audit tail — mirrors `LifecycleReport`. */
export interface LifecycleReport {
  state: RuntimeState;
  /** Whether an operation is in flight; conflicting actions must be withheld. */
  busy: boolean;
  legal_next: RuntimeState[];
  outcome: ReconciliationOutcome;
  history_tail: LifecycleStateChange[];
}

