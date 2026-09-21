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
  StagedAsset,
  StageProgress,
  DoctorProbe,
} from './types';

declare global {
  interface Window {
    __TAURI_INTERNALS__?: unknown;
  }
}

/** True inside a real Tauri webview; false in browser/dev mode. */
function hasTauriBackend(): boolean {
  return typeof window !== 'undefined' && Boolean(window.__TAURI_INTERNALS__);
}

async function invokeTauri<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  if (hasTauriBackend()) {
    const { invoke } = await import('@tauri-apps/api/core');
    return invoke<T>(cmd, args);
  }

  // Throw error instead of returning mock data to ensure the app doesn't lie during development
  throw new Error(`Tauri backend not detected. Command '${cmd}' cannot be executed in browser mode.`);
}

export async function detectWsaStatus(): Promise<WsaStatus> {
  return invokeTauri<WsaStatus>('detect_wsa_status');
}

export async function checkForUpdates(): Promise<UpdateStatus> {
  return invokeTauri<UpdateStatus>('check_for_updates');
}

export async function runDoctorScan(): Promise<DoctorProbe[]> {
  return invokeTauri<DoctorProbe[]>('run_doctor_scan');
}

// E3C.4: the legacy latest-releases IPC wrapper was removed — release truth
// now resolves from the bundled Ember Registry via `lib/registry.ts`.

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

/**
 * FB-3 — Resolve the published registry asset for (release_tag, edition),
 * stream it to the staging area with SHA-256 verification, extract it, and
 * return the staged manifest path. Progress arrives via `stage-progress`
 * events when running inside Tauri; in browser mode the wrapper still throws
 * (Zero-Mock law).
 */
export async function downloadAndStageRelease(
  releaseTag: string,
  edition: string,
  onProgress?: (p: StageProgress) => void
): Promise<StagedAsset> {
  let unlisten: (() => void) | null = null;
  if (onProgress && hasTauriBackend()) {
    const { listen } = await import('@tauri-apps/api/event');
    unlisten = await listen<StageProgress>('stage-progress', (event) =>
      onProgress(event.payload)
    );
  }
  try {
    return await invokeTauri<StagedAsset>('download_and_stage_release', {
      release_tag: releaseTag,
      edition,
    });
  } finally {
    if (unlisten) unlisten();
  }
}

export async function launchWsa(target?: string): Promise<void> {
  return invokeTauri<void>('launch_wsa', { target });
}

export async function shutdownWsa(): Promise<void> {
  return invokeTauri<void>('shutdown_wsa');
}

/**
 * Returns the host machine's CPU architecture as reported by the Rust
 * runtime (`std::env::consts::ARCH`). Examples: "x86_64", "aarch64".
 * Rule 17: no UA string guessing — architecture is a real system probe.
 */
export async function getHostArch(): Promise<string> {
  return invokeTauri<string>('get_host_arch');
}
