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

  // Pure Web Fallback for browser development/preview
  return mockInvoke<T>(cmd, args);
}

function mockInvoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  const repo = 'IamAzmathullaShaikh/Emberbird';
  const ghDomain = 'github.com';
  switch (cmd) {
    case 'detect_wsa_status':
      return Promise.resolve({
        installed: true,
        package_version: '2311.40000.5.0',
        developer_mode_enabled: true,
        virtualization_enabled: true,
        is_running: false,
        install_path:
          'C:\\Program Files\\WindowsApps\\MicrosoftCorporationII.WindowsSubsystemForAndroid_2311.40000.5.0_x64__8wekyb3d8bbwe',
        vhdx_path:
          '%LOCALAPPDATA%\\Packages\\MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe\\LocalCache\\userdata.vhdx',
        state: 'INSTALLED',
        state_evidence: [
          'Installed version 2311.40000.5.0 satisfies the supported baseline 2311.40000.5.0.',
        ],
      } as unknown as T);

    case 'check_for_updates':
      return Promise.resolve({
        update_available: false,
        current_version: '2311.40000.5.0',
        latest_version: '2311.40000.5.0',
        latest_release: null,
      } as unknown as T);

    case 'get_latest_releases':
      return Promise.resolve([] as unknown as T);

    case 'validate_manager_env':
      return Promise.resolve({
        github_repo: repo,
        repo_url: `https://${ghDomain}/${repo}`,
        releases_url: `https://${ghDomain}/${repo}/releases`,
      } as unknown as T);

    case 'create_vhdx_backup':
      return Promise.resolve({
        success: true,
        metadata: {
          id: `backup_${new Date().toISOString().replace(/[-:T.Z]/g, '').slice(0, 14)}`,
          timestamp: new Date().toISOString(),
          wsa_version: '2311.40000.5.0',
          source_path:
            '%LOCALAPPDATA%\\Packages\\MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe\\LocalCache\\userdata.vhdx',
          backup_path: '%LOCALAPPDATA%\\WSABuilds\\backups\\mock\\userdata.vhdx',
          file_size_bytes: 4294967296,
          sha256:
            'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
          description: (args?.note as string) || 'Manual snapshot',
          status: 'completed',
        },
        error: null,
      } as unknown as T);

    case 'list_backup_candidates':
      return Promise.resolve([
        {
          id: 'backup_20260901_120000',
          timestamp: '2026-09-01T12:00:00.000Z',
          wsa_version: '2311.40000.5.0',
          backup_path:
            'C:\\WSABuilds\\backups\\backup_20260901_120000\\userdata.vhdx',
          file_size_bytes: 4831838208,
          sha256:
            '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
          description: 'Stable Magisk 27.0 baseline',
          is_valid: true,
          validation_error: null,
        },
        {
          id: 'backup_20260815_093000',
          timestamp: '2026-08-15T09:30:00.000Z',
          wsa_version: '2311.40000.4.0',
          backup_path:
            'C:\\WSABuilds\\backups\\backup_20260815_093000\\userdata.vhdx',
          file_size_bytes: 3221225472,
          sha256:
            '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
          description: 'Pre-upgrade snapshot',
          is_valid: true,
          validation_error: null,
        },
      ] as unknown as T);

    case 'restore_vhdx_backup':
      return Promise.resolve({
        success: true,
        candidate_id: (args?.candidate_id as string) || 'backup_20260901_120000',
        restored_path:
          '%LOCALAPPDATA%\\Packages\\MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe\\LocalCache\\userdata.vhdx',
        restored_sha256:
          '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
        message: 'Mock restore executed and integrity verified successfully',
      } as unknown as T);

    case 'prune_backups':
      return Promise.resolve(['backup_20260815_093000'] as unknown as T);

    case 'preflight_upgrade':
      return Promise.resolve({
        windows_version_ok: true,
        windows_build: 22631,
        dev_mode_ok: true,
        virtualization_ok: true,
        disk_space_ok: true,
        free_disk_bytes: 53687091200,
        required_disk_bytes: 26843545600,
        wsa_running: false,
        has_existing_vhdx: true,
        warnings: [],
        errors: [],
        can_upgrade: true,
      } as unknown as T);

    case 'execute_upgrade':
      return Promise.resolve({
        success: true,
        backup_metadata: {
          id: 'backup_pre_upgrade',
          timestamp: new Date().toISOString(),
          wsa_version: '2311.40000.5.0',
          source_path: 'C:\\userdata.vhdx',
          backup_path:
            'C:\\WSABuilds\\backups\\backup_pre_upgrade\\userdata.vhdx',
          file_size_bytes: 4294967296,
          sha256:
            'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
          description: 'Automated pre-upgrade snapshot',
          status: 'completed',
        },
        installed_manifest: 'C:\\WSA_Latest\\AppxManifest.xml',
        message: 'Upgrade completed successfully',
      } as unknown as T);

    case 'install_wsa_package':
      return Promise.resolve({
        success: true,
        package_path:
          (args?.package_path as string) ||
          'C:\\WSABuilds\\WSA_2407.40000.4.0_x64_Release-Magisk\\AppxManifest.xml',
        message: 'WSA package registered successfully via AppX deployment API',
      } as unknown as T);

    default:
      return Promise.reject(new Error(`Unknown Tauri command: ${cmd}`));
  }
}

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

