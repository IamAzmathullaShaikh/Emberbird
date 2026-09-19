import type {
  WsaStatus,
  UpdateStatus,
  ManagerEnvConfig,
  BackupResult,
  RestoreCandidate,
  RestoreResult,
  UpgradePreflight,
  UpgradeOptions,
  UpgradeResult,
  InstallResult,
} from './types';

declare global {
  interface Window {
    __TAURI_INTERNALS__?: unknown;
  }
}

async function invokeTauri<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  if (typeof window !== 'undefined' && window.__TAURI_INTERNALS__) {
    const { invoke } = await import('@tauri-apps/api/core');
    return invoke<T>(cmd, args);
  }

  // Throw error instead of returning mock data to ensure the app doesn't lie during development
  throw new Error(`Tauri backend not detected. Command '${cmd}' cannot be executed in browser mode.`);
}

// mockInvoke is now deprecated and removed to ensure truth in status detection.

export async function detectWsaStatus(): Promise<WsaStatus> {
  return invokeTauri<WsaStatus>('detect_wsa_status');
}

export async function checkForUpdates(): Promise<UpdateStatus> {
  return invokeTauri<UpdateStatus>('check_for_updates');
}

// E3C.4: the legacy latest-releases IPC wrapper was removed — the Rust
// command it wrapped was a stub returning `[]` (zero discovery), and release
// truth now resolves from the bundled Ember Registry via `lib/registry.ts`.

export async function validateEnvironment(): Promise<ManagerEnvConfig> {
  return invokeTauri<ManagerEnvConfig>('validate_manager_env');
}

export async function createVhdxBackup(note?: string): Promise<BackupResult> {
  return invokeTauri<BackupResult>('create_vhdx_backup', { note });
}

export async function listBackupCandidates(): Promise<RestoreCandidate[]> {
  return invokeTauri<RestoreCandidate[]>('list_backup_candidates');
}

export async function restoreVhdxBackup(
  candidateId: string
): Promise<RestoreResult> {
  return invokeTauri<RestoreResult>('restore_vhdx_backup', {
    candidate_id: candidateId,
  });
}

export async function pruneBackups(retainCount: number): Promise<string[]> {
  return invokeTauri<string[]>('prune_backups', { retain_count: retainCount });
}

export async function preflightUpgrade(
  packagePath?: string
): Promise<UpgradePreflight> {
  return invokeTauri<UpgradePreflight>('preflight_upgrade', {
    package_path: packagePath,
  });
}

export async function executeUpgrade(
  options: UpgradeOptions
): Promise<UpgradeResult> {
  return invokeTauri<UpgradeResult>('execute_upgrade', { options });
}

export async function installWsaPackage(
  packagePath: string
): Promise<InstallResult> {
  return invokeTauri<InstallResult>('install_wsa_package', {
    package_path: packagePath,
  });
}

export async function launchWsa(target?: string): Promise<void> {
  return invokeTauri<void>('launch_wsa', { target });
}

export async function shutdownWsa(): Promise<void> {
  return invokeTauri<void>('shutdown_wsa');
}

