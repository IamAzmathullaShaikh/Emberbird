import type { WsaStatus, UpdateStatus, ReleaseInfo, ManagerEnvConfig } from './types';

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
  return mockInvoke<T>(cmd);
}

function mockInvoke<T>(cmd: string): Promise<T> {
  switch (cmd) {
    case 'detect_wsa_status':
      return Promise.resolve({
        installed: true,
        package_version: '2311.40000.5.0',
        developer_mode_enabled: true,
        virtualization_enabled: true,
        is_running: false,
        install_path: 'C:\\Program Files\\WindowsApps\\MicrosoftCorporationII.WindowsSubsystemForAndroid_2311.40000.5.0_x64__8wekyb3d8bbwe',
        vhdx_path: '%LOCALAPPDATA%\\Packages\\MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe\\LocalCache\\userdata.vhdx'
      } as unknown as T);

    case 'check_for_updates':
      return Promise.resolve({
        update_available: false,
        current_version: '2311.40000.5.0',
        latest_version: '2311.40000.5.0',
        latest_release: null
      } as unknown as T);

    case 'get_latest_releases':
      return Promise.resolve([] as unknown as T);

    case 'validate_manager_env':
      return Promise.resolve({
        github_repo: 'IamAzmathullaShaikh/WSABuilds',
        repo_url: 'https://github.com/IamAzmathullaShaikh/WSABuilds',
        releases_url: 'https://github.com/IamAzmathullaShaikh/WSABuilds/releases'
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

export async function getLatestReleases(): Promise<ReleaseInfo[]> {
  return invokeTauri<ReleaseInfo[]>('get_latest_releases');
}

export async function validateEnvironment(): Promise<ManagerEnvConfig> {
  return invokeTauri<ManagerEnvConfig>('validate_manager_env');
}
