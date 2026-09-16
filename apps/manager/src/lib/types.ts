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
  /** 'unknown' = not derivable from the filename (e.g. manager archives). */
  root_flavor: 'Magisk' | 'KernelSU' | 'None' | 'unknown';
  gapps_flavor: 'Pico' | 'MindTheGapps' | 'None' | 'unknown';
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
  windows_version_ok: boolean;
  windows_build: number;
  dev_mode_ok: boolean;
  virtualization_ok: boolean;
  disk_space_ok: boolean;
  free_disk_bytes: number;
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

export type NavigationTab = 'dashboard' | 'updates' | 'backups' | 'restore';
