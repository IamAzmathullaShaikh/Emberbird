/**
 * E3C.2 — Registry resolution for the Manager (G2).
 *
 * Release truth comes from the bundled Ember Registry
 * (`data/releases/releases.json`) — the repository's single source of truth —
 * mapped into the Manager's existing `ReleaseInfo` contract (types.ts). No
 * network I/O: the registry is validated by CI's Reality Gate before any
 * build that embeds it. Published artifact identities (filenames, hashes)
 * are carried verbatim (E5 boundary respected).
 *
 * The legacy release-URL derivation in env.ts/ipc.ts is config plumbing that
 * survives E3C unchanged (it derives repo URLs, not release truth); the
 * inventoried derivation modules leave the M3 inventory as their role is
 * documented, not removed — see CONSUMER_MATRIX.
 */
import type { ReleaseInfo, ReleaseAsset } from './types';
import registryData from '../../../../data/releases/releases.json' with { type: 'json' };

/** Minimal structural view of the registry consumed here. */
interface RegistryAssetRow {
  filename: string;
  sha256: string;
  source_url: string;
  size_bytes?: number;
  arch?: string;
  role?: string;
}

interface RegistryReleaseRow {
  release_id: string;
  tag: string;
  kind: string;
  channel: string;
  status: string;
  published_at: string;
  assets: RegistryAssetRow[];
}

interface RegistryFile {
  schema_version: number;
  releases: RegistryReleaseRow[];
}

const REGISTRY = registryData as unknown as RegistryFile;

const ADVERTISED_STATUSES = new Set(['published']);

/** Map registry `kind` to the Manager's product-family view. */
function kindToChannel(kind: string): 'manager' | 'wsa' | null {
  if (kind === 'manager') return 'manager';
  if (kind === 'subsystem') return 'wsa';
  return null;
}

/**
 * Registry rows → the Manager's ReleaseInfo shape. Multiple registry rows
 * legitimately publish under one GitHub tag (Standard + Banking editions);
 * they are grouped so output matches published reality (one release per tag,
 * merged assets).
 */
export function releasesFromRegistry(
  registry: RegistryFile = REGISTRY
): Array<ReleaseInfo & { channel: 'manager' | 'wsa' }> {
  const groups = new Map<string, RegistryReleaseRow[]>();
  for (const r of registry.releases) {
    if (!ADVERTISED_STATUSES.has(r.status) || kindToChannel(r.kind) === null) continue;
    const existing = groups.get(r.tag);
    if (existing) existing.push(r);
    else groups.set(r.tag, [r]);
  }

  const out: Array<ReleaseInfo & { channel: 'manager' | 'wsa' }> =
    [...groups.values()].map((rows) => {
      rows.sort((a, b) => a.release_id.localeCompare(b.release_id));
      return {
        tag_name: rows[0].tag,
        name: rows[0].release_id,
        published_at: rows.map((r) => r.published_at).sort().at(-1) as string,
        body: '',
        channel: kindToChannel(rows[0].kind) as 'manager' | 'wsa',
        assets: rows.flatMap((r) =>
          r.assets.map((a) => ({
            name: a.filename,
            size: a.size_bytes ?? 0,
            browser_download_url: a.source_url,
            architecture: detectArchitecture(a.filename),
            root_flavor: detectRootFlavor(a.filename),
            gapps_flavor: detectGAppsFlavor(a.filename)
          }))
        )
      };
    });

  return out.sort((a, b) => b.published_at.localeCompare(a.published_at));
}

function detectArchitecture(name: string): ReleaseAsset['architecture'] {
  const n = name.toLowerCase();
  if (n.includes('arm64')) return 'arm64';
  if (n.includes('x64')) return 'x64';
  return 'unknown';
}

function detectRootFlavor(name: string): ReleaseAsset['root_flavor'] {
  const n = name.toLowerCase();
  if (n.includes('magisk')) return 'Magisk';
  if (n.includes('kernelsu')) return 'KernelSU';
  if (n.includes('none') || n.includes('noroot') || n.includes('vanilla')) return 'None';
  // WSA Standard Edition archives have no root token in their filename at all
  // (e.g. `WSA_2407.40000.4.0_x64.7z`) — absence of a GApps-pure marker means
  // the rooted build (same documented convention as the website parser).
  if (n.includes('wsa_') && n.endsWith('.7z')) return 'Magisk';
  return 'unknown';
}

function detectGAppsFlavor(name: string): ReleaseAsset['gapps_flavor'] {
  const n = name.toLowerCase();
  if (n.includes('pico')) return 'Pico';
  if (n.includes('mindthegapps')) return 'MindTheGapps';
  if (n.includes('nogapps') || n.includes('no-gapps')) return 'None';
  // WSA release assets ship OpenGApps Pico by default (release.yml build
  // matrix); the Banking Edition is the `vanilla` ramdisk, not GApps-free.
  if (n.includes('wsa_') && n.endsWith('.7z')) return 'Pico';
  return 'unknown';
}

/** Resolve the newest release per product family from the registry. */
export function latestReleasesFromRegistry(
  registry: RegistryFile = REGISTRY
): Record<'manager' | 'wsa', ReleaseInfo | null> {
  const all = releasesFromRegistry(registry);
  const pick = (channel: 'manager' | 'wsa') =>
    all.find((r) => r.channel === channel) ?? null;
  return { manager: pick('manager'), wsa: pick('wsa') };
}
