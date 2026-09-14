import type { Architecture, RootFlavor, GAppsFlavor, ReleaseAsset, NormalizedAsset } from './types.ts';

export function detectArchitecture(filename: string): Architecture {
  const lower = filename.toLowerCase();
  if (lower.includes('x64') || lower.includes('x86_64')) return 'x64';
  if (lower.includes('arm64') || lower.includes('aarch64')) return 'arm64';
  return 'unknown';
}

export function detectRootFlavor(filename: string): RootFlavor {
  const lower = filename.toLowerCase();
  if (lower.includes('magisk')) return 'Magisk';
  if (lower.includes('kernelsu')) return 'KernelSU';
  if (lower.includes('none') || lower.includes('noroot') || lower.includes('vanilla')) return 'NoRoot';
  // WSA Standard Edition archives have no root token in their filename at all
  // (e.g. `WSA_2407.40000.4.0_x64.7z`) — absence of a GApps-pure marker means
  // the rooted build. Only classify when the name plausibly refers to WSA.
  if (lower.includes('wsa_') && lower.endsWith('.7z')) return 'Magisk';
  return 'unknown';
}

export function detectGAppsFlavor(filename: string): GAppsFlavor {
  const lower = filename.toLowerCase();
  if (lower.includes('pico')) return 'GApps-Pico';
  if (lower.includes('mindthegapps')) return 'MindTheGapps';
  if (lower.includes('nogapps') || lower.includes('no-gapps')) return 'NoGApps';
  // WSA release assets: both Standard and Banking editions ship OpenGApps Pico
  // (release.yml build matrix), so any WSA_*.7z archive carries GApps unless a
  // nogapps token says otherwise. The Banking Edition is the `vanilla` ramdisk.
  if (lower.includes('wsa_') && lower.endsWith('.7z')) return 'GApps-Pico';
  return 'unknown';
}

export function formatBytes(bytes: number, decimals: number = 2): string {
  if (!bytes || bytes <= 0) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const safeI = Math.min(i, sizes.length - 1);
  return `${parseFloat((bytes / Math.pow(k, safeI)).toFixed(dm))} ${sizes[safeI]}`;
}

export function formatDate(isoString: string): string {
  if (!isoString) return 'Unknown Date';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return 'Unknown Date';
    return d.toISOString().split('T')[0];
  } catch {
    return 'Unknown Date';
  }
}

export function parseNormalizedAsset(
  asset: ReleaseAsset,
  checksums?: Record<string, string>
): NormalizedAsset {
  const architecture = detectArchitecture(asset.name);
  const rootFlavor = detectRootFlavor(asset.name);
  const gappsFlavor = detectGAppsFlavor(asset.name);
  const formattedSize = formatBytes(asset.size);
  const sha256 = checksums ? checksums[asset.name] : undefined;

  return {
    assetId: asset.id,
    fileName: asset.name,
    fileSizeBytes: asset.size,
    formattedSize,
    downloadUrl: asset.browser_download_url,
    architecture,
    rootFlavor,
    gappsFlavor,
    sha256
  };
}
