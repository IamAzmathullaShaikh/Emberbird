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

export type Architecture = 'x64' | 'arm64' | 'unknown';
export type RootFlavor = 'Magisk' | 'KernelSU' | 'NoRoot' | 'unknown';
export type GAppsFlavor = 'GApps-Pico' | 'MindTheGapps' | 'NoGApps' | 'unknown';

/** A release asset parsed into its WSABuilds identity components. */
export interface ParsedPackage {
  assetId: number;
  fileName: string;
  fileSize: number;
  downloadUrl: string;
  arch: Architecture;
  root: RootFlavor;
  gapps: GAppsFlavor;
}

export interface NormalizedAsset {
  assetId: number;
  fileName: string;
  fileSizeBytes: number;
  formattedSize: string;
  downloadUrl: string;
  architecture: Architecture;
  rootFlavor: RootFlavor;
  gappsFlavor: GAppsFlavor;
  sha256?: string;
}

export interface UnifiedRelease {
  id: number;
  tag: string;
  name: string;
  publishedAt: string;
  formattedDate: string;
  notes: string;
  releaseUrl: string;
  assets: NormalizedAsset[];
  /** Coarse product family of the release, derived from its tag. */
  channel: 'manager' | 'wsa';
}

export interface ReleaseFilterOptions {
  architecture?: Architecture;
  rootFlavor?: RootFlavor;
  gappsFlavor?: GAppsFlavor;
}

export interface ReleaseProvider {
  name: string;
  getLatestRelease(): Promise<UnifiedRelease | null>;
  /** Fetch a specific release by exact tag (e.g. `v0.2.2` or `wsa-v2311.40000.5.0`). */
  getReleaseByTag(tag: string): Promise<UnifiedRelease | null>;
  /** Fetch every published release, newest first (as ordered by the GitHub API). */
  listReleases(): Promise<UnifiedRelease[]>;
}
