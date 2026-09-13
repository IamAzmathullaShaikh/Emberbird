import type { GitHubRelease, ReleaseAsset, ParsedPackage } from './types';

const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes
let cachedRelease: { data: GitHubRelease; timestamp: number } | null = null;

export async function fetchLatestRelease(
  repoOwnerRepo: string = 'IamAzmathullaShaikh/WSABuilds'
): Promise<GitHubRelease | null> {
  const now = Date.now();
  if (cachedRelease && now - cachedRelease.timestamp < CACHE_TTL_MS) {
    return cachedRelease.data;
  }

  const endpoint = `https://api.github.com/repos/${repoOwnerRepo}/releases/latest`;
  try {
    const response = await fetch(endpoint, {
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'WSABuilds-WebClient'
      }
    });

    if (!response.ok) {
      console.error(`GitHub API error: ${response.status} ${response.statusText}`);
      return null;
    }

    const release: GitHubRelease = await response.json();
    cachedRelease = { data: release, timestamp: now };
    return release;
  } catch (error) {
    console.error('Network failure fetching latest release:', error);
    return null;
  }
}

export function parsePackageFileName(asset: ReleaseAsset): ParsedPackage {
  const name = asset.name.toLowerCase();

  let arch: ParsedPackage['arch'] = 'unknown';
  if (name.includes('x64')) arch = 'x64';
  else if (name.includes('arm64')) arch = 'arm64';

  let root: ParsedPackage['root'] = 'unknown';
  if (name.includes('magisk')) root = 'Magisk';
  else if (name.includes('kernelsu')) root = 'KernelSU';
  else if (name.includes('none') || name.includes('noroot')) root = 'NoRoot';

  let gapps: ParsedPackage['gapps'] = 'unknown';
  if (name.includes('pico')) gapps = 'GApps-Pico';
  else if (name.includes('mindthegapps')) gapps = 'MindTheGapps';
  else if (name.includes('nogapps')) gapps = 'NoGApps';

  return {
    assetId: asset.id,
    fileName: asset.name,
    fileSize: asset.size,
    downloadUrl: asset.browser_download_url,
    arch,
    root,
    gapps
  };
}

export function filterPackages(
  packages: ParsedPackage[],
  filters: { arch?: string; root?: string; gapps?: string }
): ParsedPackage[] {
  return packages.filter((pkg) => {
    if (filters.arch && pkg.arch !== filters.arch) return false;
    if (filters.root && pkg.root !== filters.root) return false;
    if (filters.gapps && pkg.gapps !== filters.gapps) return false;
    return true;
  });
}
