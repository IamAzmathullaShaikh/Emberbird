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
 * Every asset claim (architecture, root flavor, GApps variant, edition) is
 * read from the registry row that published it — never parsed back out of a
 * filename. The one filename fallback left is for architecture when a row
 * genuinely carries no `arch` truth.
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
  wsa_version?: string;
  edition?: string;
  root_solution?: string;
  gapps_variant?: string;
  architectures?: string[];
  assets: RegistryAssetRow[];
}

interface RegistryFile {
  schema_version: number;
  releases: RegistryReleaseRow[];
}

const REGISTRY = registryData as unknown as RegistryFile;

const ADVERTISED_STATUSES = new Set(['published']);

export type WsaEdition = 'standard' | 'banking';

/**
 * FB-1 — The edition the Observatory recommends by default. This is product
 * policy, deliberately a single named constant: the registry's own
 * `recommended` flag is policy that is currently unset (release-contract §3),
 * so the Manager mirrors the website's documented default (Standard Edition)
 * and only the *version below it* comes from the registry.
 */
export const RECOMMENDED_WSA_EDITION: WsaEdition = 'standard';

/** Map registry `kind` to the Manager's product-family view. */
function kindToChannel(kind: string): 'manager' | 'wsa' | null {
  if (kind === 'manager') return 'manager';
  if (kind === 'subsystem') return 'wsa';
  return null;
}

function toEdition(value: string | undefined): WsaEdition | null {
  return value === 'standard' || value === 'banking' ? value : null;
}

/** Registry row truth → the Manager's flavor vocabulary. */
function rootFlavorOf(row: RegistryReleaseRow): ReleaseAsset['root_flavor'] {
  switch ((row.root_solution ?? '').toLowerCase()) {
    case 'magisk':
      return 'Magisk';
    case 'kernelsu':
      return 'KernelSU';
    case 'none':
      return 'None';
    default:
      return 'unknown';
  }
}

function gappsFlavorOf(row: RegistryReleaseRow): ReleaseAsset['gapps_flavor'] {
  switch ((row.gapps_variant ?? '').toLowerCase()) {
    case 'pico':
      return 'Pico';
    case 'mindthegapps':
      return 'MindTheGapps';
    case 'none':
      return 'None';
    default:
      return 'unknown';
  }
}

function architectureOf(
  row: RegistryReleaseRow,
  asset: RegistryAssetRow
): ReleaseAsset['architecture'] {
  const declared = asset.arch ?? row.architectures?.[0];
  if (declared === 'x64' || declared === 'arm64') return declared;
  // Filename fallback only when the registry carries no architecture truth.
  const n = asset.filename.toLowerCase();
  if (n.includes('arm64')) return 'arm64';
  if (n.includes('x64')) return 'x64';
  return 'unknown';
}

function mapAsset(row: RegistryReleaseRow, asset: RegistryAssetRow): ReleaseAsset {
  return {
    name: asset.filename,
    size: asset.size_bytes ?? 0,
    browser_download_url: asset.source_url,
    architecture: architectureOf(row, asset),
    root_flavor: rootFlavorOf(row),
    gapps_flavor: gappsFlavorOf(row),
    edition: toEdition(row.edition) ?? undefined,
  };
}

/**
 * Registry rows → the Manager's ReleaseInfo shape. Multiple registry rows
 * legitimately publish under one GitHub tag (Standard + Banking editions);
 * they are grouped so output matches published reality (one GitHub release
 * per tag, merged assets) — the same S2 parity rule the website provider
 * applies. The group `name` is display-only; asset identity is
 * (filename, sha256) and edition truth is per-asset.
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
        assets: rows.flatMap((r) => r.assets.map((a) => mapAsset(r, a)))
      };
    });

  return out.sort((a, b) => b.published_at.localeCompare(a.published_at));
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

/**
 * FB-4 — Architectures that actually ship in published WSA registry assets.
 * The UI may only offer filters/guidance for architectures present here —
 * no advertised-but-absent builds.
 */
export function publishedWsaArchitectures(): Array<'x64' | 'arm64'> {
  const archs = new Set<'x64' | 'arm64'>();
  for (const r of releasesFromRegistry()) {
    if (r.channel !== 'wsa') continue;
    for (const a of r.assets) {
      if (a.architecture === 'x64' || a.architecture === 'arm64') archs.add(a.architecture);
    }
  }
  return [...archs];
}

/**
 * FB-3 — Resolve the published package asset to download+stage for an
 * edition ('standard' | 'banking'). Returns the newest published WSA
 * registry row carrying that edition, with its package asset identity
 * (tag, filename, verified hash identity, size). `null` when the registry
 * publishes no such edition — the UI must render that honestly.
 */
export interface EditionAsset {
  release_tag: string;
  edition: WsaEdition;
  release_id: string;
  /** Registry `wsa_version` for the edition (falls back to the tag suffix). */
  wsa_version: string;
  filename: string;
  size_bytes: number;
  source_url: string;
  sha256: string;
  /** Registry root truth for the edition ('magisk' | 'none' | …). */
  root_solution?: string;
  /** Registry GApps truth for the edition ('pico' | 'mindthegapps' | …). */
  gapps_variant?: string;
}

export function resolveEditionAsset(
  edition: string,
  registry: RegistryFile = REGISTRY
): EditionAsset | null {
  const candidates = registry.releases
    .filter(
      (r) =>
        ADVERTISED_STATUSES.has(r.status) &&
        r.kind === 'subsystem' &&
        toEdition(r.edition) === edition &&
        r.assets.some((a) => a.role === 'package')
    )
    .sort((a, b) => b.published_at.localeCompare(a.published_at));

  const chosen = candidates[0];
  if (!chosen) return null;
  const resolvedEdition = toEdition(chosen.edition);
  if (resolvedEdition !== edition) return null;
  const asset = chosen.assets.find((a) => a.role === 'package');
  if (!asset) return null;

  return {
    release_tag: chosen.tag,
    edition: resolvedEdition,
    release_id: chosen.release_id,
    wsa_version: chosen.wsa_version ?? chosen.tag.replace(/^wsa-v/, ''),
    filename: asset.filename,
    size_bytes: asset.size_bytes ?? 0,
    source_url: asset.source_url,
    sha256: asset.sha256,
    root_solution: chosen.root_solution,
    gapps_variant: chosen.gapps_variant
  };
}

/**
 * FB-1 — The release the Observatory recommends: the newest published package
 * for the recommended edition. Registry truth supplies the version; the
 * edition is the named policy constant above.
 */
export function recommendedWsaAsset(registry: RegistryFile = REGISTRY): EditionAsset | null {
  return resolveEditionAsset(RECOMMENDED_WSA_EDITION, registry);
}

/**
 * FB-1 — Human label for the recommended WSA edition, derived from registry
 * truth (no hardcoded version). Falls back to '—' when the registry
 * publishes nothing, so the UI never asserts an unverifiable release.
 */
export function recommendedWsaLabel(): string {
  const asset = recommendedWsaAsset();
  if (!asset) return '—';
  return `${asset.edition === 'banking' ? 'Banking' : 'Standard'} Edition ${asset.wsa_version}`;
}
