export interface ReleaseAsset {
  id: number;
  name: string;
  size: number;
  download_count: number;
  browser_download_url: string;
  created_at: string;
}

export interface GitHubRelease {
  id: number;
  tag_name: string;
  name: string;
  published_at: string;
  body: string;
  html_url: string;
  assets: ReleaseAsset[];
}

export interface ParsedPackage {
  assetId: number;
  fileName: string;
  fileSize: number;
  downloadUrl: string;
  arch: 'x64' | 'arm64' | 'unknown';
  root: 'Magisk' | 'KernelSU' | 'NoRoot' | 'unknown';
  gapps: 'GApps-Pico' | 'MindTheGapps' | 'NoGApps' | 'unknown';
}
