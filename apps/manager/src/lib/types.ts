export interface WsaStatus {
  installed: boolean;
  package_version: string | null;
  developer_mode_enabled: boolean;
  virtualization_enabled: boolean;
  is_running: boolean;
  install_path: string | null;
  vhdx_path: string | null;
}

export interface ReleaseAsset {
  name: string;
  size: number;
  browser_download_url: string;
  architecture: 'x64' | 'arm64' | 'unknown';
  root_flavor: 'Magisk' | 'KernelSU' | 'None';
  gapps_flavor: 'Pico' | 'MindTheGapps' | 'None';
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
